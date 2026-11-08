from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


TASK_ID = "7c2a3ec6c4fb"
ROOT = Path(__file__).resolve().parents[3]
TOOL_PATH = ROOT / "generators" / TASK_ID / "workspace" / "shortcut_census.py"
SPEC = importlib.util.spec_from_file_location(f"shortcut_census_{TASK_ID}", TOOL_PATH)
assert SPEC and SPEC.loader
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)


def test_census_discovers_shortcuts_and_morphology_guardrails():
    report = TOOL.run_census(
        samples=360,
        seed="focused-census",
        layout_samples=180,
    )

    assert report["strict_failure_count"] == 0
    assert report["canonical_pair_count"] == 4
    assert report["canonical_perfect_undeclared"] == []
    assert {
        "unique_color_signature",
        "unique_color_histogram",
        "unique_geometry_and_colors",
        "unique_bbox_and_histogram",
    } <= set(report["declared_canonical_shortcuts"])

    assert set(report["answer_color_counts"]) == {"1", "2"}
    assert any(
        max(map(int, dimensions.split("x"))) >= 4
        for dimensions in report["answer_dimensions"]
    )
    assert report["layout_escape"]["eligible"] >= 100
    assert report["layout_escape"]["escaped"] > 0
    assert TOOL.evaluate_guardrails(report) == []


def test_census_reports_every_observable_control_value():
    report = TOOL.run_census(
        samples=360,
        seed="control-coverage",
        layout_samples=120,
    )

    assert set(report["scene_profiles"]) == {
        "square11_c3",
        "square12_c4",
        "square13_c3",
        "square13_c4",
    }
    assert set(report["n_pairs_counts"]) == {"2", "3", "4"}
    assert set(report["pattern_profiles"]) == {
        "color_swap",
        "shape_shift",
        "mixed_signature",
    }


def test_guardrails_reject_token_semantic_witness_support():
    report = TOOL.run_census(
        samples=360,
        seed="weak-witness-guard",
        layout_samples=120,
    )
    weakened = copy.deepcopy(report)
    witness_name = sorted(weakened["witness_hits"])[0]
    weakened["witness_hits"][witness_name] = 1

    failures = TOOL.evaluate_guardrails(weakened)

    assert any(
        witness_name in failure and "support" in failure
        for failure in failures
    ), failures


def test_census_counts_failures_not_just_retained_examples(monkeypatch):
    generator = TOOL._load_generator()
    original_generate = generator.generate
    original_observe = generator.semantic_observables

    def generate(seed, index, **kwargs):
        return [[0]] if str(seed).endswith(':main') else original_generate(seed, index, **kwargs)

    def observe(grid):
        if grid == [[0]]:
            return {'errors': ['deliberate invalid-grid fixture']}
        return original_observe(grid)

    monkeypatch.setattr(generator, 'generate', generate)
    monkeypatch.setattr(generator, 'semantic_observables', observe)
    monkeypatch.setattr(TOOL, '_load_generator', lambda: generator)
    report = TOOL.run_census(samples=35, layout_samples=2, seed='failure-count')
    assert report['strict_failure_count'] == 35
    assert len(report['strict_failures']) == 20  # bounded preview, not a count
    assert report['valid_samples'] == 0


def test_census_includes_segmentation_rivals_and_source_identity():
    import hashlib
    report = TOOL.run_census(samples=60, layout_samples=30, seed='source-identity')
    assert report['generator_sha256'] == hashlib.sha256(TOOL.GENERATOR_PATH.read_bytes()).hexdigest()
    assert report['seed'] == 'source-identity'
    assert report['signature_results']['orthogonal_components']['canonical_hits'] == 4
    assert 'orthogonal_components' in report['canonical_perfect_signatures']
