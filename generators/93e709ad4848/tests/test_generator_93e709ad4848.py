"""Independent regression coverage for the nearest-corner translation task."""

from __future__ import annotations

import importlib.util
import itertools
import random
import sys
import unittest
from pathlib import Path


TASK_ID = "93e709ad4848"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from src.core.canonical_pairs import load_task_pairs
from puzzle_generators import base


SPEC = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", TASK_DIR / "generator.py")
assert SPEC is not None and SPEC.loader is not None
generator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = generator
SPEC.loader.exec_module(generator)


def canonical_pairs():
    """Use the public normalizer with the source checkout's explicit data path."""
    return load_task_pairs(TASK_ID, REPO / "shared" / "data" / "canonical" / "puzzles.jsonl")


def components(grid):
    """Count equal-color four-connected objects without generator internals."""
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    answer = []
    while unseen:
        origin = min(unseen)
        color = grid[origin[0]][origin[1]]
        unseen.remove(origin)
        stack = [origin]
        cells = {origin}
        while stack:
            r, c = stack.pop()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in unseen and grid[p[0]][p[1]] == color:
                    unseen.remove(p)
                    cells.add(p)
                    stack.append(p)
        answer.append((color, cells))
    return answer


def digits(*rows):
    return [[int(cell) for cell in row] for row in rows]


def bbox(cells):
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def nearest_corner_expected(grid):
    """Choose among four corners by squared Euclidean distance, then translate.

    This intentionally enumerates distances rather than using per-axis midpoint
    inequalities. Its correctness is anchored by the literal fixtures below and
    all four canonical input/output pairs.
    """
    objects = components(grid)
    if len(objects) != 1:
        raise ValueError("the independent oracle requires exactly one object")
    color, cells = objects[0]
    h, w = len(grid), len(grid[0])
    top, left, bottom, right = bbox(cells)
    center_twice = (top + bottom, left + right)
    corners = ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))
    destination = min(
        corners,
        key=lambda p: sum((2 * p[i] - center_twice[i]) ** 2 for i in (0, 1)),
    )
    target_top = 0 if destination[0] == 0 else h - (bottom - top + 1)
    target_left = 0 if destination[1] == 0 else w - (right - left + 1)
    output = [[0] * w for _ in range(h)]
    for r, c in cells:
        output[r - top + target_top][c - left + target_left] = color
    return output


def fill_enclosed_holes_after_docking(grid):
    """Independent wrong rule: dock correctly, then flood-fill enclosed zeros."""
    output = nearest_corner_expected(grid)
    h, w = len(output), len(output[0])
    color = components(grid)[0][0]
    exterior = {(r, c) for r, row in enumerate(output) for c, value in enumerate(row)
                if value == 0 and (r in (0, h - 1) or c in (0, w - 1))}
    pending = list(exterior)
    while pending:
        r, c = pending.pop()
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if (0 <= nr < h and 0 <= nc < w and output[nr][nc] == 0
                    and (nr, nc) not in exterior):
                exterior.add((nr, nc))
                pending.append((nr, nc))
    for r, row in enumerate(output):
        for c, value in enumerate(row):
            if value == 0 and (r, c) not in exterior:
                output[r][c] = color
    return output


def normalized_mask(cells):
    top, left, _, _ = bbox(cells)
    return frozenset((r - top, c - left) for r, c in cells)


def dihedral_masks(cells):
    """All rotations/reflections from signed coordinates, independent of source."""
    masks = set()
    for swap, sign_r, sign_c in itertools.product((False, True), (-1, 1), (-1, 1)):
        transformed = {(sign_r * (c if swap else r), sign_c * (r if swap else c))
                       for r, c in cells}
        masks.add(normalized_mask(transformed))
    return masks


