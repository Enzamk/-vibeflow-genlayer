"""Shared fixtures for direct mode tests."""

import json
import re
import pytest
from pathlib import Path
from typing import Any, Optional, Callable

from gltest.direct.vm import VMContext
from gltest.direct.loader import deploy_contract, create_address

# ── Patch SDK to read contract headers as UTF-8 ──────────────────
# The gltest SDK's parse_contract_header() opens the contract file with
# open(path, "r") — no encoding — so on Windows it defaults to cp1252,
# which crashes on the Unicode box-drawing chars (─) and emojis (🔥) in
# our contract comments. Monkey-patch it to force UTF-8.
import gltest.direct.sdk_loader as _sdk_loader


def _parse_contract_header_utf8(contract_path: Path):
    deps = {}
    with open(contract_path, "r", encoding="utf-8") as f:
        content = f.read(2000)
    pattern = r'"Depends":\s*"([^:]+):([^"]+)"'
    for match in re.finditer(pattern, content):
        name, hash_val = match.groups()
        deps[name] = hash_val
    return deps


# setup_sdk_paths() calls parse_contract_header as a module-global, so
# patching it on the sdk_loader module is enough.
_sdk_loader.parse_contract_header = _parse_contract_header_utf8

# The gltest package (genlayer-test) auto-registers its pytest plugin via
# setuptools entry points, including the direct-mode plugin that provides:
#   direct_vm, direct_alice, direct_bob, direct_charlie, direct_owner,
#   direct_accounts
#
# We override `direct_deploy` here to pin a GenVM SDK version that ships a
# `genvm-universal.tar.xz` asset (v0.2.16). The latest GitHub release
# (v0.3.0-rc7) only has platform-specific assets, which the SDK's downloader
# cannot fetch, causing HTTP 404 on Windows.

# Stable GenVM release with a universal tarball asset
PINNED_SDK_VERSION = "v0.2.16"


@pytest.fixture(autouse=True)
def _compat_shims(direct_vm: VMContext):
    """Compatibility shims for the new gltest SDK (v0.29.2).

    1. Inject a LAZY u256 into builtins so test files can use u256(1) without
       importing. The real `u256` lives in the `genlayer` module, which the
       SDK only adds to sys.path at deploy time — so we can't import it up
       front. The shim resolves the real u256 on first call (after deploy)
       and then replaces itself in builtins for zero overhead on later calls.

    2. Add set_ai_prompt_response() compat method to direct_vm.
       The new SDK renamed set_ai_prompt_response(response) to
       mock_llm(prompt_pattern, response). This shim restores the old
       single-argument API so existing tests don't need to change every call.
    """
    import builtins

    def _lazy_u256(*args, **kwargs):
        # genlayer is added to sys.path by deploy_contract(); import lazily.
        from genlayer import u256 as _real_u256
        builtins.u256 = _real_u256  # swap in the real type for next calls
        return _real_u256(*args, **kwargs)

    builtins.u256 = _lazy_u256

    def set_ai_prompt_response(response):
        # Clear previous LLM mocks (old API replaced, new API accumulates).
        # Only clear LLM mocks, not web mocks.
        direct_vm._llm_mocks.clear()
        direct_vm._llm_mocks_hit.clear()
        # Convert dict/list to JSON string (wasi_mock auto-parses JSON strings)
        if isinstance(response, (dict, list)):
            response = json.dumps(response)
        # Catch-all pattern matches any prompt
        direct_vm.mock_llm(".*", response)

    direct_vm.set_ai_prompt_response = set_ai_prompt_response


