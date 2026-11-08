"""Focused tests for the proposed base-edge prototype, not canonical approval."""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "cde6cd1740f9"
ROOT = find_root(__file__)


@lru_cache(maxsize=1)
def prototype():
    # Task-test runtimes retain a repository mirror as well as execution paths.
    path = ROOT / "generators" / TASK_ID / "workspace/parametric/prototype.py"
    assert path.is_file(), "the task-local parametric prototype is not implemented"
    spec = importlib.util.spec_from_file_location("cde6cd1740f9_parametric", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as live:
        yield live


def test_default_rule_is_exact_canonical_program():
    variant = prototype()
    assert variant.BASE_EDGES == ("bottom", "top")
    assert variant.DEFAULT_BASE_EDGE == "bottom"
    canonical = variant.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == variant.CANONICAL_SHA256
    assert variant.materialize_rule(root=ROOT) == canonical
    assert variant.materialize_rule("bottom", root=ROOT) == canonical
    top = variant.materialize_rule("top", root=ROOT)
    assert top != canonical
    assert top.replace("(row i)", "(row (- (- h 1) i))", 1) == canonical


def test_rule_materialization_rejects_out_of_domain_and_changed_authority():
    variant = prototype()
    for value in (None, False, 1, "left", "TOP", "", ["top"]):
        with pytest.raises(ValueError, match="base_edge"):
            variant.materialize_rule(value, root=ROOT)
    with pytest.raises(ValueError, match="canonical"):
        variant.materialize_rule(source=variant.canonical_source(root=ROOT) + "\n")


def test_default_racket_replays_all_labelled_canonical_pairs(bridge):
    variant = prototype()
    source = variant.materialize_rule(root=ROOT)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        before = [row[:] for row in pair["input"]]
        assert variant.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]
        assert pair["input"] == before


def lawful_two_column_input(layer_colors):
    grid = [[0] * 11 for _ in range(16)]
    # Bottom-to-top source counts partition complete widths 5, 3, 1.
    bottom_to_top = [color for color, width in zip(layer_colors, (5, 3, 1)) for _ in range(width)]
    for row, color in zip((0, 1, 3, 4, 6, 7, 9, 10, 12), reversed(bottom_to_top)):
        grid[row][2] = color
    for row in (1, 4, 8, 11):
        grid[row][6] = 4
    return grid


