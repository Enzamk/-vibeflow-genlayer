# 🏃 Run Guide — Deploy & Execute the AI Decision Contract

> Step-by-step commands to deploy the contract, call it, and capture proof of execution.

---

## 📋 Prerequisites

```bash
# 1. Install Python 3.11+ (from python.org)
# 2. Install Node.js 18+ (from nodejs.org)

# Install Python dependencies
pip install -r requirements.txt

# Install GenLayer CLI
npm install -g genlayer
```

---

## 🚀 Step 1 — Start Local Studio (genlayer dev)

```bash
# Initialize a local GenLayer environment
genlayer init --numValidators 5 --headless

# Start the Studio (local blockchain + validators)
genlayer up
```

> This starts a local GenLayer network with 5 validators. The Studio UI runs at `http://localhost:8545`.

---

## 🌐 Step 2 — Set Network & Account

```bash
# Use localnet (the Studio you just started)
genlayer network set localnet

# Verify network config
genlayer network info

# Check your account
genlayer account
```

> If no account exists, create one:
> ```bash
> genlayer account create --name dev1
> genlayer account use dev1
> ```

---

## 📦 Step 3 — Deploy the Contract

```bash
# Deploy the AI Decision Contract (no constructor args needed)
genlayer deploy --contract contracts/decision.py
```

> **Copy the contract address from the output!** You'll need it for the next steps.
>
> Example output:
> ```
> Contract deployed at: 0x1234...abcd
> Transaction hash: 0x5678...efgh
> ```

---

## ✍️ Step 4 — Call evaluate() (Write Transaction)

```bash
# Replace <ADDRESS> with your deployed contract address
genlayer write <ADDRESS> evaluate --args "Build a REST API for a todo app with Node.js and Express"
```

> **Copy the transaction hash from the output!** You'll need it to get the receipt.
>
> Expected output:
> ```
> Transaction submitted: 0xabcd...1234
> ```

---

## 🧾 Step 5 — Get the Receipt (Proof of Execution)

```bash
# Replace <TX_HASH> with the transaction hash from Step 4
# This waits for FINALIZED status and shows full execution result
genlayer receipt <TX_HASH> --stdout --stderr
```

> Expected output (proof of successful execution):
> ```
> Status: FINALIZED
> Execution: SUCCESS
> Result: "approved"
> Consensus reached
> ```

---

## 📖 Step 6 — Read the Stored Decision (View Call)

```bash
# Read task #1 from on-chain storage
genlayer call <ADDRESS> get_task --args 1
```

> Expected output:
> ```json
> {
>   "task_id": "1",
>   "description": "Build a REST API for a todo app with Node.js and Express",
>   "decision": "approved",
>   "explanation": "The task is clear, well-defined, and feasible..."
> }
> ```

```bash
# Check total tasks evaluated
genlayer call <ADDRESS> get_task_count
```

> Expected output:
> ```
> "1"
> ```

---

## 📸 Step 7 — Capture Proof

### Option A: Screenshots
Take screenshots of:
1. ✔ Contract deployed (Step 3 output with address)
2. ✔ Function call (Step 4 output with tx hash)
3. ✔ Output result (Step 5 receipt showing `SUCCESS` + `Result: "approved"`)
4. ✔ Consensus reached (Step 5 showing `FINALIZED`)

### Option B: Copy Logs
Save the terminal output to a file:

```bash
# Capture full execution trace
{
  echo "=== CONTRACT DEPLOY ==="
  genlayer deploy --contract contracts/decision.py
  echo ""
  echo "=== EVALUATE CALL ==="
  genlayer write <ADDRESS> evaluate --args "Build a REST API for a todo app with Node.js and Express"
  echo ""
  echo "=== RECEIPT ==="
  genlayer receipt <TX_HASH> --stdout --stderr
  echo ""
  echo "=== GET TASK ==="
  genlayer call <ADDRESS> get_task --args 1
} > execution_proof.txt 2>&1
```

Then attach `execution_proof.txt` to your submission.

---

## 🧪 Alternative: Run Tests (No Network Needed)

If you just want to verify the contract logic without deploying:

```bash
# Lint
genvm-lint check contracts/decision.py

# Direct-mode tests (fast, in-memory, mocks the LLM)
pytest tests/direct/test_decision.py -v
```

---

## 🛑 Stop the Studio

When done:

```bash
genlayer stop
```

---

## 📝 Quick Reference

| Step | Command |
|------|---------|
| Start Studio | `genlayer up` |
| Set network | `genlayer network set localnet` |
| Deploy | `genlayer deploy --contract contracts/decision.py` |
| Call (write) | `genlayer write <ADDRESS> evaluate --args "..."` |
| Receipt | `genlayer receipt <TX_HASH> --stdout --stderr` |
| Read (view) | `genlayer call <ADDRESS> get_task --args 1` |
| Stop Studio | `genlayer stop` |
