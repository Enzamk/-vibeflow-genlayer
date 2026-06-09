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
GenLayer-native escrow where AI consensus replaces human arbiter: both parties submit evidence on-chain, AI evaluates through validator consensus, decision + explanation stored permanently. Demonstrates why GenLayer handles real-world ambiguity that traditional blockchains cannot.
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
## 🧠 What is VibeFlow?

VibeFlow is an **AI-native development loop** for GenLayer intelligent contracts. Instead of manually writing, compiling, debugging, and testing smart contracts, you simply **describe what you want in English**, and Claude Code (with GenLayer Skills plugin) generates production-ready code — complete with linting, tests, and deployment instructions.

## 🔥 Why GenLayer is Different from Traditional Blockchains

This contract demonstrates the **fundamental difference** between GenLayer and traditional blockchains:

### Traditional Blockchain Escrow (Ethereum/Solidity)
- payer → payee → **human arbiter** (deterministic boolean: release or refund)
- Arbiter can be: bribed, absent, biased, expensive
- `"Was work completed?"` → **code CANNOT answer this**
- No on-chain explanation for WHY a decision was made
- Single point of failure — if arbiter disappears, funds are locked

### GenLayer-Native Escrow (this contract)
- payer → payee → **AI consensus** (evaluates real-world ambiguity)
- Both parties submit **evidence on-chain** — transparent, auditable
- AI evaluates **BOTH sides** through validator consensus — fair, unbiased
- `"Was work completed?"` → **AI CAN answer this, with reasoning**
- Decision + explanation + evidence_assessment stored **permanently on-chain**
- No human gatekeeper — **any party can trigger resolution**

### The Key Insight
Traditional smart contracts handle **deterministic** conditions:
- ✅ `"Was a hash submitted?"` → yes/no → code can check
- ❌ `"Was work completed satisfactorily?"` → subjective → code CANNOT check

GenLayer's AI consensus handles exactly these **ambiguous, real-world questions**.

## 📜 The Contract: Escrow with AI Consensus Dispute Resolution

| Feature | Description | Why It Matters |
|---------|-------------|----------------|
| **Deposit** | Payer locks native tokens (no arbiter param) | Simplified — AI handles disputes |
| **Approve** | Payer releases to payee (minus fee) | Trustless settlement |
| **Cancel** | Payer gets full refund | Safety valve |
| **Dispute** | Any party raises dispute (payer address + reason) | Equal access — no arbiter gatekeeper |
| **Evidence** | Both parties submit evidence on-chain | 🔥 AI sees BOTH sides — fair evaluation |
| **AI Resolve** | AI consensus evaluates evidence → decision + explanation | 🔥 GenLayer-native — replaces human arbiter |
| **Event Logging** | All state changes + evidence + AI decisions recorded | 🔥 Full audit trail |
| **Fee Collection** | Basis-point fee on release | Monetization built-in |
| **Error Classification** | `[EXPECTED]` / `[EXTERNAL]` prefixes | GenLayer consensus safety |

### State Machine

```
                          ┌─── RELEASED (payer approves — happy path)
                          │
FUNDED ───────────────────┼─── CANCELLED (payer cancels — refund)
                          │
                          └─── DISPUTED ──► AI evaluates evidence ──► RELEASED (AI: release_payment)
                                           │                        └─► CANCELLED (AI: refund_payer)
                                           │                        └─► RELEASED  (AI: partial_refund — split)
```

### AI Decision Output (stored on-chain)

```json
{
  "decision": "partial_refund",
  "refund_percentage": 40,
  "explanation": "60% of goods delivered satisfactorily. 40% missing due to stock-out. Payer gets 40% refund.",
  "evidence_assessment": {
    "payer_evidence_strength": "moderate",
    "payee_evidence_strength": "moderate",
    "key_factors": ["60pct_confirmed_delivery", "40pct_stock_out", "both_partial_claims"]
  }
}
```

## 🧪 Testing — 24+ Tests, < 1 Second

All tests run in **direct mode** (no server, no Docker):

```
pytest tests/direct/ -v
→ 24+ passed in <1s
```

Test coverage includes:
- ✅ Deposit (happy path, zero reject, self-payee reject, duplicate reject)
- ✅ Approve (release, non-payer reject, wrong-status reject)
- ✅ Cancel (refund, post-approve reject)
- ✅ Dispute (payer raises, payee raises, non-party reject)
- ✅ Evidence (payer submits, payee submits, both sides, non-party reject, before-dispute reject)
- ✅ AI Dispute Resolution (release_payment, refund_payer, partial_refund, non-party reject, wrong-status reject, event logging, decision+explanation storage, no-evidence fallback)
- ✅ Events (deposit logged, evidence logged)
- ✅ View helpers (exists())

