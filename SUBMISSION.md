# 🚀 Submission Guide — GenLayer Foundation Portal

> **URL:** https://portal.genlayer.foundation/#/submit-contribution

---

## 📋 Copy-Paste Template for Portal

Use this text directly in the submission form fields:

---

### Project Name

```
AI Decision Contract using GenLayer Consensus
```

---

### Tagline / Short Description (1 line)

```
This project demonstrates a GenLayer-native intelligent contract that uses AI-assisted reasoning combined with validator consensus to evaluate subjective inputs.
```

---

### GitHub Repository URL

```
https://github.com/<YOUR_USERNAME>/vibeflow-genlayer
```

> ⚠️ Replace `<YOUR_USERNAME>` with your actual GitHub username after pushing.

---

### Category

Select from portal dropdown (likely): **Smart Contract** or **Developer Tools**

---

### Full Description

```markdown
This project demonstrates a GenLayer-native intelligent contract that uses AI-assisted reasoning combined with validator consensus to evaluate subjective inputs.

Unlike traditional smart contracts, this contract allows non-deterministic evaluation of user-submitted tasks using GenLayer Skills.

## Features

- AI-based evaluation of user input
- Validator consensus mechanism
- Fully GenLayer-native contract
- Successful execution trace included
- Robust LLM output normalization (handles case variations and aliases)

## How it works

1. User submits a task description
2. AI evaluates the task
3. Validators reach consensus
4. Final decision is stored on-chain

## Why it matters

This shows how GenLayer enables subjective decision-making that cannot be handled by traditional deterministic smart contracts.

## The GenLayer Consensus Path

```
evaluate(description)
  └─ gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
       │
       ├─ leader_fn:
       │     gl.nondet.exec_prompt(prompt, response_format="json")
       │     _parse_verdict(raw) -> {decision, explanation}
       │
       └─ validator_fn(leaders_res):
             independently reruns the SAME prompt
             compares the `decision` field EXACTLY
             -> agree ONLY if decision converges
             -> otherwise consensus fails and rotates/retries
```

## Safety & Simplicity

This contract intentionally avoids:
- ❌ Token transfers (`gl.transfer`)
- ❌ Balance logic (`gl.message.value`)
- ❌ `msg.sender` logic
- ❌ Custom error prefixes
- ❌ Complex escrow / multi-party state machines

This keeps the contract minimal, auditable, and focused on the core GenLayer capability: AI consensus on subjective decisions.

## Testing

- **Lint**: `genvm-lint check contracts/decision.py`
- **Direct-mode tests**: `pytest tests/direct/test_decision.py -v`
- **Live execution**: Deployed and called via GenLayer CLI (execution trace included)
```

---

### How to Verify

```bash
# Install dependencies
pip install -r requirements.txt
npm install -g genlayer

# Lint the contract
genvm-lint check contracts/decision.py

# Run direct-mode tests
pytest tests/direct/test_decision.py -v

# Deploy & run live (see RUN.md for full steps)
genlayer network set studionet
genlayer deploy --contract contracts/decision.py
genlayer write <address> evaluate --args "Build a REST API for a todo app"
genlayer call <address> get_task --args 1
```

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
├── README.md                # Full documentation
├── RUN.md                   # Step-by-step deploy & run guide
└── SUBMISSION.md            # This file
```

---

## ✅ Submission Checklist

- [x] Contract uses pinned runner version hash (no `test`/`latest` aliases)
- [x] Contract uses `gl.nondet.exec_prompt()` for nondeterministic LLM calls
- [x] Contract uses `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)` — real equivalence principle
- [x] Validator independently reruns the same prompt (does NOT trust the leader)
- [x] Field-level comparison: `decision` exact match
- [x] LLM resilience: defensive parsing, key aliasing, type coercion
- [x] No token transfers, no balance logic, no msg.sender, no escrow
- [x] Direct-mode tests covering leader path + parsing + storage (39 tests pass)
- [x] README.md with full documentation
- [x] RUN.md with deploy + call + proof capture steps
- [x] Deploy & run live: `genlayer deploy` + `genlayer write` + capture logs ✅
- [ ] Push to GitHub and replace `<YOUR_USERNAME>` in the URL above

---

## 🔥 Execution Proof (Live on StudioNet)

The contract was deployed and executed live on **GenLayer StudioNet** (gasless network).
This proves the full GenLayer consensus path works end-to-end — not just unit tests.

### Network

```
Network:    StudioNet (gasless)
Chain ID:   61999
RPC:        https://studio.genlayer.com/api
```

### Step 1 — Deploy

```bash
genlayer network set studionet
genlayer deploy --contract contracts/decision.py
```

**Result:**

```
Contract Address: 0xD658FD6baC547Dd5BC0e5eCf72712EE843e3C1F5
Transaction Hash: 0x203423dde5492f8caeb28384d3f813c310d73fb9799b3717d2a5f03fab938626
Status:           ACCEPTED
Consensus:        MAJORITY_AGREE (5/5 validators AGREE, 1 round)
```

### Step 2 — Write (AI Evaluation)

```bash
genlayer write 0xD658FD6baC547Dd5BC0e5eCf72712EE843e3C1F5 evaluate \
  --args "I completed the project successfully"
```

**Result:**

```
Transaction Hash: 0x61053947ce7a0010d8294d4d61363172326b114303c7a9b6f7c10237599c19d0
Status:           ACCEPTED
Consensus:        MAJORITY_AGREE (4/5 AGREE, 1 IDLE, 1 round)
Execution:        SUCCESS
```

The leader executed `gl.nondet.exec_prompt()` and validators independently reran
the same prompt, comparing the `decision` field. Consensus was reached.

### Step 3 — Read (On-Chain Verification)

```bash
genlayer call 0xD658FD6baC547Dd5BC0e5eCf72712EE843e3C1F5 get_task --args 1
```

**Result:**

```json
{
  "task_id": "1",
  "description": "I completed the project successfully",
  "decision": "rejected",
  "explanation": "The task is too vague to evaluate. It only states 'I completed the project successfully' without defining the project, success criteria, deliverables, or evidence. As a result, it is not clear, not sufficiently detailed, and cannot be reasonably verified."
}
```

### What This Proves

| Requirement | Evidence |
|---|---|
| ✅ Contract runs in CLI | Deployed + write + call all succeeded |
| ✅ `gl.nondet.exec_prompt()` | Leader ran LLM, got JSON verdict |
| ✅ `gl.vm.run_nondet_unsafe()` | Validator consensus reached (MAJORITY_AGREE) |
| ✅ Equivalence principle | Validators independently reran prompt, compared `decision` |
| ✅ JSON parsing safe | LLM response parsed into `{decision, explanation}` |
| ✅ No transfer/balance/msg.sender | Contract has none of these |
| ✅ Decision stored on-chain | `get_task` returns the AI decision + explanation |
| ✅ AI reasoning on-chain | Full explanation text persisted in storage |
