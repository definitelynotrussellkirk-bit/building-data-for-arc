from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared" / "runtime"))

MODULE_PATH = ROOT / "generators" / "983d0ea3bd17" / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_983d0ea3bd17", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _norm_grid(raw):
    if isinstance(raw, list) and raw and isinstance(raw[0], str):
        return [[int(ch) for ch in row] for row in raw]
    return copy.deepcopy(raw)


def _canonical_row():
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def _canonical_pairs():
    row = _canonical_row()
    raw_pairs = list(row["train"])
    test = row["test"]
    raw_pairs.extend(test if isinstance(test, list) else [test])
    return [
        {"input": _norm_grid(pair["input"]), "output": _norm_grid(pair["output"])}
        for pair in raw_pairs
    ]


def _canonical_rule_hash():
    source = _canonical_row()["program_solution"]
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _blocker_cells(grid):
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, GEN.SOURCE_COLOR)
    ]


def _surviving_competitors(demos):
    return sorted(
        name
        for name, competitor in GEN.LESSON_COMPETITORS.items()
        if all(competitor(pair["input"]) == pair["output"] for pair in demos)
    )


def test_rule_hash_and_all_canonical_pairs_are_pinned_and_accepted():
    assert GEN.RULE_HASH == _canonical_rule_hash() == "fd605125c9f8"
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_six_slot_schedule_balances_source_counts_and_anchors_two_canonical_profiles():
    grids = [GEN.generate(20260929, index, difficulty="medium") for index in range(6)]
    observed = [GEN.observe_overrides(grid) for grid in grids]

    assert [GEN.schedule_profile(20260929, index, "medium") for index in range(6)] == [
        "canonical_pair",
        "two_color_blocker_probe",
        "canonical_triple",
        "canonical_pair",
        "two_color_blocker_probe",
        "canonical_triple",
    ]
    assert [item["seed_count"] for item in observed] == [2, 2, 3, 2, 3, 3]
    assert [item["scene_kind"] for item in observed] == [
        "scattered",
        "blocked",
        "scattered",
        "scattered",
        "blocked",
        "scattered",
    ]
    for index in (0, 2, 3, 5):
        assert GEN.strict_canonical_like(grids[index]) == []
    for index in (1, 4):
        assert "canonical inputs contain no blocker" in GEN.strict_canonical_like(grids[index])


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "scene_kind",
    ["scattered", "edge_anchored", "row_aligned", "col_aligned", "blocked"],
)
def test_exact_boundary_overrides_round_trip(band, scene_kind):
    for h, w, count in ((6, 8, 2), (10, 12, 3)):
        grid = GEN.generate(
            77,
            11,
            difficulty=band,
            grid_h=h,
            grid_w=w,
            seed_count=count,
            scene_kind=scene_kind,
        )
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == {
            "grid_h": h,
            "grid_w": w,
            "seed_count": count,
            "scene_kind": scene_kind,
        }


def test_unknown_override_rejects_loudly():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)


def test_blocked_scene_has_two_colors_edge_alignment_and_two_observable_stops():
    for h, w, count in ((6, 8, 2), (10, 12, 3)):
        for seed in range(8):
            grid = GEN.generate(
                seed,
                1,
                grid_h=h,
                grid_w=w,
                seed_count=count,
                scene_kind="blocked",
            )
            blockers = _blocker_cells(grid)
            assert len(blockers) == 2
            colors = {value for _, _, value in blockers}
            assert len(colors) == 2
            assert GEN.ANCHOR_BLOCKER_COLOR in colors

            sources = GEN._positions(grid, GEN.SOURCE_COLOR)
            assert any(
                row in (0, h - 1) or col in (0, w - 1)
                for row, col in sources
            )
            assert (
                len({row for row, _ in sources}) < len(sources)
                or len({col for _, col in sources}) < len(sources)
            )
            assert all(
                GEN._blocker_is_observable(grid, (row, col))
                for row, col, _ in blockers
            )


