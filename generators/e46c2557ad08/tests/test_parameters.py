"""Focused contracts for the separate gray-component parametric family.

Literal fixtures exercise the change in component membership.  Native
qualification independently executes complete generated episodes through Racket.
"""
from __future__ import annotations

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys
import unittest


TASK_ID = "e46c2557ad08"
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
SETTINGS = ({"preprocess": "none"}, {"preprocess": "blue_to_gray"})
H2 = frozenset({(0, 0), (0, 1)})
V2 = frozenset({(0, 0), (1, 0)})
H3 = frozenset({(0, 0), (0, 1), (0, 2)})
SQUARE = frozenset({(0, 0), (0, 1), (1, 0), (1, 1)})


def _grid(*rows):
    return [[int(value) for value in row] for row in rows]


# A mixed pair is created; a gray pair is destroyed by a blue extension.
# The gray pair at the top right touches a gray singleton only diagonally.
# Vertical, longer, mixed-square, blue and green controls remain visible.
WITNESS = _grid(
    "510000550000", "000000005000", "551000000000", "000000000000",
    "500001100330", "100000000000", "000000005100", "000000001500",
    "000000000000", "555000000000",
)
INTERMEDIATE = _grid(
    "550000550000", "000000005000", "555000000000", "000000000000",
    "500005500330", "500000000000", "000000005500", "000000005500",
    "000000000000", "555000000000",
)
EXPECTED = (
    _grid(
        "510000880000", "000000005000", "881000000000", "000000000000",
        "500001100330", "100000000000", "000000005100", "000000001500",
        "000000000000", "555000000000",
    ),
    _grid(
        "880000880000", "000000005000", "555000000000", "000000000000",
        "500008800330", "500000000000", "000000005500", "000000005500",
        "000000000000", "555000000000",
    ),
)


def _module(name):
    path = PARAMETRIC / f"{name}.py"
    assert path.is_file(), f"Required native parametric source is missing: {path}"
    spec = spec_from_file_location(f"tested_{TASK_ID}_{name}", path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical():
    for root in (HOME, *HOME.parents):
        for relative in ("shared/data/canonical/puzzles.jsonl", "data/canonical/puzzles.jsonl"):
            ledger = root / relative
            if ledger.is_file():
                for line in ledger.read_text(encoding="utf-8").splitlines():
                    row = json.loads(line)
                    if row.get("task_id") == TASK_ID:
                        return row["program_solution"]
    raise AssertionError("The selected tree must include the canonical authority")


def _components(grid):
    """Independent structural measurements, not an output-label oracle."""
    seen = set()
    components = []
    height, width = len(grid), len(grid[0])
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color, cells, todo = grid[r][c], set(), [(r, c)]
            seen.add((r, c))
            while todo:
                rr, cc = todo.pop()
                cells.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = rr + dr, cc + dc
                    if (0 <= nxt[0] < height and 0 <= nxt[1] < width
                            and nxt not in seen and grid[nxt[0]][nxt[1]] == color):
                        seen.add(nxt)
                        todo.append(nxt)
            top = min(rr for rr, _ in cells)
            left = min(cc for _, cc in cells)
            shape = frozenset((rr - top, cc - left) for rr, cc in cells)
            components.append((color, cells, shape))
    return components


def _teaching_features(grid):
    merged = [[5 if value == 1 else value for value in row] for row in grid]
    before, after = _components(grid), _components(merged)
    merged_targets = [cells for color, cells, shape in after if color == 5 and shape == H2]
    target_cells = set().union(*merged_targets)
    features = set()
    for cells in merged_targets:
        if {grid[r][c] for r, c in cells} == {1, 5}:
            features.add("created_mixed_domino")
        if any(0 <= r + dr < len(grid) and 0 <= c + dc < len(grid[0])
               and (r + dr, c + dc) not in cells and merged[r + dr][c + dc] == 5
               for r, c in cells for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1))):
            features.add("diagonal_connectivity")
    for color, cells, shape in before:
        if color == 5 and shape == H2:
            features.add("preserved_gray_domino" if cells <= target_cells
                         else "destroyed_original_domino")
        if color == 5 and shape == V2:
            features.add("gray_vertical")
        if color == 5 and shape == H3:
            features.add("gray_h3")
        if color == 1 and shape == H2 and cells <= target_cells:
            features.add("blue_domino")
        if color == 3 and shape == H2:
            features.add("green_domino")
    for color, cells, shape in after:
        if color == 5 and shape == SQUARE and {grid[r][c] for r, c in cells} == {1, 5}:
            features.add("mixed_square")
    return features


