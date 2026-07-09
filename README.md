# 🤖 VibeFlow — AI Smart Contract Builder on GenLayer

> **Build, Validate, Test, Deploy** — GenLayer intelligent contracts using Claude Code + GenLayer Skills plugin.
>
> *Zero manual Python coding. Full AI collaboration loop.*
>
> This contract follows the GenLayer equivalence principle: validators independently re-execute nondeterministic steps and compare outputs for consensus.

---

## 🧠 The VibeFlow Thesis

Most smart contract development is:
- Slow (write → compile → debug → repeat)
- Error-prone (gas issues, reentrancy, consensus bugs)
- Opaque (judges can't see the iterative refinement)

**VibeFlow** changes that. We use **Claude Code** + **GenLayer Skills plugin** to create an **AI-native development loop**:

```
🧑 Prompt (English) → 🤖 AI writes contract → ✅ Auto-lint → 🧪 Auto-tests → 🚀 Deploy
```

---

## 🔥 The Contract: AI-Assisted Decision Contract (MINIMAL)

The **simplest GenLayer intelligent contract that WORKS**:

```
Input (string) → AI evaluates → Decision saved on-chain
```

1. **Input** → a string (task description / question)
2. **AI** → evaluates through GenLayer consensus (leader + validator)
3. **Output** → `"approved"` or `"rejected"` — saved permanently on-chain

> ⚠️ **No token transfers, no balances, no msg.sender, no custom errors, no escrow logic.**
> Pure AI-assisted decision recording — safe, simple, and GenLayer-native.

### Why This Works

This contract demonstrates the **core GenLayer capability** that traditional blockchains cannot provide: **AI-mediated consensus on subjective decisions**.

| Question | Traditional Blockchain | GenLayer (this contract) |
|----------|----------------------|--------------------------|
| `"Was a hash submitted?"` | ✅ Code can check (deterministic) | ✅ Code can check |
| `"Is the balance > 0?"` | ✅ Code can check (deterministic) | ✅ Code can check |
| `"Is this task clear and feasible?"` | ❌ Code CANNOT answer (subjective) | ✅ **AI CAN answer, with reasoning** |
| `"Should this submission be approved?"` | ❌ Code CANNOT answer (ambiguous) | ✅ **AI evaluates through validator consensus** |

---

## 📦 What We Built

### AI-Assisted Decision Contract (`contracts/decision.py`)

| Feature | Description | Why It Matters |
|---------|-------------|----------------|
| **One method** | `evaluate(description)` — input, AI, output | Minimal & focused |
| **AI Consensus** | Leader + validator equivalence principle | 🔥 GenLayer-native |
| **Decision Storage** | `approved` / `rejected` stored on-chain | Permanent, auditable |
| **AI Explanation** | Reasoning stored with the decision | 🔥 Full transparency |
| **LLM Resilience** | Defensive parsing, key aliasing, type coercion | Handles unpredictable LLM formats |

#### State Machine

```
evaluate(description) ──► AI consensus ──► APPROVED  (saved on-chain)
                                    └──► REJECTED  (saved on-chain)
```

---

## 🧬 The GenLayer Consensus Path

This is the **critical part** that makes this a real GenLayer contract — not just a single leader LLM call.

```
evaluate(description)
  └─ _evaluate(description)
       └─ gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
            │
            ├─ leader_fn:
            │     gl.nondet.exec_prompt(prompt, response_format="json")
            │     _parse_verdict(raw) -> {decision, explanation}
            │
            └─ validator_fn(leaders_res):
                  independently reruns the SAME prompt
                  compares:
                    * decision must match EXACTLY (the substantive outcome)
                  -> agree ONLY if decision converges
                  -> otherwise consensus fails and rotates/retries
```

### Why this is a real consensus path

| Requirement | How it's met |
|---|---|
| **Supported nondeterministic call** | `gl.nondet.exec_prompt(prompt, response_format="json")` |
| **Equivalence principle** | `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)` |
| **Validator does NOT trust the leader** | Validator independently reruns the same prompt and compares the `decision` field |
| **Field-level comparison (not schema-only)** | `decision` exact match |
| **Deterministic prompt** | Built from the input string via `_build_prompt()` — leader and validator build the SAME prompt |
| **LLM resilience** | `_parse_verdict()` accepts dict OR JSON string, aliases keys, coerces types |
| **Pinned runner** | `# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }` (no `test`/`latest` aliases) |

---

## 📁 Project Structure

```
VibeFlow — AI Smart Contract Builder on GenLayer/
├── contracts/
│   └── decision.py          # AI-Assisted Decision Contract (GenLayer-native, minimal)
├── tests/
│   └── direct/
│       ├── conftest.py       # Shared test fixtures (genlayer_test plugin)
│       └── test_decision.py  # Direct-mode tests (fast, in-memory)
├── requirements.txt          # genlayer-test, genvm-linter, pytest
├── README.md                # This file
└── SUBMISSION.md            # Portal submission guide
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- pip

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Lint the Contract

```bash
genvm-lint check contracts/decision.py
```

### Run Tests

```bash
# Direct-mode tests (fast, in-memory, no server)
pytest tests/direct/test_decision.py -v

# All tests
pytest tests/direct/ -v
```

### Deploy

Use the GenLayer CLI to deploy the contract:

```bash
genlayer deploy contracts/decision.py
```

---

## 🧪 Testing Strategy

1. **Lint first**: `genvm-lint check contracts/decision.py`
2. **Direct mode tests**: Fast (30ms), no server. Tests business logic, parsing, storage. Validator logic NOT exercised.
3. **Integration tests**: Slow (seconds-minutes), full consensus. Tests validator agreement, real LLM calls. Run before deployment.

Tests mock the nondeterministic LLM via `direct_vm.set_ai_prompt_response()`. In direct mode the validator is NOT exercised (per GenLayer testing strategy); the leader path + parsing + storage is validated here.

---

## 📜 Contract API

### Write Methods

| Method | Description |
|--------|-------------|
| `evaluate(description: str) -> str` | Input a string, AI consensus evaluates, returns `"approved"` or `"rejected"`, saves on-chain. |

### View Methods

| Method | Description |
|--------|-------------|
| `get_task(task_id: u256) -> dict` | Read a task's description, decision, and explanation. |
| `get_task_count() -> u256` | Total tasks evaluated. |

---

## 🛡️ Safety & Simplicity

This contract intentionally avoids:
- ❌ Token transfers (`gl.transfer`)
- ❌ Balance logic (`gl.message.value`)
- ❌ `msg.sender` logic (`gl.message.sender_account`)
- ❌ Custom error prefixes
- ❌ Complex escrow / multi-party state machines
- ❌ Event logging

This keeps the contract **minimal, auditable, and focused** on the core GenLayer capability: **AI consensus on subjective decisions**.
