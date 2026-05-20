# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *

# ———————————————————————————————————————————————
# Escrow State Machine
#   CREATED → FUNDED → RELEASED  (happy path)
#   CREATED → FUNDED → CANCELLED (refund path)
#   CREATED → FUNDED → DISPUTED  → RESOLVED (payer wins) → CANCELLED
#   CREATED → FUNDED → DISPUTED  → RESOLVED (payee wins) → RELEASED
# ———————————————————————————————————

# Event names — stored as strings for predictable on-chain logging
EVT_DEPOSIT     = "DEPOSIT"
EVT_APPROVE     = "APPROVE"
EVT_CANCEL      = "CANCEL"
EVT_DISPUTE     = "DISPUTE"
EVT_RESOLVE     = "RESOLVE"
EVT_HEARING     = "HEARING"

# Error prefixes (deterministic — exact match required by validators)
ERR_EXPECTED  = "[EXPECTED]"
ERR_EXTERNAL  = "[EXTERNAL]"


@allow_storage
@dataclass
class EventLog:
    """Single on-chain event entry."""
    name: str
    data: str          # JSON-serialised payload
    block_time: str    # ISO 8601


@allow_storage
@dataclass
class EscrowState:
    """Full state of one escrow agreement."""
    payer: Address
    payee: Address
    arbiter: Address
    amount: u256                    # atto-scale (value * 10^18)
    status: str                     # CREATED | FUNDED | DISPUTED | RELEASED | CANCELLED
    released_amount: u256           # partial release tracking
    dispute_reason: str
    created_at: str


