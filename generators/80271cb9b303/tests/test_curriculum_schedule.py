from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = REPO_ROOT / "generators" / "80271cb9b303" / "generator.py"
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"

if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

spec = importlib.util.spec_from_file_location(
    "generator_80271cb9b303_curriculum_test", GENERATOR_PATH
)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_period_curriculum_is_4_then_3_then_long_period(difficulty):
    """The declared three-example lesson must reserve slot 2 for periods 5 or 6."""
    long_periods: set[int] = set()
    for seed in range(64):
        observed = [
            gen.observe_overrides(gen.generate(seed, slot, difficulty=difficulty))["period"]
            for slot in range(gen.EXAMPLES_NEEDED)
        ]
        assert observed[0] == 4
        assert observed[1] == 3
        assert observed[2] in {5, 6}
        long_periods.add(observed[2])

    # The repair must not collapse the long-period slot to a single value.
    assert long_periods == {5, 6}
