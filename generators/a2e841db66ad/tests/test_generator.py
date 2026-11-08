from __future__ import annotations

import copy

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "a2e841db66ad"
ROOT = find_root(__file__)
gen, _SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


CANONICAL_PROFILES = {(9, 15, 5), (10, 16, 5), (11, 17, 5)}


def _pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _labeled(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _signature(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_canonical_rule_binding_and_python_mirror() -> None:
    assert gen.RULE_HASH == "b5be85c39dab"
    pairs = _pairs()
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_default_draws_are_lawful_observable_and_profile_anchored() -> None:
    from puzzle_generators import base

    assert set(gen.AXES) == {
        "height", "width", "selected_rows", "n_components", "header_layout"
    }
    for band in ("easy", "medium", "hard"):
        for sample_index in range(12):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = gen.generate(4100 + sample_index, sample_index, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert gen.self_check(grid) == []
            recorded = {
                name: value
                for name, value in captured[-1].recorded_draws().items()
                if name in gen.AXES
            }
            assert recorded == gen.observe_overrides(grid)

        for sample_index in (0, 1):
            assert _signature(gen.generate(999, sample_index, difficulty=band)) in CANONICAL_PROFILES


def test_exact_override_cross_product_round_trips() -> None:
    for band in ("easy", "medium", "hard"):
        for height in (9, 22):
            for width in (15, 22):
                for selected_rows in (2, 6):
                    for n_components in (3, 5):
                        for header_layout in gen.HEADER_LAYOUTS:
                            requested = {
                                "height": height,
                                "width": width,
                                "selected_rows": selected_rows,
                                "n_components": n_components,
                                "header_layout": header_layout,
                            }
                            grid = gen.generate(73, 17, difficulty=band, **requested)
                            assert gen.self_check(grid) == []
                            assert gen.observe_overrides(grid) == requested


def test_invalid_scalar_calls_and_unknown_overrides_fail_loudly() -> None:
    bad_calls = [
        ((True, 0), {}),
        ((1.0, 0), {}),
        (("1", 0), {}),
        ((1, True), {}),
        ((1, 1.0), {}),
        ((1, "1"), {}),
        ((1, -1), {}),
    ]
    for args, overrides in bad_calls:
        with pytest.raises((TypeError, ValueError)):
            gen.generate(*args, difficulty="easy", **overrides)

    for difficulty in (True, False, 0, 1.0, "impossible"):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, 0, difficulty=difficulty)

    for axis, value in (
        ("height", True),
        ("width", 15.0),
        ("selected_rows", "2"),
        ("n_components", False),
        ("header_layout", 1),
    ):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, 0, difficulty="easy", **{axis: value})

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, difficulty="easy", typo_axis=3)


def test_blue_span_shortcut_fits_canonical_and_generated_scattered_headers_refute_it() -> None:
    rival = gen.CANONICAL_SHORTCUTS["blue_span_selects_height"]
    for pair in _pairs():
        assert rival(pair["input"]) == pair["output"]

    for band in ("easy", "medium", "hard"):
        for sample_index in (0, 2, 4, 6):
            grid = gen.generate(800 + sample_index, sample_index, difficulty=band)
            assert gen.SEMANTIC_WITNESSES["scattered_header"](grid)
            assert rival(grid) != gen.rule_mirror(grid)


def test_every_rotation_of_five_consecutive_pairs_is_identifiable() -> None:
    assert gen.EXAMPLES_NEEDED == 4
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            pairs = [_labeled(7000 + start, start + offset, band) for offset in range(5)]
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert len(demos) == gen.EXAMPLES_NEEDED
                assert gen.lesson_identifiable(demos, query) == []


def test_lawful_solid_crop_endpoint_is_explicitly_justified() -> None:
    grid = gen.generate(1002, 2, difficulty="easy")
    output = gen.rule_mirror(grid)
    assert gen.self_check(grid) == []
    assert len(output) * len(output[0]) >= 9
    assert {value for row in output for value in row} == {8}
    text = gen.SOLID_OUTPUT_JUSTIFICATION.strip()
    assert len(text) >= 30
    assert "canonical" in text.lower() or "racket" in text.lower()


def test_shortcut_probe_tracks_live_declarations_and_rotations() -> None:
    import importlib.util

    probe_path = ROOT / "generators" / TASK_ID / "workspace" / "shortcut_probe.py"
    spec = importlib.util.spec_from_file_location("a2e841db66ad_shortcut_probe", probe_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    report = module.build_report(per_band=4, starts=4)
    assert report["generator_sha256"] == _SOURCE_SHA256
    assert report["canonical_shortcuts"]["blue_span_selects_height"] == {
        "checked": 3,
        "matched": 3,
        "errors": [],
    }
    assert report["generated_counterexamples"]["blue_span_selects_height"]
    assert report["rotation_check"]["checked"] == 3 * 4 * 5
    assert report["rotation_check"]["failures"] == []


def test_retained_blue_span_counterexample_replays() -> None:
    import json

    path = ROOT / "generators" / TASK_ID / "counterexamples" / "blue-span-selects-height.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["generator_sha256"] == _SOURCE_SHA256
    assert payload["rule_hash"] == gen.RULE_HASH
    assert gen.self_check(payload["input"]) == []
    assert gen.rule_mirror(payload["input"]) == payload["racket_output"]
    rival = gen.CANONICAL_SHORTCUTS[payload["rival_name"]]
    assert rival(payload["input"]) == payload["rival_output"]
    assert payload["racket_output"] != payload["rival_output"]
