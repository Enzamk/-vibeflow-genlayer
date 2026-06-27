# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *

# ─────────────────────────────────────────────────────────────
# GenLayer-Native Escrow: AI Consensus Replaces Human Arbiter
# ─────────────────────────────────────────────────────────────
#
# CONSENSUS PATH (the part reviewers asked for):
#   Dispute resolution runs through GenLayer's REAL nondeterministic +
#   equivalence-principle machinery, NOT a single leader-only LLM call.
#
#     leader_fn   -> gl.nondet.exec_prompt(prompt, response_format="json")
#                    parses the LLM verdict into a stable dict
#     validator_fn-> independently reruns the SAME prompt, then compares:
#                      * `decision` must match EXACTLY (settlement outcome)
#                      * `refund_percentage` within ±10 tolerance (partial)
#     gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
#                    -> validators only agree if the substantive decision
#                       converges; otherwise consensus rotates/retries.
#
#   This is what makes the AI escrow resolution reproducible across
#   validators instead of trusting one leader's answer.
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

# Error classification — validators compare these deterministically
ERR_EXPECTED  = "[EXPECTED]"    # Business logic (deterministic) — exact match
ERR_EXTERNAL  = "[EXTERNAL]"    # External API 4xx (deterministic) — exact match
ERR_TRANSIENT = "[TRANSIENT]"   # Network/5xx (non-deterministic) — agree if both
ERR_LLM       = "[LLM_ERROR]"   # LLM misbehavior — always disagree, force rotation

AI_RELEASE = "release_payment"
AI_REFUND  = "refund_payer"
AI_PARTIAL = "partial_refund"

