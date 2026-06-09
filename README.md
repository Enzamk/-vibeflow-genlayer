# 🤖 VibeFlow — AI Smart Contract Builder on GenLayer

> **Build, Validate, Test, Deploy** — GenLayer intelligent contracts using Claude Code + GenLayer Skills plugin.
>
> *Zero manual Python coding. Full AI collaboration loop.*

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

## 🔥 Why GenLayer is Different from Traditional Blockchains

This contract demonstrates the **fundamental difference** between GenLayer and traditional blockchains (Ethereum, Solana, etc.):

### Traditional Blockchain Escrow (Ethereum/Solidity)

```
payer → payee → human arbiter
```

- Arbiter decides: `release()` or `refund()` — **deterministic boolean**
- Arbiter can be: **bribed, absent, biased, expensive**
- `"Was work completed?"` → **code CANNOT answer this**
- No on-chain explanation for **WHY** a decision was made
- Single point of failure — if arbiter disappears, funds are locked

### GenLayer-Native Escrow (this contract)

```
payer → payee → AI consensus
```

- Both parties submit **evidence on-chain** — transparent, auditable
- AI evaluates **BOTH sides** through validator consensus — fair, unbiased
- `"Was work completed?"` → **AI CAN answer this, with reasoning**
- Decision + explanation + evidence assessment stored **permanently on-chain**
- No human gatekeeper — **any party can trigger resolution**
- No single point of failure — consensus is distributed

### The Key Insight

Traditional smart contracts handle **deterministic** conditions:
- ✅ `"Was a hash submitted?"` → yes/no → code can check
- ✅ `"Is the balance > 0?"` → yes/no → code can check
- ❌ `"Was work completed satisfactorily?"` → subjective → **code CANNOT check**
- ❌ `"Did the seller deliver what was promised?"` → ambiguous → **code CANNOT check**

GenLayer's AI consensus handles exactly these **ambiguous, real-world questions** — the ones that traditional blockchains simply cannot resolve.

---

## 📦 What We Built

### 1️⃣ GenLayer-Native Escrow (`contracts/escrow.py`)

A production-grade escrow on GenLayer where **AI consensus replaces the human arbiter**:

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

#### State Machine

```
                          ┌─── RELEASED (payer approves — happy path)
                          │
FUNDED ───────────────────┼─── CANCELLED (payer cancels — refund)
                          │
                          └─── DISPUTED ──► AI evaluates evidence ──► RELEASED (AI: release_payment)
                                           │                        └─► CANCELLED (AI: refund_payer)
                                           │                        └─► RELEASED  (AI: partial_refund — split)
```

#### AI Decision Output (stored on-chain)

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

### 2️⃣ Direct Mode Tests (`tests/direct/test_escrow.py`)

**24 test cases** covering:

- ✅ Deposit (happy path, zero reject, self-payee reject, duplicate reject)
- ✅ Approve (release, non-payer reject, wrong-status reject)
- ✅ Cancel (refund, post-approve reject)
- ✅ Dispute (payer raises, payee raises, non-party reject)
- ✅ Evidence (payer submits, payee submits, both sides, non-party reject, before-dispute reject)
- ✅ AI Dispute Resolution (release_payment, refund_payer, partial_refund, non-party reject, wrong-status reject, event logging, decision+explanation storage, no-evidence fallback)
- ✅ Events (deposit logged, evidence logged)
- ✅ View helpers (`exists()`)

### 3️⃣ AI Collaboration Loop — *The "Vibe Layer"*

```
Prompt 1: "Create escrow with deposit/approve/cancel"
   → AI generates base contract

Prompt 2: "Improve by adding dispute resolution, logging events, optimizing gas"
   → AI adds: raise_dispute(), DynArray[EventLog], error classification

Prompt 3: "Transform into GenLayer-native contract — replace arbiter with AI consensus"
   → AI adds:
       • 🔥 Remove arbiter entirely — AI consensus IS the arbiter
       • 🔥 submit_evidence() — both parties present their side on-chain
       • 🔥 resolve_with_ai() — any party can trigger, no human gatekeeper
       • 🔥 AI prompt designed for real-world ambiguity ("was work completed?")
       • 🔥 evidence_assessment in AI output — structured reasoning
       • 🔥 Full explanation stored on-chain for transparency
   → This demonstrates WHY GenLayer is different from traditional blockchains
```

