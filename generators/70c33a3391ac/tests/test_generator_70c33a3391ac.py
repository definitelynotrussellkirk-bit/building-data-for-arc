from __future__ import annotations

import copy
import hashlib
import importlib
import itertools
import json
import random
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
DATA_ROOT = canonical_path(ROOT).parents[1]
TASK_ID = "70c33a3391ac"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.70c33a3391ac.generator"
)


def _canonical_rows():
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    assert len(rows) == 2
    return rows


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _output(grid):
    return [list(row) for row in GEN._analysis(grid)["duplicate"]["crop"]]


def _blank_component(grid, component):
    result = copy.deepcopy(grid)
    for row, col in component["cells"]:
        result[row][col] = 0
    return result


def test_metadata_canonical_pairs_and_authorities_are_synchronized():
    rows = _canonical_rows()
    canonical = rows[0]["program_solution"]
    assert all(row["program_solution"] == canonical for row in rows)
    assert GEN.VERSION == "3.1.0"
    assert GEN.RULE_HASH == _normalized_hash(canonical) == "4fc872f50360"
    assert set(GEN.AXES) == {
        "canonical_prior",
        "n_components",
        "duplicate_rank",
        "duplicate_palette_relation",
    }
    seen = set()
    for row in rows:
        for pair in [*row["train"], *row["test"]]:
            original = copy.deepcopy(pair["input"])
            assert GEN.self_check(pair["input"]) == []
            assert _output(pair["input"]) == pair["output"]
            assert pair["input"] == original
            seen.add(tuple(map(tuple, pair["input"])))
    assert len(seen) == 4
    for path in (
        DATA_ROOT / "base/solutions/training/f5aa3634__70c33a3391ac.json",
        DATA_ROOT / "base/solutions/augmented/f5aa3634__51683b0b6449.json",
    ):
        target = json.loads(path.read_text())["racket_target"]
        # raw_code is archival; selected target_code is the active authority.
        assert _normalized_hash(target["raw_code"]) == _normalized_hash(canonical)
        assert target["target_code"] == canonical
        assert target["canonicalization_status"] == "canonical"
        assert target["code_form"] == "canonical_rule"


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("n_components", [4, 5, 6])
@pytest.mark.parametrize("duplicate_rank", GEN.DUPLICATE_RANKS)
@pytest.mark.parametrize("relation", GEN.PALETTE_RELATIONS)
def test_every_generalized_exact_axis_combination_is_observable(
    difficulty, n_components, duplicate_rank, relation
):
    overrides = {
        "canonical_prior": False,
        "n_components": n_components,
        "duplicate_rank": duplicate_rank,
        "duplicate_palette_relation": relation,
    }
    grid = GEN.generate(2000 + n_components, 31, difficulty=difficulty, **overrides)
    assert GEN.self_check(grid, difficulty=difficulty, meta={"overrides": overrides}) == []
    assert GEN.observe_overrides(grid) == overrides


def test_single_semantic_overrides_never_sporadically_enter_an_incompatible_canonical_profile():
    for seed in range(60):
        grid = GEN.generate(seed, seed + 9, difficulty="medium", duplicate_rank="smallest")
        observed = GEN.observe_overrides(grid)
        assert observed["duplicate_rank"] == "smallest"
        assert observed["canonical_prior"] is False


def test_canonical_prior_accepts_only_compatible_profiles():
    for index, facts in enumerate(GEN._CANONICAL_FACTS):
        overrides = {
            "canonical_prior": True,
            "n_components": facts["n_components"],
            "duplicate_rank": facts["duplicate_rank"],
            "duplicate_palette_relation": facts["duplicate_palette_relation"],
        }
        grid = GEN.generate(3100 + index, 7, difficulty="hard", **overrides)
        assert GEN.observe_overrides(grid) == overrides
    with pytest.raises(ValueError, match="no canonical profile"):
        GEN.generate(1, 2, canonical_prior=True, duplicate_rank="smallest")
    with pytest.raises(ValueError, match="no canonical profile"):
        GEN.generate(
            1,
            2,
            canonical_prior=True,
            n_components=6,
            duplicate_palette_relation="private",
        )


