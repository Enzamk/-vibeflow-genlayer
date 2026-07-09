# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
import re
from dataclasses import dataclass
from genlayer import *

# ─────────────────────────────────────────────────────────────
# AI-Assisted Decision Contract (GenLayer-Native) — MINIMAL
# ─────────────────────────────────────────────────────────────
#
# The simplest GenLayer intelligent contract that WORKS:
#   1. Input  → a string (task description / question)
#   2. AI     → evaluates through GenLayer consensus
#   3. Output → "approved" or "rejected" — saved on-chain
#
# ⚠️  NO token transfers, NO balances, NO msg.sender,
#     NO custom errors, NO escrow logic.
#
# CONSENSUS PATH (required by GenLayer):
#   evaluate() runs gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
#     leader_fn   -> gl.nondet.exec_prompt(prompt, response_format="json")
#     validator_fn -> independently reruns the SAME prompt, compares
#                     the `decision` field EXACTLY
# ─────────────────────────────────────────────────────────────


@allow_storage
@dataclass
class Task:
    """One submitted task + its AI decision. No money, no sender."""
    description: str
    decision: str          # approved | rejected
    explanation: str       # AI reasoning — stored on-chain


class AIDecisionContract(gl.Contract):
    """Minimal AI-assisted decision contract.

    Input a string → AI consensus evaluates → decision saved on-chain.
    """

    # ── Storage ──────────────────────────────────────
    tasks: TreeMap[u256, Task]
    next_id: u256

    # ── Init ────────────────────────────────────────

    def __init__(self):
        self.next_id = u256(1)

    # ── AI Evaluation (GenLayer consensus) ──────────

    def _build_prompt(self, description: str) -> str:
        """Build the evaluation prompt. Deterministic — leader and
        validator build the SAME prompt from the same input."""
        return (
            "You are an impartial AI evaluator on the GenLayer blockchain.\n"
            "Evaluate the following task and decide whether to approve or reject it.\n\n"
            "=== TASK ===\n"
            f"{description}\n\n"
            "=== CRITERIA ===\n"
            "1. Is the task clear and well-defined?\n"
            "2. Is it reasonable and feasible?\n"
            "3. Is there enough detail to evaluate?\n\n"
            "Return STRICT JSON:\n"
            '{"decision": "approved|rejected", "explanation": "<your reasoning>"}\n'
        )

    def _parse_verdict(self, raw) -> dict:
        """Parse the LLM response into a stable dict.
        Handles dict OR JSON string, aliases keys, coerces types."""
        if isinstance(raw, str):
            first = raw.find("{")
            last = raw.rfind("}")
            if first == -1 or last == -1:
                raise gl.vm.UserError("No JSON in response")
            raw = raw[first:last + 1]
            raw = re.sub(r",(?!\s*?[\{\[\"\'\w])", "", raw)
            raw = json.loads(raw)

        if not isinstance(raw, dict):
            raise gl.vm.UserError("Non-dict response")

        decision = raw.get("decision")
        if decision is None:
            for alt in ("verdict", "outcome", "result", "ruling"):
                if alt in raw:
                    decision = raw[alt]
                    break

        # Robust normalization: handle case variations + common aliases
        # e.g. "APPROVED", "Approved", "yes", "approve" -> "approved"
        decision_raw = str(decision).lower().strip()
        if "approve" in decision_raw or decision_raw in ("yes", "accept", "pass", "true", "1"):
            decision = "approved"
        elif "reject" in decision_raw or decision_raw in ("no", "deny", "fail", "false", "0"):
            decision = "rejected"
        else:
            raise gl.vm.UserError("Invalid decision: " + str(decision))

        explanation = str(raw.get("explanation", raw.get("reasoning", "")))

        return {"decision": decision, "explanation": explanation}

    def _evaluate(self, description: str) -> dict:
        """Run AI evaluation through GenLayer's nondeterministic consensus.

        leader_fn    -> calls the LLM and parses the verdict
        validator_fn -> independently reruns the SAME prompt and compares
                        the `decision` field EXACTLY
        """
        prompt = self._build_prompt(description)

        def run() -> dict:
            raw = gl.nondet.exec_prompt(prompt, response_format="json")
            return self._parse_verdict(raw)

        def validator_fn(leaders_res: gl.vm.Result) -> bool:
            # If leader errored, disagree (forces rotation/retry)
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            # Validator independently reruns the SAME prompt
            validator_result = run()
            # Decision must converge EXACTLY
            return leaders_res.calldata["decision"] == validator_result["decision"]

        return gl.vm.run_nondet_unsafe(run, validator_fn)

    # ── Public methods ───────────────────────────────

    @gl.public.write
    def evaluate(self, description: str) -> str:
        """Submit a task, AI evaluates it, decision is saved on-chain.

        Returns: "approved" or "rejected"
        """
        if len(description) == 0:
            raise gl.vm.UserError("Description cannot be empty")

        # Run AI evaluation through GenLayer consensus
        verdict = self._evaluate(description)

        # Save result on-chain
        task_id = self.next_id
        self.next_id = task_id + u256(1)
        self.tasks[task_id] = Task(
            description=description,
            decision=verdict["decision"],
            explanation=verdict["explanation"],
        )

        return verdict["decision"]

    @gl.public.view
    def get_task(self, task_id: u256) -> dict:
        """Read a task's decision + explanation from on-chain storage."""
        t = self.tasks[task_id]
        return {
            "task_id": str(task_id),
            "description": t.description,
            "decision": t.decision,
            "explanation": t.explanation,
        }

    @gl.public.view
    def get_task_count(self) -> u256:
        """Total tasks evaluated."""
        return self.next_id - u256(1)