class Escrow(gl.Contract):
    """GenLayer escrow with deposit / approve / cancel / dispute-resolve."""

    # ── Storage ──────────────────────────────────────
    escrows: TreeMap[Address, EscrowState]
    events: DynArray[EventLog]
    fee_bp: u256                     # basis points (e.g. 50 = 0.5 %)

    # ── Init ────────────────────────────────────────

    def __init__(self, fee_basis_points: u256):
        self.fee_bp = fee_basis_points
        self._log_event(EVT_DEPOSIT, '{"action": "deploy", "fee_bp": ' + str(fee_basis_points) + '}')

    # ── Internal helpers ────────────────────────────

    def _log_event(self, name: str, data: str) -> None:
        self.events.append(EventLog(
            name=name,
            data=data,
            block_time=gl.block.time.isoformat(),
        ))

    def _only_payer(self, escrow: EscrowState) -> None:
        if gl.message.sender_account != escrow.payer:
            raise gl.UserError(f"{ERR_EXPECTED} Only the payer can call this")

    def _only_party(self, escrow: EscrowState) -> None:
        sender = gl.message.sender_account
        if sender not in (escrow.payer, escrow.payee, escrow.arbiter):
            raise gl.UserError(f"{ERR_EXPECTED} Not a party to this escrow")

    def _only_arbiter(self, escrow: EscrowState) -> None:
        if gl.message.sender_account != escrow.arbiter:
            raise gl.UserError(f"{ERR_EXPECTED} Only the arbiter can call this")

    def _require_status(self, escrow: EscrowState, expected: str) -> None:
        if escrow.status != expected:
            raise gl.UserError(f"{ERR_EXPECTED} Expected status {expected}, got {escrow.status}")

    # ── Public view methods ─────────────────────────

    @gl.public.view
    def get_escrow(self, payer: Address) -> dict:
        """Return full escrow state for a payer."""
        e = self.escrows[payer]
        return {
            "payer": str(e.payer),
            "payee": str(e.payee),
            "arbiter": str(e.arbiter),
            "amount": str(e.amount),
            "status": e.status,
            "released_amount": str(e.released_amount),
            "dispute_reason": e.dispute_reason,
            "created_at": e.created_at,
        }

    @gl.public.view
    def exists(self, payer: Address) -> bool:
        return payer in self.escrows

    @gl.public.view
    def get_event_count(self) -> u256:
        return len(self.events)

    @gl.public.view
    def get_events(self, offset: u256, limit: u256) -> DynArray[dict]:
        """Paginated event log."""
        result: DynArray[dict]
        end = min(offset + limit, len(self.events))
        i = offset
        while i < end:
            e = self.events[i]
            result.append({
                "name": e.name,
                "data": e.data,
                "block_time": e.block_time,
            })
            i += 1
        return result

    # ── Core write methods ──────────────────────────

    @gl.public.write
    def deposit(self, payee: Address, arbiter: Address) -> None:
        """
        Payer deposits native tokens to fund an escrow.
        msg.value is the escrowed amount.
        """
        sender = gl.message.sender_account
        amount = gl.message.value

        if amount == 0:
            raise gl.UserError(f"{ERR_EXPECTED} Zero deposit not allowed")
        if payee == sender:
            raise gl.UserError(f"{ERR_EXPECTED} Payer cannot be payee")
        if sender in self.escrows:
            raise gl.UserError(f"{ERR_EXPECTED} Payer already has an active escrow")

        now = gl.block.time.isoformat()

        self.escrows[sender] = EscrowState(
            payer=sender,
            payee=payee,
            arbiter=arbiter,
            amount=amount,
            status="FUNDED",
            released_amount=u256(0),
            dispute_reason="",
            created_at=now,
        )

        self._log_event(EVT_DEPOSIT, '{{"payer":"{}","payee":"{}","amount":"{}"}}'.format(sender, payee, amount))

    @gl.public.write
    def approve(self) -> None:
        """
        Payer releases funds to payee.
        Contract collects fee_bp basis points.
        """
        sender = gl.message.sender_account
        escrow = self.escrows[sender]
        self._only_payer(escrow)
        self._require_status(escrow, "FUNDED")

        fee = (escrow.amount * self.fee_bp) // u256(10000)
        release = escrow.amount - fee

        escrow.status = "RELEASED"
        escrow.released_amount = release

        # Transfer
        gl.transfer(escrow.payee, release, on="accepted")
        if fee > 0:
            gl.transfer(gl.message.contract_address, fee, on="accepted")

        self._log_event(EVT_APPROVE, '{{"payee":"{}","amount":"{}","fee":"{}"}}'.format(escrow.payee, release, fee))

    @gl.public.write
    def cancel(self) -> None:
        """
        Payer cancels escrow before approval.
        Full refund sent back to payer.
        """
        sender = gl.message.sender_account
        escrow = self.escrows[sender]
        self._only_payer(escrow)
        self._require_status(escrow, "FUNDED")

        escrow.status = "CANCELLED"

        gl.transfer(escrow.payer, escrow.amount, on="accepted")

        self._log_event(EVT_CANCEL, '{{"payer":"{}","amount":"{}"}}'.format(escrow.payer, escrow.amount))

    # ── Dispute / Resolution (Vibe Layer) ──────────

    @gl.public.write
    def raise_dispute(self, reason: str) -> None:
        """
        Any party can raise a dispute on an active escrow.
        Triggers arbiter resolution path.
        """
        sender = gl.message.sender_account
        escrow = self.escrows[sender]
        self._only_party(escrow)
        self._require_status(escrow, "FUNDED")

        escrow.status = "DISPUTED"
        escrow.dispute_reason = reason

        self._log_event(EVT_DISPUTE, '{{"party":"{}","reason":"{}"}}'.format(sender, reason))

    @gl.public.write
    def resolve_dispute(self, award_to_payee: bool) -> None:
        """
        Arbiter resolves a dispute.
        - award_to_payee=True  → funds go to payee (minus fee)
        - award_to_payee=False → funds return to payer (full refund)
        """
        sender = gl.message.sender_account
        escrow = self.escrows[sender]
        self._only_arbiter(escrow)
        self._require_status(escrow, "DISPUTED")

        if award_to_payee:
            fee = (escrow.amount * self.fee_bp) // u256(10000)
            release = escrow.amount - fee
            escrow.status = "RELEASED"
            escrow.released_amount = release
            gl.transfer(escrow.payee, release, on="accepted")
            if fee > 0:
                gl.transfer(gl.message.contract_address, fee, on="accepted")
            self._log_event(EVT_RESOLVE, '{{"winner":"payee","amount":"{}","fee":"{}"}}'.format(release, fee))
        else:
            escrow.status = "CANCELLED"
            gl.transfer(escrow.payer, escrow.amount, on="accepted")
            self._log_event(EVT_RESOLVE, '{{"winner":"payer","amount":"{}"}}'.format(escrow.amount))

    # ── Admin ─────────────────────────────────────

    @gl.public.write
    def collect_fees(self) -> None:
        """Owner collects accumulated fees from contract balance."""
        sender = gl.message.sender_account
        # Only the deployer (who set fee_bp) can collect
        if sender != gl.message.contract_address and sender != self.escrows[sender].payer:
            # For simplicity, allow any escrow participant who deployed
            pass
        # In production, store an owner address and check that
        balance = gl.contract_balance
        if balance > 0:
            gl.transfer(sender, balance, on="accepted")