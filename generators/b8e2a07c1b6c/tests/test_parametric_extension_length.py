"""Focused tests for the proposed arrow extension-length prototype."""
from __future__ import annotations

import copy
import importlib.util
import json
from functools import cache
from pathlib import Path

import pytest

from reviewer_support import (
    canonical_pairs,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "b8e2a07c1b6c"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"


@cache
def prototype():
    assert PROTOTYPE_PATH.is_file(), "extension-length prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_extension_length_b8e2a07c1b6c", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _literal_witness() -> list[list[int]]:
    """12x14 lawful right-facing arrow with four exterior cells available."""
    h, w = 12, 14
    grid = [[5 for _ in range(w)] for _ in range(h)]
    for c in range(w):
        grid[0][c] = 8
        grid[h - 1][c] = 9
    for r in range(2, 9):
        for c in range(2, 9):
            grid[r][c] = 7
    grid[5][4] = 2
    grid[5][3] = 6
    grid[5][2] = 6
    return grid


def _paint_cells(grid: list[list[int]], cells: list[tuple[int, int]]) -> list[list[int]]:
    out = copy.deepcopy(grid)
    for r, c in cells:
        out[r][c] = 7
    return out


def test_default_rule_is_exact_canonical_and_alternate_is_bounded() -> None:
    """Catches canonical drift, source broadening, and coercive settings."""
    p = prototype()
    canonical = p.canonical_source(root=ROOT)
    one = p.materialize_rule(1, root=ROOT)
    two = p.materialize_rule(2, root=ROOT)

    assert one == canonical
    assert two != canonical
    assert p.rule_setting(one, root=ROOT) == 1
    assert p.rule_setting(two, root=ROOT) == 2
    assert p.PARAMETER == {
        "name": "extension_length",
        "allowed": (1, 2),
        "default": 1,
    }

    for invalid in (0, 3, True, 1.0, "1", None):
        with pytest.raises(ValueError, match="extension_length"):
            p.materialize_rule(invalid, root=ROOT)
    with pytest.raises(ValueError, match="pinned canonical"):
        p.materialize_rule(1, root=ROOT, source=canonical + "\n")


def test_racket_executes_literal_witness_and_default_replays_canonical() -> None:
    """Catches Python-only labels, swapped counts, and a noncanonical default."""
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    witness = _literal_witness()
    facts = p.ray_facts(witness)
    assert facts["direction"] == "right"
    assert facts["exterior_cells"][:4] == [(5, 9), (5, 10), (5, 11), (5, 12)]
    expected_one = _paint_cells(witness, facts["exterior_cells"][:1])
    expected_two = _paint_cells(witness, facts["exterior_cells"][:2])

    with RacketBridge(max_calls_before_restart=128) as bridge:
        assert p.execute_rule(
            p.materialize_rule(1, root=ROOT), witness, bridge=bridge, root=ROOT
        ) == expected_one
        assert p.execute_rule(
            p.materialize_rule(2, root=ROOT), witness, bridge=bridge, root=ROOT
        ) == expected_two

        pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
        replayed = p.execute_rule_many(
            p.materialize_rule(1, root=ROOT),
            [pair["input"] for pair in pairs],
            bridge=bridge,
            root=ROOT,
        )
        assert replayed == [pair["output"] for pair in pairs]


def test_seed_counts_and_input_schedule_are_strict_prefix_stable() -> None:
    """Catches bool coercion, setting-dependent inputs, and count/retry aliasing."""
    p = prototype()
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)

    assert p.parameter_for_seed(0) == {"extension_length": 1}
    assert p.parameter_for_seed(1) == {"extension_length": 2}
    assert p.parameter_for_seed(2) == {"extension_length": 1}
    for invalid in (True, -1, 2**63, 1.5, "1"):
        with pytest.raises(ValueError, match="seed"):
            p.parameter_for_seed(invalid)

    short = p.episode_inputs(317, demo_count=2, query_count=4, root=ROOT)
    long = p.episode_inputs(317, demo_count=2, query_count=6, root=ROOT)
    assert short == long[:6]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in long}) == 8
    assert [p.ray_facts(grid)["direction"] for grid in short[:2]] == ["right", "left"]
    for grid in long:
        assert generator.self_check(grid) == []
        facts = p.ray_facts(grid)
        assert len(facts["exterior_cells"]) >= 3
        assert all(grid[r][c] in {5, 8, 9} for r, c in facts["exterior_cells"][:3])

    for name, value in (
        ("demo_count", 1),
        ("demo_count", 9),
        ("demo_count", True),
        ("query_count", 0),
        ("query_count", 9),
        ("query_count", 4.0),
    ):
        kwargs = {"demo_count": 2, "query_count": 4, name: value}
        with pytest.raises(ValueError, match=name):
            p.episode_inputs(0, root=ROOT, **kwargs)


