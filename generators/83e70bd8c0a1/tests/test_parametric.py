"""Native parametric contract for anti-diagonal reflection plus cue relay."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator, evaluate_contract
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "83e70bd8c0a1"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PROTO = HOME / "workspace" / "parametric"
SETTINGS = (
    {"rule": "full_reflection"},
    {"rule": "probe_relay"},
)


def load_adapter():
    path = PROTO / "adapter.py"
    assert path.is_file(), "the requested parametric adapter has not been built"
    spec = importlib.util.spec_from_file_location(
        "tested_83e70bd8c0a1_parametric_adapter", path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


def anti(cell: tuple[int, int], n: int) -> tuple[int, int]:
    r, c = cell
    return n - 1 - c, n - 1 - r


def probe_position(grid: list[list[int]]) -> tuple[int, int]:
    positions = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    assert len(positions) == 1
    return positions[0]


def cue_color(grid: list[list[int]], position: tuple[int, int]) -> int:
    h, w = len(grid), len(grid[0])
    r, c = position
    values = [
        grid[rr][cc]
        for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] not in (0, 1)
    ]
    assert len(values) == 1
    return values[0]


def move_probe(grid: list[list[int]], *, keep_source: bool = False) -> list[list[int]]:
    output = copy.deepcopy(grid)
    n = len(grid)
    source = probe_position(grid)
    destination = anti(source, n)
    if not keep_source:
        output[source[0]][source[1]] = 0
    output[destination[0]][destination[1]] = 1
    return output


def transpose_color(grid: list[list[int]], color: int) -> list[list[int]]:
    output = copy.deepcopy(grid)
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    for r, c in cells:
        output[r][c] = 0
    for r, c in cells:
        output[c][r] = color
    return output


def relay_oracle(grid: list[list[int]]) -> list[list[int]]:
    moved = move_probe(grid)
    destination = probe_position(moved)
    return transpose_color(moved, cue_color(moved, destination))


def full_reflection(grid: list[list[int]]) -> list[list[int]]:
    n = len(grid)
    return [
        [grid[n - 1 - c][n - 1 - r] for c in range(n)]
        for r in range(n)
    ]


def all_inputs(episode: dict) -> list[list[list[int]]]:
    return [
        pair["input"]
        for split in ("train", "test")
        for pair in episode[split]
    ]


def test_default_program_is_exact_canonical_and_alternative_executes_differently():
    adapter = load_adapter()
    authority = canonical_program()
    assert adapter.program(SETTINGS[0]) == authority
    assert adapter.program(SETTINGS[1]) != authority

    canonical = adapter.generate(0, SETTINGS[0], demos=2, queries=1)
    relay = adapter.generate(0, SETTINGS[1], demos=2, queries=1)
    assert all_inputs(canonical) == all_inputs(relay)

    grid = canonical["train"][0]["input"]
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, PROTO):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            assert identity["backend"] == "racket"
            assert identity["protected"] is True
            canonical_output = apply(adapter.program(SETTINGS[0]), grid)
            relay_output = apply(adapter.program(SETTINGS[1]), grid)
        finally:
            bridge.close()
    assert canonical_output == full_reflection(grid)
    assert relay_output == relay_oracle(grid)
    assert canonical_output != relay_output


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_matched_inputs_prefix_stability_and_substantive_30x30(demos):
    adapter = load_adapter()
    canonical = adapter.generate(17, SETTINGS[0], demos=demos, queries=4)
    relay = adapter.generate(17, SETTINGS[1], demos=demos, queries=4)
    one_query = adapter.generate(17, SETTINGS[1], demos=demos, queries=1)

    assert len(canonical["train"]) == len(relay["train"]) == demos
    assert len(canonical["test"]) == len(relay["test"]) == 4
    assert relay["train"] == one_query["train"]
    assert relay["test"][:1] == one_query["test"]
    assert all_inputs(canonical) == all_inputs(relay)
    encoded = [json.dumps(grid, separators=(",", ":")) for grid in all_inputs(relay)]
    assert len(encoded) == len(set(encoded)) == demos + 4
    assert all(
        left["output"] != right["output"]
        for split in ("train", "test")
        for left, right in zip(canonical[split], relay[split], strict=True)
    )
    public_challenge_bytes(relay)

    large = relay["test"][-1]["input"]
    assert len(large) == len(large[0]) == 30
    nonzero = {(r, c) for r, row in enumerate(large) for c, value in enumerate(row) if value}
    assert len(nonzero) >= 90
    assert {0, 29} <= {r for r, _ in nonzero}
    assert {0, 29} <= {c for _, c in nonzero}
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


@pytest.mark.parametrize("seed", (0, 1, 17, 63))
def test_claim_labels_match_independent_geometry_and_landing_cue_varies(seed):
    adapter = load_adapter()
    episode = adapter.generate(seed, SETTINGS[1], demos=6, queries=4)
    targets = []
    sources = []
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        source = probe_position(grid)
        moved = move_probe(grid)
        destination = probe_position(moved)
        original = cue_color(grid, source)
        landing = cue_color(moved, destination)
        assert original != landing
        assert pair["output"] == relay_oracle(grid)
        assert sum(value == landing for row in grid for value in row) >= 3
        targets.append(landing)
        sources.append(source)
    assert len(set(targets[:3])) >= 2
    assert len(set(targets)) == 3
    assert len(set(sources)) >= 3


def test_first_two_demos_reject_plausible_relay_shortcuts():
    adapter = load_adapter()
    episode = adapter.generate(0, SETTINGS[1], demos=2, queries=1)
    demos = episode["train"]

    def probe_only(grid):
        return move_probe(grid)

    def skip_a_uses_original_cue(grid):
        original = cue_color(grid, probe_position(grid))
        return transpose_color(move_probe(grid), original)

    def copy_probe_then_relay(grid):
        copied = move_probe(grid, keep_source=True)
        return transpose_color(copied, cue_color(copied, anti(probe_position(grid), len(grid))))

    def fixed_color(color):
        return lambda grid: transpose_color(move_probe(grid), color)

    def recolor_selected(grid):
        moved = move_probe(grid)
        selected = cue_color(moved, probe_position(moved))
        return [[9 if value == selected else value for value in row] for row in moved]

    rivals = {
        "identity": lambda grid: copy.deepcopy(grid),
        "probe_only": probe_only,
        "skip_a_original_cue": skip_a_uses_original_cue,
        "copy_probe": copy_probe_then_relay,
        "fixed_color_2": fixed_color(2),
        "fixed_color_3": fixed_color(3),
        "fixed_color_4": fixed_color(4),
        "recolor_selected": recolor_selected,
        "transpose_everything": lambda grid: [list(row) for row in zip(*grid)],
        "full_reflection": full_reflection,
    }
    for name, rival in rivals.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_first_two_demos_reject_plausible_canonical_shortcuts():
    adapter = load_adapter()
    episode = adapter.generate(0, SETTINGS[0], demos=2, queries=1)
    demos = episode["train"]
    rivals = {
        "identity": lambda grid: copy.deepcopy(grid),
        "transpose": lambda grid: [list(row) for row in zip(*grid)],
        "rotate_180": lambda grid: [row[::-1] for row in grid[::-1]],
        "flip_lr": lambda grid: [row[::-1] for row in grid],
        "probe_relay": relay_oracle,
    }
    for name, rival in rivals.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_public_view_reveals_one_query_without_private_or_future_fields():
    adapter = load_adapter()
    many = adapter.generate(9, SETTINGS[1], demos=3, queries=4)
    one = adapter.generate(9, SETTINGS[1], demos=3, queries=1)
    first_many = adapter.public_view(many, 0)
    first_one = adapter.public_view(one, 0)
    assert public_challenge_bytes(first_many) == public_challenge_bytes(first_one)
    assert len(first_many["test"]) == 1
    assert first_many["test"][0] == {"input": many["test"][0]["input"]}
    serialized = json.dumps(first_many, sort_keys=True)
    for forbidden in ("settings", "program_solution", "seed", "query_index", "query_count"):
        assert forbidden not in serialized
    with pytest.raises(ValueError):
        adapter.public_view(many, True)
    with pytest.raises(ValueError):
        adapter.public_view(many, 4)


def test_protected_racket_labels_and_demo_only_setting_identification():
    load_adapter()
    contract = json.loads((PROTO / "promotion.json").read_text(encoding="utf-8"))
    jobs = [
        {"seed": seed, "settings": settings, "demos": demos, "queries": 4}
        for seed, demos in ((0, 2), (17, 6))
        for settings in SETTINGS
    ]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert result["racket"]["backend"] == "racket"
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
        {"seed": True},
        {"seed": -1},
        {"seed": 2**63},
        {"seed": 1.0},
        {"settings": {}},
        {"settings": {"rule": True}},
        {"settings": {"rule": "unknown"}},
        {"settings": {"rule": "full_reflection", "extra": 1}},
        {"demos": 1},
        {"demos": 7},
        {"demos": True},
        {"demos": 3.0},
        {"queries": 0},
        {"queries": 5},
        {"queries": True},
        {"queries": 4.0},
    ],
)
def test_invalid_controls_fail_before_generation(patch):
    request = {"seed": 17, "settings": SETTINGS[0], "demos": 3, "queries": 4}
    request.update(patch)
    with pytest.raises(ValueError):
        load_adapter().generate(**request)


def load_audit():
    path = PROTO / "audit.py"
    assert path.is_file(), "the reusable bounded audit has not been built"
    spec = importlib.util.spec_from_file_location(
        "tested_83e70bd8c0a1_parametric_audit", path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_bounded_audit_covers_counts_settings_rivals_and_projection():
    report = load_audit().build_report(seed_count=8, execute_racket=False)
    assert report["schema"] == "arcpuzzles-probe-relay-audit-v1"
    assert report["status"] == "PASS"
    assert report["episodes"] == 8 * 3 * 2
    assert report["labeled_pairs"] == 8 * (2 + 4 + 3 + 4 + 6 + 4) * 2
    assert report["demo_counts"] == [2, 3, 6]
    assert report["query_count"] == 4
    assert report["target_colors"] == [2, 3, 4]
    assert report["rival_failures"] == []
    assert report["projection_failures"] == []
    assert report["racket"] == {"executed": False}