# These are the public finite mask families, not values read from the generator.
SHAPE_MASKS = {
    "ell": {(0, 0), (1, 0), (1, 1)},
    "zigzag": {(0, 0), (1, 0), (1, 1), (2, 1)},
    "hook": {(0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (3, 0)},
    "ring": {(r, c) for r in range(3) for c in range(3) if (r, c) != (1, 1)},
    "rectangle": {(r, c) for r in range(2) for c in range(3)},
}
SHAPE_VARIANTS = {name: dihedral_masks(mask) for name, mask in SHAPE_MASKS.items()}
AXES = {"grid_h", "grid_w", "object_color", "shape_kind"}
DIFFICULTIES = ("easy", "medium", "hard")


def observed_axes(grid):
    objects = components(grid)
    if len(objects) != 1:
        raise ValueError("expected one object")
    color, cells = objects[0]
    mask = normalized_mask(cells)
    kinds = [name for name, variants in SHAPE_VARIANTS.items() if mask in variants]
    if len(kinds) != 1:
        raise ValueError(f"mask matches {len(kinds)} declared shape families")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "object_color": color,
        "shape_kind": kinds[0],
    }


# These targets are literal grids. Neither oracle nor generator constructs them.
LITERAL_CASES = (
    (
        "ties choose top and left",
        digits("0000000", "0000000", "0050000", "0050000", "0055500", "0000000", "0000000"),
        digits("5000000", "5000000", "5550000", "0000000", "0000000", "0000000", "0000000"),
    ),
    (
        "row tie chooses top while columns choose right",
        digits("000000000", "000000000", "000000700", "000000700", "000000770", "000000000", "000000000"),
        digits("000000070", "000000070", "000000077", "000000000", "000000000", "000000000", "000000000"),
    ),
    (
        "column tie chooses left while rows choose bottom",
        digits("0000000", "0000000", "0000000", "0000000", "0000000", "0000000", "0022200", "0020000", "0000000"),
        digits("0000000", "0000000", "0000000", "0000000", "0000000", "0000000", "0000000", "2220000", "2000000"),
    ),
    (
        "bbox center chooses top although occupied-cell centroid chooses bottom",
        digits("000000000", "000000004", "000000004", "000000004", "000000004", "004444444", "000000000", "000000000", "000000000"),
        digits("000000004", "000000004", "000000004", "000000004", "004444444", "000000000", "000000000", "000000000", "000000000"),
    ),
    (
        "wide canvas compares column center to width",
        digits("00000000000", "00003000000", "00003300000", "00000000000", "00000000000", "00000000000"),
        digits("30000000000", "33000000000", "00000000000", "00000000000", "00000000000", "00000000000"),
    ),
    (
        "tall canvas compares row center to height",
        digits("000000", "000000", "000000", "000000", "000600", "000660", "000000", "000000", "000000", "000000", "000000"),
        digits("000060", "000066", "000000", "000000", "000000", "000000", "000000", "000000", "000000", "000000", "000000"),
    ),
    (
        "translation preserves ring holes and color nine",
        digits("0000000000", "0000000000", "0000000000", "0000000000", "0000099990", "0000090090", "0000099990", "0000000000"),
        digits("0000000000", "0000000000", "0000000000", "0000000000", "0000000000", "0000009999", "0000009009", "0000009999"),
    ),
)


