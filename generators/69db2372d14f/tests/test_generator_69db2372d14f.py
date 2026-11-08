"""Focused regression coverage for marker-aligned rectangle composition."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs

TASK_ID = "69db2372d14f"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_rows():
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    assert rows, "canonical task rows not found"
    return rows


def _canonical_pairs():
    return canonical_pairs(TASK_ID)


def _sha(grid):
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def test_rule_hash_summary_and_semantic_contract_are_task_linked():
    assert GEN.RULE_HASH == "657328d7828c"
    text = ((GEN.__doc__ or "") + " " + GEN.SUMMARY).lower()
    for phrase in ("largest", "rectangle", "marker", "align", "paste"):
        assert phrase in text
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.SEMANTIC_RIVALS
    assert GEN.SEMANTIC_WITNESSES


def test_all_canonical_pairs_are_accepted_solved_and_input_pure():
    pairs = _canonical_pairs()
    assert len(pairs) == 8
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_python(source) == pair["output"]
        assert source == pair["input"]


def test_every_generated_piece_is_multicolor_and_has_one_exact_alignment():
    """Regression: v2 emitted monochrome L-pieces with no shared markers."""
    for band in ("easy", "medium", "hard"):
        for sample_index in range(12):
            grid = GEN.generate(1000 + sample_index, sample_index, difficulty=band)
            errors, analysis = GEN._analyze_grid(grid)
            assert errors == []
            assert analysis is not None
            assert analysis["piece_count"] in {1, 2, 3}
            for piece in analysis["pieces"]:
                assert len(piece["colors"]) == 2
                assert piece["marker"] in analysis["container"]["colors"]
                assert piece["changed"] > 0
                assert GEN._alignment_hits(
                    analysis["initial_out"], piece["rect"], piece["marker"]
                ) or analysis["piece_count"] > 1


def test_three_consecutive_demos_identify_each_query_residue():
    for start in range(6):
        episode = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(2000 + sample_index, sample_index, difficulty="medium")
            episode.append({"input": grid, "output": GEN.rule_python(grid)})
        assert GEN.lesson_identifiable(episode[: GEN.EXAMPLES_NEEDED], episode[-1]) == []


def test_schedule_covers_piece_count_marker_and_position_branches():
    for band in ("easy", "medium", "hard"):
        analyses = []
        for sample_index in range(3):
            grid = GEN.generate(3000 + sample_index, sample_index, difficulty=band)
            errors, analysis = GEN._analyze_grid(grid)
            assert errors == [] and analysis is not None
            analyses.append(analysis)
        assert {a["piece_count"] for a in analyses} == {1, 2, 3}
        assert {a["container_top"] for a in analyses} == {False, True}
        assert any(
            a["piece_count"] >= 2 and len(set(a["marker_colors"])) == 1
            for a in analyses
        )
        assert any(
            a["piece_count"] >= 2
            and len(set(a["marker_colors"])) == a["piece_count"]
            for a in analyses
        )
        assert any(GEN.strict_canonical_like(GEN.generate(3000 + i, i, difficulty=band)) == [] for i in range(3))


def test_override_boundaries_are_exact_observable_and_unknowns_reject():
    cases = (
        {"grid_h": 24},
        {"grid_h": 30},
        {"grid_w": 24},
        {"grid_w": 30},
        {"piece_count": 1},
        {"piece_count": 3},
        {"container_top": False},
        {"container_top": True},
        {"grid_h": 24, "grid_w": 30, "piece_count": 3, "container_top": False},
    )
    for band in ("easy", "medium", "hard"):
        for index, case in enumerate(cases):
            grid = GEN.generate(4000 + index, 12 + index, difficulty=band, **case)
            observed = GEN.observe_overrides(grid)
            for key, value in case.items():
                assert observed[key] == value
            assert GEN.self_check(grid, meta={"overrides": case}) == []
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, bogus_axis=3)


def test_deterministic_fresh_returns_and_global_rng_state():
    random.seed(987654321)
    before = random.getstate()
    first = GEN.generate(77, 19, difficulty="hard")
    intervening = GEN.generate(78, 20, difficulty="easy")
    second = GEN.generate(77, 19, difficulty="hard")
    after = random.getstate()

    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    assert intervening != first
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(77, 19, difficulty="hard") == second


def test_self_check_rejects_marker_and_rectangle_impostors():
    grid = GEN.generate(555, 0, difficulty="medium")
    errors, analysis = GEN._analyze_grid(grid)
    assert errors == [] and analysis is not None

    # Remove one cell from a piece: its connected component is no longer rectangular.
    non_rect = copy.deepcopy(grid)
    piece = analysis["pieces"][0]
    row, col = piece["cells"][0]
    non_rect[row][col] = analysis["background"]
    assert GEN.self_check(non_rect)

    # Replace a marker by its piece fill: the piece no longer shares a usable marker.
    no_marker = copy.deepcopy(grid)
    marker = piece["marker"]
    fill = next(color for color in piece["colors"] if color != marker)
    for row, col in piece["cells"]:
        if no_marker[row][col] == marker:
            no_marker[row][col] = fill
    assert any("shared marker" in error or "multicolor" in error for error in GEN.self_check(no_marker))

    # Add a second marker cell that creates more than one exact single-marker window.
    cr0, cc0, _, _ = analysis["container"]["bbox"]
    ambiguous = None
    for local_r in range(analysis["container"]["height"]):
        for local_c in range(analysis["container"]["width"]):
            candidate = copy.deepcopy(grid)
            if candidate[cr0 + local_r][cc0 + local_c] == marker:
                continue
            candidate[cr0 + local_r][cc0 + local_c] = marker
            candidate_errors = GEN.self_check(candidate)
            if any("marker alignment" in error for error in candidate_errors):
                ambiguous = candidate
                break
        if ambiguous is not None:
            break
    assert ambiguous is not None
    assert GEN.self_check(ambiguous)


def test_task_local_racket_authorities_are_exactly_synchronized():
    canonical = _canonical_rows()[0]["program_solution"]
    training = json.loads(
        (ROOT / "data/base/solutions/training/83eb0a57__69db2372d14f.json")
        .read_text(encoding="utf-8")
    )["racket_target"]
    augmented = json.loads(
        (ROOT / "data/base/solutions/augmented/83eb0a57__b9ad4bb03f8c.json")
        .read_text(encoding="utf-8")
    )["racket_target"]

    assert training["target_code"] == canonical
    assert training["raw_code"] == canonical
    assert augmented["target_code"] == canonical
    assert augmented["raw_code"] != canonical
    assert augmented["raw_code_role"] == "archival_executable_source"


def test_additional_boundary_fixtures_are_stable_and_nonidentity():
    fixtures = ((9201, 0, "easy"), (9202, 1, "medium"), (9203, 2, "hard"))
    seen = set()
    for seed, sample_index, band in fixtures:
        grid = GEN.generate(seed, sample_index, difficulty=band)
        out = GEN.rule_python(grid)
        assert out != grid
        seen.add((_sha(grid), _sha(out)))
    assert len(seen) == len(fixtures)