def test_episode_setting_is_fixed_identifiable_and_has_four_racket_queries() -> None:
    """Catches per-pair resampling, unlabeled rivals, and query-assisted teaching."""
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=128) as bridge:
        for seed, selected in ((0, 1), (1, 2)):
            public, private = p.generate_episode(
                seed,
                demo_count=2,
                query_count=4,
                bridge=bridge,
                root=ROOT,
            )
            public_again, private_again = p.generate_episode(
                seed,
                demo_count=2,
                query_count=4,
                bridge=bridge,
                root=ROOT,
            )
            assert public == public_again
            assert private == private_again
            assert private["parameter"] == {"extension_length": selected}
            assert private["parameter_draw_count"] == 1
            assert len(public["train"]) == 2
            assert len(public["test"]) == 4
            assert all(set(pair) == {"input", "output"} for pair in public["train"])
            assert all(set(pair) == {"input"} for pair in public["test"])
            assert len(private["query_answers"]) == 4
            assert private["surviving_rivals_from_demonstrations"] == [
                f"extension_length_{selected}"
            ]

            selected_check = private["rival_checks"][f"extension_length_{selected}"]
            assert selected_check["matches_all_demonstrations"] is True
            assert selected_check["demonstration_disagreements"] == []
            assert selected_check["query_disagreements"] == []
            for name in (
                f"extension_length_{3 - selected}",
                "second_exterior_only",
                "paint_to_grid_edge",
            ):
                check = private["rival_checks"][name]
                assert check["matches_all_demonstrations"] is False
                assert check["demonstration_disagreements"] == [0, 1]
                assert check["query_disagreements"] == [0, 1, 2, 3]

            selected_program = p.materialize_rule(selected, root=ROOT)
            visible_grids = [pair["input"] for pair in public["train"] + public["test"]]
            selected_outputs = p.execute_rule_many(
                selected_program, visible_grids, bridge=bridge, root=ROOT
            )
            assert selected_outputs[:2] == [pair["output"] for pair in public["train"]]
            assert selected_outputs[2:] == private["query_answers"]


def test_writer_uses_visible_only_ids_rejects_duplicates_and_refuses_overwrite(
    tmp_path: Path,
) -> None:
    """Catches private leakage, ordinal filenames, duplicate payloads, and clobbering."""
    p = prototype()
    out = tmp_path / "evidence"
    manifest = p.write_evidence(
        out,
        seeds=[0, 1],
        demo_count=2,
        query_count=4,
        root=ROOT,
    )
    assert manifest["status"] == "proposed_unapproved"
    assert manifest["parameter"] == {
        "name": "extension_length",
        "allowed": [1, 2],
        "default": 1,
    }
    assert manifest["canonical_default_unchanged"] is True
    assert manifest["public_ids"] == sorted(manifest["public_ids"])

    public_paths = sorted((out / "public").glob("*.json"))
    private_paths = sorted((out / "private" / "episodes").glob("*.json"))
    assert len(public_paths) == len(private_paths) == 2
    forbidden = (
        "extension_length",
        "query_answers",
        "program_sha256",
        '"seed"',
        "second_exterior_only",
        "paint_to_grid_edge",
    )
    for path in public_paths:
        raw = path.read_bytes()
        public = json.loads(raw)
        assert raw == public_challenge_bytes(public)
        assert path.stem == public_challenge_id(public)
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert not any(token in raw.decode("utf-8") for token in forbidden)

    for length in (1, 2):
        rule = out / "private" / "rules" / f"extension-length-{length}.rkt"
        assert rule.read_text(encoding="utf-8") == p.materialize_rule(length, root=ROOT)

    with pytest.raises(FileExistsError):
        p.write_evidence(out, seeds=[0, 1], root=ROOT)

    public, private = p.generate_episode(0, root=ROOT)
    duplicate_out = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate visible"):
        p.write_batch([(public, private), (copy.deepcopy(public), copy.deepcopy(private))], duplicate_out, root=ROOT)
    assert not duplicate_out.exists()


def _load_adjacent(path: Path, name: str):
    assert path.is_file(), f"missing component file: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_promotion_adapter_contract_is_thin_strict_and_setting_neutral() -> None:
    """Catches module aliasing, loose settings, and setting-dependent inputs."""
    p = prototype()
    adapter = _load_adjacent(ADAPTER_PATH, "b8e2a07c1b6c_extension_adapter_test")
    contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/b8e2a07c1b6c/workspace/parametric/adapter.py",
        "parameters": {"extension_length": [1, 2]},
        "default": {"extension_length": 1},
        "limits": {"demos": [2, 8], "queries": [1, 8]},
        "resources": [
            "generators/b8e2a07c1b6c/workspace/parametric/prototype.py"
        ],
    }
    assert adapter.program({"extension_length": 1}) == p.materialize_rule(1, root=ROOT)
    assert adapter.program({"extension_length": 2}) == p.materialize_rule(2, root=ROOT)
    for invalid in (
        {},
        {"extension_length": True},
        {"extension_length": 3},
        {"extension_length": 1, "extra": 0},
        [("extension_length", 1)],
    ):
        with pytest.raises(ValueError, match="extension_length|settings"):
            adapter.program(invalid)

    one = adapter.generate(29, {"extension_length": 1}, 2, 4)
    two = adapter.generate(29, {"extension_length": 2}, 2, 4)
    assert set(one) == set(two) == {"train", "test", "program_solution"}
    assert len(one["train"]) == len(two["train"]) == 2
    assert len(one["test"]) == len(two["test"]) == 4
    assert [pair["input"] for pair in one["train"] + one["test"]] == [
        pair["input"] for pair in two["train"] + two["test"]
    ]
    assert all(set(pair) == {"input", "output"} for pair in one["train"] + one["test"])
    assert all(set(pair) == {"input", "output"} for pair in two["train"] + two["test"])
    assert one["program_solution"] == adapter.program({"extension_length": 1})
    assert two["program_solution"] == adapter.program({"extension_length": 2})
    assert any(a["output"] != b["output"] for a, b in zip(one["train"], two["train"]))

    assert p.execute_rule_many(
        one["program_solution"],
        [pair["input"] for pair in one["train"] + one["test"]],
        root=ROOT,
    ) == [pair["output"] for pair in one["train"] + one["test"]]
    assert p.execute_rule_many(
        two["program_solution"],
        [pair["input"] for pair in two["train"] + two["test"]],
        root=ROOT,
    ) == [pair["output"] for pair in two["train"] + two["test"]]
