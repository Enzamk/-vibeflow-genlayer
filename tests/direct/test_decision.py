"""Direct mode tests for the MINIMAL AI-Assisted Decision Contract.

🔥 GenLayer-native: AI consensus evaluates a string input → decision saved.

Flow:
  evaluate(description)  →  AI consensus (leader + validator)  →  "approved"/"rejected" saved

NO token transfers, NO balances, NO msg.sender, NO escrow.

CONSENSUS PATH:
- evaluate() runs gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
- leader_fn   -> gl.nondet.exec_prompt(prompt, response_format="json")
- validator_fn -> independently reruns the SAME prompt, compares `decision` EXACTLY

Tests mock the LLM via direct_vm.set_ai_prompt_response().
In direct mode the validator is NOT exercised (per GenLayer testing strategy);
the leader path + parsing + storage is validated here.
"""

import pytest


# ── Test: Evaluate (the ONE core method) ───────────

def test_evaluate_approves(direct_vm, direct_deploy):
    """🔥 Input string → AI says approved → saved on-chain."""
    contract = direct_deploy("contracts/decision.py")

    direct_vm.set_ai_prompt_response({
        "decision": "approved",
        "explanation": "Task is clear, well-defined, and feasible."
    })

    result = contract.evaluate("Build a REST API for a todo app with Node.js")
    assert result == "approved"

    state = contract.get_task(u256(1))
    assert state["decision"] == "approved"
    assert state["description"] == "Build a REST API for a todo app with Node.js"
    assert state["explanation"] != ""


def test_evaluate_rejects(direct_vm, direct_deploy):
    """🔥 Input string → AI says rejected → saved on-chain."""
    contract = direct_deploy("contracts/decision.py")

    direct_vm.set_ai_prompt_response({
        "decision": "rejected",
        "explanation": "Task is too vague to evaluate."
    })

    result = contract.evaluate("do something")
    assert result == "rejected"

    state = contract.get_task(u256(1))
    assert state["decision"] == "rejected"
    assert state["explanation"] != ""


def test_evaluate_empty_reverts(direct_vm, direct_deploy):
    """Empty input should fail."""
    contract = direct_deploy("contracts/decision.py")

    with direct_vm.expect_revert("Description cannot be empty"):
        contract.evaluate("")


# ── Test: Multiple tasks increment IDs ─────────────

def test_evaluate_multiple_tasks(direct_vm, direct_deploy):
    """Multiple evaluations get incrementing IDs."""
    contract = direct_deploy("contracts/decision.py")

    direct_vm.set_ai_prompt_response({"decision": "approved", "explanation": "OK"})
    contract.evaluate("Task one")

    direct_vm.set_ai_prompt_response({"decision": "rejected", "explanation": "No"})
    contract.evaluate("Task two")

    assert contract.get_task_count() == 2

    t1 = contract.get_task(u256(1))
    t2 = contract.get_task(u256(2))
    assert t1["decision"] == "approved"
    assert t2["decision"] == "rejected"


# ── Test: LLM Resilience (defensive parsing) ───────

def test_evaluate_handles_json_string(direct_vm, direct_deploy):
    """🔥 LLM returns JSON wrapped in text — contract parses it."""
    contract = direct_deploy("contracts/decision.py")

    direct_vm.set_ai_prompt_response(
        'Here is my eval: {"decision": "approved", "explanation": "Good."} Done.'
    )

    result = contract.evaluate("Build a blog")
    assert result == "approved"


def test_evaluate_handles_key_aliases(direct_vm, direct_deploy):
    """🔥 LLM uses alternate key names — contract aliases them."""
    contract = direct_deploy("contracts/decision.py")

    direct_vm.set_ai_prompt_response({
        "verdict": "rejected",
        "reasoning": "Too vague."
    })

    result = contract.evaluate("stuff")
    assert result == "rejected"

    state = contract.get_task(u256(1))
    assert state["explanation"] == "Too vague."


def test_evaluate_accepts_exact_decision_alias(direct_vm, direct_deploy):
    """A known decision alias is normalized."""
    contract = direct_deploy("contracts/decision.py")

    direct_vm.set_ai_prompt_response({
        "decision": "APPROVE",
        "explanation": "Clear enough."
    })

    assert contract.evaluate("Build a documented API") == "approved"


@pytest.mark.parametrize("decision", ["maybe", "unapproved", "not rejected"])
def test_evaluate_invalid_decision_reverts(direct_vm, direct_deploy, decision):
    """Unknown or ambiguous decisions are rejected."""
    contract = direct_deploy("contracts/decision.py")

    direct_vm.set_ai_prompt_response({
        "decision": decision,
        "explanation": "Invalid output."
    })

    with direct_vm.expect_revert():
        contract.evaluate("Some task")


# ── Test: View methods ─────────────────────────────

def test_get_task_count(direct_vm, direct_deploy):
    """Task count reflects evaluations done."""
    contract = direct_deploy("contracts/decision.py")

    assert contract.get_task_count() == 0

    direct_vm.set_ai_prompt_response({"decision": "approved", "explanation": "OK"})
    contract.evaluate("Task A")

    assert contract.get_task_count() == 1


def test_get_task_returns_full_state(direct_vm, direct_deploy):
    """get_task returns description + decision + explanation."""
    contract = direct_deploy("contracts/decision.py")

    direct_vm.set_ai_prompt_response({
        "decision": "approved",
        "explanation": "Clear and feasible."
    })
    contract.evaluate("Build a weather app")

    state = contract.get_task(u256(1))
    assert state["task_id"] == "1"
    assert state["description"] == "Build a weather app"
    assert state["decision"] == "approved"
    assert state["explanation"] == "Clear and feasible."
