"""Focused checks for the native layout-times-mask parametric family.

Python outputs are claims. Native qualification independently replays every
selected program and label through protected Racket.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break

from reviewer_support import canonical_path, find_root  # noqa: E402


TASK_ID = "86af5978a32a"
FINISHES = ("stamp_only", "highlight_largest_component")
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
ADAPTER_PATH = HOME / "adapter.py"
PROMOTION_PATH = HOME / "promotion.json"
PROBE_PATH = HOME / "probe.py"


def _load_adapter():
    assert ADAPTER_PATH.is_file(), "the task-local parametric adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("parametric_86af5978a32a_tests", ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load_adapter()


def _canonical_program() -> str:
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as source:
        rows = [json.loads(line) for line in source]
    programs = {
        row["program_solution"]
        for row in rows
        if row.get("task_id") == TASK_ID and row.get("program_solution")
    }
    assert len(programs) == 1
    return next(iter(programs))


def _split(grid):
    h, w = len(grid), len(grid[0])
    if w == 2 * h:
        k = h
        first = [row[:k] for row in grid]
        second = [row[k:] for row in grid]
    elif h == 2 * w:
        k = w
        first = grid[:k]
        second = grid[k:]
    else:
        raise ValueError("not two equal square panels")
    first_colors = {v for row in first for v in row if v}
    second_colors = {v for row in second for v in row if v}
    if len(first_colors) > len(second_colors):
        return k, first, second
    return k, second, first


def _stamp(grid):
    k, layout, shape = _split(grid)
    mask = [(r, c) for r in range(k) for c in range(k) if shape[r][c]]
    out = [[0] * (k * k) for _ in range(k * k)]
    for lr in range(k):
        for lc in range(k):
            color = layout[lr][lc]
            if not color:
                continue
            for sr, sc in mask:
                out[lr * k + sr][lc * k + sc] = color
    return out


def _components(grid, *, color_sensitive=False):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in seen:
                        continue
                    if grid[nr][nc] == 0:
                        continue
                    if color_sensitive and grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))
            result.append(sorted(cells))
    return sorted(result, key=lambda cells: (-len(cells), cells[0]))


def _oracle(grid, finish):
    stamped = _stamp(grid)
    facts = {
        "binary_components": _components(stamped),
        "color_components": _components(stamped, color_sensitive=True),
    }
    if finish == "stamp_only":
        return stamped, facts
    out = deepcopy(stamped)
    for r, c in facts["binary_components"][0]:
        out[r][c] = 9
    return out, facts


def _input_keys(episode):
    return [
        json.dumps(pair["input"], separators=(",", ":"))
        for split in ("train", "test")
        for pair in episode[split]
    ]


def test_parametric_adapter_is_present():
    assert ADAPTER_PATH.is_file(), "the task-local parametric adapter has not been implemented"


def test_contract_and_default_program_are_exact(adapter):
    contract = json.loads(PROMOTION_PATH.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"finish": list(FINISHES)},
        "default": {"finish": "stamp_only"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/rules/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rules/highlight_largest_component.rkt",
        ],
    }
    canonical = _canonical_program()
    assert tuple(adapter.FINISHES) == FINISHES
    assert adapter.program({"finish": "stamp_only"}).encode() == canonical.encode()
    alternative = adapter.program({"finish": "highlight_largest_component"})
    assert alternative != canonical
    assert alternative.lstrip().startswith("(rule!")


def test_literal_case_requires_binary_post_stamp_component(adapter):
    grid = [
        [8, 1, 0, 3, 3, 3],
        [0, 0, 0, 0, 3, 0],
        [2, 0, 2, 0, 0, 0],
    ]
    canonical, facts = _oracle(grid, "stamp_only")
    highlighted, _ = _oracle(grid, "highlight_largest_component")
    assert [len(c) for c in facts["binary_components"]] == [8, 4, 4]
    assert [len(c) for c in facts["color_components"]] == [4, 4, 4, 4]
    assert adapter.solve(grid, "stamp_only") == canonical
    assert adapter.solve(grid, "highlight_largest_component") == highlighted
    intermediate = adapter.component_intermediate(grid)
    assert intermediate["selected_cells"] == facts["binary_components"][0]
    assert intermediate["binary_component_sizes"] == [8, 4, 4]
    assert adapter.color_sensitive_solve(grid) != highlighted
    assert adapter.most_frequent_color_solve(grid) != highlighted


@pytest.mark.parametrize("finish", FINISHES)
def test_generated_counts_prefixes_labels_and_setting_matched_inputs(adapter, finish):
    setting = {"finish": finish}
    for seed in (0, 17):
        one = adapter.generate(seed, setting, demos=3, queries=1)
        four = adapter.generate(seed, setting, demos=3, queries=4)
        six = adapter.generate(seed, setting, demos=6, queries=4)
        assert one["train"] == four["train"] == six["train"][:3]
        assert one["test"] == four["test"][:1] == six["test"][:1]
        assert four["test"] == six["test"]
        for demos in (2, 3, 6):
            episode = adapter.generate(seed, setting, demos=demos, queries=4)
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == 4
            assert episode["program_solution"] == adapter.program(setting)
            keys = _input_keys(episode)
            assert len(keys) == len(set(keys))
            for split in ("train", "test"):
                for pair in episode[split]:
                    expected, facts = _oracle(pair["input"], finish)
                    assert pair["output"] == expected
                    if finish == "highlight_largest_component":
                        sizes = [len(c) for c in facts["binary_components"]]
                        assert len(sizes) >= 2 and sizes[0] > sizes[1]


@pytest.mark.parametrize("seed", [0, 17, 91])
def test_settings_share_inputs_and_first_two_demos_identify_the_setting(adapter, seed):
    episodes = {
        finish: adapter.generate(seed, {"finish": finish}, demos=6, queries=4)
        for finish in FINISHES
    }
    assert _input_keys(episodes[FINISHES[0]]) == _input_keys(episodes[FINISHES[1]])
    for index in range(6):
        assert episodes[FINISHES[0]]["train"][index]["output"] != episodes[FINISHES[1]]["train"][index]["output"]
    first_two = episodes["highlight_largest_component"]["train"][:2]
    assert all(adapter.color_sensitive_solve(p["input"]) != p["output"] for p in first_two)
    assert all(adapter.most_frequent_color_solve(p["input"]) != p["output"] for p in first_two)
    assert any(adapter.layout_cluster_solve(p["input"]) != p["output"] for p in first_two)


def test_curriculum_covers_source_axes_and_maximum_lawful_25x25_stress(adapter):
    episode = adapter.generate(20261024, {"finish": "highlight_largest_component"}, demos=6, queries=4)
    all_pairs = episode["train"] + episode["test"]
    facts = [adapter.input_facts(pair["input"]) for pair in all_pairs]
    assert {item["orientation"] for item in facts} == {"horizontal", "vertical"}
    assert {item["layout_position"] for item in facts} == {"first", "second"}
    assert {item["color_role"] for item in facts} == {"shape_is_8", "layout_has_8"}
    assert {item["half_size"] for item in facts} == {3, 4, 5}
    largest = episode["test"][-1]
    assert len(largest["output"]) == len(largest["output"][0]) == 25
    assert sum(v != 0 for row in _stamp(largest["input"]) for v in row) >= 120
    assert sum(v == 9 for row in largest["output"] for v in row) >= 30
    assert adapter.color_sensitive_solve(largest["input"]) != largest["output"]
    assert adapter.layout_cluster_solve(largest["input"]) != largest["output"]


def test_bounded_rival_bank_is_refuted_by_each_six_demo_lesson(adapter):
    for seed in (0, 17, 97):
        episode = adapter.generate(seed, {"finish": "highlight_largest_component"}, demos=6, queries=4)
        for name, rival in adapter.RIVALS.items():
            mismatches = sum(rival(pair["input"]) != pair["output"] for pair in episode["train"])
            assert mismatches > 0, (seed, name)


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"finish": "unknown"}, {"finish": 1}, {"finish": True},
     {"finish": "stamp_only", "extra": 1}],
)
def test_invalid_settings_reject(adapter, settings):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, settings, demos=3, queries=4)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (0, True, 4),
     (0, 1, 4), (0, 7, 4), (0, 3, True), (0, 3, 0), (0, 3, 5)],
)
def test_invalid_request_controls_reject(adapter, seed, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, {"finish": "stamp_only"}, demos=demos, queries=queries)


def test_generation_is_deterministic_fresh_and_global_rng_neutral(adapter):
    random.seed(20261024)
    state = random.getstate()
    first = adapter.generate(77, {"finish": "highlight_largest_component"}, demos=3, queries=4)
    assert random.getstate() == state
    second = adapter.generate(77, {"finish": "highlight_largest_component"}, demos=3, queries=4)
    assert first == second and first is not second
    first["train"][0]["input"][0][0] = 99
    third = adapter.generate(77, {"finish": "highlight_largest_component"}, demos=3, queries=4)
    assert third == second


def _load_probe():
    assert PROBE_PATH.is_file(), "the reusable authoring probe has not been implemented"
    spec = importlib.util.spec_from_file_location("parametric_86af5978a32a_probe_tests", PROBE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_authoring_probe_reports_bounded_self_audit(tmp_path):
    probe = _load_probe()
    report = probe.build_report(seeds=[0, 17], demos=6, queries=4)
    assert report["schema"] == "arcpuzzles-parametric-authoring-probe-v1"
    assert report["task_id"] == TASK_ID
    assert report["counts"] == {"demos": 6, "queries": 4, "cases": 20}
    assert report["settings"] == [{"finish": value} for value in FINISHES]
    assert all(report["checks"].values())
    assert report["checks"]["canonical_program_exact"]
    assert report["checks"]["same_inputs_across_settings"]
    assert report["checks"]["every_demo_identifies_setting"]
    assert report["checks"]["bounded_rivals_refuted"]
    assert report["checks"]["contains_25x25_max_lawful_query"]
    target = tmp_path / "authoring-probe.json"
    probe.write_report(target, report)
    assert json.loads(target.read_text()) == report
