from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
TASK_ID = "c1ee27b39d13"
generator, GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(
    TASK_ID, root=ROOT
)
CANONICAL = canonical_path(ROOT)
_BASE_RELATIVE = Path(
    "data/base/solutions/banks/0e5302a13aba/S5_H7__c1ee27b39d13.json"
)
BASE = next(
    path
    for path in (ROOT / _BASE_RELATIVE, ROOT / "shared" / _BASE_RELATIVE)
    if path.is_file()
)


def _canonical_rows():
    return [
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]


def _pairs(value):
    return [value] if isinstance(value, dict) else list(value)


def _norm(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return copy.deepcopy(grid)


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_and_task_local_target_are_synchronized():
    rows = _canonical_rows()
    assert len(rows) == 1
    program = rows[0]["program_solution"]
    digest = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
    base = json.loads(BASE.read_text())

    assert digest == generator.RULE_HASH == "6a46c5a9b416"
    assert base["racket_target"]["target_code"] == program


def test_all_canonical_pairs_pass_structural_check_and_mirror():
    for row in _canonical_rows():
        for split in ("train", "test"):
            for pair in _pairs(row[split]):
                grid = _norm(pair["input"])
                before = copy.deepcopy(grid)
                assert generator.self_check(grid) == []
                assert generator.rule_mirror(grid) == _norm(pair["output"])
                assert grid == before


def test_deterministic_replay_is_fresh_and_global_rng_pure():
    random.seed(271828)
    state = random.getstate()
    first = generator.generate(17, 29, difficulty="hard")
    assert random.getstate() == state
    second = generator.generate(17, 29, difficulty="hard")
    assert random.getstate() == state

    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert second[0][0] == 0


def test_exact_overrides_are_observable_and_textures_are_live():
    grids = {}
    for texture in generator.HELPFUL_TEXTURES:
        grid = generator.generate(
            41,
            43,
            difficulty="medium",
            grid_h=6,
            grid_w=16,
            n_row_marks=4,
            n_col_marks=4,
            texture=texture,
        )
        assert (len(grid), len(grid[0])) == (6, 16)
        assert generator.observe_overrides(grid) == {
            "n_row_marks": 4,
            "n_col_marks": 4,
        }
        assert generator.self_check(grid) == []
        grids[texture] = _frozen(grid)

    assert len(set(grids.values())) == len(generator.HELPFUL_TEXTURES)


def test_self_check_rejects_targeted_semantic_impostors():
    base = generator.generate(
        101,
        7,
        difficulty="medium",
        grid_h=10,
        grid_w=11,
        n_row_marks=3,
        n_col_marks=3,
        texture="default",
    )
    _, selected_rows, selected_cols = generator._selector_facts(base)
    unselected_rows = [
        row for row in range(1, len(base)) if row not in selected_rows
    ]
    unselected_cols = [
        col for col in range(1, len(base[0])) if col not in selected_cols
    ]

    impostors = {}

    grid = copy.deepcopy(base)
    for row in selected_rows:
        grid[row][0] = 0
    impostors["no row selectors"] = grid

    grid = copy.deepcopy(base)
    for col in selected_cols:
        grid[0][col] = 0
    impostors["no column selectors"] = grid

    grid = copy.deepcopy(base)
    for row in range(1, len(grid)):
        grid[row][0] = 5
    for col in range(1, len(grid[0])):
        grid[0][col] = 4
    impostors["all rows and columns selected"] = grid

    grid = copy.deepcopy(base)
    grid[0][unselected_cols[0]] = 7
    impostors["illegal top-row distractor"] = grid

    grid = copy.deepcopy(base)
    for row in unselected_rows:
        grid[row][0] = 0
    impostors["missing left-border distractor"] = grid

    grid = copy.deepcopy(base)
    for row in range(1, len(grid)):
        for col in range(1, len(grid[0])):
            if grid[row][col] in (4, 5):
                grid[row][col] = 1
    impostors["globally unique marker colors"] = grid

    grid = copy.deepcopy(base)
    for row in selected_rows:
        for col in selected_cols:
            grid[row][col] = 1
    impostors["uniform selected answer"] = grid

    failures = {
        name: generator.self_check(grid) for name, grid in impostors.items()
    }
    assert all(errors for errors in failures.values()), failures
    assert len(failures) >= 4


def test_semantic_census_spans_counts_layouts_and_marker_payload_roles():
    row_counts = set()
    col_counts = set()
    answer_marker_roles = set()
    output_shapes = set()
    selector_layouts = set()

    for band in ("easy", "medium", "hard"):
        for seed in range(1000, 1040):
            grid = generator.generate(seed, seed * 13 + 5, difficulty=band)
            assert generator.self_check(grid, difficulty=band) == []
            _, selected_rows, selected_cols = generator._selector_facts(grid)
            answer = generator.rule_mirror(grid)
            values = {value for row in answer for value in row}

            row_counts.add(len(selected_rows))
            col_counts.add(len(selected_cols))
            answer_marker_roles.add((4 in values, 5 in values))
            output_shapes.add((len(answer), len(answer[0])))
            selector_layouts.add((selected_rows, selected_cols))

    assert row_counts == {2, 3, 4}
    assert col_counts == {2, 3, 4}
    assert answer_marker_roles == {
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    }
    assert len(output_shapes) >= 7
    assert len(selector_layouts) >= 80
