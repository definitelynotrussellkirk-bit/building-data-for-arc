"""Focused tests for the proposed relation-matrix ordering family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "df5e596e5e96"
ROOT = find_root(__file__)
HOME = ROOT / f"generators/{TASK_ID}/workspace/parametric"
PROTOTYPE_PATH = HOME / "prototype.py"
ADAPTER_PATH = HOME / "adapter.py"
PROMOTION_PATH = HOME / "promotion.json"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing requested artifact: {path}"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def prototype():
    return _load(PROTOTYPE_PATH, "_test_df5e596e5e96_matrix_order")


def adapter():
    return _load(ADAPTER_PATH, "_test_df5e596e5e96_matrix_adapter")


def frozen_grid(grid):
    return tuple(tuple(row) for row in grid)


def episode_inputs(episode):
    return [frozen_grid(pair["input"]) for pair in episode["train"] + episode["test"]]


def canonical_source() -> str:
    sources = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line.strip()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(sources) == 1
    return sources.pop()


def test_default_is_exact_canonical_and_alternate_composes_from_canonical_matrix():
    module = prototype()
    canonical = canonical_source()
    assert module.CANONICAL_SOURCE_SHA256 == hashlib.sha256(canonical.encode()).hexdigest()
    assert module.program(module.DEFAULT_SETTINGS, root=ROOT) == canonical

    alternate_settings = {"matrix_order": "relation_signature"}
    alternate_program = module.program(alternate_settings, root=ROOT)
    assert alternate_program != canonical

    generator, _source, _digest = load_selected_generator(TASK_ID, root=ROOT)
    grid = generator.generate(0, 0, difficulty="hard", n_panels=5)
    canonical_matrix = module.transform(grid, module.DEFAULT_SETTINGS, root=ROOT)
    order = module.relation_signature_order(canonical_matrix)
    alternate_matrix = module.transform(grid, alternate_settings, root=ROOT)
    assert order == [1, 4, 3, 0, 2]
    assert alternate_matrix == [
        [canonical_matrix[order[row]][order[col]] for col in range(len(order))]
        for row in range(len(order))
    ]
    assert alternate_matrix != canonical_matrix

    with RacketBridge(max_calls_before_restart=32) as bridge:
        assert module.execute_rule(canonical, grid, bridge=bridge) == canonical_matrix
        assert module.execute_rule(alternate_program, grid, bridge=bridge) == alternate_matrix


def test_promotion_contract_and_thin_adapter_match_prototype():
    module = prototype()
    promoted = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
    assert promoted == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"matrix_order": list(module.MATRIX_ORDERS)},
        "default": module.DEFAULT_SETTINGS,
        "limits": {"demos": [2, 6], "queries": [1, 8]},
        "resources": [f"generators/{TASK_ID}/workspace/parametric/prototype.py"],
    }
    promoted_adapter = adapter()
    for settings in module.ALL_SETTINGS:
        assert promoted_adapter.program(settings) == module.program(settings, root=ROOT)


def test_same_seed_has_matched_unique_maximum_lawful_inputs_and_identifying_demos():
    module = prototype()
    promoted_adapter = adapter()
    episodes = [
        promoted_adapter.generate(17, settings, demos=3, queries=4)
        for settings in module.ALL_SETTINGS
    ]
    inputs = [episode_inputs(episode) for episode in episodes]
    assert all(value == inputs[0] for value in inputs)
    assert len(inputs[0]) == len(set(inputs[0])) == 7

    for settings, episode in zip(module.ALL_SETTINGS, episodes, strict=True):
        assert episode["task_id"] == TASK_ID
        assert episode["settings"] == settings
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == module.program(settings, root=ROOT)
        assert module.fit_settings(episode["train"], root=ROOT) == [settings]
        audit = module.audit_episode(episode, root=ROOT)
        assert audit["ambiguous_rivals"] == []
        assert all(not row["fits_all_demos"] for row in audit["rivals"].values())
        for pair in episode["train"] + episode["test"]:
            assert len(pair["input"]) == 5 and len(pair["input"][0]) == 29
            assert len(pair["output"]) == len(pair["output"][0]) == 5
            assert pair["output"] == module.transform(pair["input"], settings, root=ROOT)

    for pair_index in range(7):
        split = "train" if pair_index < 3 else "test"
        index = pair_index if split == "train" else pair_index - 3
        assert len({frozen_grid(episode[split][index]["output"]) for episode in episodes}) == 2


def test_demo_and_query_counts_are_independent_prefixes_from_two_through_six():
    module = prototype()
    promoted_adapter = adapter()
    full = promoted_adapter.generate(29, module.DEFAULT_SETTINGS, demos=6, queries=8)
    small = promoted_adapter.generate(29, module.DEFAULT_SETTINGS, demos=2, queries=1)
    medium = promoted_adapter.generate(29, module.DEFAULT_SETTINGS, demos=5, queries=4)
    assert [frozen_grid(pair["input"]) for pair in small["train"]] == [
        frozen_grid(pair["input"]) for pair in full["train"][:2]
    ]
    assert [frozen_grid(pair["input"]) for pair in small["test"]] == [
        frozen_grid(full["test"][0]["input"])
    ]
    assert [frozen_grid(pair["input"]) for pair in medium["train"]] == [
        frozen_grid(pair["input"]) for pair in full["train"][:5]
    ]
    assert [frozen_grid(pair["input"]) for pair in medium["test"]] == [
        frozen_grid(pair["input"]) for pair in full["test"][:4]
    ]
    assert module.fit_settings(small["train"], root=ROOT) == [module.DEFAULT_SETTINGS]


def test_every_setting_episode_label_and_self_audit_execute_in_racket():
    module = prototype()
    promoted_adapter = adapter()
    with RacketBridge(max_calls_before_restart=256) as bridge:
        for settings in module.ALL_SETTINGS:
            episode = promoted_adapter.generate(31, settings, demos=2, queries=4)
            report = module.verify_episode(episode, root=ROOT, bridge=bridge)
            assert report["settings"] == settings
            assert report["label_count"] == 6
            assert report["surviving_settings"] == [settings]
            assert all(row["matches_python"] for row in report["program_checks"])
            assert report["audit"]["ambiguous_rivals"] == []


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, {"matrix_order": "input"}, 2, 1),
        (-1, {"matrix_order": "input"}, 2, 1),
        (2**63, {"matrix_order": "input"}, 2, 1),
        (0, {"matrix_order": "input"}, 1, 1),
        (0, {"matrix_order": "input"}, 7, 1),
        (0, {"matrix_order": "input"}, 2, 0),
        (0, {"matrix_order": "input"}, 2, 9),
        (0, {"matrix_order": "sideways"}, 2, 1),
        (0, {}, 2, 1),
        (0, {"matrix_order": "input", "extra": True}, 2, 1),
    ],
)
def test_adapter_rejects_invalid_requests(seed, settings, demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(seed, settings, demos, queries)