def test_normal_draws_cover_all_semantic_branches_and_canonical_profiles():
    observed = set()
    canonical_signatures = set()
    inputs = set()
    outputs = set()
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        for seed in range(180):
            grid = GEN.generate(10_000 + seed, band_index * 1000 + seed, difficulty=difficulty)
            assert GEN.self_check(grid, difficulty=difficulty) == []
            info = GEN.observe_overrides(grid)
            observed.add((info["n_components"], info["duplicate_rank"], info["duplicate_palette_relation"]))
            if info["canonical_prior"]:
                canonical_signatures.add(GEN._equality_signature(grid))
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, _output(grid))))
    assert {item[0] for item in observed} == {4, 5, 6}
    assert {item[1] for item in observed} == set(GEN.DUPLICATE_RANKS)
    assert {item[2] for item in observed} == set(GEN.PALETTE_RELATIONS)
    assert canonical_signatures == GEN._CANONICAL_SIGNATURES
    assert len(inputs) > 530
    assert len(outputs) > 500



def test_three_demo_schedule_contains_decisive_shape_palette_and_count_rebuttals():
    for seed in range(100):
        grids = [GEN.generate(seed, sample_index, difficulty="medium") for sample_index in range(3)]
        infos = [GEN._analysis(grid) for grid in grids]
        observed = [GEN.observe_overrides(grid) for grid in grids]
        assert [item["canonical_prior"] for item in observed] == [True, False, False]

        first_general = infos[1]
        assert first_general["components"][0]["crop"] != first_general["duplicate"]["crop"]
        assert any(
            distractor["mask"] == first_general["duplicate"]["mask"]
            and distractor["crop"] != first_general["duplicate"]["crop"]
            for distractor in first_general["distractors"]
        )

        decisive = infos[2]
        assert decisive["components"][-1]["crop"] != decisive["duplicate"]["crop"]
        assert observed[2]["duplicate_rank"] == "middle"
        assert observed[2]["duplicate_palette_relation"] == "shared"
        assert observed[2]["n_components"] >= 5
        assert any(
            distractor["mask"] == decisive["duplicate"]["mask"]
            and distractor["crop"] != decisive["duplicate"]["crop"]
            for distractor in decisive["distractors"]
        )
        assert any(
            distractor["colors"] == decisive["duplicate"]["colors"]
            and distractor["crop"] != decisive["duplicate"]["crop"]
            for distractor in decisive["distractors"]
        )
        counts = [component["cell_count"] for component in decisive["distractors"]]
        assert min(counts) < decisive["duplicate"]["cell_count"] < max(counts)

def test_self_check_rejects_targeted_semantic_impostors():
    grid = GEN.generate(
        81,
        14,
        difficulty="medium",
        canonical_prior=False,
        n_components=6,
        duplicate_rank="middle",
        duplicate_palette_relation="shared",
    )
    info = GEN._analysis(grid)
    duplicate_components = [
        component for component in info["components"]
        if component["crop"] == info["duplicate"]["crop"]
    ]
    no_duplicate = _blank_component(grid, duplicate_components[1])

    monochrome_duplicate = copy.deepcopy(grid)
    for component in duplicate_components:
        for row, col in component["cells"]:
            monochrome_duplicate[row][col] = 1

    collapsed_palette = [
        [0 if value == 0 else 1 + (value % 2) for value in row]
        for row in grid
    ]

    triple_duplicate = [[0] * 16 for _ in range(12)]
    pattern = ((1, 2, 0), (1, 2, 2))
    other_a = ((3, 4, 0), (3, 4, 4))
    other_b = ((5, 6, 0), (5, 6, 6))
    for top, left, crop in ((0, 0, pattern), (0, 6, pattern), (5, 0, pattern), (5, 6, other_a), (9, 10, other_b)):
        for dr, row in enumerate(crop):
            for dc, value in enumerate(row):
                if value:
                    triple_duplicate[top + dr][left + dc] = value

    flat_rank = [[0] * 16 for _ in range(10)]
    crops = (
        ((1, 2, 0), (1, 2, 2)),
        ((1, 2, 0), (1, 2, 2)),
        ((3, 4, 0), (3, 4, 4)),
        ((5, 6, 0), (5, 6, 6)),
    )
    for (top, left), crop in zip(((0, 0), (0, 6), (5, 0), (5, 6)), crops):
        for dr, row in enumerate(crop):
            for dc, value in enumerate(row):
                if value:
                    flat_rank[top + dr][left + dc] = value

    for impostor in (no_duplicate, monochrome_duplicate, collapsed_palette, triple_duplicate, flat_rank):
        assert GEN.self_check(impostor), impostor


