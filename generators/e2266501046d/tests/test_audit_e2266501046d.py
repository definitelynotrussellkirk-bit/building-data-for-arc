from pathlib import Path
import importlib.util
import pytest
from reviewer_support import canonical_pairs, find_root
ROOT = find_root(__file__)
SPEC = importlib.util.spec_from_file_location("audited_" + Path(__file__).parents[1].name, Path(__file__).parents[1] / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

@pytest.mark.parametrize("value", [True, False, 1.0, "2", -1])
def test_invalid_exact_color_rejected(value):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(991, 0, difficulty="easy", color=value)

@pytest.mark.parametrize("value", [True, False, 1.0, "2", -1])
def test_invalid_index_rejected(value):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(991, value, difficulty="easy")

def test_metadata_checks_type_as_well_as_value():
    grid = GEN.generate(991, 0, color=1)
    assert GEN.self_check(grid, meta={"overrides": {"color": True}})
