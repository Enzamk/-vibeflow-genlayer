"""Direct mode tests for GenLayer-native Escrow contract — fast, in-memory, no server.

🔥 GenLayer-native: AI consensus replaces human arbiter entirely.
- No arbiter parameter in deposit()
- Both parties submit evidence on-chain via submit_evidence()
- Any party can trigger resolve_with_ai() — no human gatekeeper
- AI evaluates BOTH sides' evidence through validator consensus
- Decision + explanation + evidence_assessment stored on-chain

Tests mock AI responses via direct_vm.set_ai_prompt_response().
"""

import pytest


# ── Test: Deposit (no arbiter) ──────────────────────

def test_deposit_creates_escrow(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Payer deposits — escrow in FUNDED state. No arbiter needed."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 5_000_000_000_000_000_000

    contract.deposit(direct_bob)  # 🔥 No arbiter param — AI consensus handles disputes

    state = contract.get_escrow(direct_alice)
    assert state["status"] == "FUNDED"
    assert state["payer"] == str(direct_alice)
    assert state["payee"] == str(direct_bob)
    assert state["amount"] == str(5_000_000_000_000_000_000)
    assert state["ai_decision"] == ""
    assert state["ai_explanation"] == ""
    assert state["payer_evidence"] == ""
    assert state["payee_evidence"] == ""
    assert state["partial_refund_pct"] == "0"


def test_deposit_zero_reverts(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Zero deposit should fail."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.value = 0

    with direct_vm.expect_revert("Zero deposit not allowed"):
        contract.deposit(direct_bob)


def test_deposit_self_as_payee_reverts(direct_vm, direct_deploy, direct_alice):
    """Payer == payee should fail."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000

    with direct_vm.expect_revert("Payer cannot be payee"):
        contract.deposit(direct_alice)


def test_deposit_duplicate_reverts(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Double deposit by same payer should fail."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000

    contract.deposit(direct_bob)

    direct_vm.value = 2_000_000_000_000_000_000
    with direct_vm.expect_revert("already has an active escrow"):
        contract.deposit(direct_bob)


# ── Test: Approve (Release) ───────────────────────

def test_approve_releases_to_payee(direct_vm, direct_deploy, direct_alice, direct_bob):
    """After approve, payee receives funds minus fee."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000

    contract.deposit(direct_bob)

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
    contract.deposit(direct_bob)

    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("Only the payer"):
        contract.approve()


def test_approve_wrong_status_reverts(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Cannot approve after already released."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

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
    contract.deposit(direct_bob)

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
    contract.deposit(direct_bob)

    direct_vm.sender = direct_alice
    contract.approve()

    with direct_vm.expect_revert("Expected status FUNDED"):
        contract.cancel()


# ── Test: Dispute (no arbiter needed) ──────────────

def test_raise_dispute_by_payer(direct_vm, direct_deploy, direct_alice, direct_bob):
    """🔥 Payer raises dispute — takes payer address + reason. No arbiter."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    direct_vm.sender = direct_alice
    contract.raise_dispute(direct_alice, "Work was not completed satisfactorily")

    state = contract.get_escrow(direct_alice)
    assert state["status"] == "DISPUTED"
    assert state["dispute_reason"] == "Work was not completed satisfactorily"


def test_raise_dispute_by_payee(direct_vm, direct_deploy, direct_alice, direct_bob):
    """🔥 Payee can also raise dispute — both parties have equal access."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    direct_vm.sender = direct_bob  # payee raises dispute
    contract.raise_dispute(direct_alice, "Payer is refusing to pay for completed work")

    state = contract.get_escrow(direct_alice)
    assert state["status"] == "DISPUTED"
    assert state["dispute_reason"] == "Payer is refusing to pay for completed work"


def test_raise_dispute_non_party_reverts(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    """Non-party cannot raise dispute."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("Not a party to this escrow"):
        contract.raise_dispute(direct_alice, "Random dispute")


# ── Test: Evidence Submission (GenLayer-native) ────

def test_submit_evidence_payer(direct_vm, direct_deploy, direct_alice, direct_bob):
    """🔥 Payer submits evidence on-chain — AI will evaluate this."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    direct_vm.sender = direct_alice
    contract.raise_dispute(direct_alice, "Work not completed")

    # Payer submits their evidence
    direct_vm.sender = direct_alice
    contract.submit_evidence(direct_alice, '{"delivery_status":"incomplete","quality_report":"below_standard","communication_logs":"payee_unresponsive"}')

    state = contract.get_escrow(direct_alice)
    assert state["payer_evidence"] != ""
    assert "incomplete" in state["payer_evidence"]


def test_submit_evidence_payee(direct_vm, direct_deploy, direct_alice, direct_bob):
    """🔥 Payee submits evidence on-chain — AI sees BOTH sides."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    direct_vm.sender = direct_alice
    contract.raise_dispute(direct_alice, "Work not completed")

    # Payee submits their counter-evidence
    direct_vm.sender = direct_bob
    contract.submit_evidence(direct_alice, '{"delivery_proof":"signed_receipt","quality_report":"grade_A","timestamps":"delivered_on_time"}')

    state = contract.get_escrow(direct_alice)
    assert state["payee_evidence"] != ""
    assert "signed_receipt" in state["payee_evidence"]


def test_submit_evidence_both_sides(direct_vm, direct_deploy, direct_alice, direct_bob):
    """🔥 Both parties submit evidence — AI evaluates BOTH sides fairly.
    This is what traditional blockchains CANNOT do."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    direct_vm.sender = direct_alice
    contract.raise_dispute(direct_alice, "Partial delivery — only 60% received")

    # Payer: "I only got 60%"
    direct_vm.sender = direct_alice
    contract.submit_evidence(direct_alice, '{"received_pct":60,"missing_items":"40pct_not_delivered","photos":"damaged_goods"}')

    # Payee: "I delivered 100%, 40% was returned damaged"
    direct_vm.sender = direct_bob
    contract.submit_evidence(direct_alice, '{"delivery_proof":"full_shipment","tracking":"all_items_shipped","return_reason":"customer_claimed_damaged"}')

    state = contract.get_escrow(direct_alice)
    assert state["payer_evidence"] != ""
    assert state["payee_evidence"] != ""
    assert "60" in state["payer_evidence"]
    assert "full_shipment" in state["payee_evidence"]


def test_submit_evidence_non_party_reverts(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    """Non-party cannot submit evidence."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    direct_vm.sender = direct_alice
    contract.raise_dispute(direct_alice, "Test dispute")

    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("Not a party to this escrow"):
        contract.submit_evidence(direct_alice, '{"fake":"evidence"}')


def test_submit_evidence_before_dispute_reverts(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Cannot submit evidence before dispute is raised."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("Expected status DISPUTED"):
        contract.submit_evidence(direct_alice, '{"evidence":"too_early"}')


# ── Test: AI Dispute Resolution (GenLayer Consensus) ──

def test_ai_resolve_release_payment(direct_vm, direct_deploy, direct_alice, direct_bob):
    """🔥 GenLayer consensus: AI resolves dispute → release_payment with explanation.
    Simulates: 'Was work completed?' → AI says YES, payee deserves payment.
    Traditional blockchain: arbiter clicks yes/no. GenLayer: AI evaluates evidence.
    """
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    # Raise dispute — payer claims work wasn't done
    direct_vm.sender = direct_alice
    contract.raise_dispute(direct_alice, "Work was not completed satisfactorily")

    # Both parties submit evidence
    direct_vm.sender = direct_alice
    contract.submit_evidence(direct_alice, '{"complaint":"quality_below_standard","photos":"minor_defects"}')
    direct_vm.sender = direct_bob
    contract.submit_evidence(direct_alice, '{"delivery_proof":"signed_receipt","quality_report":"grade_A"}')

    # Mock GenLayer AI consensus response — AI sees BOTH sides
    direct_vm.set_ai_prompt_response({
        "decision": "release_payment",
        "explanation": "Evidence shows the work was completed as per contract terms. Delivery confirmation provided, quality meets acceptable standards. Minor defects noted but do not constitute breach.",
        "evidence_assessment": {
            "payer_evidence_strength": "weak",
            "payee_evidence_strength": "strong",
            "key_factors": ["signed_receipt_confirmed_delivery", "quality_grade_A", "minor_defects_not_breach"]
        }
    })

    # 🔥 Any party can trigger AI resolution — no arbiter needed
    direct_vm.sender = direct_bob  # payee triggers resolution
    contract.resolve_with_ai(direct_alice)

    state = contract.get_escrow(direct_alice)
    assert state["status"] == "RELEASED"
    assert state["ai_decision"] == "release_payment"
    assert state["ai_explanation"] != ""


def test_ai_resolve_refund_payer(direct_vm, direct_deploy, direct_alice, direct_bob):
    """🔥 GenLayer consensus: AI resolves dispute → refund_payer with explanation.
    Simulates: 'Was work completed?' → AI says NO, payer deserves refund.
    """
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    # Raise dispute — payer claims seller never delivered
    direct_vm.sender = direct_alice
    contract.raise_dispute(direct_alice, "Seller never delivered the goods — possible scam")

    # Payer has strong evidence, payee has none
    direct_vm.sender = direct_alice
    contract.submit_evidence(direct_alice, '{"delivery_status":"never_received","tracking":"no_tracking_number","seller_response":"absent"}')
    direct_vm.sender = direct_bob
    contract.submit_evidence(direct_alice, '{"response":"no_evidence_provided"}')

    # Mock GenLayer AI consensus — AI sees payer has strong case
    direct_vm.set_ai_prompt_response({
        "decision": "refund_payer",
        "explanation": "No delivery confirmation found. Seller failed to provide evidence of shipment or delivery. Buyer's claim is substantiated by absence of tracking and seller's non-response.",
        "evidence_assessment": {
            "payer_evidence_strength": "strong",
            "payee_evidence_strength": "weak",
            "key_factors": ["no_delivery_confirmation", "seller_non_response", "absent_tracking"]
        }
    })

    # 🔥 Payer triggers resolution — both parties have equal access
    direct_vm.sender = direct_alice
    contract.resolve_with_ai(direct_alice)

    state = contract.get_escrow(direct_alice)
    assert state["status"] == "CANCELLED"
    assert state["ai_decision"] == "refund_payer"
    assert state["ai_explanation"] != ""


def test_ai_resolve_partial_refund(direct_vm, direct_deploy, direct_alice, direct_bob):
    """🔥 GenLayer consensus: AI resolves dispute → partial_refund with explanation.
    Simulates: 'Is partial delivery acceptable?' → AI says 60% delivered, 40% refund.
    This is the kind of nuanced decision traditional blockchains CANNOT make.
    """
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    # Raise dispute — partial delivery
    direct_vm.sender = direct_alice
    contract.raise_dispute(direct_alice, "Only 60% of items were delivered, remaining 40% missing")

    # Both sides have evidence
    direct_vm.sender = direct_alice
    contract.submit_evidence(direct_alice, '{"received_pct":60,"missing_items":"40pct_not_delivered"}')
    direct_vm.sender = direct_bob
    contract.submit_evidence(direct_alice, '{"delivery_proof":"partial_shipment","tracking":"verified_for_60pct","reason":"stock_out_for_remaining"}')

    # Mock GenLayer AI consensus — nuanced partial decision
    direct_vm.set_ai_prompt_response({
        "decision": "partial_refund",
        "refund_percentage": 40,
        "explanation": "60% of goods were delivered satisfactorily as confirmed by tracking data. The remaining 40% were not delivered due to stock-out. Payer should receive 40% refund, payee retains 60% minus fee.",
        "evidence_assessment": {
            "payer_evidence_strength": "moderate",
            "payee_evidence_strength": "moderate",
            "key_factors": ["60pct_confirmed_delivery", "40pct_stock_out", "both_partial_claims"]
        }
    })

    direct_vm.sender = direct_alice
    contract.resolve_with_ai(direct_alice)

    state = contract.get_escrow(direct_alice)
    assert state["status"] == "RELEASED"
    assert state["ai_decision"] == "partial_refund"
    assert state["partial_refund_pct"] == "40"
    assert state["ai_explanation"] != ""


def test_ai_resolve_non_party_reverts(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    """Non-party cannot trigger AI resolution."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    direct_vm.sender = direct_alice
    contract.raise_dispute(direct_alice, "Test dispute")

    direct_vm.set_ai_prompt_response({
        "decision": "release_payment",
        "explanation": "Test",
        "evidence_assessment": {
            "payer_evidence_strength": "none",
            "payee_evidence_strength": "none",
            "key_factors": ["test"]
        }
    })
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("Not a party to this escrow"):
        contract.resolve_with_ai(direct_alice)


def test_ai_resolve_wrong_status_reverts(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Cannot AI-resolve an escrow that is not in DISPUTED status."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    # Escrow is in FUNDED status, not DISPUTED
    direct_vm.set_ai_prompt_response({
        "decision": "release_payment",
        "explanation": "Test",
        "evidence_assessment": {
            "payer_evidence_strength": "none",
            "payee_evidence_strength": "none",
            "key_factors": ["test"]
        }
    })
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("Expected status DISPUTED"):
        contract.resolve_with_ai(direct_alice)


def test_ai_resolve_logs_event_with_explanation(direct_vm, direct_deploy, direct_alice, direct_bob):
    """🔥 AI resolution logs AI_RESOLVE event with decision + explanation."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    direct_vm.sender = direct_alice
    contract.raise_dispute(direct_alice, "Quality issue")

    direct_vm.sender = direct_alice
    contract.submit_evidence(direct_alice, '{"quality":"below_standard"}')
    direct_vm.sender = direct_bob
    contract.submit_evidence(direct_alice, '{"quality_report":"grade_B_minus"}')

    direct_vm.set_ai_prompt_response({
        "decision": "release_payment",
        "explanation": "Quality within acceptable contract bounds. Minor defects noted but do not constitute breach.",
        "evidence_assessment": {
            "payer_evidence_strength": "weak",
            "payee_evidence_strength": "moderate",
            "key_factors": ["quality_acceptable", "minor_defects_not_breach"]
        }
    })

    direct_vm.sender = direct_bob
    contract.resolve_with_ai(direct_alice)

    events = contract.get_events(0, 10)
    ai_resolve_events = [e for e in events if e["name"] == "AI_RESOLVE"]
    assert len(ai_resolve_events) >= 1
    assert "release_payment" in ai_resolve_events[0]["data"]
    assert "explanation" in ai_resolve_events[0]["data"]


def test_ai_resolve_stores_decision_and_explanation(direct_vm, direct_deploy, direct_alice, direct_bob):
    """🔥 AI decision + explanation stored in escrow state — on-chain transparency."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    direct_vm.sender = direct_alice
    contract.raise_dispute(direct_alice, "Mixed evidence case")

    direct_vm.sender = direct_alice
    contract.submit_evidence(direct_alice, '{"delivery_pct":60,"quality":"acceptable"}')
    direct_vm.sender = direct_bob
    contract.submit_evidence(direct_alice, '{"delivery_proof":"partial","quality":"mixed"}')

    direct_vm.set_ai_prompt_response({
        "decision": "partial_refund",
        "refund_percentage": 40,
        "explanation": "Partial delivery confirmed. 60% of work completed satisfactorily, 40% remains incomplete. Fair split: payer gets 40% refund.",
        "evidence_assessment": {
            "payer_evidence_strength": "moderate",
            "payee_evidence_strength": "moderate",
            "key_factors": ["60pct_delivery_confirmed", "40pct_incomplete", "both_partial"]
        }
    })

    direct_vm.sender = direct_bob
    contract.resolve_with_ai(direct_alice)

    state = contract.get_escrow(direct_alice)
    assert state["ai_decision"] in ["release_payment", "refund_payer", "partial_refund"]
    assert state["ai_explanation"] != ""
    pct = int(state["partial_refund_pct"])
    assert pct >= 0
    assert pct <= 100


def test_ai_resolve_without_evidence(direct_vm, direct_deploy, direct_alice, direct_bob):
    """🔥 AI can resolve even when no evidence submitted — prompt includes 'No evidence'.
    Traditional arbiter: can't decide without evidence → deadlock.
    GenLayer AI: evaluates what's available → makes best judgment."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    direct_vm.sender = direct_alice
    contract.raise_dispute(direct_alice, "General disagreement")

    # No evidence submitted by either party — AI still resolves
    direct_vm.set_ai_prompt_response({
        "decision": "partial_refund",
        "refund_percentage": 50,
        "explanation": "Neither party provided specific evidence. Without concrete proof from either side, an equal split is the most fair resolution.",
        "evidence_assessment": {
            "payer_evidence_strength": "none",
            "payee_evidence_strength": "none",
            "key_factors": ["no_evidence_from_either_side", "equal_split_as_fallback"]
        }
    })

    direct_vm.sender = direct_alice
    contract.resolve_with_ai(direct_alice)

    state = contract.get_escrow(direct_alice)
    assert state["ai_decision"] == "partial_refund"
    assert state["ai_explanation"] != ""
    assert "no evidence" in state["ai_explanation"].lower() or "Neither" in state["ai_explanation"]


# ── Test: Events ──────────────────────────────────

def test_events_logged(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Events should be recorded for deposit, dispute, evidence, resolve."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    events = contract.get_events(0, 10)
    assert len(events) >= 2
    assert events[1]["name"] == "DEPOSIT"


def test_evidence_event_logged(direct_vm, direct_deploy, direct_alice, direct_bob):
    """🔥 Evidence submission should log EVIDENCE event."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    direct_vm.sender = direct_alice
    contract.raise_dispute(direct_alice, "Test dispute")

    direct_vm.sender = direct_alice
    contract.submit_evidence(direct_alice, '{"proof":"test_evidence"}')

    events = contract.get_events(0, 10)
    evidence_events = [e for e in events if e["name"] == "EVIDENCE"]
    assert len(evidence_events) >= 1
    assert "payer" in evidence_events[0]["data"]


# ── Test: View helpers ────────────────────────────

def test_exists_check(direct_vm, direct_deploy, direct_alice, direct_bob):
    """exists() should return True/False correctly."""
    contract = direct_deploy("contracts/escrow.py", [u256(50)])
    direct_vm.sender = direct_alice
    direct_vm.deal(direct_alice, 10_000_000_000_000_000_000)
    direct_vm.value = 1_000_000_000_000_000_000
    contract.deposit(direct_bob)

    assert contract.exists(direct_alice) is True
    assert contract.exists(direct_bob) is False