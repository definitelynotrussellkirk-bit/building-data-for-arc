"""Native-ready minimum/maximum room-extreme parametric family."""
from __future__ import annotations

from collections import defaultdict, deque
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator, evaluate_contract
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "953db766893d"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PROTO = HOME / "workspace" / "parametric"
SETTINGS = ({"extreme": "minimum"}, {"extreme": "maximum"})


def load_adapter():
    path = PROTO / "adapter.py"
    assert path.is_file(), "the requested parametric adapter has not been built"
    spec = importlib.util.spec_from_file_location("tested_953db766893d_parametric_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


def zero_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0}
    components = []
    while unseen:
        start = unseen.pop()
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (rr, cc) in unseen:
                    unseen.remove((rr, cc))
                    component.add((rr, cc))
                    queue.append((rr, cc))
        components.append(component)
    return components


def component_size_labels(pair: dict) -> dict[int, set[int]]:
    labels: dict[int, set[int]] = defaultdict(set)
    for component in zero_components(pair["input"]):
        component_labels = {pair["output"][r][c] for r, c in component}
        assert len(component_labels) == 1
        labels[len(component)].update(component_labels)
    return labels


def is_filled_rectangle(component: set[tuple[int, int]]) -> bool:
    rows = [r for r, _ in component]
    cols = [c for _, c in component]
    return len(component) == (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def has_door_opening(grid: list[list[int]]) -> bool:
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            horizontal_door = (
                grid[r][c - 1] == grid[r][c + 1] == 0
                and grid[r - 1][c] != 0
                and grid[r + 1][c] != 0
            )
            vertical_door = (
                grid[r - 1][c] == grid[r + 1][c] == 0
                and grid[r][c - 1] != 0
                and grid[r][c + 1] != 0
            )
            if horizontal_door or vertical_door:
                return True
    return False


def test_default_program_is_exact_canonical_and_both_rules_execute_differently():
    adapter = load_adapter()
    authority = canonical_program()
    assert adapter.program(SETTINGS[0]) == authority
    assert adapter.program(SETTINGS[1]) != authority

    episode = adapter.generate(0, SETTINGS[0], demos=2, queries=1)
    grid = episode["train"][0]["input"]
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, PROTO):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            assert identity["backend"] == "racket" and identity["protected"] is True
            minimum = apply(adapter.program(SETTINGS[0]), grid)
            maximum = apply(adapter.program(SETTINGS[1]), grid)
        finally:
            bridge.close()
    assert minimum == episode["train"][0]["output"]
    assert minimum != maximum


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_matched_inputs_prefix_distinctness_and_large_query(demos):
    adapter = load_adapter()
    minimum = adapter.generate(17, SETTINGS[0], demos=demos, queries=4)
    maximum = adapter.generate(17, SETTINGS[1], demos=demos, queries=4)
    one = adapter.generate(17, SETTINGS[0], demos=demos, queries=1)

    assert len(minimum["train"]) == demos and len(minimum["test"]) == 4
    assert minimum["train"] == one["train"]
    assert minimum["test"][:1] == one["test"]
    left_inputs = [pair["input"] for split in ("train", "test") for pair in minimum[split]]
    right_inputs = [pair["input"] for split in ("train", "test") for pair in maximum[split]]
    assert left_inputs == right_inputs
    assert len({json.dumps(grid, separators=(",", ":")) for grid in left_inputs}) == demos + 4
    assert all(
        a["output"] != b["output"]
        for split in ("train", "test")
        for a, b in zip(minimum[split], maximum[split], strict=True)
    )
    public_challenge_bytes(minimum)

    large = minimum["test"][-1]["input"]
    assert len(large) == len(large[0]) == 30
    assert sum(cell != 0 for row in large for cell in row) >= 190
    assert has_door_opening(large)
    sizes = {len(component) for component in zero_components(large)}
    assert len(sizes) >= 3
    quadrants = [
        any(large[r][c] for r in rs for c in cs)
        for rs, cs in (
            (range(0, 15), range(0, 15)),
            (range(0, 15), range(15, 30)),
            (range(15, 30), range(0, 15)),
            (range(15, 30), range(15, 30)),
        )
    ]
    assert all(quadrants)


