from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"


def _load(name: str):
    path = PARAM / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_c286_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_is_exact_canonical_source():
    p = _load("prototype")
    source = (PARAM / "canonical.rkt").read_text()
    assert p.program({"finish": "transfer_only"}) == source
    assert hashlib.sha256(source.encode()).hexdigest() == p.CANONICAL_PROGRAM_SHA256


def test_counts_prefixes_matched_inputs_and_distinctness():
    p = _load("prototype")
    small = p.generate(17, {"finish": "transfer_only"}, 3, 1)
    large = p.generate(17, {"finish": "transfer_only"}, 6, 4)
    alt = p.generate(17, {"finish": "fill_transferred_holes"}, 6, 4)
    assert small["train"] == large["train"][:3]
    assert small["test"] == large["test"][:1]
    assert [x["input"] for x in large["train"] + large["test"]] == [
        x["input"] for x in alt["train"] + alt["test"]
    ]
    inputs = [repr(x["input"]) for x in large["train"] + large["test"]]
    assert len(inputs) == len(set(inputs))
    assert len(large["train"]) == 6 and len(large["test"]) == 4


def test_three_demos_identify_hole_finish_and_oracle_labels():
    p = _load("prototype")
    base = p.generate(3, {"finish": "transfer_only"}, 3, 4)
    alt = p.generate(3, {"finish": "fill_transferred_holes"}, 3, 4)
    assert any(a["output"] != b["output"] for a, b in zip(base["train"], alt["train"]))
    for finish, episode in (("transfer_only", base), ("fill_transferred_holes", alt)):
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == p.solve(pair["input"], finish)



def test_demo_bank_refutes_mirror_toward_target_on_asymmetric_right_source():
    p = _load("prototype")
    pair = p.generate(0, {"finish": "transfer_only"}, 3, 1)["train"][0]
    grid = pair["input"]
    info = p.describe(grid, {"finish": "transfer_only"})
    sr0, sc0, sr1, sc1 = info["source_bbox"]
    tr0, tc0, tr1, tc1 = info["target_bbox"]
    assert sc0 > tc1  # source is deliberately right of the target
    cells = [(r - sr0, c - sc0) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    width = sc1 - sc0 + 1
    mirrored = [[0 for _ in row] for row in grid]
    for dr, dc in cells:
        mirrored[tr0 + dr][tc0 + (width - 1 - dc)] = 8
    assert mirrored != pair["output"]

def test_fourth_query_is_substantive_30x30_with_multiple_holes():
    p = _load("prototype")
    episode = p.generate(29, {"finish": "fill_transferred_holes"}, 3, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    info = p.describe(grid, {"finish": "fill_transferred_holes"})
    assert info["source_cells"] >= 35
    assert info["enclosed_regions"] >= 2
    assert episode["test"][3]["output"] != p.solve(grid, "transfer_only")


def test_public_turn_reveals_one_query_input_only():
    p = _load("prototype")
    episode = p.generate(5, {"finish": "fill_transferred_holes"}, 3, 4)
    view = p.public_turn(episode, 2)
    assert set(view) == {"train", "test"}
    assert len(view["test"]) == 1
    assert set(view["test"][0]) == {"input"}
    assert "settings" not in repr(view)


@pytest.mark.parametrize("demos,queries", [(2, 4), (7, 4), (3, 0), (3, 5)])
def test_invalid_count_requests_fail_closed(demos, queries):
    p = _load("prototype")
    with pytest.raises(ValueError):
        p.generate(0, {"finish": "transfer_only"}, demos, queries)


def test_invalid_settings_fail_closed():
    p = _load("prototype")
    with pytest.raises(ValueError):
        p.program({"finish": "unknown"})
    with pytest.raises(ValueError):
        p.program({"finish": "transfer_only", "extra": 1})


def test_reusable_self_audit_covers_domain_and_shortcut_rivals():
    audit = _load("audit")
    report = audit.run()
    assert report["status"] == "passed"
    assert report["seeds"] == [0, 17, 97]
    assert report["checks"]["matched_inputs"] > 0
    assert report["checks"]["stable_prefixes"] > 0
    assert report["checks"]["privacy_views"] > 0
    assert all(count > 0 for count in report["rival_disagreements"].values())
