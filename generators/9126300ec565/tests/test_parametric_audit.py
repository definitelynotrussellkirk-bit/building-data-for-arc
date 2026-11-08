"""The teaching checker must expose an underidentified lesson."""
from pathlib import Path
import importlib.util


def test_audit_detects_constant_axis_after_missing_orientation_demo():
    home = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
    path = home / "self_audit.py"
    assert path.is_file(), "Need executable demonstration-only shortcut audit"
    spec = importlib.util.spec_from_file_location("frame_axis_audit_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Two wide demos permit always-horizontal; a tall query exposes it.
    train0, _ = mod.prototype.inputs(0, 2, 4)
    train2, _ = mod.prototype.inputs(2, 2, 4)
    apply, _, bridge = mod.prototype._real_evaluator(mod.prototype.ROOT / "shared/runtime")
    try:
        report = mod.audit_lesson([train0[0], train2[0]], [train0[1]], "long_axis", apply)
    finally:
        bridge.close()
    assert "setting_horizontal" in report["ambiguous_rivals"]
    assert report["status"] == "ambiguous"


def test_transposed_demos_refute_first_frame_shortcut():
    home = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
    spec = importlib.util.spec_from_file_location("frame_axis_order_audit_test", home / "self_audit.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    train, test = mod.prototype.inputs(17, 2, 4)
    apply, _, bridge = mod.prototype._real_evaluator(mod.prototype.ROOT / "shared/runtime")
    try:
        report = mod.audit_lesson(train, test, "long_axis", apply)
    finally:
        bridge.close()
    assert report["status"] == "passed", report["ambiguous_rivals"]


def test_canvas_aspect_does_not_choose_long_axis():
    home = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
    spec = importlib.util.spec_from_file_location("frame_canvas_aspect_test", home / "prototype.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    train, _ = mod.inputs(0, 2, 4)
    rule = mod.program({"axis": "long_axis"})
    wrong = rule.replace("(> (- c2 c1) (- r2 r1))", "(> (length (first g)) (length g))")
    assert wrong != rule
    apply, _, bridge = mod._real_evaluator(mod.ROOT / "shared/runtime")
    try:
        assert any(apply(rule, grid) != apply(wrong, grid) for grid in train), \
            "Demos must teach selected-frame orientation, not canvas orientation"
    finally:
        bridge.close()
