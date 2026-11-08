"""Behavioral tests for the native parametric family of 6b6e3acc8a0a."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

try:
    from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator
except ModuleNotFoundError as error:
    if error.name != "reviewer_support":
        raise
    for ancestor in Path(__file__).resolve().parents:
        helper = ancestor / "shared" / "runtime" / "reviewer_support.py"
        if helper.is_file():
            sys.path.insert(0, str(helper.parent))
            break
    else:
        raise
    from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "6b6e3acc8a0a"
ROOT = find_root(__file__)
ADAPTER_PATH = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "adapter.py"
SPEC = importlib.util.spec_from_file_location("_parametric_6b6e3acc8a0a", ADAPTER_PATH)
assert SPEC is not None and SPEC.loader is not None
ADAPTER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ADAPTER
SPEC.loader.exec_module(ADAPTER)

CANONICAL = {"translation_mode": "canonical_all"}
SELECTOR = {"translation_mode": "pointer_select_color"}


def _authority_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    matches = [row["program_solution"] for row in rows if row.get("task_id") == TASK_ID]
    assert len(set(matches)) == 1
    return matches[0]


def _positions(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def _manual_canonical(grid):
    h, w = len(grid), len(grid[0])
    source = _positions(grid, 1)[0]
    destination = _positions(grid, 2)[0]
    dr, dc = destination[0] - source[0], destination[1] - source[1]
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 1, 2):
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = value
    return out


def _manual_selector(grid):
    h, w = len(grid), len(grid[0])
    source = _positions(grid, 1)[0]
    destination = _positions(grid, 2)[0]
    pointer = _positions(grid, 8)[0]
    dr, dc = destination[0] - source[0], destination[1] - source[1]
    selector = (pointer[0] + dr, pointer[1] + dc)
    selected_color = grid[selector[0]][selector[1]]
    assert selected_color in (3, 4, 6, 7)
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in _positions(grid, 9):
        rr, cc = r + dr, c + dc
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = selected_color
    return out


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_selected_canonical():
    assert ADAPTER.program(CANONICAL) == _authority_program()


def test_determinism_settings_neutrality_and_count_prefixes():
    canonical = ADAPTER.generate(17, CANONICAL, 6, 4)
    selector = ADAPTER.generate(17, SELECTOR, 6, 4)
    assert _inputs(canonical) == _inputs(selector)
    assert canonical == ADAPTER.generate(17, CANONICAL, 6, 4)

    shorter = ADAPTER.generate(17, CANONICAL, 2, 1)
    assert shorter["train"] == canonical["train"][:2]
    assert shorter["test"] == canonical["test"][:1]
    assert len({json.dumps(grid) for grid in _inputs(canonical)}) == 10


def test_python_labels_match_independent_oracles_and_teach_both_settings():
    canonical = ADAPTER.generate(0, CANONICAL, 3, 4)
    selector = ADAPTER.generate(0, SELECTOR, 3, 4)
    for left, right in zip(canonical["train"] + canonical["test"], selector["train"] + selector["test"]):
        assert left["input"] == right["input"]
        assert left["output"] == _manual_canonical(deepcopy(left["input"]))
        assert right["output"] == _manual_selector(deepcopy(right["input"]))
        assert left["output"] != right["output"]


def test_selector_intermediate_changes_with_input_and_controls_cargo_color():
    episode = ADAPTER.generate(3, SELECTOR, 6, 4)
    selected = []
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        source = _positions(grid, 1)[0]
        destination = _positions(grid, 2)[0]
        pointer = _positions(grid, 8)[0]
        dr, dc = destination[0] - source[0], destination[1] - source[1]
        color = grid[pointer[0] + dr][pointer[1] + dc]
        selected.append(color)
        painted = {value for row in pair["output"] for value in row if value != 0}
        assert painted == {color}
    assert len(set(selected)) >= 3


def test_query_bank_contains_substantive_30_by_30_stress():
    episode = ADAPTER.generate(5, SELECTOR, 2, 4)
    stress = episode["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    assert sum(value != 0 for row in stress for value in row) >= 100
    assert len(_positions(stress, 9)) >= 60


def test_existing_base_labels_and_ordinary_generation_are_sound():
    module, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        source = deepcopy(pair["input"])
        assert module.self_check(source) == []
        assert _manual_canonical(source) == pair["output"]
    for difficulty, seed in ((None, 17), ("medium", 43)):
        for sample_index in range(3):
            grid = module.generate(seed, sample_index, difficulty=difficulty)
            assert module.self_check(grid, difficulty=difficulty) == []
            assert grid == module.generate(seed, sample_index, difficulty=difficulty)


def _wrong_outputs(grid):
    h, w = len(grid), len(grid[0])
    source = _positions(grid, 1)[0]
    destination = _positions(grid, 2)[0]
    dr, dc = destination[0] - source[0], destination[1] - source[1]

    def move(filter_fn, row_delta, col_delta, recolor=None):
        out = [[0 for _ in range(w)] for _ in range(h)]
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if not filter_fn(value):
                    continue
                rr, cc = r + row_delta, c + col_delta
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = value if recolor is None else recolor
        return out

    pointer = _positions(grid, 8)[0]
    selected = grid[pointer[0] + dr][pointer[1] + dc]
    return {
        "opposite-vector": move(lambda v: v not in (0, 1, 2), -dr, -dc),
        "copy-nonanchors": move(lambda v: v not in (0, 1, 2), 0, 0),
        "cargo-preserves-nine": move(lambda v: v == 9, dr, dc),
        "fixed-color-three": move(lambda v: v == 9, dr, dc, 3),
        "pointer-reads-origin": move(lambda v: v == 9, dr, dc, grid[pointer[0]][pointer[1]]),
        "selected-color-but-no-translation": move(lambda v: v == 9, 0, 0, selected),
    }


def test_visible_demos_reject_named_shortcuts():
    for seed in (0, 17):
        for settings in (CANONICAL, SELECTOR):
            episode = ADAPTER.generate(seed, settings, 2, 4)
            intended = [pair["output"] for pair in episode["train"]]
            survivors = []
            for name in _wrong_outputs(episode["train"][0]["input"]):
                claims = [_wrong_outputs(pair["input"])[name] for pair in episode["train"]]
                if claims == intended:
                    survivors.append(name)
            assert survivors == []


def test_structured_self_audit_tool_passes():
    audit_path = ADAPTER_PATH.with_name("audit.py")
    spec = importlib.util.spec_from_file_location("_audit_tool_6b6e3acc8a0a", audit_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    report = module.run()
    assert report["status"] == "passed"
    assert report["task_id"] == TASK_ID
    assert report["racket_executed"] is False


def test_preflight_compat_normalizes_only_single_pair_object_shape():
    path = ADAPTER_PATH.with_name("preflight_compat.py")
    spec = importlib.util.spec_from_file_location("_preflight_compat_6b6e3acc8a0a", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    pair = {"input": [[0]], "output": [[0]]}
    assert module.pair_list(pair) == [pair]
    assert module.pair_list([pair]) == [pair]
    with pytest.raises(ValueError, match="list or one pair object"):
        module.pair_list("bad")


@pytest.mark.parametrize(
    "args, message",
    [
        ((True, CANONICAL, 2, 1), "seed"),
        ((0, CANONICAL, 1, 1), "demos"),
        ((0, CANONICAL, 2, 5), "queries"),
        ((0, {"translation_mode": "unknown"}, 2, 1), "translation_mode"),
        ((0, {"translation_mode": True}, 2, 1), "translation_mode"),
    ],
)
def test_invalid_requests_fail_closed(args, message):
    with pytest.raises(ValueError, match=message):
        ADAPTER.generate(*args)
