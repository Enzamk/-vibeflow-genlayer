# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *

# ─────────────────────────────────────────────────────────────
# GenLayer-Native Escrow: AI Consensus Replaces Human Arbiter
# ─────────────────────────────────────────────────────────────
#
# TRADITIONAL ESCROW (Ethereum/Solidity):
#   payer → payee → human arbiter
#   - Arbiter decides: release or refund (deterministic boolean)
#   - Arbiter can be: bribed, absent, biased, expensive
#   - "Was work completed?" → code CANNOT answer this
#   - No on-chain explanation for WHY a decision was made
#
# GENLAYER ESCROW (this contract):
#   payer → payee → AI consensus
#   - Both parties submit evidence on-chain
#   - AI evaluates evidence through validator consensus
#   - Decision + explanation stored permanently on-chain
#   - "Was work completed?" → AI CAN answer, with reasoning
#   - No human gatekeeper — any party can trigger resolution
#
# State Machine:
#   FUNDED → RELEASED       (payer approves — happy path)
#   FUNDED → CANCELLED      (payer cancels — refund path)
#   FUNDED → DISPUTED → RELEASED  (AI: release_payment)
#   FUNDED → DISPUTED → CANCELLED (AI: refund_payer)
#   FUNDED → DISPUTED → RELEASED  (AI: partial_refund — split)
# ─────────────────────────────────────────────────────────────

EVT_DEPOSIT    = "DEPOSIT"
EVT_APPROVE    = "APPROVE"
EVT_CANCEL     = "CANCEL"
EVT_DISPUTE    = "DISPUTE"
EVT_EVIDENCE   = "EVIDENCE"
EVT_AI_RESOLVE = "AI_RESOLVE"

ERR_EXPECTED = "[EXPECTED]"
ERR_EXTERNAL = "[EXTERNAL]"

AI_RELEASE = "release_payment"
AI_REFUND  = "refund_payer"
AI_PARTIAL = "partial_refund"


@allow_storage
@dataclass
class EventLog:
    """Single on-chain event entry."""
    name: str
    data: str
    block_time: str


@allow_storage
@dataclass
class EscrowState:
    """Full state of one escrow agreement — NO arbiter field.
    AI consensus replaces the human arbiter entirely."""
    payer: Address
    payee: Address
    amount: u256
    status: str                     # FUNDED | DISPUTED | RELEASED | CANCELLED
    released_amount: u256
    dispute_reason: str
    payer_evidence: str             # JSON evidence submitted by payer
    payee_evidence: str             # JSON evidence submitted by payee
    created_at: str
    ai_decision: str                # release_payment | refund_payer | partial_refund
    ai_explanation: str             # AI reasoning — stored on-chain for transparency
    partial_refund_pct: u256        # 0-100 percentage for partial refunds