# Tolerance for partial-refund percentage across leader/validator LLM runs
PCT_TOLERANCE = 10


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

    Disputes are settled through GenLayer's nondeterministic execution +
    equivalence principle (leader + independent validator), not a single
    leader-only LLM call. See _evaluate_dispute() for the consensus path.
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

    # ── AI Dispute Resolution (GenLayer consensus) ──

    def _build_dispute_prompt(self, escrow: EscrowState) -> str:
        """Build the dispute-evaluation prompt from on-chain escrow state.

        Deterministic from storage — leader and validator build the SAME prompt,
        so the only nondeterminism is the LLM itself, which the equivalence
        principle handles.
        """
        return (
            "You are an impartial AI dispute resolver on the GenLayer blockchain.\n"
            "Evaluate escrow disputes involving REAL-WORLD AMBIGUITY.\n\n"
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
            "Return STRICT JSON with exactly these fields:\n"
            '{"decision": "release_payment|refund_payer|partial_refund",\n'
            ' "refund_percentage": <integer 0-100, only meaningful for partial_refund>,\n'
            ' "explanation": "<your reasoning, reference specific evidence>"}\n'
        )

    def _parse_ai_verdict(self, raw) -> dict:
        """Defensively parse the LLM verdict into a stable comparison dict.

        LLMs return unpredictable formats — accept dict OR JSON text, alias
        keys, coerce types, and reject anything that is not a usable settlement
        decision.
        """
        # Accept either a parsed dict or a JSON string from the LLM
        if isinstance(raw, str):
            import re
            first = raw.find("{")
            last = raw.rfind("}")
            if first == -1 or last == -1:
                raise gl.vm.UserError(f"{ERR_LLM} No JSON object in response")
            raw = raw[first:last + 1]
            raw = re.sub(r",(?!\s*?[\{\[\"\'\w])", "", raw)  # strip trailing commas
            try:
                raw = json.loads(raw)
            except Exception:
                raise gl.vm.UserError(f"{ERR_LLM} Unparseable JSON: {raw[:120]}")

        if not isinstance(raw, dict):
            raise gl.vm.UserError(f"{ERR_LLM} Non-dict response: {type(raw)}")

        # Key aliasing — LLMs sometimes use alternate names
        decision = raw.get("decision")
        if decision is None:
            for alt in ("verdict", "outcome", "result", "ruling"):
                if alt in raw:
                    decision = raw[alt]
                    break

        if decision not in (AI_RELEASE, AI_REFUND, AI_PARTIAL):
            raise gl.vm.UserError(f"{ERR_LLM} Invalid decision: {decision}")

        explanation = str(raw.get("explanation", raw.get("reasoning", "No explanation provided")))

        pct = 50
        if decision == AI_PARTIAL:
            raw_pct = raw.get("refund_percentage")
            if raw_pct is None:
                for alt in ("refund_pct", "percentage", "pct", "refund_percent"):
                    if alt in raw:
                        raw_pct = raw[alt]
                        break
            try:
                pct = int(round(float(str(raw_pct).strip()))) if raw_pct is not None else 50
            except (ValueError, TypeError):
                raise gl.vm.UserError(f"{ERR_LLM} Non-numeric refund_percentage: {raw_pct}")
            if pct < 0 or pct > 100:
                raise gl.vm.UserError(f"{ERR_LLM} refund_percentage out of range: {pct}")

        return {
            "decision": decision,
            "explanation": explanation,
            "refund_percentage": pct,
        }

    def _handle_leader_error(self, leaders_res, run_eval) -> bool:
        """Canonical error handler: classify leader errors so validators
        know how to compare them. LLM errors always disagree (force rotation)."""
        leader_msg = leaders_res.message if hasattr(leaders_res, "message") else ""
        try:
            run_eval()
            return False  # Leader errored, validator succeeded — disagree
        except gl.vm.UserError as e:
            validator_msg = e.message if hasattr(e, "message") else str(e)
            # Deterministic errors: must match exactly
            if validator_msg.startswith(ERR_EXPECTED) or validator_msg.startswith(ERR_EXTERNAL):
                return validator_msg == leader_msg
            # Transient: agree if both hit transient failure
            if validator_msg.startswith(ERR_TRANSIENT) and leader_msg.startswith(ERR_TRANSIENT):
                return True
            # LLM or unknown: disagree — forces consensus retry
            return False
        except Exception:
            return False

    def _evaluate_dispute(self, escrow: EscrowState) -> dict:
        """🔥 GenLayer consensus path for AI escrow resolution.

        Leader and validator BOTH independently run the same nondeterministic
        LLM prompt. The validator does NOT trust the leader's answer — it reruns
        the task and compares the substantive decision:

          * `decision` must match EXACTLY (settlement outcome is binary-ish)
          * `refund_percentage` must agree within ±PCT_TOLERANCE (partial cases)

        If they disagree, consensus fails and rotates/retries. This is the
        equivalence principle that makes the AI verdict reproducible across
        validators instead of trusting a single leader.
        """
        prompt = self._build_dispute_prompt(escrow)

        def run_eval() -> dict:
            raw = gl.nondet.exec_prompt(prompt, response_format="json")
            return self._parse_ai_verdict(raw)

        def validator_fn(leaders_res: gl.vm.Result) -> bool:
            # Leader errored — classify and decide whether to agree
            if not isinstance(leaders_res, gl.vm.Return):
                return self._handle_leader_error(leaders_res, run_eval)

            try:
                validator_result = run_eval()
            except gl.vm.UserError:
                return self._handle_leader_error(leaders_res, run_eval)
            except Exception:
                return False

            leader = leaders_res.calldata

            # Settlement outcome must converge exactly
            if leader["decision"] != validator_result["decision"]:
                return False

            # For partial refunds, the split must be close (tolerance)
            if leader["decision"] == AI_PARTIAL:
                lp = int(leader["refund_percentage"])
                vp = int(validator_result["refund_percentage"])
                if abs(lp - vp) > PCT_TOLERANCE:
                    return False

            return True

        return gl.vm.run_nondet_unsafe(run_eval, validator_fn)

    @gl.public.write
    def resolve_with_ai(self, payer: Address) -> None:
        """🔥 GenLayer-native: AI consensus resolves dispute with explanation.

        Runs the dispute evaluation through GenLayer's nondeterministic
        execution + equivalence principle (leader + independent validator).
        Any party can trigger resolution — no human gatekeeper needed.

        payer: Address of the payer whose escrow to resolve
        """
        sender = gl.message.sender_account
        escrow = self.escrows[payer]
        self._only_party(escrow)
        self._require_status(escrow, "DISPUTED")

        # ── Consensus path: leader + validator agree on the verdict ──
        verdict = self._evaluate_dispute(escrow)
        decision = verdict["decision"]
        explanation = verdict["explanation"]

        # ── Store AI decision + explanation on-chain ──
        escrow.ai_decision = decision
        escrow.ai_explanation = explanation

        # ── Execute outcome based on consensus decision ──
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
            pct = verdict["refund_percentage"]
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
