## Canonical Contract

The primary contract for this submission is [`contracts/decision.py`](contracts/decision.py).

This contract implements the AI-powered decision system using GenLayer’s nondeterministic execution and validator consensus.

All submitted functionality, canonical tests, deployment, and documentation are aligned with this contract.

The escrow prototype and its legacy tests remain only as historical/experimental work. They are **not part of this submission** and are not used for deployment or evaluation.

---

# 🤖 VibeFlow — AI Smart Contract Builder on GenLayer

> **Build, Validate, Test, Deploy** — GenLayer intelligent contracts using Claude Code + GenLayer Skills plugin.
> *Zero manual Python coding. Full AI collaboration loop.*

This contract follows the GenLayer equivalence principle: validators independently re-execute nondeterministic steps and compare outputs for consensus.

---

## 🧠 The VibeFlow Thesis

Most smart contract development is:
- Slow (write → compile → debug → repeat)
- Error-prone (gas issues, reentrancy, consensus bugs)
- Opaque (limited visibility into iterative refinement)

**VibeFlow** introduces an AI-native development loop:

```
🧑 Prompt (English) → 🤖 AI writes contract → ✅ Auto-lint → 🧪 Auto-tests → 🚀 Deploy
```

---

## Submission Scope

This submission focuses exclusively on the AI-assisted decision contract.

Included:
- [`contracts/decision.py`](contracts/decision.py)
- [`tests/direct/test_decision.py`](tests/direct/test_decision.py)
- StudioNet deployment and execution proof in [`SUBMISSION.md`](SUBMISSION.md)

Excluded:
- [`contracts/escrow.py`](contracts/escrow.py) and [`tests/direct/test_escrow.py`](tests/direct/test_escrow.py) (experimental legacy work)

---

## 🔥 The Contract: AI-Assisted Decision Contract (MINIMAL)

A minimal GenLayer intelligent contract demonstrating AI-assisted decision consensus.

The `evaluate()` method is the only write entry point and triggers the full GenLayer nondeterministic consensus flow. Two view methods expose the persisted result.

```
Input (string) → AI evaluates → Decision saved on-chain
```

### Flow

1. **Input** → a string (task description / question)
2. **AI Evaluation** → executed via GenLayer leader + validator consensus
3. **Output** → `"approved"` or `"rejected"` stored on-chain

> ⚠️ No token transfers, balances, msg.sender logic, or escrow complexity.
> Focused purely on AI-assisted decision recording.

---

## Why This Matters

This contract demonstrates a core GenLayer capability:

👉 **AI-mediated consensus on subjective decisions**

| Question | Traditional Blockchain | GenLayer |
|----------|----------------------|----------|
| Deterministic checks | ✅ | ✅ |
| Subjective evaluation | ❌ | ✅ |
| Human-like reasoning | ❌ | ✅ |

---

## 📦 What We Built

### AI-Assisted Decision Contract ([`contracts/decision.py`](contracts/decision.py))

| Feature | Description | Value |
|--------|-------------|------|
| Single entry point | `evaluate(description)` | Minimal design |
| AI consensus | Leader + validator | GenLayer-native |
| On-chain storage | Decision persisted | Auditable |
| Explanation | AI reasoning stored | Transparent |
| Robust parsing | Handles LLM variability | Reliable |

---

## State Machine

```
evaluate(description)
   └── AI consensus
         ├── APPROVED → stored on-chain
         └── REJECTED → stored on-chain
```

---

## 🧬 GenLayer Consensus Path

```
evaluate(description)
  └─ _evaluate(description)
       └─ gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

            leader_fn:
              gl.nondet.exec_prompt(prompt, response_format="json")
              → parse decision

            validator_fn:
              reruns same prompt
              compares decision

            → consensus only if decisions match
```

---

## Consensus Guarantees

| Requirement | Implementation |
|------------|--------------|
| Nondeterministic execution | `gl.nondet.exec_prompt(prompt, response_format="json")` |
| Equivalence principle | `gl.vm.run_nondet_unsafe(run, validator_fn)` |
| Independent validation | Validator reruns the same prompt |
| Deterministic comparison | Exact normalized `decision` match |
| Prompt consistency | One `_build_prompt()` result is reused by leader and validator |
| LLM resilience | Defensive JSON parsing and exact alias normalization |
| Runtime stability | Concrete `py-genlayer` content hash pinned in the contract header |

---

## 📁 Project Structure

```
VibeFlow/
├── contracts/
│   └── decision.py
├── tests/
│   └── direct/
│       ├── conftest.py
│       └── test_decision.py
├── requirements.txt
├── README.md
└── SUBMISSION.md
```

---

## 🚀 Getting Started

### Install

```bash
pip install -r requirements.txt
```

### Lint

```bash
genvm-lint check contracts/decision.py
```

### Test

```bash
pytest tests/direct/test_decision.py -v
```

### Deploy

```bash
genlayer network set studionet
genlayer deploy --contract contracts/decision.py
```

---

## 🧪 Testing Strategy

- Direct tests are fast, local, and deterministic.
- The LLM is mocked in direct mode, validating the leader path, parsing, errors, IDs, and storage.
- Direct mode does not execute independent validators.
- StudioNet deployment and write/read receipts provide the live consensus evidence recorded in [`SUBMISSION.md`](SUBMISSION.md).

---

## 📜 Contract API

### Write

| Method | Description |
|--------|-------------|
| `evaluate(description: str) -> str` | Stores and returns `"approved"` or `"rejected"` |

### Read

| Method | Description |
|--------|-------------|
| `get_task(task_id: u256) -> dict` | Returns the stored description, decision, and explanation |
| `get_task_count() -> u256` | Returns the total number of evaluations |

---

## 🛡️ Design Principles

This contract intentionally avoids:

- Token transfers
- Balance logic
- msg.sender usage
- Escrow/state complexity
- Event emissions

👉 Result: **minimal, auditable, and focused**

---

## ✅ Summary

This submission demonstrates:

- A working GenLayer intelligent contract
- Proper AI consensus integration
- Clean validator equivalence design
- Minimal and reviewer-friendly scope

The focus is correctness, clarity, and alignment with GenLayer’s core model.
