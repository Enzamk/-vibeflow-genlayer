# Re-review Clarification

Thank you for the earlier review. The repository previously emphasized an experimental AI escrow prototype, which made the submitted scope ambiguous.

## Canonical submission

The only contract submitted for re-review is [`contracts/decision.py`](contracts/decision.py).

Its only write entry point, `evaluate(description)`, executes the complete GenLayer nondeterministic consensus path:

1. The leader calls `gl.nondet.exec_prompt(prompt, response_format="json")`.
2. The validator independently reruns the same prompt.
3. The validator accepts only when its normalized `decision` exactly matches the leader's normalized `decision`.
4. `gl.vm.run_nondet_unsafe(run, validator_fn)` coordinates the equivalence check.
5. The final decision and explanation are persisted on-chain.

## Scope boundary

The following files are experimental legacy work and are not part of this submission:

- [`contracts/escrow.py`](contracts/escrow.py)
- [`tests/direct/test_escrow.py`](tests/direct/test_escrow.py)

They are not used in the submitted deployment or evaluation.

## Verification

```bash
pip install -r requirements.txt
genvm-lint check contracts/decision.py
pytest tests/direct/test_decision.py -v
genlayer network set studionet
genlayer deploy --contract contracts/decision.py
```

The exact deployment address, transaction hashes, receipt status, and persisted-state output are recorded in [`SUBMISSION.md`](SUBMISSION.md).

This re-submission is intentionally minimal: one canonical decision contract, one canonical direct test module, and one StudioNet deployment flow.