class Escrow(gl.Contract):
    """GenLayer-native escrow: AI consensus replaces human arbiter.

    Traditional escrow on Ethereum: payer → payee → human arbiter (deterministic yes/no)
    GenLayer escrow: payer → payee → AI consensus (evaluates real-world ambiguity)

    The key difference: "Was work completed?" can't be answered by code.
    GenLayer's AI consensus handles exactly this kind of question.
    """

    # ── Storage ──────────────────────────────────────
    escrows: TreeMap[Address, EscrowState]
    events: DynArray[EventLog]
    fee_bp: u256                     # basis points (e.g. 50 = 0.5 %)

    # ── Init ────────────────────────────────────────

    def __init__(self, fee_basis_points: u256):
        self.fee_bp = fee_basis_points
        self._log_event(EVT_DEPOSIT, '{"action":"deploy","fee_bp":"' + str(fee_basis_points) + '"}')

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
        """Check caller is payer or payee — NO arbiter check.
        In GenLayer-native escrow, only the two transacting parties matter."""
        sender = gl.message.sender_account
        if sender not in (escrow.payer, escrow.payee):
            raise gl.UserError(f"{ERR_EXPECTED} Not a party to this escrow")

    def _require_status(self, escrow: EscrowState, expected: str) -> None:
        if escrow.status != expected:
            raise gl.UserError(f"{ERR_EXPECTED} Expected status {expected}, got {escrow.status}")

    # ── Public view methods ─────────────────────────

    @gl.public.view
    def get_escrow(self, payer: Address) -> dict:
        """Return full escrow state — includes evidence + AI explanation."""
        e = self.escrows[payer]
        return {
            "payer": str(e.payer),
            "payee": str(e.payee),
            "amount": str(e.amount),
            "status": e.status,
            "released_amount": str(e.released_amount),
            "dispute_reason": e.dispute_reason,
            "payer_evidence": e.payer_evidence,
            "payee_evidence": e.payee_evidence,
            "created_at": e.created_at,
            "ai_decision": e.ai_decision,
            "ai_explanation": e.ai_explanation,
            "partial_refund_pct": str(e.partial_refund_pct),
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
    def deposit(self, payee: Address) -> None:
        """Payer deposits native tokens to fund an escrow.
        No arbiter parameter — AI consensus handles disputes."""
        sender = gl.message.sender_account
        amount = gl.message.value

        if amount == 0:
            raise gl.UserError(f"{ERR_EXPECTED} Zero deposit not allowed")
        if payee == sender:
            raise gl.UserError(f"{ERR_EXPECTED} Payer cannot be payee")
        if sender in self.escrows:
            raise gl.UserError(f"{ERR_EXPECTED} Payer already has an active escrow")

        self.escrows[sender] = EscrowState(
            payer=sender,
            payee=payee,
            amount=amount,
            status="FUNDED",
            released_amount=u256(0),
            dispute_reason="",
            payer_evidence="",
            payee_evidence="",
            created_at=gl.block.time.isoformat(),
            ai_decision="",
            ai_explanation="",
            partial_refund_pct=u256(0),
        )

        self._log_event(EVT_DEPOSIT, '{{"payer":"{}","payee":"{}","amount":"{}"}}'.format(sender, payee, amount))

    @gl.public.write
    def approve(self) -> None:
        """Payer releases funds to payee (minus fee). Happy path."""
        sender = gl.message.sender_account
        escrow = self.escrows[sender]
        self._only_payer(escrow)
        self._require_status(escrow, "FUNDED")

        fee = (escrow.amount * self.fee_bp) // u256(10000)
        release = escrow.amount - fee

        escrow.status = "RELEASED"
        escrow.released_amount = release

        gl.transfer(escrow.payee, release, on="accepted")
        if fee > 0:
            gl.transfer(gl.message.contract_address, fee, on="accepted")

        self._log_event(EVT_APPROVE, '{{"payee":"{}","amount":"{}","fee":"{}"}}'.format(escrow.payee, release, fee))

    @gl.public.write
    def cancel(self) -> None:
        """Payer cancels escrow and gets full refund. Only before dispute."""
        sender = gl.message.sender_account
        escrow = self.escrows[sender]
        self._only_payer(escrow)
        self._require_status(escrow, "FUNDED")

        escrow.status = "CANCELLED"
        gl.transfer(escrow.payer, escrow.amount, on="accepted")

        self._log_event(EVT_CANCEL, '{{"payer":"{}","amount":"{}"}}'.format(escrow.payer, escrow.amount))

    # ── Dispute & Evidence (GenLayer-native) ────────

    @gl.public.write
    def raise_dispute(self, payer: Address, reason: str) -> None:
        """Any party raises a dispute. No arbiter — AI consensus will resolve.

        Traditional escrow: dispute → human arbiter (deterministic yes/no)
        GenLayer escrow:    dispute → evidence → AI evaluation → consensus

        payer: Address of the payer whose escrow to dispute
        reason: Human-readable dispute reason
        """
        sender = gl.message.sender_account
        escrow = self.escrows[payer]
        self._only_party(escrow)
        self._require_status(escrow, "FUNDED")

        escrow.status = "DISPUTED"
        escrow.dispute_reason = reason

        self._log_event(EVT_DISPUTE, '{{"party":"{}","payer":"{}","reason":"{}"}}'.format(sender, payer, reason))

    @gl.public.write
    def submit_evidence(self, payer: Address, evidence: str) -> None:
        """Submit evidence during dispute. Both parties present their side on-chain.

        This is critical for GenLayer's AI evaluation:
        - Payer: "Work wasn't completed, here's my proof"
        - Payee: "Work was completed, here's delivery confirmation"
        - AI sees BOTH sides and makes a fair judgment

        Traditional blockchains can't do this — single arbiter sees only what they choose.

        payer:    Address of the payer whose escrow this evidence belongs to
        evidence: JSON string describing this party's evidence
        """
        sender = gl.message.sender_account
        escrow = self.escrows[payer]
        self._only_party(escrow)
        self._require_status(escrow, "DISPUTED")

        if sender == escrow.payer:
            escrow.payer_evidence = evidence
        elif sender == escrow.payee:
            escrow.payee_evidence = evidence

        role = "payer" if sender == escrow.payer else "payee"
        self._log_event(EVT_EVIDENCE, '{{"party":"{}","payer":"{}","role":"{}","evidence":"{}"}}'.format(
            sender, payer, role, evidence))

    @gl.public.write
    def resolve_with_ai(self, payer: Address) -> None:
        """🔥 GenLayer-native: AI consensus resolves dispute with explanation.

        THIS IS WHY GENLAYER IS DIFFERENT FROM TRADITIONAL BLOCKCHAINS.

        Traditional blockchain escrow:
          → Human arbiter clicks "release" or "refund" (deterministic boolean)
          → Arbiter can be bribed, absent, or biased
          → No explanation stored on-chain
          → "Was work completed?" → code can't answer this

        GenLayer escrow:
          → AI evaluates BOTH parties' evidence through consensus
          → Multiple validators run the same AI prompt
          → Consensus converges on majority decision
          → Full explanation stored on-chain (transparent, auditable)
          → "Was work completed?" → AI CAN answer this

        Any party can trigger resolution — no human gatekeeper needed.

        payer: Address of the payer whose escrow to resolve
        """
        sender = gl.message.sender_account
        escrow = self.escrows[payer]
        self._only_party(escrow)
        self._require_status(escrow, "DISPUTED")

        # ── AI Prompt: designed for real-world ambiguity ──
        # This prompt asks questions that traditional code CANNOT answer.
        # "Was work completed?" is subjective — it requires judgment, not boolean logic.
        prompt = (
            "You are an impartial AI dispute resolver on the GenLayer blockchain.\n"
            "Your job: evaluate escrow disputes involving REAL-WORLD AMBIGUITY.\n\n"
            "Traditional smart contracts can only check deterministic conditions:\n"
            "  - 'Was a hash submitted?' → yes/no → code can check\n"
            "  - 'Was work completed satisfactorily?' → subjective → code CANNOT check\n\n"
            "GenLayer solves this through AI consensus. You evaluate evidence from\n"
            "both parties and make a fair judgment — transparent, unbiased, with\n"
            "on-chain explanation that anyone can verify.\n\n"
            "=== DISPUTE CASE ===\n"
            f"Escrow amount: {escrow.amount} atto units\n"
            f"Dispute reason: {escrow.dispute_reason}\n\n"
            "=== PAYER'S EVIDENCE (party who funded the escrow) ===\n"
            f"{escrow.payer_evidence if escrow.payer_evidence else 'No evidence submitted by payer'}\n\n"
            "=== PAYEE'S EVIDENCE (party who was to receive payment) ===\n"
            f"{escrow.payee_evidence if escrow.payee_evidence else 'No evidence submitted by payee'}\n\n"
            "=== EVALUATION CRITERIA ===\n"
            "1. Evidence strength: Which party provided stronger, more specific evidence?\n"
            "2. Relevance: Does the evidence address the dispute reason?\n"
            "3. Corroboration: Receipts, confirmations, timestamps?\n"
            "4. Contradictions: Gaps or inconsistencies in either side?\n"
            "5. Fairness: What would a reasonable person conclude?\n\n"
            "=== POSSIBLE DECISIONS ===\n"
            "- release_payment: Payee deserves full payment\n"
            "- refund_payer: Payer deserves full refund\n"
            "- partial_refund: Both have partial claims (specify refund_percentage 0-100)\n\n"
            "You MUST explain your reasoning clearly. Your explanation will be stored\n"
            "on-chain permanently — reference specific evidence, explain why you weighted\n"
            "certain factors more, and justify the outcome. This transparency is what\n"
            "makes GenLayer different: every AI decision has a traceable, on-chain\n"
            "explanation that anyone can audit."
        )

        # ── Call GenLayer AI oracle — validators reach consensus ──
        # This is the key GenLayer differentiator: non-deterministic execution
        # where validators use AI to evaluate ambiguous real-world questions.
        ai_result = gl.ai.prompt(
            prompt,
            json_schema={
                "type": "object",
                "properties": {
                    "decision": {
                        "type": "string",
                        "enum": ["release_payment", "refund_payer", "partial_refund"]
                    },
                    "refund_percentage": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "explanation": {
                        "type": "string"
                    },
                    "evidence_assessment": {
                        "type": "object",
                        "properties": {
                            "payer_evidence_strength": {
                                "type": "string",
                                "enum": ["strong", "moderate", "weak", "none"]
                            },
                            "payee_evidence_strength": {
                                "type": "string",
                                "enum": ["strong", "moderate", "weak", "none"]
                            },
                            "key_factors": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["payer_evidence_strength", "payee_evidence_strength", "key_factors"]
                    }
                },
                "required": ["decision", "explanation", "evidence_assessment"]
            }
        )

        decision = ai_result["decision"]
        explanation = ai_result.get("explanation", "No explanation provided")

        # ── Validate AI decision ──
        if decision not in [AI_RELEASE, AI_REFUND, AI_PARTIAL]:
            raise gl.UserError(f"{ERR_EXTERNAL} AI returned invalid decision: {decision}")

        # ── Store AI decision + explanation on-chain ──
        # This is the transparency differentiator — every decision has a traceable reason.
        escrow.ai_decision = decision
        escrow.ai_explanation = explanation

        # ── Execute outcome based on AI decision ──
        if decision == AI_RELEASE:
            fee = (escrow.amount * self.fee_bp) // u256(10000)
            release = escrow.amount - fee
            escrow.status = "RELEASED"
            escrow.released_amount = release
            gl.transfer(escrow.payee, release, on="accepted")
            if fee > 0:
                gl.transfer(gl.message.contract_address, fee, on="accepted")
            self._log_event(EVT_AI_RESOLVE, '{{"decision":"release_payment","payee":"{}","amount":"{}","fee":"{}","explanation":"{}"}}'.format(
                escrow.payee, release, fee, explanation))

        elif decision == AI_REFUND:
            escrow.status = "CANCELLED"
            gl.transfer(escrow.payer, escrow.amount, on="accepted")
            self._log_event(EVT_AI_RESOLVE, '{{"decision":"refund_payer","payer":"{}","amount":"{}","explanation":"{}"}}'.format(
                escrow.payer, escrow.amount, explanation))

        elif decision == AI_PARTIAL:
            pct = ai_result.get("refund_percentage", 50)
            if pct < 0 or pct > 100:
                pct = 50  # fallback to equal split if AI gives invalid percentage
            escrow.partial_refund_pct = u256(pct)

            payer_refund = (escrow.amount * u256(pct)) // u256(100)
            payee_portion = escrow.amount - payer_refund
            fee = (payee_portion * self.fee_bp) // u256(10000)
            payee_net = payee_portion - fee

            escrow.status = "RELEASED"
            escrow.released_amount = payee_net

            gl.transfer(escrow.payer, payer_refund, on="accepted")
            gl.transfer(escrow.payee, payee_net, on="accepted")
            if fee > 0:
                gl.transfer(gl.message.contract_address, fee, on="accepted")

            self._log_event(EVT_AI_RESOLVE, '{{"decision":"partial_refund","payer":"{}","payer_amount":"{}","payee":"{}","payee_amount":"{}","fee":"{}","pct":"{}","explanation":"{}"}}'.format(
                escrow.payer, payer_refund, escrow.payee, payee_net, fee, pct, explanation))

    # ── Admin ─────────────────────────────────────

    @gl.public.write
    def collect_fees(self) -> None:
        """Collect accumulated fees from contract balance."""
        balance = gl.contract_balance
        if balance > 0:
            gl.transfer(gl.message.sender_account, balance, on="accepted")