class GeneratorRegressionTests(unittest.TestCase):
    def test_every_public_canonical_input_passes_self_check(self):
        pairs = canonical_pairs()
        self.assertEqual(len(pairs), 4)
        for pair in pairs:
            self.assertEqual(len(components(pair["input"])), 1)
            self.assertEqual(generator.self_check(pair["input"]), [])

    def test_default_draw_is_one_monochrome_object(self):
        grid = generator.generate(0, 0, difficulty="medium")
        self.assertEqual(len(components(grid)), 1)
        self.assertEqual(len({v for row in grid for v in row if v}), 1)

    def test_independent_oracle_matches_literal_and_all_canonical_targets(self):
        for name, grid, expected in LITERAL_CASES:
            with self.subTest(literal=name):
                self.assertEqual(nearest_corner_expected(grid), expected)
        pairs = canonical_pairs()
        self.assertEqual([(p["split"], p["pair_index"]) for p in pairs],
                         [("train", 0), ("train", 1), ("train", 2), ("test", 0)])
        for pair in pairs:
            with self.subTest(split=pair["split"], pair=pair["pair_index"]):
                self.assertEqual(nearest_corner_expected(pair["input"]), pair["output"])

    def test_generator_oracle_matches_all_canonical_targets_without_mutation(self):
        for pair in canonical_pairs():
            before = [row[:] for row in pair["input"]]
            with self.subTest(split=pair["split"], pair=pair["pair_index"]):
                self.assertEqual(generator._semantic_oracle(pair["input"]), pair["output"])
                self.assertEqual(generator.strict_canonical_like(pair["input"]), [])
                self.assertEqual(pair["input"], before)

    def test_literal_ties_rectangles_centroid_holes_and_colors(self):
        for name, grid, expected in LITERAL_CASES:
            with self.subTest(literal=name):
                before = [row[:] for row in grid]
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(generator.strict_canonical_like(grid), [])
                self.assertEqual(generator._semantic_oracle(grid), expected)
                self.assertEqual(grid, before)

    def test_bbox_vs_centroid_fixture_really_distinguishes_the_rules(self):
        _, grid, expected = LITERAL_CASES[3]
        _, cells = components(grid)[0]
        top, _, bottom, _ = bbox(cells)
        canvas_midpoint = (len(grid) - 1) / 2
        self.assertLess((top + bottom) / 2, canvas_midpoint)
        self.assertGreater(sum(r for r, _ in cells) / len(cells), canvas_midpoint)
        self.assertEqual(bbox(components(expected)[0][1])[0], 0)

    def test_all_default_bands_seeds_and_indices_are_lawful_and_deterministic(self):
        self.addCleanup(random.setstate, random.getstate())
        random.seed(47001)
        initial_state = random.getstate()
        corners_seen = set()
        for band, seed, sample_index in itertools.product(DIFFICULTIES, range(10), range(6)):
            with self.subTest(band=band, seed=seed, sample_index=sample_index):
                grid = generator.generate(seed, sample_index, difficulty=band)
                before = [row[:] for row in grid]
                self.assertEqual(generator.generate(seed, sample_index, difficulty=band), grid)
                self.assertEqual(len(components(grid)), 1)
                self.assertEqual(len({value for row in grid for value in row if value}), 1)
                self.assertTrue(6 <= len(grid) <= 24)
                self.assertTrue(6 <= len(grid[0]) <= 24)
                self.assertEqual(generator.self_check(grid, difficulty=band), [])
                self.assertEqual(generator.strict_canonical_like(grid), [])
                expected = nearest_corner_expected(grid)
                self.assertNotEqual(expected, grid)
                self.assertEqual(generator._semantic_oracle(grid), expected)
                self.assertEqual(generator.observe_overrides(grid), observed_axes(grid))
                top, left, _, _ = bbox(components(expected)[0][1])
                corners_seen.add((top == 0, left == 0))
                self.assertEqual(grid, before)
        self.assertEqual(corners_seen, {(True, True), (True, False), (False, True), (False, False)})
        self.assertEqual(random.getstate(), initial_state)

    def test_all_declared_axis_combinations_are_constructive_and_observed(self):
        """Exercise all 16,245 tuples; rotate bands and all six schedule indices."""
        self.assertEqual(set(generator.AXES), AXES)
        combinations = itertools.product(range(6, 25), range(6, 25), range(1, 10), SHAPE_MASKS)
        for index, (h, w, color, kind) in enumerate(combinations):
            kwargs = {"grid_h": h, "grid_w": w, "object_color": color, "shape_kind": kind}
            band = DIFFICULTIES[index % len(DIFFICULTIES)]
            with self.subTest(**kwargs, band=band):
                grid = generator.generate(index % 10, index % 6, difficulty=band, **kwargs)
                self.assertEqual(observed_axes(grid), kwargs)
                self.assertEqual(generator.observe_overrides(grid), kwargs)
                self.assertEqual(generator.self_check(grid), [])
                self.assertNotEqual(nearest_corner_expected(grid), grid)

    def test_boundary_axis_combinations_work_in_every_difficulty_band(self):
        for band, h, w, color, kind in itertools.product(
            DIFFICULTIES, (6, 24), (6, 24), (1, 9), SHAPE_MASKS
        ):
            kwargs = {"grid_h": h, "grid_w": w, "object_color": color, "shape_kind": kind}
            with self.subTest(band=band, **kwargs):
                grid = generator.generate(19, 5, difficulty=band, **kwargs)
                self.assertEqual(observed_axes(grid), kwargs)
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(generator._semantic_oracle(grid), nearest_corner_expected(grid))
                self.assertNotEqual(generator._semantic_oracle(grid), grid)

    def test_recorded_axis_values_and_used_overrides_match_observation(self):
        cases = ({}, {"grid_h": 6}, {"grid_w": 24}, {"object_color": 9}, {"shape_kind": "ring"},
                 {"grid_h": 6, "grid_w": 24, "object_color": 1, "shape_kind": "hook"})
        for band, kwargs in itertools.product(DIFFICULTIES, cases):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = generator.generate(41, 2, difficulty=band, **kwargs)
            finally:
                base.set_ctx_observer(None)
            with self.subTest(band=band, kwargs=kwargs):
                self.assertEqual(len(captured), 1)
                observed = observed_axes(grid)
                self.assertEqual({key: captured[0].axis_value(key) for key in AXES}, observed)
                self.assertEqual(captured[0].overrides_used(), kwargs)

    def test_every_axis_rejects_unknown_out_of_range_boolean_and_invalid_type_values(self):
        invalid = [
            {"bogus": 1}, {"n_components": 3}, {"texture": "single_component"},
            {"palette_kind": "default"}, {"position_bias": "scattered_components"},
        ]
        for axis, lower, upper in (("grid_h", 6, 24), ("grid_w", 6, 24), ("object_color", 1, 9)):
            for value in (lower - 1, upper + 1, True, False, str(lower), float(lower), None, [], {}):
                invalid.append({axis: value})
        for value in ("ELL", "triangle", "", True, False, 1, 1.0, None, [], {}):
            invalid.append({"shape_kind": value})
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, difficulty="medium", **kwargs)
        for difficulty in ("expert", "", 0, 0.5, True, [], {}):
            with self.subTest(difficulty=difficulty):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, difficulty=difficulty)

    def test_valid_default_difficulty_and_fresh_returns(self):
        implicit = generator.generate(29, 3)
        explicit = generator.generate(29, 3, difficulty=None)
        self.assertEqual(implicit, explicit)
        self.assertIsNot(implicit, explicit)
        self.assertTrue(all(first is not second for first, second in zip(implicit, explicit)))
        implicit[0][0] = (implicit[0][0] + 1) % 10
        self.assertEqual(generator.generate(29, 3), explicit)

    def test_validators_reject_malformed_and_multicomponent_inputs(self):
        malformed = {
            "none": None,
            "scalar": 3,
            "string": "000",
            "empty": [],
            "zero-width": [[]],
            "ragged": [[0, 1], [0]],
            "digit-string-rows": ["000", "010"],
            "boolean-cell": [[0, True], [0, 0]],
            "float-cell": [[0, 1.0], [0, 0]],
            "negative-cell": [[0, -1], [0, 0]],
            "out-of-palette": [[0, 10], [0, 0]],
            "all-background": [[0, 0], [0, 0]],
            "missing-zero-background": [[1, 1], [1, 1]],
            "too-tall": [[0, 1]] + [[0, 0] for _ in range(30)],
            "too-wide": [[1] + [0] * 30],
            "disconnected-same-color": digits("000000", "010010", "000000"),
            "diagonal-same-color": digits("0000", "0100", "0010", "0000"),
            "touching-different-colors": digits("00000", "01200", "00000"),
            "disconnected-different-colors": digits("000000", "010020", "000000"),
        }
        for name, grid in malformed.items():
            with self.subTest(case=name):
                reasons = generator.self_check(grid)
                self.assertIsInstance(reasons, list)
                self.assertTrue(reasons)
                self.assertTrue(all(isinstance(reason, str) and reason for reason in reasons))
                strict_reasons = generator.strict_canonical_like(grid)
                self.assertIsInstance(strict_reasons, list)
                self.assertTrue(strict_reasons)
        self.assertEqual(len(components(malformed["disconnected-same-color"])), 2)
        self.assertEqual(len(components(malformed["diagonal-same-color"])), 2)
        self.assertEqual(len(components(malformed["touching-different-colors"])), 2)

    def test_broader_lawful_domain_includes_identity_and_one_dimensional_grids(self):
        cases = (
            (digits("22000000", "20000000", "00000000"), digits("22000000", "20000000", "00000000")),
            (digits("00800"), digits("80000")),
            (digits("0", "0", "7", "0", "0"), digits("7", "0", "0", "0", "0")),
            (digits("01"), digits("01")),
        )
        for grid, expected in cases:
            with self.subTest(grid=grid):
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(generator.strict_canonical_like(grid), [])
                self.assertEqual(generator._semantic_oracle(grid), expected)
                self.assertEqual(nearest_corner_expected(grid), expected)

    def test_strong_witnesses_require_actual_rival_disagreement_on_broad_domain(self):
        # When an object spans an axis, choosing either end along that axis
        # produces identical pixels. A coordinate disagreement is insufficient.
        full_height = [[0, 1, 0, 0, 0, 0] for _ in range(6)]
        full_width = [[0] * 10, [1] * 10] + [[0] * 10 for _ in range(4)]
        with self.subTest(witness="exact tie", fixture="full height"):
            self.assertEqual(generator.self_check(full_height), [])
            self.assertFalse(generator._exact_tie(full_height))
        with self.subTest(witness="independent axes", fixture="full width"):
            self.assertEqual(generator.self_check(full_width), [])
            self.assertFalse(generator._independent_axes(full_width))
        with self.subTest(witness="exact tie", fixture="visible tie"):
            self.assertTrue(generator._exact_tie(LITERAL_CASES[0][1]))
        with self.subTest(witness="independent axes", fixture="visible width difference"):
            self.assertTrue(generator._independent_axes(LITERAL_CASES[4][1]))

        fixtures = [
            ("full-height column", full_height),
            ("full-width row", full_width),
            ("transposed full-height column", [list(row) for row in zip(*full_height)]),
            ("transposed full-width row", [list(row) for row in zip(*full_width)]),
        ]
        fixtures.extend((name, grid) for name, grid, _ in LITERAL_CASES)
        fixtures.extend((f"canonical {pair['split']} {pair['pair_index']}", pair["input"])
                        for pair in canonical_pairs())
        for band, seed, sample_index in itertools.product(DIFFICULTIES, range(2), range(3)):
            fixtures.append((f"{band} seed {seed} index {sample_index}",
                             generator.generate(seed, sample_index, difficulty=band)))
        for fixture_name, grid in fixtures:
            self.assertEqual(len(components(grid)), 1)
            self.assertEqual(generator.self_check(grid), [])
            expected = nearest_corner_expected(grid)
            for name, predicate in generator.SEMANTIC_WITNESSES.items():
                with self.subTest(fixture=fixture_name, witness=name):
                    if predicate(grid):
                        rivals = generator.WITNESS_RIVALS[name]
                        self.assertTrue(rivals)
                        self.assertTrue(
                            any(generator.SEMANTIC_RIVALS[rival](grid) != expected
                                for rival in rivals),
                            f"{name} fires but every named rival produces the correct grid",
                        )

    def test_hole_filling_rival_fits_canonical_pairs_and_fills_literal_ring_only(self):
        for pair in canonical_pairs():
            with self.subTest(split=pair["split"], pair=pair["pair_index"]):
                self.assertEqual(fill_enclosed_holes_after_docking(pair["input"]), pair["output"])
        _, ring, preserved = LITERAL_CASES[6]
        filled = digits("0000000000", "0000000000", "0000000000", "0000000000",
                        "0000000000", "0000009999", "0000009999", "0000009999")
        self.assertEqual(fill_enclosed_holes_after_docking(ring), filled)
        self.assertNotEqual(filled, preserved)
        _, open_notch, expected = LITERAL_CASES[0]
        self.assertEqual(fill_enclosed_holes_after_docking(open_notch), expected)

    def test_default_three_demo_two_query_lessons_expose_hole_preservation_when_needed(self):
        ambiguous = []
        for band, seed, start in itertools.product(DIFFICULTIES, range(100), range(3)):
            inputs = [generator.generate(seed, index, difficulty=band)
                      for index in range(start, start + 5)]
            expected = [nearest_corner_expected(grid) for grid in inputs]
            wrong = [fill_enclosed_holes_after_docking(grid) for grid in inputs]
            if wrong[:3] == expected[:3] and wrong[3:] != expected[3:]:
                ambiguous.append((band, seed, start))
                if seed == 14 and start == 0:
                    with self.subTest(band=band, seed=seed, start=start):
                        self.fail("hole-filling fits all three demos but disagrees on a query")
        self.assertFalse(ambiguous,
                         f"{len(ambiguous)} ambiguous default lessons; first cases: {ambiguous[:12]}")


if __name__ == "__main__":
    unittest.main()