def test_canonical_fitting_shortcuts_are_declared_and_generated_probes_refute_them():
    expected = {
        "paint_through_nonzero",
        "single_blocker_color_only",
        "all_nonzero_cells_emit",
        "dedupe_shared_axis",
    }
    assert expected <= set(GEN.CANONICAL_SHORTCUTS)
    assert expected <= set(GEN.SEMANTIC_RIVALS)

    for name in expected:
        shortcut = GEN.CANONICAL_SHORTCUTS[name]
        for pair in _canonical_pairs():
            assert shortcut(pair["input"]) == pair["output"], name

    blocked = GEN.generate(
        91,
        1,
        grid_h=7,
        grid_w=10,
        seed_count=3,
        scene_kind="blocked",
    )
    intended = GEN.rule_mirror(blocked)
    for name in expected:
        assert GEN.SEMANTIC_RIVALS[name](blocked) != intended, name


def test_every_three_consecutive_demos_refutes_every_named_competitor():
    expected_competitors = {
        "paint_through_nonzero",
        "single_blocker_color_only",
        "all_nonzero_cells_emit",
        "dedupe_shared_axis",
        "interior_sources_only",
        "first_two_sources_only",
        "erase_blockers",
        "recolor_blockers_orange",
    }
    assert expected_competitors <= set(GEN.LESSON_COMPETITORS)

    for band in ("easy", "medium", "hard"):
        for seed in (1, 91, 20260929):
            for start in range(12):
                demos = []
                for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                    inp = GEN.generate(seed, sample_index, difficulty=band)
                    demos.append({"input": inp, "output": GEN.rule_mirror(inp)})
                assert _surviving_competitors(demos) == [], (
                    band,
                    seed,
                    start,
                    [GEN.observe_overrides(pair["input"]) for pair in demos],
                )


def test_lesson_identifiable_matches_consecutive_materialization():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                inp = GEN.generate(111, sample_index, difficulty=band)
                demos.append({"input": inp, "output": GEN.rule_mirror(inp)})
            query_input = GEN.generate(111, start + GEN.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": query_input, "output": GEN.rule_mirror(query_input)}
            assert GEN.lesson_identifiable(demos, query) == []


def test_self_check_rejects_targeted_impostors():
    fixtures = dict(GEN.mutation_fixtures())
    assert {
        "all_background",
        "one_source",
        "four_sources",
        "input_contains_7",
        "one_blocker",
        "same_color_blockers",
    } <= fixtures.keys()
    for name, grid in fixtures.items():
        assert GEN.self_check(grid), f"declared impostor {name!r} unexpectedly passed"


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(991)
    before = random.getstate()
    first = GEN.generate(2026, 11, difficulty="hard")
    second = GEN.generate(2026, 11, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert random.getstate() == before


def _load_deep_audit_module():
    path = ROOT / "generators" / GEN.TASK_ID / "workspace" / "deep_audit.py"
    spec = importlib.util.spec_from_file_location("deep_audit_983d0ea3bd17", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_deep_audit_reports_no_shortcut_survivors_or_probe_contract_failures():
    audit = _load_deep_audit_module()
    result = audit.run_audit(
        bands=("easy",),
        seeds=(1,),
        starts=range(6),
    )
    assert result["passed"] is True
    assert result["canonical_shortcuts"]["all_fit_all_canonical"] is True
    assert result["lesson_windows"]["windows_checked"] == 6
    assert result["lesson_windows"]["survivor_counts"] == {}
    assert result["blocker_probes"]["probes_checked"] == 6
    assert result["blocker_probes"]["failures"] == []


def test_deep_audit_cli_writes_replayable_json(tmp_path):
    audit = _load_deep_audit_module()
    output = tmp_path / "audit.json"
    assert audit.main([
        "--bands", "medium",
        "--seeds", "91",
        "--starts", "0:3",
        "--out", str(output),
    ]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["passed"] is True
    assert payload["config"] == {
        "bands": ["medium"],
        "seeds": [91],
        "starts": [0, 1, 2],
    }
