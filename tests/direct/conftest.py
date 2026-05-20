"""Shared fixtures for direct mode tests."""
import pytest

pytest_plugins = ["genlayer_test"]

# conftest.py is auto-discovered by pytest. The genlayer_test plugin provides:
#   direct_vm        — VMContext with cheatcodes
#   direct_deploy    — deploy a contract file
#   direct_alice     — test address
#   direct_bob       — test address
#   direct_charlie   — test address
#   direct_owner     — owner address
#   direct_accounts  — list of test addresses