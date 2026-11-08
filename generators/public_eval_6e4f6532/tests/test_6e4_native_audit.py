from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
AUDIT = HOME / "workspace/parametric/audit_native.py"


def load():
    spec = importlib.util.spec_from_file_location("_6e4_audit_test", AUDIT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_rival_programs_are_distinct_and_cover_core_shortcuts():
    audit = load()
    native_spec = importlib.util.spec_from_file_location("_6e4_native_for_audit", HOME / "workspace/parametric/native_family.py")
    native = importlib.util.module_from_spec(native_spec)
    sys.modules[native_spec.name] = native
    native_spec.loader.exec_module(native)
    episode = native.generate(17, {"orientation_mode": "toward"}, 2, 4)
    rivals = audit.rival_programs(episode["program_solution"], native.program({"orientation_mode": "away"}), episode["train"][0])
    assert set(rivals) == {
        "declared_other_setting", "identity", "ignore_all_guide_tabs",
        "use_only_first_guide_tab", "match_only_guide_axis", "keep_source_objects",
        "erase_without_relocation", "fixed_first_demo_background",
    }
    assert len(set(rivals.values())) == len(rivals)


def test_bounded_audit_rejects_all_authored_rivals(tmp_path):
    report = load().run_audit(tmp_path / "audit.json", seeds=(17,))
    assert report["status"] == "passed"
    assert report["unresolved"] == []
    assert report["invalid_rivals"] == []
    assert report["evaluations"] > 0
