"""Native matched-input selector family for isolated-source expansion."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root, public_challenge_bytes

TASK_ID = "0f26224a6da3"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PARAM = HOME / "workspace" / "parametric"
SETTINGS = (
    {"source_scope": "all_isolated"},
    {"source_scope": "rarest_color"},
)
DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIRS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if dr or dc
)


def _load(name: str):
    path = PARAM / f"{name}.py"
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(f"tested_0f26_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _sources(grid, dirs=DIRS4):
    h, w = len(grid), len(grid[0])
    return [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0
        and all(
            not (0 <= r + dr < h and 0 <= c + dc < w)
            or grid[r + dr][c + dc] == 0
            for dr, dc in dirs
        )
    ]


def test_default_program_is_exact_authority_and_alternative_executes_differently():
    adapter = _load("adapter")
    programs = {
        variant["program_solution"]
        for variant in Catalog(ROOT).get(TASK_ID)["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    authority = programs.pop()
    assert adapter.program(SETTINGS[0]) == authority
    assert adapter.program(SETTINGS[1]) != authority

    canonical_episode = adapter.generate(0, SETTINGS[0], demos=2, queries=1)
    alternate_episode = adapter.generate(0, SETTINGS[1], demos=2, queries=1)
    assert canonical_episode["train"][0]["input"] == alternate_episode["train"][0]["input"]
    assert canonical_episode["train"][0]["output"] != alternate_episode["train"][0]["output"]


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_matched_inputs_prefixes_structure_and_30x30_stress(demos):
    adapter = _load("adapter")
    canonical = adapter.generate(17, SETTINGS[0], demos=demos, queries=4)
    alternate = adapter.generate(17, SETTINGS[1], demos=demos, queries=4)
    one_query = adapter.generate(17, SETTINGS[0], demos=demos, queries=1)
    fewer_demos = adapter.generate(17, SETTINGS[0], demos=2, queries=4)

    assert len(canonical["train"]) == demos
    assert len(canonical["test"]) == 4
    assert canonical["test"][:1] == one_query["test"]
    assert canonical["train"][:2] == fewer_demos["train"]
    assert canonical["test"] == fewer_demos["test"]

    left_inputs = [pair["input"] for split in ("train", "test") for pair in canonical[split]]
    right_inputs = [pair["input"] for split in ("train", "test") for pair in alternate[split]]
    assert left_inputs == right_inputs
    assert len({json.dumps(grid, separators=(",", ":")) for grid in left_inputs}) == demos + 4
    assert all(
        a["output"] != b["output"]
        for split in ("train", "test")
        for a, b in zip(canonical[split], alternate[split], strict=True)
    )
    public_challenge_bytes(canonical)

    for grid in left_inputs:
        sources = _sources(grid)
        counts = Counter(grid[r][c] for r, c in sources)
        assert len(counts) >= 2
        minimum = min(counts.values())
        assert sum(value == minimum for value in counts.values()) == 1
        assert len(sources) >= 5

    # The minimum two-example lesson must visibly teach boundary clipping,
    # four-neighbor (not eight-neighbor) isolation, and inert foreground.
    lesson = [pair["input"] for pair in canonical["train"][:2]]
    assert any(
        any(r in (0, len(grid) - 1) or c in (0, len(grid[0]) - 1) for r, c in _sources(grid))
        for grid in lesson
    )
    assert any(set(_sources(grid)) - set(_sources(grid, DIRS8)) for grid in lesson)
    assert any(sum(value != 0 for row in grid for value in row) > len(_sources(grid)) for grid in lesson)

    large = canonical["test"][-1]["input"]
    large_output = canonical["test"][-1]["output"]
    assert (len(large), len(large[0])) == (30, 30)
    assert len(_sources(large)) >= 16
    assert sum(value != 0 for row in large_output for value in row) >= 75
    assert all(
        any(large[r][c] for r in rs for c in cs)
        for rs, cs in (
            (range(0, 15), range(0, 15)),
            (range(0, 15), range(15, 30)),
            (range(15, 30), range(0, 15)),
            (range(15, 30), range(15, 30)),
        )
    )


def test_minimum_lesson_refutes_bounded_shortcuts_for_both_settings():
    audit = _load("rival_audit")
    for seed in range(24):
        for settings in SETTINGS:
            report = audit.audit_episode(seed, settings, demos=2, queries=4)
            assert report["harmful_survivors"] == [], report
            assert report["constant_query_failures"] == 4


def test_protected_racket_labels_and_demo_only_identification():
    _load("adapter")
    contract = json.loads((PARAM / "promotion.json").read_text())
    jobs = [
        dict(seed=seed, settings=settings, demos=demos, queries=4)
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
        {"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 1.0},
        {"settings": {}}, {"settings": {"source_scope": True}},
        {"settings": {"source_scope": "all"}},
        {"settings": {"source_scope": "all_isolated", "extra": 1}},
        {"demos": 1}, {"demos": 7}, {"demos": True}, {"demos": 3.0},
        {"queries": 0}, {"queries": 5}, {"queries": True}, {"queries": 4.0},
    ],
)
def test_invalid_native_requests_are_rejected(patch):
    request = dict(seed=17, settings=SETTINGS[0], demos=3, queries=4)
    request.update(patch)
    with pytest.raises(ValueError):
        _load("adapter").generate(**request)
