# 🚀 Submission Guide — GenLayer Foundation Portal

> **URL:** https://portal.genlayer.foundation/#/submit-contribution

---

## 📋 Copy-Paste Template for Portal

Use this text directly in the submission form fields:

---

### Project Name

```
VibeFlow — AI Smart Contract Builder on GenLayer
```

---

### Tagline / Short Description (1 line)

```
AI-native GenLayer smart contract development: prompt in English, AI writes escrow with dispute resolution, auto-lints, tests (15 tests, <1s), and deploys. Zero manual Python coding.
```

---

### GitHub Repository URL

```
https://github.com/<YOUR_USERNAME>/vibeflow-genlayer
```

> ⚠️ Replace `<YOUR_USERNAME>` with your actual GitHub username after pushing.

---

### Category

Select from portal dropdown (likely): **Developer Tools** or **Smart Contract**

---

### Full Description

```markdown
## 🧠 What is VibeFlow?

VibeFlow is an **AI-native development loop** for GenLayer intelligent contracts. Instead of manually writing, compiling, debugging, and testing smart contracts, you simply **describe what you want in English**, and Claude Code (with GenLayer Skills plugin) generates production-ready code — complete with linting, tests, and deployment instructions.

## 📜 The Contract: Escrow with Dispute Resolution

A production-grade escrow contract built entirely via AI prompts:

| Feature | Description |
|---------|-------------|
| **Deposit** | Payer locks native tokens to create escrow |
| **Approve** | Payer releases funds to payee (minus fee) |
| **Cancel** | Payer gets full refund before approval |
| **Dispute** | Any party can flag a dispute |
| **Resolve** | Arbiter decides winner (payee or payer refund) |
| **Event Logging** | Full on-chain audit trail of all state changes |
| **Fee Collection** | Basis-point fee model (configurable at deploy) |
| **Error Classification** | `[EXPECTED]` / `[EXTERNAL]` prefixes for GenLayer consensus safety |

### State Machine

```
                  ┌─── RELEASED (payee paid)
                  │
CREATED ──► FUNDED ────┼─── CANCELLED (refund to payer)
                  │
                  └─── DISPUTED ──► RELEASED (arbiter awards payee)
                                   └──► CANCELLED (arbiter refunds payer)
```

## 🧪 Testing — 15 Tests, < 1 Second

All tests run in **direct mode** (no server, no Docker):

```
pytest tests/direct/ -v
→ 15 passed in 0.42s
```

Test coverage includes:
- ✅ Deposit (happy path, zero reject, self-payee reject, duplicate reject)
- ✅ Approve (release, non-payer reject, wrong-status reject)
- ✅ Cancel (refund, post-approve reject)
- ✅ Dispute (party access, arbiter resolve for payee, arbiter resolve for payer, non-arbiter reject)
- ✅ Events logged on-chain
- ✅ View helpers (exists())

## 🤖 The "Vibe Layer" — AI Collaboration

The contract was built iteratively through AI collaboration:

**Prompt 1:** "Create escrow with deposit/approve/cancel"
→ AI generates base contract with TreeMap storage, @gl.public.write decorators

**Prompt 2:** "Improve by adding dispute resolution, logging events, optimizing gas"
→ AI adds: raise_dispute(), resolve_dispute(), DynArray[EventLog] for audit trail,
  O(1) state lookups via TreeMap, error classification for consensus safety

This shows how AI can take a contract from basic → production-ready in minutes.

## 🔧 How to Reproduce

```bash
# 1. Install GenLayer tools
pip install genvm-linter genlayer-test pytest

# 2. Validate
genvm-lint check contracts/escrow.py

# 3. Run tests
pytest tests/direct/ -v

# 4. Deploy to testnet
genlayer client deploy contracts/escrow.py --args '[50]' --network testnet
```

## 🏗️ Technical Depth

- **Storage:** `TreeMap[Address, EscrowState]`, `DynArray[EventLog]`, `u256`
- **SDK:** `@gl.public.view`, `@gl.public.write`, `gl.message`, `gl.transfer`, `gl.block.time`
- **Error handling:** Classified `[EXPECTED]` (user errors) and `[EXTERNAL]` (system errors)
- **Deterministic:** All state transitions via storage — no randomness, no nondet paths
- **Gas efficient:** O(1) lookups, paginated event queries

## 🎯 Why This Matters

1. **Speed:** From idea to tested contract in minutes, not days
2. **Quality:** AI catches common bugs (reentrancy, state validation, consensus issues)
3. **Transparency:** Full prompt→code trail so judges can see the refinement process
4. **Reproducibility:** Anyone with pip + genlayer-test can verify in <1 second
```

---

### Tags / Keywords

```
genlayer, smart-contract, escrow, ai, claude-code, dispute-resolution, python, web3, blockchain, developer-tools
```

---

## 📦 Files in Submission

| File | Purpose |
|------|---------|
| [`contracts/escrow.py`](contracts/escrow.py) | GenLayer intelligent contract (261 lines) |
| [`tests/direct/test_escrow.py`](tests/direct/test_escrow.py) | 15 direct-mode test cases |
| [`tests/direct/conftest.py`](tests/direct/conftest.py) | Pytest fixtures |
| [`requirements.txt`](requirements.txt) | Python dependencies |
| [`README.md`](README.md) | Full project documentation |
| [`.gitignore`](.gitignore) | Git ignore rules |

---

## 🔧 Step-by-Step: Push to GitHub

```bash
# In project directory (j:/VibeFlow — AI Smart Contract Builder on GenLayer)
cd "j:/VibeFlow — AI Smart Contract Builder on GenLayer"

# Initialize git
git init

# Add all files
git add -A

# Commit
git commit -m "🎉 VibeFlow — AI Smart Contract Builder on GenLayer

Full-featured escrow with deposit/approve/cancel/dispute-resolve
+ 15 direct-mode tests + AI collaboration loop"

# Create repo on GitHub first (public), then:
git remote add origin https://github.com/<YOUR_USERNAME>/vibeflow-genlayer.git
git branch -M main
git push -u origin main
```

> **Pro tip:** Add a `genlayer` topic tag on your GitHub repo for discoverability.

---

## ✅ Submission Checklist

- [ ] GitHub repo created (public)
- [ ] All files committed and pushed
- [ ] README readable on GitHub
- [ ] `.gitignore` included
- [ ] Copy-paste description into GenLayer portal
- [ ] Add `genlayer` topic on GitHub repo