def test_replay_freshness_global_rng_and_request_validation():
    kwargs = dict(
        difficulty="hard",
        canonical_prior=False,
        n_components=6,
        duplicate_rank="largest",
        duplicate_palette_relation="private",
    )
    random.seed(91273)
    state = random.getstate()
    first = GEN.generate(991, 17, **kwargs)
    assert random.getstate() == state
    second = GEN.generate(991, 17, **kwargs)
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert second == GEN.generate(991, 17, **kwargs)
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, texture="warm")
    with pytest.raises(ValueError, match="unsupported difficulty"):
        GEN.generate(1, 2, difficulty="extreme")
    with pytest.raises(ValueError):
        GEN.generate(1, 2, n_components=3)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, duplicate_rank="flat")


def test_generate_rejects_non_plain_scalar_call_arguments_and_overrides():
    invalid_calls = (
        (True, 0),
        (False, 0),
        (1.0, 0),
        (1.75, 0),
        ("1", 0),
        (1, True),
        (1, False),
        (1, 1.0),
        (1, 1.75),
        (1, -1),
    )
    for seed, sample_index in invalid_calls:
        with pytest.raises(ValueError, match="seed|sample_index"):
            GEN.generate(seed, sample_index, difficulty="easy")
    for value in (True, False, 4.0, 6.0, "4"):
        with pytest.raises(ValueError, match="n_components"):
            GEN.generate(1, 2, n_components=value)
    for value in (1, 0, "false"):
        with pytest.raises(ValueError, match="canonical_prior"):
            GEN.generate(1, 2, canonical_prior=value)


def _declared_combination_matches(case, declaration):
    if isinstance(declaration, dict):
        items = declaration.items()
    else:
        items = ((name, None) for name in declaration)
    for name, expected in items:
        if name not in case:
            return False
        if expected is None:
            continue
        allowed = expected if isinstance(expected, (list, tuple, set, frozenset)) else (expected,)
        if case[name] not in allowed:
            return False
    return True


def test_every_rejected_canonical_override_tuple_is_declared_incompatible():
    declarations = GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS
    axes = {
        "n_components": (4, 5, 6),
        "duplicate_rank": GEN.DUPLICATE_RANKS,
        "duplicate_palette_relation": GEN.PALETTE_RELATIONS,
    }
    for count in range(len(axes) + 1):
        for names in itertools.combinations(axes, count):
            for values in itertools.product(*(axes[name] for name in names)):
                case = {"canonical_prior": True, **dict(zip(names, values))}
                try:
                    GEN.generate(173, 7, difficulty="medium", **case)
                except ValueError:
                    assert any(
                        _declared_combination_matches(case, declaration)
                        for declaration in declarations
                    ), case


def _label(grid):
    return {"input": copy.deepcopy(grid), "output": _output(grid)}


def test_semantic_contract_makes_exact_orientation_shape_and_palette_load_bearing():
    expected = {
        "d4_equivalent_crop_first",
        "shape_only_first",
        "palette_only_first",
    }
    assert set(GEN.SEMANTIC_WITNESSES) == expected
    assert set(GEN.SEMANTIC_RIVALS) == expected
    assert set(GEN.LESSON_COMPETITORS) == expected
    assert set(GEN.CANONICAL_SHORTCUTS) == expected
    assert set(GEN.WITNESS_RIVALS) == expected

    for difficulty in ("easy", "medium", "hard"):
        for seed in range(30):
            for sample_index in (1, 2):
                grid = GEN.generate(50_000 + seed, sample_index, difficulty=difficulty)
                observed = GEN.observe_overrides(grid)
                assert observed["canonical_prior"] is False
                assert observed["duplicate_palette_relation"] == "shared"
                exact = _output(grid)
                for name in expected:
                    assert GEN.SEMANTIC_WITNESSES[name](grid), (difficulty, seed, sample_index, name)
                    assert GEN.SEMANTIC_RIVALS[name](grid) != exact