---

## 🚀 Full Demo Flow (For Judges)

### Step 1 — Prompt → Contract Generated

```
claude "Write a GenLayer escrow contract where AI consensus replaces the human arbiter"
```

🤖 **Result:** `contracts/escrow.py` — GenLayer-native contract with:
- No arbiter parameter — AI handles disputes
- `submit_evidence()` for both parties
- `resolve_with_ai()` using `gl.ai.prompt()` with consensus
- Evidence assessment + explanation stored on-chain

### Step 2 — Auto Validation (genvm-lint)

```bash
genvm-lint check contracts/escrow.py
```

### Step 3 — AI Generates & Runs Tests

```bash
pytest tests/direct/ -v
```

**Expected output:**
```
✓ test_deposit_creates_escrow
✓ test_deposit_zero_reverts
✓ test_deposit_self_as_payee_reverts
✓ test_deposit_duplicate_reverts
✓ test_approve_releases_to_payee
✓ test_approve_non_payer_reverts
✓ test_approve_wrong_status_reverts
✓ test_cancel_refunds_payer
✓ test_cancel_after_approve_reverts
✓ test_raise_dispute_by_payer
✓ test_raise_dispute_by_payee
✓ test_raise_dispute_non_party_reverts
✓ test_submit_evidence_payer
✓ test_submit_evidence_payee
✓ test_submit_evidence_both_sides
✓ test_submit_evidence_non_party_reverts
✓ test_submit_evidence_before_dispute_reverts
✓ test_ai_resolve_release_payment
✓ test_ai_resolve_refund_payer
✓ test_ai_resolve_partial_refund
✓ test_ai_resolve_non_party_reverts
✓ test_ai_resolve_wrong_status_reverts
✓ test_ai_resolve_logs_event_with_explanation
✓ test_ai_resolve_stores_decision_and_explanation
✓ test_ai_resolve_without_evidence
✓ test_events_logged
✓ test_evidence_event_logged
✓ test_exists_check

24+ passed in <1s
```

### Step 4 — Deploy via GenLayer CLI

```bash
genlayer client deploy contracts/escrow.py --args '[50]' --network testnet
```

---

## 🔧 How to Run This Yourself

### Prerequisites

```bash
# 1. Python 3.10+
python --version

# 2. Install GenLayer tools
pip install genvm-linter genlayer-test pytest
```

### Validate

```bash
genvm-lint check contracts/escrow.py
```

### Test

```bash
pytest tests/direct/ -v
```

### Deploy

```bash
genlayer client deploy contracts/escrow.py --args '[50]' --network testnet
```

---

## 🏗️ Technical Depth

- **Storage:** `TreeMap[Address, EscrowState]`, `DynArray[EventLog]`, `u256`
- **SDK:** `@gl.public.view`, `@gl.public.write`, `gl.message`, `gl.transfer`, `gl.block.time`, `gl.ai.prompt`
- **Error handling:** Classified `[EXPECTED]` (user errors) and `[EXTERNAL]` (system/AI errors)
- **GenLayer-native:** AI consensus replaces human arbiter — non-deterministic dispute resolution
- **Evidence system:** Both parties submit on-chain — AI evaluates BOTH sides
- **Transparency:** Decision + explanation + evidence_assessment stored permanently on-chain
- **Gas efficient:** O(1) lookups, paginated event queries

---

## 🎯 Why This Matters

1. **Real-world ambiguity:** "Was work completed?" → AI CAN answer, traditional code CANNOT
2. **No human arbiter:** AI consensus is unbiased, always available, cannot be bribed
3. **Transparency:** Every AI decision has a traceable, on-chain explanation
4. **Fairness:** Both parties submit evidence — AI sees BOTH sides
5. **Speed:** From idea to tested contract in minutes, not days
6. **Quality:** AI catches common bugs (reentrancy, state validation, consensus issues)
7. **Reproducibility:** Anyone with pip + genlayer-test can verify in <1 second