def _input_keys(pairs):
    return [tuple(tuple(row) for row in pair["input"]) for pair in pairs]


def _nonblack_component_rival(grid):
    """Wrong rule: touching green enlarges an otherwise eligible gray object."""
    intermediate = [[5 if cell == 1 else cell for cell in row] for row in grid]
    foreground_mask = [[1 if cell != 0 else 0 for cell in row] for row in intermediate]
    output = deepcopy(intermediate)
    for _, cells, shape in _components(foreground_mask):
        if shape == H2 and all(intermediate[r][c] == 5 for r, c in cells):
            for r, c in cells:
                output[r][c] = 8
    return output


class ParameterContracts(unittest.TestCase):
    def test_native_entrypoints_exist(self):
        missing = [name for name in ("adapter.py", "prototype.py")
                   if not (PARAMETRIC / name).is_file()]
        self.assertEqual(missing, [], "Implement the native parametric entry points")

    def test_default_keeps_exact_canonical_program(self):
        adapter = _module("adapter")
        self.assertEqual(adapter.program(SETTINGS[0]), _canonical())
        self.assertNotEqual(adapter.program(SETTINGS[1]), _canonical())

    def test_created_destroyed_and_diagonal_components_have_literal_answers(self):
        prototype = _module("prototype")
        original = deepcopy(WITNESS)
        self.assertEqual(prototype.merge_blue(WITNESS), INTERMEDIATE)
        for settings, expected in zip(SETTINGS, EXPECTED):
            with self.subTest(settings=settings):
                self.assertEqual(prototype.transform(WITNESS, settings), expected)
                self.assertEqual(WITNESS, original, "Transforms must not mutate their input")

    def test_real_racket_matches_literal_answers_and_wrong_order_differs(self):
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule

        adapter = _module("adapter")
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")"
                                  for row in WITNESS) + ")"
        bridge = RacketBridge()
        try:
            self.assertEqual(bridge.runtime_identity["backend"], "racket")
            self.assertIs(bridge.runtime_identity["protected"], True)
            def execute(program):
                return bridge.eval_text(f"({wrap_rule(program)} {literal})")
            for settings, expected in zip(SETTINGS, EXPECTED):
                with self.subTest(settings=settings):
                    self.assertEqual(execute(adapter.program(settings)), expected)
            self.assertEqual(execute("(rule! (recolor g 1 5))"), INTERMEDIATE)
            canonical = _canonical()
            self.assertTrue(canonical.startswith("(rule! "))
            wrong_order = "(rule! (recolor " + canonical[len("(rule! "):-1] + " 1 5))"
            wrong_output = execute(wrong_order)
            self.assertNotEqual(wrong_output, EXPECTED[1])
            self.assertEqual(wrong_output[0][:2], [5, 5])
            self.assertEqual(wrong_output[2][:3], [8, 8, 5])
        finally:
            bridge.close()

    def test_settings_and_typed_request_bounds_are_enforced(self):
        adapter = _module("adapter")
        for bad in (None, {}, [], "none", {"preprocess": False},
                    {"preprocess": "unknown"}, {"preprocess": "none", "extra": 1}):
            with self.subTest(settings=bad):
                with self.assertRaises((ValueError, TypeError)):
                    adapter.program(bad)
                with self.assertRaises((ValueError, TypeError)):
                    adapter.generate(seed=17, settings=bad, demos=3, queries=4)
        invalid = {
            "seed": (True, False, 17.0, "17", None),
            "demos": (True, False, 2.0, "2", 0, 1, 7),
            "queries": (True, False, 4.0, "4", 0, 5),
        }
        for argument, values in invalid.items():
            for value in values:
                request = dict(seed=17, settings=SETTINGS[0], demos=3, queries=4)
                request[argument] = value
                with self.subTest(argument=argument, value=value):
                    with self.assertRaises((ValueError, TypeError)):
                        adapter.generate(**request)

    def test_counts_are_independent_and_input_prefixes_are_stable(self):
        adapter = _module("adapter")
        largest = [adapter.generate(seed=17, settings=settings, demos=6, queries=4)
                   for settings in SETTINGS]
        self.assertEqual(_input_keys(largest[0]["train"]), _input_keys(largest[1]["train"]))
        self.assertEqual(_input_keys(largest[0]["test"]), _input_keys(largest[1]["test"]))
        for settings, baseline in zip(SETTINGS, largest):
            self.assertEqual(baseline, adapter.generate(seed=17, settings=settings, demos=6, queries=4))
            for demos, queries in ((2, 1), (2, 4), (3, 4), (6, 1), (6, 4)):
                with self.subTest(settings=settings, demos=demos, queries=queries):
                    episode = adapter.generate(seed=17, settings=settings, demos=demos, queries=queries)
                    self.assertEqual(len(episode["train"]), demos)
                    self.assertEqual(len(episode["test"]), queries)
                    self.assertEqual(episode["program_solution"], adapter.program(settings))
                    self.assertEqual(episode["train"], baseline["train"][:demos])
                    self.assertEqual(episode["test"], baseline["test"][:queries])
                    keys = _input_keys(episode["train"] + episode["test"])
                    self.assertEqual(len(set(keys)), demos + queries, "All query inputs must be novel")

    def test_two_demonstrations_expose_the_relevant_shortcuts(self):
        adapter = _module("adapter")
        required = {"created_mixed_domino", "destroyed_original_domino", "preserved_gray_domino",
                    "gray_vertical", "gray_h3", "mixed_square", "blue_domino", "green_domino",
                    "diagonal_connectivity"}
        for seed in (0, 17):
            episodes = [adapter.generate(seed=seed, settings=settings, demos=2, queries=4)
                        for settings in SETTINGS]
            for episode in episodes:
                features = set().union(*(_teaching_features(pair["input"])
                                         for pair in episode["train"]))
                self.assertEqual(required - features, set(), f"Missing teaching witnesses at seed {seed}")
            self.assertNotEqual([pair["output"] for pair in episodes[0]["train"]],
                                [pair["output"] for pair in episodes[1]["train"]],
                                "The setting must be learnable from demonstrations alone")

    def test_first_two_demos_reject_multicolor_component_shortcut(self):
        adapter = _module("adapter")
        episode = adapter.generate(seed=0, settings=SETTINGS[1], demos=2, queries=4)
        query_four = episode["test"][3]
        self.assertNotEqual(_nonblack_component_rival(query_four["input"]), query_four["output"],
                            "Keep the query's meaningful gray-versus-green component distinction")
        rejected_by = [index for index, pair in enumerate(episode["train"])
                       if _nonblack_component_rival(pair["input"]) != pair["output"]]
        self.assertTrue(rejected_by,
                        "The nonblack-component rival fits both visible demonstrations but changes "
                        "query four; teach the color boundary before presenting the queries")

    def test_fourth_query_has_substantive_large_content_and_strict_grids(self):
        adapter = _module("adapter")
        for settings in SETTINGS:
            episode = adapter.generate(seed=23, settings=settings, demos=3, queries=4)
            for pair in episode["train"] + episode["test"]:
                for role in ("input", "output"):
                    grid = pair[role]
                    self.assertIs(type(grid), list)
                    self.assertTrue(1 <= len(grid) <= 30)
                    self.assertTrue(1 <= len(grid[0]) <= 30)
                    for row in grid:
                        self.assertIs(type(row), list)
                        self.assertEqual(len(row), len(grid[0]))
                        self.assertTrue(all(type(cell) is int and 0 <= cell <= 9 for cell in row))
                self.assertEqual((len(pair["input"]), len(pair["input"][0])),
                                 (len(pair["output"]), len(pair["output"][0])))
                self.assertLessEqual({cell for row in pair["input"] for cell in row}, {0, 1, 3, 5})
            grid = episode["test"][3]["input"]
            self.assertEqual((len(grid), len(grid[0])), (30, 30))
            occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
            self.assertGreaterEqual(len(occupied), 40)
            self.assertGreaterEqual(len({r for r, _ in occupied}), 10)
            self.assertGreaterEqual(len({c for _, c in occupied}), 10)
            self.assertEqual({(r // 15, c // 15) for r, c in occupied},
                             {(0, 0), (0, 1), (1, 0), (1, 1)})
            self.assertTrue(any(r in (0, 29) or c in (0, 29) for r, c in occupied),
                            "Large examples must include a boundary contact")


if __name__ == "__main__":
    unittest.main()