def test_default_three_demo_lesson_refutes_declared_canonical_shortcuts():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(24):
            pairs = [
                _label(GEN.generate(61_000 + seed, sample_index, difficulty=difficulty))
                for sample_index in range(4)
            ]
            assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []

    canonical_demos = []
    for facts in GEN._CANONICAL_FACTS[:3]:
        canonical_demos.append(
            _label(
                GEN.generate(
                    72_000 + len(canonical_demos),
                    0,
                    canonical_prior=True,
                    n_components=facts["n_components"],
                    duplicate_rank=facts["duplicate_rank"],
                    duplicate_palette_relation=facts["duplicate_palette_relation"],
                )
            )
        )
    canonical_query = _label(
        GEN.generate(
            72_010,
            0,
            canonical_prior=True,
            n_components=GEN._CANONICAL_FACTS[3]["n_components"],
            duplicate_rank=GEN._CANONICAL_FACTS[3]["duplicate_rank"],
            duplicate_palette_relation=GEN._CANONICAL_FACTS[3]["duplicate_palette_relation"],
        )
    )
    reasons = GEN.lesson_identifiable(canonical_demos, canonical_query)
    assert reasons
    assert any("d4_equivalent_crop_first" in reason for reason in reasons)


def test_strict_canonical_hook_accepts_all_canonical_profiles_and_rejects_generalized():
    for scene in GEN._CANONICAL_SCENES:
        assert GEN.strict_canonical_like(GEN._scene_grid(scene)) == []
    generalized = GEN.generate(
        8801,
        1,
        difficulty="hard",
        canonical_prior=False,
        n_components=6,
        duplicate_rank="middle",
        duplicate_palette_relation="shared",
    )
    assert GEN.strict_canonical_like(generalized)


def _load_parametric_prototype():
    path = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
    assert path.is_file(), f"missing proposed parametric prototype: {path}"
    spec = importlib.util.spec_from_file_location(
        "parametric_70c33a3391ac", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parametric_minimum_occurrences_prototype_is_episode_fixed_and_distinguishing():
    proto = _load_parametric_prototype()
    assert proto.MINIMUM_OCCURRENCES == (2, 3)
    assert proto.DEFAULT_MINIMUM_OCCURRENCES == 2
    assert proto.PARAMETERS["minimum_occurrences"] == {
        "allowed": (2, 3),
        "default": 2,
        "selected_once_per_episode": True,
    }

    canonical = _canonical_rows()[0]["program_solution"]
    assert proto.program_for(2) == canonical
    assert _normalized_hash(proto.program_for(3)) != _normalized_hash(canonical)

    for minimum in proto.MINIMUM_OCCURRENCES:
        episode = proto.build_episode(
            20261021,
            minimum_occurrences=minimum,
            n_train=3,
            n_test=1,
        )
        assert episode["parameter_draw_count"] == 1
        assert episode["parameter"] == {"minimum_occurrences": minimum}
        assert episode["program"] == proto.program_for(minimum)
        assert proto.episode_errors(episode) == []
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1

        for pair in [*episode["train"], *episode["test"]]:
            outputs = {
                candidate: proto.apply_python(pair["input"], candidate)
                for candidate in proto.MINIMUM_OCCURRENCES
            }
            assert pair["output"] == outputs[minimum]
            assert outputs[2] != outputs[3]

        public = proto.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        serialized = json.dumps(public)
        assert "minimum_occurrences" not in serialized
        assert "(rule!" not in serialized

    assert proto.build_episode(20261021, minimum_occurrences=2) == proto.build_episode(
        20261021, minimum_occurrences=2
    )
