"""Focused regression checks for generator 91b531b5d3f4."""
from __future__ import annotations

import copy
import importlib
import random

gen = importlib.import_module("puzzle_generators.per_puzzle.91b531b5d3f4.generator")


def _rule_mirror(grid):
    out = [list(row) for row in grid]
    for r in range(1, len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 1 and grid[0][c] != 0:
                out[r][c] = grid[0][c]
    return out


def _must_reject(grid, label):
    errors = gen.self_check(grid)
    assert errors, f"self_check accepted targeted impostor: {label}"


def main():
    # The default-only canonical prior reaches every complete official linked
    # profile in every band without interfering with explicit overrides.
    prior_examples = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        signatures = []
        for offset in range(300):
            grid = gen.generate(
                50_000 + band_index * 1_000 + offset,
                offset * 19 + 5,
                difficulty=band,
            )
            signature = gen._canonical_profile_signature(grid)
            if signature is not None:
                signatures.append(signature)
                prior_examples.setdefault(signature, grid)
        assert set(signatures) == set(gen._CANONICAL_PROFILES), (band, signatures)
        assert 60 <= len(signatures) <= 120, (band, len(signatures))

    # A plausible marginal recombination remains generally lawful but is not
    # mislabeled as one of the linked official profiles.
    linked = copy.deepcopy(prior_examples[(7, 8, (1, 4), (2, 2))])
    linked[0][2] = linked[0][1]
    linked[0][1] = 0
    for row in range(1, len(linked)):
        linked[row][2] = linked[row][1]
        linked[row][1] = 0
    assert not gen.self_check(linked)
    assert gen._canonical_profile_signature(linked) is None

    # Exact override boundaries and profile observability.
    for texture in gen.HELPFUL_TEXTURES:
        for h, w, headers in ((5, 6, 1), (12, 13, 3)):
            grid = gen.generate(
                101,
                h * 100 + w,
                difficulty="hard",
                grid_h=h,
                grid_w=w,
                header_cols=headers,
                texture=texture,
            )
            assert not gen.self_check(grid)
            assert gen.observe_overrides(grid) == {
                "header_cols": headers,
                "texture": texture,
            }
            assert _rule_mirror(grid) != grid

    # Deterministic replay, fresh returns, and process-global RNG purity.
    state = random.getstate()
    first = gen.generate(23, 7, difficulty="medium")
    second = gen.generate(23, 7, difficulty="medium")
    assert first == second and first is not second
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(23, 7, difficulty="medium") == second
    assert random.getstate() == state

    base = gen.generate(
        17,
        3,
        difficulty="medium",
        texture="canonical",
        header_cols=3,
    )
    analysis = gen._analysis(base)
    header_columns = list(analysis["header_columns"])

    # Four mutation-sensitive structural impostors.
    no_witness = copy.deepcopy(base)
    victim = header_columns[0]
    for r in range(1, len(no_witness)):
        if no_witness[r][victim] == 1:
            no_witness[r][victim] = 0
    _must_reject(no_witness, "one header has no marker witness")

    duplicate_header = copy.deepcopy(base)
    duplicate_header[0][header_columns[1]] = duplicate_header[0][header_columns[0]]
    _must_reject(duplicate_header, "duplicate header colors")

    marker_in_header = copy.deepcopy(base)
    marker_in_header[0][header_columns[0]] = 1
    _must_reject(marker_in_header, "marker color in row 0")

    full_one_color = [[2] * 6 for _ in range(5)]
    _must_reject(full_one_color, "full one-color grid")

    # A distractor that reuses a header color violates the profile grammar.
    distractors = gen.generate(41, 9, texture="distractors", header_cols=2)
    bad_distractor = copy.deepcopy(distractors)
    dcolor = next(
        value
        for row in bad_distractor[1:]
        for value in row
        if value not in (0, 1)
    )
    for r in range(1, len(bad_distractor)):
        for c in range(len(bad_distractor[0])):
            if bad_distractor[r][c] == dcolor:
                bad_distractor[r][c] = bad_distractor[0][
                    next(i for i, value in enumerate(bad_distractor[0]) if value != 0)
                ]
    _must_reject(bad_distractor, "distractor reuses a header color")

    print("focused generator contract: PASS")


def test_generator_contract():
    main()


if __name__ == "__main__":
    main()
