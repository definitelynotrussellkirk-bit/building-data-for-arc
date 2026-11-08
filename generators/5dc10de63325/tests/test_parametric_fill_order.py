"""Contracts for the isolated fill-order parametric rule prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import find_root


TASK_ID = "5dc10de63325"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def prototype():
    assert PROTOTYPE_PATH.is_file(), "fill-order prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("cyan_fill_order_prototype", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def witness_grid(count: int) -> list[list[int]]:
    return [[8 if r * 6 + c < count else 0 for c in range(6)] for r in range(6)]


def test_parameter_is_bounded_and_chosen_deterministically_once_per_episode():
    module = prototype()
    assert module.PARAMETER_NAME == "fill_order"
    assert module.DEFAULT_FILL_ORDER in module.ALLOWED_FILL_ORDERS
    assert len(module.ALLOWED_FILL_ORDERS) == 3
    for seed in range(20):
        first = module.choose_parameters(seed)
        second = module.choose_parameters(seed)
        assert first == second
        assert set(first) == {module.PARAMETER_NAME}
        assert first[module.PARAMETER_NAME] in module.ALLOWED_FILL_ORDERS
    assert {module.choose_parameters(seed)[module.PARAMETER_NAME] for seed in range(200)} == set(module.ALLOWED_FILL_ORDERS)


def test_default_rule_is_exact_canonical_and_every_variant_restores_to_it():
    module = prototype()
    canonical = module.canonical_source(root=ROOT)
    assert module.materialize_rule(module.DEFAULT_FILL_ORDER, source=canonical) == canonical
    variants = {setting: module.materialize_rule(setting, source=canonical) for setting in module.ALLOWED_FILL_ORDERS}
    assert len(set(variants.values())) == len(module.ALLOWED_FILL_ORDERS)
    for source in variants.values():
        assert module.restore_canonical(source) == canonical


def test_q2_witness_distinguishes_all_fill_orders_and_default_glyph_is_preserved():
    module = prototype()
    grid = witness_grid(9)
    outputs = {
        setting: module.python_reference(grid, fill_order=setting)
        for setting in module.ALLOWED_FILL_ORDERS
    }
    assert len({module.digest(output) for output in outputs.values()}) == 3
    assert outputs[module.DEFAULT_FILL_ORDER] == [
        [0, 0, 0, 0, 0],
        [8, 8, 0, 8, 8],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [8, 8, 0, 8, 8],
    ]


def test_declared_demo_counts_distinguish_each_setting_from_every_rival():
    module = prototype()
    grids = [witness_grid(count) for count in module.DEMO_COUNTS]
    for selected in module.ALLOWED_FILL_ORDERS:
        selected_outputs = [module.python_reference(grid, fill_order=selected) for grid in grids]
        for rival in module.ALLOWED_FILL_ORDERS:
            if rival == selected:
                continue
            rival_outputs = [module.python_reference(grid, fill_order=rival) for grid in grids]
            assert any(actual != alternative for actual, alternative in zip(selected_outputs, rival_outputs))


def test_public_challenge_redacts_hidden_rule_seed_and_query_answer():
    module = prototype()
    episode = {
        "train": [{"input": [[0]], "output": [[1]]}],
        "test": [{"input": [[2]], "output": [[3]]}],
    }
    public = module.public_challenge(episode)
    assert public == {
        "train": episode["train"],
        "test": [{"input": [[2]]}],
    }
    serialized = repr(public).lower()
    assert "fill_order" not in serialized
    assert "racket" not in serialized
    assert "seed" not in serialized
