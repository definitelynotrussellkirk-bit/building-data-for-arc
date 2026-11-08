"""Shared protected-runtime fixture for this task's portable test suite."""
from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def protected_racket_bridge():
    """Reuse one protected Racket process across all parity checks.

    Repeated process startup was intermittently stalling the staged task-test
    runner even though every individual parity check was sound.  A single
    bounded bridge keeps the same protected execution semantics while removing
    that startup-only flake.
    """
    from arc_repl.racket_bridge import RacketBridge

    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        yield bridge
    finally:
        bridge.shutdown()
