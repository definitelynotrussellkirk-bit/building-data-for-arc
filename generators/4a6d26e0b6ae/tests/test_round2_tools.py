"""Regression contracts for the reusable round-two tools."""
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]


def load(name):
    path = HOME / "workspace" / name
    assert path.is_file(), f"missing reusable tool: {name}"
    spec = importlib.util.spec_from_file_location("round2_" + path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_request_matrix_contains_all_sizes_and_separates_unsupported_counts():
    m = load("verify_boundary_contract.py")
    rows = list(m.requests(1))
    assert len(rows) == 4900  # 6 nonblank textures x 100 shapes x 8 counts + 100 blanks
    keys = {(r["seed"], r["overrides"]["grid_h"], r["overrides"]["grid_w"],
             r["overrides"]["texture"], r["overrides"].get("gap_count")) for r in rows}
    assert len(keys) == len(rows)
    small = [r for r in rows if r["overrides"] == {"grid_h": 5, "grid_w": 5, "texture": "horizontal", "gap_count": 8}]
    assert len(small) == 1 and not small[0]["expected_accept"]
    assert all(r["expected_accept"] for r in rows if r["overrides"]["texture"] == "no_gaps")


@pytest.mark.parametrize("h,w,texture,expected", [(5, 5, "default", 3), (5, 14, "horizontal", 8),
    (5, 14, "vertical", 7), (14, 5, "vertical", 8), (14, 14, "mismatched_endpoints", 4)])
def test_request_capacity_is_derived_without_generator_internals(h, w, texture, expected):
    assert load("verify_boundary_contract.py").capacity(h, w, texture) == expected


def test_geometric_transforms_preserve_integer_colors_and_produce_eight_operations():
    m = load("verify_boundary_contract.py")
    grid = [[1, 0, 2], [3, 4, 5]]
    variants = list(m.symmetries(grid))
    assert len(variants) == 8
    assert len({repr(g) for g in variants}) == 8
    assert all(sorted(c for row in g for c in row) == list(range(6)) for g in variants)
    assert grid == [[1, 0, 2], [3, 4, 5]]


def test_fixture_patch_changes_only_the_named_test_and_fails_on_duplicate_application():
    m = load("verify_repository_fixture.py")
    root = HOME.parents[1]
    before = (root / "tests/test_review_solve.py").read_text()
    after = m.proposed_fixture_text(before)
    prefix = before.split("def test_duties_solve_preparation_runs_from_packet_root", 1)[0]
    assert after.startswith(prefix)
    assert 'library / "src/arcpuzzles"' in after
    assert after.count("copytree(") == before.count("copytree(") + 1
    assert "run_process(args, root, timeout=30)" in after
    with pytest.raises(ValueError):
        m.proposed_fixture_text(after)


def test_fixture_patch_refuses_unrecognized_source():
    with pytest.raises(ValueError):
        load("verify_repository_fixture.py").proposed_fixture_text("def something_else(): pass\n")
