"""Protected Racket fixture for task-local parametric tests."""
from __future__ import annotations
import pytest

@pytest.fixture(scope="session")
def protected_racket_bridge():
    from arc_repl.racket_bridge import RacketBridge
    bridge = RacketBridge(max_calls_before_restart=96)
    try:
        yield bridge
    finally:
        bridge.shutdown()
