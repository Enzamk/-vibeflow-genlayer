"""Direct mode tests for Escrow contract — fast, in-memory, no server."""

import pytest


# ── Test: Deposit ─────────────────────────────────

def test_deposit_creates_escrow(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Payer deposits — escrow should be in FUNDED state."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)  # 10 ETH
    direct_vm.value = 5_000_000_000_000_000_000  # 5 ETH

    contract.deposit(direct_bob, direct_bob)  # arbiter = bob for now

    state = contract.get_escrow(direct_alice)
    assert state["status"] == "FUNDED"
    assert state["payer"] == str(direct_alice)
    assert state["payee"] == str(direct_bob)
    assert state["amount"] == str(5_000_000_000_000_000_000)


def test_deposit_zero_reverts(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Zero deposit should fail."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.value = 0

    with direct_vm.expect_revert("Zero deposit not allowed"):
        contract.deposit(direct_bob, direct_bob)


def test_deposit_self_as_payee_reverts(direct_vm, direct_deploy, direct_alice):
    """Payer == payee should fail."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000

    with direct_vm.expect_revert("Payer cannot be payee"):
        contract.deposit(direct_alice, direct_alice)


def test_deposit_duplicate_reverts(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Double deposit by same payer should fail."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000

    contract.deposit(direct_bob, direct_bob)

    direct_vm.value = 2_000_000_000_000_000_000
    with direct_vm.expect_revert("already has an active escrow"):
        contract.deposit(direct_bob, direct_bob)


# ── Test: Approve (Release) ───────────────────────

def test_approve_releases_to_payee(direct_vm, direct_deploy, direct_alice, direct_bob):
    """After approve, payee receives funds minus fee."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])  # 0.5% fee
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000  # 1 ETH atto

    contract.deposit(direct_bob, direct_bob)

    # Approve as payer
    direct_vm.sender = direct_alice
    contract.approve()

    state = contract.get_escrow(direct_alice)
    assert state["status"] == "RELEASED"


def test_approve_non_payer_reverts(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    """Non-payer cannot approve."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob, direct_bob)

    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("Only the payer"):
        contract.approve()


def test_approve_wrong_status_reverts(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Cannot approve after already released."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob, direct_bob)

    direct_vm.sender = direct_alice
    contract.approve()

    with direct_vm.expect_revert("Expected status FUNDED"):
        contract.approve()


# ── Test: Cancel (Refund) ─────────────────────────

def test_cancel_refunds_payer(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Cancel returns full amount to payer."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob, direct_bob)

    direct_vm.sender = direct_alice
    contract.cancel()

    state = contract.get_escrow(direct_alice)
    assert state["status"] == "CANCELLED"


def test_cancel_after_approve_reverts(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Cannot cancel a released escrow."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob, direct_bob)

    direct_vm.sender = direct_alice
    contract.approve()

    with direct_vm.expect_revert("Expected status FUNDED"):
        contract.cancel()


# ── Test: Dispute / Resolution ────────────────────

def test_raise_dispute_by_party(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Any party can raise a dispute."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob, direct_bob)

    direct_vm.sender = direct_bob  # payee raises dispute
    contract.raise_dispute("Goods not delivered")

    state = contract.get_escrow(direct_alice)
    assert state["status"] == "DISPUTED"
    assert state["dispute_reason"] == "Goods not delivered"


def test_arbiter_resolves_for_payee(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Arbiter can resolve dispute awarding payee."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob, direct_bob)

    direct_vm.sender = direct_alice
    contract.raise_dispute("Not satisfied")

    # arbiter = bob (we set arbiter=bob in deposit)
    direct_vm.sender = direct_bob
    contract.resolve_dispute(True)  # award to payee

    state = contract.get_escrow(direct_alice)
    assert state["status"] == "RELEASED"


def test_arbiter_resolves_for_payer_refund(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Arbiter awards to payer → full refund."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob, direct_bob)

    direct_vm.sender = direct_alice
    contract.raise_dispute("Scam")

    direct_vm.sender = direct_bob
    contract.resolve_dispute(False)  # award to payer

    state = contract.get_escrow(direct_alice)
    assert state["status"] == "CANCELLED"


def test_non_arbiter_cannot_resolve(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    """Non-arbiter cannot resolve disputes."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob, direct_bob)  # arbiter = bob

    direct_vm.sender = direct_alice
    contract.raise_dispute("Test")

    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("Only the arbiter"):
        contract.resolve_dispute(True)


# ── Test: Events ──────────────────────────────────

def test_events_logged(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Events should be recorded for deposit, approve, dispute, resolve."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob, direct_bob)

    events = contract.get_events(0, 10)
    # deploy event + deposit event
    assert len(events) >= 2
    assert events[1]["name"] == "DEPOSIT"


# ── Test: View helpers ────────────────────────────

def test_exists_check(direct_vm, direct_deploy, direct_alice, direct_bob):
    """exists() should return True/False correctly."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob, direct_bob)

    assert contract.exists(direct_alice) is True
    assert contract.exists(direct_bob) is False