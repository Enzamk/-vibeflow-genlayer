## Canonical Contract

The primary contract for this submission is:

contracts/decision.py

This contract implements the AI-powered decision system using GenLayer’s nondeterministic execution and validator consensus.

All functionality, tests, deployment, and documentation in this submission are aligned with this contract.

The escrow contract present in the repository is experimental and NOT part of this submission. It is not used in deployment, evaluation, or testing.

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
- contracts/decision.py
- tests/direct/test_decision.py
- StudioNet deployment and execution proof

Excluded:
- Escrow contract (experimental, not used in this submission)

---

## 🔥 The Contract: AI-Assisted Decision Contract (MINIMAL)

A minimal GenLayer intelligent contract demonstrating AI-assisted decision consensus.

The `evaluate()` method is the only entry point and triggers the full GenLayer nondeterministic consensus flow.

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

### AI-Assisted Decision Contract (`contracts/decision.py`)

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
              gl.nondet.exec_prompt(prompt)
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
| Nondeterministic execution | `gl.nondet.exec_prompt` |
| Equivalence principle | `gl.vm.run_nondet_unsafe` |
| Independent validation | Validator reruns prompt |
| Deterministic comparison | Exact `decision` match |
| Prompt consistency | Same builder function |
| LLM resilience | Defensive parsing |
| Runtime stability | Pinned dependency |

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
genlayer deploy contracts/decision.py
```

---

## 🧪 Testing Strategy

- Direct tests → fast, local, deterministic  
- Integration tests → full consensus validation  
- LLM mocked in direct mode  
- Validator path tested in integration  

---

## 📜 Contract API

### Write

| Method | Description |
|--------|-------------|
| `evaluate(description: str)` | Returns `"approved"` or `"rejected"` |

### Read

| Method | Description |
|--------|-------------|
| `get_task(task_id)` | Returns stored result |
| `get_task_count()` | Total evaluations |

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