def _apply_gl_compat_shims(direct_vm: VMContext) -> None:
    """Patch genlayer.gl with transfer() and contract_balance.

    The pinned SDK (v0.2.16) doesn't expose gl.transfer() or
    gl.contract_balance as top-level names. We add them using the
    wasi_mock's get_balance / get_self_balance + the VM's _balances dict.

    Called after every deploy_contract() because the loader re-imports
    genlayer.gl each time, wiping any attributes we set previously.
    """
    import genlayer.gl as _gl

    def _to_addr_bytes(addr) -> bytes:
        if hasattr(addr, 'as_bytes') and not isinstance(addr, (bytes, bytearray)):
            return addr.as_bytes
        if hasattr(addr, '__bytes__'):
            return bytes(addr)
        if isinstance(addr, (bytes, bytearray)):
            return bytes(addr)
        return bytes(str(addr), 'utf-8')

    def _transfer(to, amount, on="accepted") -> None:
        """Move native tokens from contract balance to recipient."""
        amount = int(amount)
        if amount <= 0:
            return
        vm = direct_vm
        # debit contract
        contract_addr = vm._contract_address
        if contract_addr is not None:
            ca = _to_addr_bytes(contract_addr)
            vm._balances[ca] = vm._balances.get(ca, 0) - amount
        # credit recipient
        ra = _to_addr_bytes(to)
        vm._balances[ra] = vm._balances.get(ra, 0) + amount

    class _ContractBalanceDesc:
        """Int-like proxy for gl.contract_balance."""
        def __int__(self) -> int:
            from _genlayer_wasi import get_self_balance
            return get_self_balance()
        def __eq__(self, other):
            return int(self) == int(other)
        def __gt__(self, other):
            return int(self) > int(other)
        def __lt__(self, other):
            return int(self) < int(other)

    _gl.transfer = _transfer
    _gl.contract_balance = _ContractBalanceDesc()


@pytest.fixture
def direct_deploy(direct_vm: VMContext) -> Callable[..., Any]:
    """Factory fixture for deploying contracts directly.

    Overrides the default to pin a GenVM SDK version that has a downloadable
    universal artifact.
    """
    def _deploy(
        contract_path: str,
        *args: Any,
        sdk_version: Optional[str] = PINNED_SDK_VERSION,
        **kwargs: Any,
    ) -> Any:
        path = Path(contract_path)

        if not path.is_absolute():
            if path.exists():
                path = path.resolve()
            else:
                for base in [
                    Path.cwd(),
                    Path.cwd() / "contracts",
                    Path.cwd() / "intelligent-contracts",
                ]:
                    candidate = base / contract_path
                    if candidate.exists():
                        path = candidate.resolve()
                        break

        result = deploy_contract(path, direct_vm, *args, sdk_version=sdk_version, **kwargs)
        # Apply gl.transfer / gl.contract_balance shim after genlayer is loaded
        _apply_gl_compat_shims(direct_vm)
        return result

    return _deploy


# ── Address fixtures: return proper Address objects ──────────────
# create_address() falls back to raw bytes when genlayer isn't on sys.path
# yet (before first deploy). We wrap the result so tests always get a real
# Address with proper str() (hex) and comparison semantics.
def _make_addr(seed: str):
    """Create a deterministic Address, converting bytes fallback to Address.

    create_address() returns raw bytes when genlayer isn't on sys.path yet.
    We add the cached SDK path so we can build a proper Address (with hex
    str() and comparison semantics) before any deploy runs.
    """
    raw = create_address(seed)
    # If it's already a proper Address (genlayer was importable), return as-is
    if hasattr(raw, 'as_bytes') and not isinstance(raw, (bytes, bytearray)):
        return raw
    # Add cached genlayer SDK to sys.path so we can import Address
    import sys as _sys
    try:
        from genlayer.py.types import Address
    except ImportError:
        # Find the cached std lib and add to path
        cache_dir = _sdk_loader.CACHE_DIR
        for root, dirs, _ in __import__('os').walk(cache_dir):
            if root.endswith('py-lib-genlayer-std'):
                # The actual package is one level deeper (hash subdir)
                for d in dirs:
                    candidate = __import__('os').path.join(root, d)
                    if candidate not in _sys.path:
                        _sys.path.insert(0, candidate)
                    break
                break
        try:
            from genlayer.py.types import Address
        except ImportError:
            return raw  # give up, return bytes
    return Address(bytes(raw))


@pytest.fixture
def direct_alice():
    return _make_addr("alice")


@pytest.fixture
def direct_bob():
    return _make_addr("bob")


@pytest.fixture
def direct_charlie():
    return _make_addr("charlie")


@pytest.fixture
def direct_owner():
    return _make_addr("default_sender")
