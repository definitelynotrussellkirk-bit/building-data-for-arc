"""Regressions for the reusable cyclic lesson probe."""
import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
PROBE = HOME / "workspace/curriculum_probe.py"
spec = importlib.util.spec_from_file_location("cf09_curriculum_probe", PROBE)
probe = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(probe)


def test_probe_certifies_each_requested_cyclic_window():
    report = probe.audit(seed=17, starts=range(6), bands=("easy",))
    assert report["windows"] == 6
    assert report["failures"] == []
    assert report["unique_inputs"] == 9  # starts 0..5 overlap on sample indices 0..8
    assert set(report["competitors"]) == {
        "degree_at_least_three",
        "exact_five_component",
        "large_component_only",
    }
    assert all(count == 6 for count in report["refuted_windows"].values())
