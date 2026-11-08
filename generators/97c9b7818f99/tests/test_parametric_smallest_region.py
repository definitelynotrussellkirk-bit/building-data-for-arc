from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "97c9b7818f99"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
CANONICAL_PATH = PARAMETRIC / "canonical.rkt"
ALTERNATIVE_PATH = PARAMETRIC / "highlight_smallest_region.rkt"
COUNTERFACTUAL_PATH = PARAMETRIC / "skip_region_sizes.rkt"
AUDIT_PATH = PARAMETRIC / "audit.py"
MODES = ("fill_only", "highlight_smallest_region")


def _load(path: Path, stem: str):
    name = f"_{stem}_{hashlib.sha256(str(path).encode()).hexdigest()[:16]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def adapter():
    return _load(ADAPTER_PATH, "voronoi_parametric_adapter")


def audit_module():
    return _load(AUDIT_PATH, "voronoi_parametric_audit")


def canonical_program() -> str:
    return CANONICAL_PATH.read_text(encoding="utf-8")


def _copy(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def independent_fill(grid: list[list[int]], *, squared: bool = False) -> list[list[int]]:
    out = _copy(grid)
    seeds = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 8)
    ]
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            if grid[r][c] != 0:
                continue
            distances = [
                (r - sr) ** 2 + (c - sc) ** 2
                if squared
                else abs(r - sr) + abs(c - sc)
                for sr, sc, _ in seeds
            ]
            minimum = min(distances)
            owners = [seed for seed, distance in zip(seeds, distances) if distance == minimum]
            out[r][c] = 5 if len(owners) > 1 else owners[0][2]
    return out


def independent_smallest(grid: list[list[int]]) -> tuple[list[list[int]], int, dict[int, int]]:
    filled = independent_fill(grid)
    seeds = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 8)
    ]
    owned: dict[int, set[tuple[int, int]]] = {value: set() for _, _, value in seeds}
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            distances = [abs(r - sr) + abs(c - sc) for sr, sc, _ in seeds]
            minimum = min(distances)
            owners = [seed for seed, distance in zip(seeds, distances) if distance == minimum]
            if len(owners) == 1:
                owned[owners[0][2]].add((r, c))
    counts = {color: len(cells) for color, cells in owned.items()}
    selected = min(counts, key=lambda color: (counts[color], color))
    out = _copy(filled)
    for r, c in owned[selected]:
        out[r][c] = 9
    return out, selected, counts


def literal_input() -> list[list[int]]:
    # The center-right seed has the unique smallest Manhattan region, while its
    # color is neither the lowest nor highest seed color.
    return [
        [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8],
        [8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8],
        [8, 0, 2, 0, 0, 0, 0, 0, 0, 0, 8],
        [8, 0, 0, 0, 0, 0, 0, 0, 4, 0, 8],
        [8, 0, 0, 0, 0, 0, 6, 0, 0, 0, 8],
        [8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8],
        [8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8],
        [8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8],
        [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8],
    ]


@pytest.fixture(scope="module")
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge(timeout=20) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        counter = 0

        def apply(program: str, grid: list[list[int]]) -> list[list[int]]:
            nonlocal counter
            counter += 1
            name = f"voronoi-parametric-test-{counter}"
            bridge.define_grid(name, grid)
            return bridge.eval_text(f"({wrap_rule(program)} {name})")

        yield apply


def all_inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_byte_exact_canonical_and_alternative_is_distinct():
    module = adapter()
    default = module.program({"finish": "fill_only"})
    alternative = module.program({"finish": "highlight_smallest_region"})
    assert default == canonical_program()
    assert alternative == ALTERNATIVE_PATH.read_text(encoding="utf-8")
    assert alternative != default


@pytest.mark.parametrize("finish", MODES)
def test_literal_labels_match_independent_reference_and_protected_racket(racket, finish):
    module = adapter()
    source = literal_input()
    expected = independent_fill(source)
    if finish == "highlight_smallest_region":
        expected, selected, counts = independent_smallest(source)
        assert selected not in (min(counts), max(counts))
        assert list(counts.values()).count(min(counts.values())) == 1
    assert module.transform(source, finish) == expected
    assert racket(module.program({"finish": finish}), source) == expected
    assert source == literal_input()


def test_dependency_explanation_uses_filled_region_sizes():
    explanation = adapter().explain_dependency(literal_input())
    expected, selected, counts = independent_smallest(literal_input())
    assert explanation["step_a"].startswith("fill every empty interior cell")
    assert explanation["intermediate"]["region_sizes"] == {str(k): v for k, v in counts.items()}
    assert explanation["intermediate"]["selected_color"] == selected
    assert explanation["step_b"].startswith("recolor every cell")
    assert explanation["final"] == expected


def test_skip_region_size_counterfactual_is_executable_and_changes_output(racket):
    module = adapter()
    source = literal_input()
    actual = racket(module.program({"finish": "highlight_smallest_region"}), source)
    wrong = racket(COUNTERFACTUAL_PATH.read_text(encoding="utf-8"), source)
    expected, selected, counts = independent_smallest(source)
    assert actual == expected
    assert selected != min(counts)
    assert wrong != actual


