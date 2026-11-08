"""Focused authority, override, validator, and curriculum regressions."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import random
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    canonical_pairs,
    canonical_rule_source,
    connected,
    intended_output,
    load_generator,
    normalized_rule_hash,
    prototype_cells,
    rival_outputs,
    sequence_codes,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
BANDS = (None, "easy", "medium", "hard")


def test_rule_pin_and_python_mirror_match_every_canonical_pair():
    pairs = canonical_pairs()
    assert len(pairs) == 5
    assert gen.RULE_HASH == normalized_rule_hash(canonical_rule_source()) == "e8e6e0187218"
    for pair in pairs:
        source = deepcopy(pair["input"])
        before = deepcopy(source)
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert intended_output(source) == pair["output"]
        assert gen.rule_mirror(source) == pair["output"]
        assert source == before


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("count", (4, 8))
def test_exact_prototype_cell_override_is_observable_in_every_band(band, count):
    grid = gen.generate(3107, 19, difficulty=band, prototype_cells=count)
    assert gen.self_check(grid) == []
    assert connected(prototype_cells(grid))
    assert len(prototype_cells(grid)) == count
    assert gen.observe_overrides(grid) == {"prototype_cells": count}


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 4},
        {"prototype_cells": 3},
        {"prototype_cells": 9},
        {"prototype_cells": True},
        {"prototype_cells": 4.0},
        {"prototype_cells": "4"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises(ValueError):
        gen.generate(1, 0, **overrides)


def test_validator_rejects_disconnected_prototype_impostor():
    grid = deepcopy(canonical_pairs()[0]["input"])
    occupied = sorted(prototype_cells(grid))
    r, c = occupied[-1]
    grid[r][c] = 0
    grid[0][4] = 1
    assert len(prototype_cells(grid)) == len(occupied)
    assert not connected(prototype_cells(grid))
    assert gen.self_check(grid)
    assert gen.strict_canonical_like(grid)


@pytest.mark.parametrize("band", BANDS)
def test_generated_inputs_are_lawful_deterministic_fresh_and_nontrivial(band):
    seen = set()
    counts = set()
    palette_sizes = set()
    for index in range(96):
        grid = gen.generate(80_000 + index, index, difficulty=band)
        again = gen.generate(80_000 + index, index, difficulty=band)
        assert grid == again
        assert grid is not again
        assert all(a is not b for a, b in zip(grid, again))
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert connected(prototype_cells(grid))
        assert gen.rule_mirror(grid) == intended_output(grid)
        assert gen.rule_mirror(grid) != grid
        assert len(grid) == 6 and all(len(row) == 5 for row in grid)
        counts.add(len(prototype_cells(grid)))
        palette_sizes.add(len({value for row in grid for value in row}))
        seen.add(json.dumps(grid, separators=(",", ":")))
    assert len(seen) >= 88
    assert counts >= ({4, 5} if band == "easy" else {7, 8} if band == "hard" else {4, 8})
    assert palette_sizes <= {4, 5, 6}
    assert palette_sizes


def test_every_three_consecutive_schedule_profiles_cover_all_opcodes_and_refute_rivals():
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.SCHEDULE_PROFILES) == {"codes_0124", "codes_0345", "codes_1235"}
    for start in range(24):
        grids = [gen.generate(91_000 + start, start + offset, difficulty="medium")
                 for offset in range(gen.EXAMPLES_NEEDED)]
        assert {gen.schedule_profile(91_000 + start, start + offset, difficulty="medium")
                for offset in range(gen.EXAMPLES_NEEDED)} == set(gen.SCHEDULE_PROFILES)
        assert set().union(*(set(sequence_codes(grid)) for grid in grids)) == set(range(6))
        for grid in grids:
            intended = intended_output(grid)
            assert all(output != intended for output in rival_outputs(grid).values())
            assert all(rival(grid) != intended for rival in gen.LESSON_COMPETITORS.values())


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_cyclic_three_demo_lesson_is_declared_identifiable(band):
    for start in range(18):
        demos = []
        for offset in range(gen.EXAMPLES_NEEDED):
            grid = gen.generate(120_000 + start, start + offset, difficulty=band)
            demos.append({"input": grid, "output": intended_output(grid)})
        query_grid = gen.generate(220_000 + start, start + gen.EXAMPLES_NEEDED, difficulty=band)
        query = {"input": query_grid, "output": intended_output(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
        for name, competitor in gen.LESSON_COMPETITORS.items():
            assert any(competitor(pair["input"]) != pair["output"] for pair in demos), name


def test_generation_does_not_touch_global_random_state():
    random.seed(20261004)
    state = random.getstate()
    gen.generate(999, 17, difficulty="hard")
    assert random.getstate() == state


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import importlib.util,json,sys;"
        "p=sys.argv[1];s=importlib.util.spec_from_file_location('g',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.generate(712,11,difficulty='hard'),separators=(',',':')))"
    )
    outputs = []
    for hash_seed in ("1", "98765"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        env["PYTHONPATH"] = os.pathsep.join(
            [str(HOME.parents[1] / "shared/runtime"), env.get("PYTHONPATH", "")]
        )
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "generator.py")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_difficulty_bands_change_default_cell_count_distribution_without_clipping_domain():
    easy = [len(prototype_cells(gen.generate(330_000 + i, i, difficulty="easy"))) for i in range(64)]
    medium = [len(prototype_cells(gen.generate(330_000 + i, i, difficulty="medium"))) for i in range(64)]
    hard = [len(prototype_cells(gen.generate(330_000 + i, i, difficulty="hard"))) for i in range(64)]
    assert easy != medium != hard
    assert sum(easy) < sum(medium) < sum(hard)
    for band in ("easy", "medium", "hard"):
        assert len(prototype_cells(gen.generate(44, 2, difficulty=band, prototype_cells=4))) == 4
        assert len(prototype_cells(gen.generate(44, 2, difficulty=band, prototype_cells=8))) == 8


def test_every_leave_one_out_rotation_of_four_consecutive_pairs_covers_all_opcodes():
    for band in ("easy", "medium", "hard"):
        for start in range(18):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(510_000 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": intended_output(grid)})
            for query_index in range(len(pairs)):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                assert set().union(*(set(sequence_codes(pair["input"])) for pair in demos)) == set(range(6))
                assert gen.lesson_identifiable(demos, query) == []
