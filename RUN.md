# Run and Verify the Canonical Decision Contract

This guide applies only to [`contracts/decision.py`](contracts/decision.py). The escrow prototype is outside the submission scope.

## Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer
- GenLayer CLI

```bash
pip install -r requirements.txt
npm install -g genlayer
```

## 1. Validate locally

Run the canonical direct tests and lint the exact file that will be deployed:

```bash
pytest tests/direct/test_decision.py -v
genvm-lint check contracts/decision.py
```

Direct mode mocks the LLM and validates the leader path, parsing, errors, ID allocation, and storage. Independent validator execution is verified by the live StudioNet transaction.

## 2. Select StudioNet

```bash
genlayer network set studionet
genlayer network info
genlayer account
```

StudioNet is gasless, so a zero GEN balance does not block deployment or interaction.

## 3. Deploy

```bash
genlayer deploy --contract contracts/decision.py
```

Record both values from the output:

- Contract address
- Deployment transaction hash

Inspect the deployment receipt and confirm execution succeeded:

```bash
genlayer receipt <DEPLOY_TX_HASH> --stdout --stderr
genlayer schema <CONTRACT_ADDRESS>
genlayer code <CONTRACT_ADDRESS>
```

A transaction can reach `ACCEPTED` or `FINALIZED` even when contract execution failed. Treat the deployment as successful only when the receipt shows successful execution and the schema/code commands return the deployed contract.

## 4. Execute the AI decision

```bash
genlayer write <CONTRACT_ADDRESS> evaluate --args "Build a documented REST API with tests and clear acceptance criteria"
```

Record the write transaction hash, then inspect it:

```bash
genlayer receipt <WRITE_TX_HASH> --stdout --stderr
```

Confirm the receipt shows successful execution and a consensus result.

## 5. Verify persisted state

For a fresh deployment, the first evaluation is task `1`:

```bash
genlayer call <CONTRACT_ADDRESS> get_task --args 1
genlayer call <CONTRACT_ADDRESS> get_task_count
```

The stored task must contain:

- The submitted description
- A decision of `approved` or `rejected`
- A non-empty AI explanation
- A task count of `1`

## Evidence

The verified address, transaction hashes, receipt outcomes, and state output for the submitted deployment are recorded in [`SUBMISSION.md`](SUBMISSION.md).