def test_first_two_demos_defeat_opening_and_fixed_absolute_size_shortcuts():
    adapter = load_adapter()
    for settings in SETTINGS:
        episode = adapter.generate(0, settings, demos=2, queries=1)
        first, second = episode["train"]

        first_components = zero_components(first["input"])
        assert not has_door_opening(first["input"])
        assert all(is_filled_rectangle(component) for component in first_components)
        assert len({len(component) for component in first_components}) >= 3
        assert {first["output"][next(iter(component))[0]][next(iter(component))[1]]
                for component in first_components} == {3, 4}

        size_labels: dict[int, set[int]] = defaultdict(set)
        for pair in (first, second):
            for size, labels in component_size_labels(pair).items():
                size_labels[size].update(labels)
        assert any(labels == {3, 4} for labels in size_labels.values())
        assert has_door_opening(second["input"])


def test_walls_are_preserved_and_each_zero_component_gets_one_claimed_color():
    adapter = load_adapter()
    for settings in SETTINGS:
        episode = adapter.generate(41, settings, demos=6, queries=4)
        for pair in episode["train"] + episode["test"]:
            grid, output = pair["input"], pair["output"]
            for r, row in enumerate(grid):
                for c, value in enumerate(row):
                    if value != 0:
                        assert output[r][c] == value
            labels = component_size_labels(pair)
            assert set().union(*labels.values()) == {3, 4}


def test_protected_racket_labels_and_demo_only_identification():
    load_adapter()
    contract = json.loads((PROTO / "promotion.json").read_text())
    jobs = [
        dict(seed=seed, settings=settings, demos=demos, queries=4)
        for seed, demos in ((0, 2), (17, 6))
        for settings in SETTINGS
    ]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert result["racket"]["protected"] is True
    assert [check["survivors"] for check in result["checks"]] == [
        [job["settings"]] for job in jobs
    ]
    assert [check["label_count"] for check in result["checks"]] == [
        job["demos"] + 4 for job in jobs
    ]


@pytest.mark.parametrize(
    "patch",
    [
        {"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 1.0},
        {"settings": {}}, {"settings": {"extreme": True}},
        {"settings": {"extreme": "median"}},
        {"settings": {"extreme": "minimum", "extra": 1}},
        {"demos": 1}, {"demos": 7}, {"demos": True}, {"demos": 3.0},
        {"queries": 0}, {"queries": 5}, {"queries": True}, {"queries": 4.0},
    ],
)
def test_invalid_controls_fail_before_generation(patch):
    request = dict(seed=17, settings=SETTINGS[0], demos=3, queries=4)
    request.update(patch)
    with pytest.raises(ValueError):
        load_adapter().generate(**request)


def load_lesson_audit():
    path = PROTO / "audit_lessons.py"
    assert path.is_file(), "the reproducible lesson audit has not been built"
    spec = importlib.util.spec_from_file_location("tested_953db766893d_lesson_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reproducible_lesson_audit_records_both_shortcut_counterexamples():
    report = load_lesson_audit().build_report(seed=0, execute_racket=False)
    assert report["schema"] == "arcpuzzles-room-extreme-lesson-audit-v1"
    assert report["first_demo"]["has_opening"] is False
    assert report["first_demo"]["all_components_rectangular"] is True
    assert report["first_demo"]["opened_wall_rival_mismatched_cells"] > 0
    assert 10 in report["fixed_absolute_area_role_reversal"]["minimum"]
    assert 20 in report["fixed_absolute_area_role_reversal"]["maximum"]
    assert report["large_query"]["shape"] == [30, 30]
    assert report["large_query"]["has_opening"] is True
    assert len(report["large_query"]["component_sizes"]) >= 3
    assert report["racket"] == {"executed": False}
