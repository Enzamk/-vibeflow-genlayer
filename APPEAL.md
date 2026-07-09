# Appeal — VibeFlow GenLayer-Native Escrow

> **Rejection reason received:**
> *"This cannot be accepted because the reviewed contract did not provide a runnable GenLayer consensus path for the claimed AI escrow resolution. Please update the contract to use supported GenLayer nondeterministic and equivalence-principle patterns."*

Thank you for the precise feedback. The reviewer was correct — the original submission used `gl.ai.prompt()`, a single leader-only LLM call with **no equivalence principle and no validator**. That is not a runnable GenLayer consensus path. I've fixed exactly that.

---

## What was wrong (acknowledged)

The original `resolve_with_ai()` called `gl.ai.prompt()` directly and trusted the leader's answer 100%. There was:

- No `gl.vm.run_nondet_unsafe()` wrapper
- No validator function
- No equivalence principle
- No independent re-execution of the task

In other words: one leader decided alone, and validators had nothing to compare. That fails the core GenLayer consensus requirement, so the rejection was justified.

## What I changed (the fix)

Dispute resolution now runs through GenLayer's **supported nondeterministic + equivalence-principle machinery**:

```python
# contracts/escrow.py — _evaluate_dispute()

def run_eval() -> dict:
    raw = gl.nondet.exec_prompt(prompt, response_format="json")  # real nondet LLM call
    return self._parse_ai_verdict(raw)

def validator_fn(leaders_res: gl.vm.Result) -> bool:
    # Leader errored -> classify and decide whether to agree
    if not isinstance(leaders_res, gl.vm.Return):
        return self._handle_leader_error(leaders_res, run_eval)

    validator_result = run_eval()  # validator INDEPENDENTLY reruns the SAME prompt
    leader = leaders_res.calldata

    # Settlement outcome must converge EXACTLY
    if leader["decision"] != validator_result["decision"]:
        return False

    # For partial refunds, the split must be close (±10 tolerance)
    if leader["decision"] == AI_PARTIAL:
        if abs(int(leader["refund_percentage"]) - int(validator_result["refund_percentage"])) > PCT_TOLERANCE:
            return False

    return True

return gl.vm.run_nondet_unsafe(run_eval, validator_fn)
```

### Why this is a real consensus path

| Requirement | How it's met |
|---|---|
| **Supported nondeterministic call** | `gl.nondet.exec_prompt(prompt, response_format="json")` |
| **Equivalence principle** | `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)` |
| **Validator does NOT trust the leader** | Validator independently reruns the same prompt and compares the substantive `decision` field |
| **Field-level comparison (not schema-only)** | `decision` exact match + `refund_percentage` within ±10 tolerance |
| **Deterministic prompt** | Built from on-chain escrow state via `_build_dispute_prompt()` — leader and validator build the SAME prompt, so the only nondeterminism is the LLM itself |
| **Error classification** | `[EXPECTED]` / `[EXTERNAL]` / `[TRANSIENT]` / `[LLM_ERROR]` prefixes; LLM errors always disagree (force rotation) |
| **LLM resilience** | `_parse_ai_verdict()` accepts dict OR JSON string, aliases keys, coerces types |
| **Pinned runner** | `# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }` (no `test`/`latest` aliases) |

## The full consensus flow

```
resolve_with_ai(payer)
  └─ _evaluate_dispute(escrow)
       └─ gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
            │
            ├─ leader_fn:
            │     gl.nondet.exec_prompt(prompt, response_format="json")
            │     _parse_ai_verdict(raw) -> {decision, refund_percentage, explanation}
            │
            └─ validator_fn(leaders_res):
                  independently reruns the SAME prompt
                  compares:
                    * decision must match EXACTLY (settlement outcome)
                    * refund_percentage within ±10 (partial cases)
                  -> agree ONLY if substantive decision converges
                  -> otherwise consensus fails and rotates/retries
```

This is exactly the pattern the GenLayer documentation recommends for classification/settlement decisions: rerun the task and compare the decision field, rather than trusting the leader's answer or only checking JSON shape.

## Verification

```bash
# Lint
genvm-lint check contracts/escrow.py

# Direct-mode tests (leader path + parsing + settlement)
pytest tests/direct/ -v
```

Direct mode exercises the leader path, defensive parsing, and settlement logic. Validator agreement (the equivalence-principle comparison) is covered by integration tests against a real GenLayer environment, per the GenLayer testing strategy.

## Summary

The rejection was correct: the original contract had no runnable consensus path. I've replaced the single leader-only `gl.ai.prompt()` call with the supported `gl.nondet.exec_prompt()` + `gl.vm.run_nondet_unsafe()` equivalence-principle pattern, where validators independently rerun the dispute evaluation and only agree if the substantive settlement decision converges. The AI escrow resolution is now reproducible across validators instead of trusting one leader's answer.

I'd be grateful for a re-review. Happy to address any further concerns.
