from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
HOME = ROOT / "generators/1713e09a3132/workspace/parametric"
RUNTIME = ROOT / "shared/runtime"
for path in (RUNTIME, HOME):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _module(filename: str, name: str):
    path = HOME / filename
    assert path.is_file(), f"missing {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _pairs(grid):
    by_color = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append((r, c))
    return by_color


def _has_overlap(grid):
    boxes = []
    for points in _pairs(grid).values():
        (r0, c0), (r1, c1) = points
        boxes.append((min(r0, r1), min(c0, c1), max(r0, r1), max(c0, c1)))
    return any(max(a[0], b[0]) <= min(a[2], b[2]) and max(a[1], b[1]) <= min(a[3], b[3])
               for i, a in enumerate(boxes) for b in boxes[i + 1:])


def test_default_program_is_exact_catalog_canonical():
    prototype = _module("prototype.py", "rect_parametric_prototype")
    canonical = json.loads((ROOT / "shared/data/base/solutions/banks/50e2f7e22580/medium_49_draw_rectangles_from_opposite_corners__1713e09a3132.json").read_text())["racket_target"]["target_code"]
    assert prototype.program_for("outline") == canonical
    assert (HOME / "canonical.rkt").read_text() == canonical


def test_matched_inputs_are_identifying_and_cover_overlap_orientation_long_span_stress():
    prototype = _module("prototype.py", "rect_parametric_prototype_counts")
    for demos in range(2, 7):
        outline = prototype.generate_claims(17, "outline", demos=demos, queries=4)
        filled = prototype.generate_claims(17, "paint_enclosed", demos=demos, queries=4)
        inputs = [p["input"] for p in outline["train"] + outline["test"]]
        assert inputs == [p["input"] for p in filled["train"] + filled["test"]]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == demos + 4
        assert all(a["output"] != b["output"] for a, b in zip(outline["train"], filled["train"]))
        assert all(_has_overlap(grid) for grid in inputs)
        for grid in inputs:
            pairs = _pairs(grid)
            signs = {(r1 - r0) * (c1 - c0) > 0 for (r0, c0), (r1, c1) in pairs.values()}
            assert signs == {False, True}
            assert any(max(abs(r1 - r0), abs(c1 - c0)) >= 8 for (r0, c0), (r1, c1) in pairs.values())
        assert (len(inputs[-1]), len(inputs[-1][0])) == (30, 30)


def test_wrong_order_counterfactual_changes_the_final_output():
    prototype = _module("prototype.py", "rect_parametric_prototype_causal")
    episode = prototype.generate_claims(43, "paint_enclosed", demos=3, queries=4)
    assert all(
        prototype.python_mirror(pair["input"], "paint_enclosed") != prototype.python_wrong_order(pair["input"])
        for pair in episode["train"] + episode["test"]
    )


def test_adapter_rejects_malformed_settings_and_counts():
    adapter = _module("adapter.py", "rect_parametric_adapter")
    with pytest.raises(ValueError):
        adapter.program({"finish_mode": "unknown"})
    with pytest.raises(ValueError):
        adapter.program({"finish_mode": "outline", "extra": 1})
    with pytest.raises(ValueError):
        adapter.generate(0, {"finish_mode": "outline"}, 1, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"finish_mode": "outline"}, 2, 3)