@pytest.mark.parametrize("layer_colors", [(2, 2, 7), (2, 7, 7), (2, 7, 8)])
def test_both_racket_settings_preserve_exact_layers_counts_and_source_columns(bridge, layer_colors):
    variant = prototype()
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    grid = lawful_two_column_input(layer_colors)
    assert generator.self_check(grid) == []
    outputs = {}
    for edge in variant.BASE_EDGES:
        actual = variant.execute_rule(variant.materialize_rule(edge, root=ROOT), grid, bridge=bridge)
        expected = [[0] * 11 for _ in range(16)]
        for center, colors, widths in ((2, layer_colors, (5, 3, 1)), (6, (4, 4), (3, 1))):
            for depth, (color, width) in enumerate(zip(colors, widths)):
                row = 15 - depth if edge == "bottom" else depth
                for col in range(center - width // 2, center + width // 2 + 1):
                    expected[row][col] = color
        assert actual == expected
        assert Counter(value for row in actual for value in row if value) == Counter(
            value for row in grid for value in row if value
        )
        outputs[edge] = actual
    assert outputs["top"] == list(reversed(outputs["bottom"]))
    assert outputs["top"] != outputs["bottom"]


def test_seed_selects_one_episode_parameter_without_global_rng_mutation():
    variant = prototype()
    random.seed(923)
    state = random.getstate()
    assert {variant.choose_base_edge(seed) for seed in (0, 1)} == set(variant.BASE_EDGES)
    assert variant.choose_base_edge(177) == variant.choose_base_edge(177)
    assert random.getstate() == state
    for value in (True, -1, 2**63, 0.5, "1"):
        with pytest.raises(ValueError, match="seed"):
            variant.choose_base_edge(value)


def test_complete_episodes_use_one_rule_and_demonstrations_eliminate_parameter_rival(bridge):
    variant = prototype()
    generator, _, digest = load_selected_generator(TASK_ID, root=ROOT)
    observed = set()
    for seed in (0, 1):
        episode = variant.generate_episode(seed, root=ROOT, bridge=bridge)
        challenge, private = episode["challenge"], episode["private"]
        edge = private["parameters"]["base_edge"]
        observed.add(edge)
        assert edge == variant.choose_base_edge(seed)
        assert set(challenge) == {"train", "test"}
        assert len(challenge["train"]) == generator.EXAMPLES_NEEDED
        assert len(challenge["test"]) == 1
        assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
        assert all(set(pair) == {"input"} for pair in challenge["test"])
        assert private["bindings"]["generator_sha256"] == digest
        assert private["reference_rule"]["racket"] == variant.materialize_rule(edge, root=ROOT)
        assert private["identifiable_against_parameter_rivals"] is True
        for position, pair in enumerate(challenge["train"]):
            assert generator.self_check(pair["input"]) == []
            assert pair["output"] == variant.execute_rule(
                private["reference_rule"]["racket"], pair["input"], bridge=bridge
            )
        for edge_name, rival in private["parameter_rivals"].items():
            if edge_name == edge:
                assert rival["status"] == "selected"
                assert rival["demo_disagreements"] == []
            else:
                assert rival["status"] == "eliminated_by_demonstrations"
                assert rival["demo_disagreements"] == list(range(generator.EXAMPLES_NEEDED))
                assert rival["query_disagreements"] == [0]
        assert private["query_answers"][0]["output"] == variant.execute_rule(
            private["reference_rule"]["racket"], challenge["test"][0]["input"], bridge=bridge
        )
        assert variant.generate_episode(seed, root=ROOT, bridge=bridge) == episode
    assert observed == set(variant.BASE_EDGES)


def test_episode_sampling_arguments_are_validated(bridge):
    variant = prototype()
    for arguments in ({"start": -1}, {"start": True}, {"difficulty": "unknown"}):
        with pytest.raises(ValueError):
            variant.generate_episode(0, root=ROOT, bridge=bridge, **arguments)


def test_reusable_cli_retains_exact_rules_queries_and_source_bound_private_evidence(tmp_path):
    variant = prototype()
    out = tmp_path / "episodes"
    completed = subprocess.run(
        [sys.executable, str(Path(variant.__file__)), "--seeds", "0", "1", "--out", str(out)],
        capture_output=True, text=True, timeout=120,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads((out / "private/report.json").read_text())
    assert report["status"] == "bounded_checks_passed"
    assert report["settings_observed"] == ["bottom", "top"]
    assert report["canonical_replay"]["failed"] == 0
    assert report["canonical_replay"]["pairs"] > 0
    assert report["distinguishing_witness"]["outputs_differ"] is True
    assert report["commands"]["payload_argv"][1:] == completed.args[1:]
    for index in range(2):
        public_path = out / "public" / f"episode-{index:03d}.json"
        private_path = out / "private" / f"episode-{index:03d}.json"
        public = json.loads(public_path.read_text())
        private = json.loads(private_path.read_text())
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert private["public_file_sha256"] == hashlib.sha256(public_path.read_bytes()).hexdigest()
        assert private["parameters"]["base_edge"] in variant.BASE_EDGES
    for edge in variant.BASE_EDGES:
        rule_path = out / "private/rules" / f"base-{edge}.rkt"
        assert rule_path.read_text() == variant.materialize_rule(edge, root=ROOT)
    manifest = report["source_files"]
    for relative, digest in manifest.items():
        copied = out / "private/source_snapshot" / relative
        assert hashlib.sha256(copied.read_bytes()).hexdigest() == digest
    assert set(manifest) >= {"prototype.py", "generator.py", "test_parametric_cde6cd1740f9.py"}