@pytest.mark.parametrize("finish", MODES)
def test_generation_is_setting_neutral_deterministic_prefix_stable_and_rng_pure(finish):
    module = adapter()
    before = random.getstate()
    episode = module.generate(17, {"finish": finish}, 2, 4)
    other_finish = next(value for value in MODES if value != finish)
    other = module.generate(17, {"finish": other_finish}, 2, 4)
    one_query = module.generate(17, {"finish": finish}, 2, 1)
    six_demo = module.generate(17, {"finish": finish}, 6, 4)

    assert all_inputs(episode) == all_inputs(other)
    assert episode == module.generate(17, {"finish": finish}, 2, 4)
    assert random.getstate() == before
    assert episode["train"] == six_demo["train"][:2]
    assert episode["test"] == six_demo["test"]
    assert one_query["train"] == episode["train"]
    assert one_query["test"][0] == episode["test"][0]
    keys = [json.dumps(value, separators=(",", ":")) for value in all_inputs(six_demo)]
    assert len(keys) == len(set(keys)) == 10


@pytest.mark.parametrize("seed", [0, 1, 17, 2**63 - 1])
@pytest.mark.parametrize("finish", MODES)
def test_supported_count_boundaries_generate_identifiable_lessons(seed, finish):
    module = adapter()
    for demos, queries in ((2, 1), (2, 4), (3, 4), (6, 1), (6, 4)):
        episode = module.generate(seed, {"finish": finish}, demos, queries)
        certificate = module.certificate(
            episode["train"], [pair["input"] for pair in episode["test"]]
        )
        assert certificate["survivors"] == [finish]
        assert certificate["demonstrations"] == demos
        assert certificate["queries"] == queries
        assert set(certificate["query_disagreements"]) == set(module.HYPOTHESES) - {finish}


def test_fourth_query_is_substantive_30x30_and_depends_on_full_partition():
    module = adapter()
    canonical = module.generate(91, {"finish": "fill_only"}, 3, 4)["test"][3]
    alternative = module.generate(91, {"finish": "highlight_smallest_region"}, 3, 4)["test"][3]
    source = canonical["input"]
    info = module.observe(source)
    assert (len(source), len(source[0])) == (30, 30)
    assert info["seed_count"] == 4
    assert info["tie_count"] >= 10
    assert min(info["region_sizes"].values()) >= 20
    assert max(info["region_sizes"].values()) - min(info["region_sizes"].values()) >= 20
    rows = [seed[0] for seed in info["seeds"]]
    cols = [seed[1] for seed in info["seeds"]]
    assert min(rows) <= 5 and max(rows) >= 24
    assert min(cols) <= 5 and max(cols) >= 24
    assert canonical["output"] != alternative["output"]
    changed = sum(
        left != right
        for left_row, right_row in zip(canonical["output"], alternative["output"])
        for left, right in zip(left_row, right_row)
    )
    assert changed == min(info["region_sizes"].values())


@pytest.mark.parametrize("finish", MODES)
def test_two_demos_identify_setting_and_declared_shortcuts(finish):
    module = adapter()
    episode = module.generate(23, {"finish": finish}, 2, 4)
    certificate = module.certificate(
        episode["train"], [pair["input"] for pair in episode["test"]]
    )
    assert certificate["survivors"] == [finish]
    assert set(certificate["declared_hypotheses"]) >= {
        "fill_only",
        "highlight_smallest_region",
        "highlight_largest_region",
        "highlight_second_smallest_region",
        "highlight_lowest_color",
        "highlight_highest_color",
        "highlight_smallest_seed_only",
        "highlight_smallest_bbox",
        "euclidean_smallest_region",
        "identity",
    }


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, {"finish": "fill_only"}, 2, 4),
        (-1, {"finish": "fill_only"}, 2, 4),
        (2**63, {"finish": "fill_only"}, 2, 4),
        (0, {"finish": "wrong"}, 2, 4),
        (0, {"finish": "fill_only", "extra": 1}, 2, 4),
        (0, {"finish": "fill_only"}, 1, 4),
        (0, {"finish": "fill_only"}, 7, 4),
        (0, {"finish": "fill_only"}, 2, 0),
        (0, {"finish": "fill_only"}, 2, 5),
        (0, {"finish": "fill_only"}, 2, True),
    ],
)
def test_bad_requests_fail_explicitly(seed, settings, demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(seed, settings, demos, queries)


def test_boolean_grid_cells_are_rejected():
    source = literal_input()
    source[1][1] = False
    with pytest.raises(ValueError):
        adapter().transform(source, "highlight_smallest_region")


def test_public_projection_hides_settings_program_answers_and_future_queries():
    module = adapter()
    episode = module.generate(5, {"finish": "highlight_smallest_region"}, 3, 4)
    first_turn = {"train": episode["train"], "test": [episode["test"][0]]}
    raw = public_challenge_bytes(first_turn)
    public = json.loads(raw)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1 and set(public["test"][0]) == {"input"}
    assert b"settings" not in raw and b"program_solution" not in raw
    assert public_challenge_id(first_turn) == hashlib.sha256(raw).hexdigest()

    one_query = module.generate(5, {"finish": "highlight_smallest_region"}, 3, 1)
    assert public_challenge_bytes(one_query) == raw


def test_all_generated_labels_match_protected_racket(racket):
    module = adapter()
    for finish in MODES:
        episode = module.generate(7, {"finish": finish}, 6, 4)
        selected_program = module.program({"finish": finish})
        for pair in episode["train"] + episode["test"]:
            assert racket(selected_program, pair["input"]) == pair["output"]


def test_audit_tool_checks_bounded_lessons_and_writes_machine_report(tmp_path):
    report = audit_module().run_audit(seed_start=0, seed_count=8)
    assert report["status"] == "passed"
    assert report["episodes"] == 8 * 2 * 3
    assert report["failures"] == []
    assert report["declared_hypotheses"] >= 10
    assert report["exact_30x30_pairs"] == 8 * 2 * 3
    output = tmp_path / "audit.json"
    audit_module().write_report(output, report)
    assert json.loads(output.read_text()) == report
