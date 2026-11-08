"""Independent bounded verification of the v2.1 review fixes.

Run from WORK/repo: python3 ../checks/code-review/final_controls.py
Writes only a fresh final_controls.json; retains earlier review evidence.
"""
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

from additional_rivals import components, rival

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / "repo"
SOURCE = REPO / "generators/899e2a4cfac9/generator.py"
EXPECTED = "0fe1fd03f31b285873c464d28ad3e0356299f3f6709fb75c1af57c5dd68a7ce5"
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("final_review_generator", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
BANDS = (None, "easy", "medium", "hard")


def inspect(grid, *, n, colors=None, h=None, w=None):
    groups = components(grid)
    actual_h, actual_w = len(grid), len(grid[0])
    assert h is None or actual_h == h
    assert w is None or actual_w == w
    actual_colors = len({v for row in grid for v in row})
    assert colors is None or actual_colors == colors
    assert len(groups) == n, (len(groups), n)
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    inside = [g for g in groups if not any(r in (0, actual_h-1) or c in (0, actual_w-1) for r, c in g)]
    sizes = sorted(map(len, inside))
    expected = [[0] * actual_w for _ in grid]
    for group in inside:
        for r, c in group:
            expected[r][c] = grid[r][c]
    if n == 3:
        assert len(inside) == 1 and sizes[0] in (3, 4), sizes
        assert sorted(len(g) for g in groups if g not in inside) == [2, 2]
    elif n == 7:
        assert len(inside) == 3 and sizes[0] == 1 and sizes[1] >= 2, sizes
        for name in ("discard_internal_singletons", "keep_largest_internal_components"):
            assert rival(grid, name) != expected
        for name, predictor in gen.SEMANTIC_RIVALS.items():
            assert predictor(grid) != expected, name
    return tuple(sizes), actual_colors


def main():
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert before == EXPECTED
    counts, profiles, failures = Counter(), Counter(), []
    cases = itertools.chain(
        itertools.product(range(6, 13), range(7, 15), ((3, 3), (3, 4)), BANDS, range(4)),
        itertools.product((6,), (7,), ((3, 3), (3, 4)), BANDS, range(4, 128)),
        itertools.product(range(6, 13), range(7, 15), ((7, 3), (7, 4), (7, 5), (7, 6)), BANDS, range(4)),
        itertools.product((6,), (7,), ((7, 3), (7, 4), (7, 5), (7, 6)), BANDS, range(4, 128)),
    )
    for h, w, (n, colors), band, index in cases:
        request = dict(grid_h=h, grid_w=w, n_blobs=n, n_distinct_colors=colors)
        try:
            grid = gen.generate("final-construction-review", index, difficulty=band, **request)
            sizes, _ = inspect(grid, n=n, colors=colors, h=h, w=w)
            profiles[str(sizes)] += 1
            counts[f"exact_{n}_object_draws"] += 1
        except Exception as exc:
            failures.append(dict(kind="joint_controls", request=request, band=band, index=index, error=repr(exc)))
            break
    for colors, band, index in itertools.product((5, 6), BANDS, range(0, 64, 2)):
        try:
            grid = gen.generate("standalone-color-review", index, difficulty=band, n_distinct_colors=colors)
            inspect(grid, n=7, colors=colors)
            counts["standalone_5_or_6_colors_at_even_indices"] += 1
        except Exception as exc:
            failures.append(dict(kind="standalone_palette", colors=colors, band=band, index=index, error=repr(exc)))
            break
    canonical_hits = Counter()
    for band in BANDS:
        for index in range(64):
            grid = gen.generate("final-default-review", index, difficulty=band)
            n = 3 if index % 2 == 0 else 7
            sizes, colors = inspect(grid, n=n, colors=4 if n == 3 else None)
            if (len(grid), len(grid[0]), colors) in ((7, 8, 4), (8, 9, 4), (9, 10, 4)):
                canonical_hits[str(band)] += 1
            counts["default_draws"] += 1
    rejected = []
    for bad in (None, True, False, 1.0, "1", -1, [], {}):
        try:
            gen.generate("index-review", bad)
        except (TypeError, ValueError):
            rejected.append(repr(bad))
        else:
            failures.append(dict(kind="invalid_sample_index", value=repr(bad)))
    prior = json.loads((HERE / "additional-rivals.json").read_text())
    for name, finding in prior["rivals"].items():
        for witness in finding["witnesses"]:
            pairs = [gen.generate(witness["seed"], witness["sample_index"] + offset,
                                  difficulty=witness["band"]) for offset in range(4)]
            rich = [grid for grid in pairs if len(components(grid)) == 7]
            assert len(rich) == 2
            for query_position in range(4):
                demos = [grid for i, grid in enumerate(pairs) if i != query_position]
                # Every rotated demonstration set retains a rich witness that
                # independently rejects the previously ambiguous hypothesis.
                assert any(len(components(grid)) == 7 and
                           rival(grid, name) != gen._connectivity_rival(grid)
                           for grid in demos)
                counts["prior_counterexample_seed_rotations_now_refuted"] += 1
    result = dict(source_sha256=before, post_source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  counts=dict(counts), interior_size_profiles=dict(profiles),
                  canonical_profile_hits_per_64_draws=dict(canonical_hits),
                  invalid_sample_indices_rejected=rejected, failures=failures,
                  review_conclusion="No important remaining issue found in the changed branches." if not failures else "Failures found.",
                  limits=["Finite source-bound controls and rival checks, not universal identifiability.",
                          "Production census and full battery are run separately by the parent reviewer."])
    (HERE / "final_controls.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    assert not failures
    assert result["post_source_sha256"] == before


if __name__ == "__main__":
    main()
