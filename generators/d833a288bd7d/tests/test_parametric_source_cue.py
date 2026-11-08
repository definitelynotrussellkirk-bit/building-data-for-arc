from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "d833a288bd7d"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(PROTOTYPE_PATH, "d833a288bd7d_parametric_prototype_test")


def _adapter():
    return _load(ADAPTER_PATH, "d833a288bd7d_parametric_adapter_test")


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return next(iter(programs))



def _racket_apply(bridge: RacketBridge, program: str, grid: list[list[int]]):
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")

def test_program_contract_preserves_exact_canonical_default():
    prototype = _prototype()
    canonical = _canonical_program()

    assert prototype.TASK_ID == TASK_ID
    assert prototype.SOURCE_CUES == ("yellow_marker", "minority_centroid")
    assert prototype.DEFAULT_SOURCE_CUE == "yellow_marker"
    assert prototype.program_for("yellow_marker") == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "4f1476e0a09bb89804dc679485b5b6c8e14562ea16130d6a4f2b9091cd9dea5d"
    )
    alternate = prototype.program_for("minority_centroid")
    assert alternate != canonical
    assert "minority-color" in alternate
    assert "minority-cells" in alternate

    for bad in (None, True, 0, "majority_centroid", {"source_cue": "yellow_marker"}):
        with pytest.raises((TypeError, ValueError)):
            prototype.program_for(bad)


def test_counts_are_independent_prefix_stable_and_large_query_is_substantive():
    prototype = _prototype()

    two = prototype.generate_episode(
        91, source_cue="yellow_marker", demos=2, queries=4
    )
    one = prototype.generate_episode(
        91, source_cue="yellow_marker", demos=3, queries=1
    )
    four = prototype.generate_episode(
        91, source_cue="yellow_marker", demos=3, queries=4
    )
    six = prototype.generate_episode(
        91, source_cue="yellow_marker", demos=6, queries=4
    )
    alternate = prototype.generate_episode(
        91, source_cue="minority_centroid", demos=3, queries=4
    )

    assert two["train"] == four["train"][:2]
    assert two["test"] == four["test"]
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    assert six["train"][:3] == four["train"]
    assert six["test"] == four["test"]
    assert [pair["input"] for pair in alternate["train"] + alternate["test"]] == [
        pair["input"] for pair in four["train"] + four["test"]
    ]

    inputs = [pair["input"] for pair in four["train"] + four["test"]]
    encoded = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
    assert len(encoded) == len(set(encoded))

    for pair in four["train"] + four["test"]:
        facts = prototype.analyze_input(pair["input"])
        assert facts["minority_count"] < facts["majority_count"]
        assert facts["minority_diag"] in range(4)
        assert facts["yellow_source_diag"] in range(4)
        assert facts["target_diag"] in range(4)

    for marker_pair, minority_pair in zip(
        four["train"][:2], alternate["train"][:2], strict=True
    ):
        facts = prototype.analyze_input(marker_pair["input"])
        assert facts["yellow_source_diag"] != facts["minority_diag"]
        assert marker_pair["output"] != minority_pair["output"]

    stress = four["test"][3]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    stress_facts = prototype.analyze_input(stress)
    assert stress_facts["shape_dim"] == 16
    assert stress_facts["shape_size"] == 256
    assert stress_facts["nonzero_count"] == 260

    with pytest.raises(ValueError):
        prototype.generate_episode(True, source_cue="yellow_marker", demos=3, queries=4)
    with pytest.raises(ValueError):
        prototype.generate_episode(0, source_cue="yellow_marker", demos=1, queries=4)
    with pytest.raises(ValueError):
        prototype.generate_episode(0, source_cue="yellow_marker", demos=3, queries=5)


def test_adapter_contract_and_public_projection_keep_private_fields_hidden():
    prototype = _prototype()
    adapter = _adapter()
    promotion = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))

    assert promotion["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert promotion["adapter"] == (
        "generators/d833a288bd7d/workspace/parametric/adapter.py"
    )
    assert promotion["parameters"] == {
        "source_cue": ["yellow_marker", "minority_centroid"]
    }
    assert promotion["default"] == {"source_cue": "yellow_marker"}
    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert promotion["qualification_demos"] == 3
    assert promotion["resources"] == [
        "generators/d833a288bd7d/workspace/parametric/prototype.py",
        "generators/d833a288bd7d/workspace/parametric/canonical.rkt",
    ]

    settings = {"source_cue": "minority_centroid"}
    assert adapter.program(settings) == prototype.program_for("minority_centroid")
    episode = adapter.generate(17, settings, 3, 4)
    assert episode["program_solution"] == adapter.program(settings)
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4

    original_bytes = public_challenge_bytes(episode)
    original_id = public_challenge_id(episode)
    poisoned = copy.deepcopy(episode)
    poisoned["settings"] = {"source_cue": "yellow_marker"}
    poisoned["program_solution"] = "private program changed"
    poisoned["seed"] = 999999
    for pair in poisoned["test"]:
        pair["output"] = [[9]]
    assert public_challenge_bytes(poisoned) == original_bytes
    assert public_challenge_id(poisoned) == original_id
    public = json.loads(original_bytes)
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "source_cue" not in original_bytes.decode()

    for bad in (
        {},
        {"source_cue": "yellow_marker", "extra": 1},
        {"source_cue": "majority_centroid"},
        {"source_cue": True},
    ):
        with pytest.raises(ValueError):
            adapter.program(bad)


def test_protected_racket_matches_python_for_both_settings_and_stress_query():
    prototype = _prototype()
    with RacketBridge(timeout=30, max_calls_before_restart=64) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for setting in prototype.SOURCE_CUES:
            episode = prototype.generate_episode(
                211, source_cue=setting, demos=3, queries=4
            )
            for pair in episode["train"] + episode["test"]:
                assert _racket_apply(
                    bridge, prototype.program_for(setting), pair["input"]
                ) == pair["output"]


def test_two_demonstrations_identify_each_setting_and_refute_named_shortcuts():
    prototype = _prototype()
    for seed in range(32):
        for setting in prototype.SOURCE_CUES:
            episode = prototype.generate_episode(
                seed, source_cue=setting, demos=2, queries=4
            )
            certificate = prototype.teaching_certificate(episode, setting)
            assert certificate["declared_setting_survivors"] == [setting]
            assert certificate["surviving_rivals"] == []
            assert certificate["query_changing_survivors"] == []
            assert certificate["demos_checked"] == 2
            assert certificate["queries_checked"] == 4
            assert episode["teaching_certificate"] == certificate


def test_input_dependent_source_intermediate_controls_the_final_rotation():
    prototype = _prototype()
    grid = prototype.make_input(313, split="query", index=3)
    yellow = prototype.intermediate_source_diag(grid, "yellow_marker")
    minority = prototype.intermediate_source_diag(grid, "minority_centroid")
    facts = prototype.analyze_input(grid)

    assert yellow == facts["yellow_source_diag"] == 3
    assert minority == facts["minority_diag"] == 0
    assert yellow != minority
    assert prototype.apply_python(grid, "yellow_marker") != prototype.apply_python(
        grid, "minority_centroid"
    )