## 🤖 The "Vibe Layer" — AI Collaboration

The contract was built iteratively through AI collaboration:

**Prompt 1:** "Create escrow with deposit/approve/cancel"
→ AI generates base contract with TreeMap storage, @gl.public.write decorators

**Prompt 2:** "Improve by adding dispute resolution, logging events, optimizing gas"
→ AI adds: raise_dispute(), DynArray[EventLog] for audit trail, error classification

**Prompt 3:** "Transform into GenLayer-native contract — replace arbiter with AI consensus"
→ AI adds:
  • 🔥 Remove arbiter entirely — AI consensus IS the arbiter
  • 🔥 submit_evidence() — both parties present their side on-chain
  • 🔥 resolve_with_ai() — any party can trigger, no human gatekeeper
  • 🔥 AI prompt designed for real-world ambiguity ("was work completed?")
  • 🔥 evidence_assessment in AI output — structured reasoning
  • 🔥 Full explanation stored on-chain for transparency

This shows how AI can take a contract from basic → production-ready → GenLayer-native in minutes.

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
- **SDK:** `@gl.public.view`, `@gl.public.write`, `gl.message`, `gl.transfer`, `gl.block.time`, `gl.ai.prompt`
- **Error handling:** Classified `[EXPECTED]` (user errors) and `[EXTERNAL]` (system/AI errors)
- **GenLayer-native:** AI consensus replaces human arbiter — non-deterministic dispute resolution
- **Evidence system:** Both parties submit on-chain — AI evaluates BOTH sides
- **Transparency:** Decision + explanation + evidence_assessment stored permanently on-chain
- **Gas efficient:** O(1) lookups, paginated event queries

## 🎯 Why This Matters

1. **Real-world ambiguity:** "Was work completed?" → AI CAN answer, traditional code CANNOT
2. **No human arbiter:** AI consensus is unbiased, always available, cannot be bribed
3. **Transparency:** Every AI decision has a traceable, on-chain explanation
4. **Fairness:** Both parties submit evidence — AI sees BOTH sides
5. **Speed:** From idea to tested contract in minutes, not days
6. **Reproducibility:** Anyone with pip + genlayer-test can verify in <1 second
```

---

### Tags / Keywords

```
genlayer, smart-contract, escrow, ai-consensus, dispute-resolution, evidence-based, python, web3, blockchain, developer-tools, non-deterministic
```

---

## 📦 Files in Submission

| File | Purpose |
|------|---------|
| [`contracts/escrow.py`](contracts/escrow.py) | GenLayer-native intelligent contract (AI consensus replaces arbiter) |
| [`tests/direct/test_escrow.py`](tests/direct/test_escrow.py) | 24+ direct-mode test cases (evidence + AI resolution) |
| [`tests/direct/conftest.py`](tests/direct/conftest.py) | Pytest fixtures |
| [`requirements.txt`](requirements.txt) | Python dependencies |
| [`README.md`](README.md) | Full project documentation |
| [`SUBMISSION.md`](SUBMISSION.md) | Submission guide |
| [`.gitignore`](.gitignore) | Git ignore rules |

---

## 🔧 Step-by-Step: Push to GitHub

```bash
# In project directory
cd "j:/VibeFlow — AI Smart Contract Builder on GenLayer"

# Initialize git
git init

# Add all files
git add -A

# Commit
git commit -m "🔥 VibeFlow — GenLayer-native escrow: AI consensus replaces human arbiter

- Removed arbiter entirely — AI consensus IS the arbiter
- Both parties submit evidence on-chain via submit_evidence()
- resolve_with_ai() — any party can trigger, no human gatekeeper
- AI evaluates real-world ambiguity ('was work completed?')
- Decision + explanation + evidence_assessment stored on-chain
- 24+ direct-mode tests covering evidence + AI resolution"

# Create repo on GitHub first (public), then:
git remote add origin https://github.com/<YOUR_USERNAME>/vibeflow-genlayer.git
git branch -M main
git push -u origin main
```

> **Pro tip:** Add a `genlayer` topic tag on your GitHub repo for discoverability.

---

## ✅ Submission Checklist

- [x] Contract is GenLayer-native (uses `gl.ai.prompt` for consensus)
- [x] No human arbiter — AI consensus handles disputes
- [x] Both parties can submit evidence on-chain
- [x] AI decision + explanation stored permanently on-chain
- [x] Error classification (`[EXPECTED]` / `[EXTERNAL]`) for consensus safety
- [x] Event logging for full audit trail
- [x] Direct-mode tests (no server, no Docker, <1s)
- [x] README explains why GenLayer is different from traditional blockchains
- [x] Reproducible: `pip install` + `pytest` → verify in <1 second