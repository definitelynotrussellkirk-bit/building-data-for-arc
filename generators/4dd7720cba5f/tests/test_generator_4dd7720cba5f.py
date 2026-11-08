"""Focused semantic tests for generator 4dd7720cba5f."""

from __future__ import annotations

from collections import Counter, defaultdict
import copy
import hashlib
import json
from pathlib import Path
import random
import unittest

from puzzle_generators.runner import _load_generator_module
from reviewer_support import canonical_pairs, canonical_path, find_root


ROOT = find_root(__file__)
TASK_ID = "4dd7720cba5f"


def canonical_rows() -> list[dict]:
    rows = []
    path = canonical_path(ROOT)
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    return rows


def data_path(relative: str) -> Path:
    """Resolve copied-runtime and source-tree data layouts explicitly."""
    for prefix in ("data", "shared/data"):
        candidate = ROOT / prefix / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(relative)


def tile_summary(grid: list[list[int]]) -> dict:
    """Extract source counts without using generator analysis helpers."""
    height, width = len(grid), len(grid[0])
    row_starts = list(range(1, height, 6))
    col_starts = list(range(1, width, 6))
    groups: dict[int, list[set[tuple[int, int]]]] = defaultdict(list)
    frames_complete = True
    for row_start in row_starts:
        for col_start in col_starts:
            color = grid[row_start][col_start]
            border = {
                (row, col)
                for row in range(5)
                for col in range(5)
                if row in (0, 4) or col in (0, 4)
            }
            frames_complete &= all(
                grid[row_start + row][col_start + col] == color
                for row, col in border
            )
            groups[color].append(
                {
                    (row, col)
                    for row in range(1, 4)
                    for col in range(1, 4)
                    if grid[row_start + row][col_start + col] == color
                }
            )
    return {
        "layout": (len(row_starts), len(col_starts)),
        "multiplicities": tuple(
            sorted((len(motifs) for motifs in groups.values()), reverse=True)
        ),
        "source_counts": {
            color: sum(bool(motif) for motif in motifs)
            for color, motifs in groups.items()
        },
        "active_repeated_multiplicities": tuple(
            sorted(
                (
                    len(motifs)
                    for motifs in groups.values()
                    if len(motifs) > 1 and any(motifs)
                ),
                reverse=True,
            )
        ),
        "active_repeated_sources": tuple(
            sorted(
                (
                    (len(motifs), len(next(
                        motif for motif in motifs if motif
                    )))
                    for motifs in groups.values()
                    if len(motifs) > 1
                    and sum(bool(motif) for motif in motifs) == 1
                ),
                reverse=True,
            )
        ),
        "fragmented_repeated_sources": tuple(
            sorted(
                (
                    (
                        len(motifs),
                        len(set().union(*(motif for motif in motifs if motif))),
                        tuple(
                            sorted(
                                (len(motif) for motif in motifs if motif),
                                reverse=True,
                            )
                        ),
                    )
                    for motifs in groups.values()
                    if len(motifs) > 1
                    and sum(bool(motif) for motif in motifs) > 1
                ),
                reverse=True,
            )
        ),
        "active_unique": sum(
            len(motifs) == 1 and bool(motifs[0])
            for motifs in groups.values()
        ),
        "active_unique_motif_sizes": tuple(
            sorted(
                len(motifs[0])
                for motifs in groups.values()
                if len(motifs) == 1 and motifs[0]
            )
        ),
        "motif_sizes": [
            len(motif)
            for motifs in groups.values()
            for motif in motifs
            if motif
        ],
        "frames_complete": frames_complete,
    }


def simple_two_tile_grid() -> list[list[int]]:
    grid = [[0 for _ in range(13)] for _ in range(7)]
    for col_start in (1, 7):
        for offset in range(5):
            grid[1][col_start + offset] = 2
            grid[5][col_start + offset] = 2
            grid[1 + offset][col_start] = 2
            grid[1 + offset][col_start + 4] = 2
    grid[3][3] = 2
    return grid


class Generator4dd7720cba5fTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_generator_module(TASK_ID)
        cls.rows = canonical_rows()
        cls.public_pairs = canonical_pairs(TASK_ID, root=ROOT)
        cls.unique_public_inputs = {
            json.dumps(pair["input"], separators=(",", ":"))
            for pair in cls.public_pairs
        }

    def test_metadata_and_exact_profile_axis(self) -> None:
        self.assertEqual(self.module.VERSION, "4.0.0")
        self.assertEqual(self.module.RULE_HASH, "d947d085ded3")
        self.assertEqual(set(self.module.AXES), {"scene_profile"})
        declared = set(
            self.module.AXES["scene_profile"]["valid"].split("|")
        )
        self.assertEqual(declared, set(self.module.SCENE_PROFILES))
        self.assertEqual(len(self.module.PUBLIC_PROFILES), 5)

    def test_all_canonical_rows_are_exact_positive_controls(self) -> None:
        self.assertEqual(len(self.rows), 2)
        self.assertEqual(len(self.public_pairs), 10)
        self.assertEqual(len(self.unique_public_inputs), 5)
        profiles = set()
        for index, pair in enumerate(self.public_pairs):
            with self.subTest(index=index):
                source = copy.deepcopy(pair["input"])
                self.assertEqual(self.module.self_check(source), [])
                self.assertEqual(
                    self.module.solve_python(source), pair["output"]
                )
                self.assertEqual(source, pair["input"])
                profiles.add(
                    self.module.observe_overrides(source)["scene_profile"]
                )
        self.assertEqual(profiles, set(self.module.PUBLIC_PROFILES))

    def test_every_profile_is_observable_in_every_band(self) -> None:
        for band in ("easy", "medium", "hard"):
            for profile, spec in self.module.SCENE_SPECS.items():
                for seed in range(8):
                    with self.subTest(
                        band=band, profile=profile, seed=seed
                    ):
                        grid = self.module.generate(
                            seed,
                            seed * 37 + 5,
                            difficulty=band,
                            scene_profile=profile,
                        )
                        summary = tile_summary(grid)
                        self.assertEqual(self.module.self_check(grid), [])
                        self.assertEqual(
                            summary["layout"], (spec.rows, spec.cols)
                        )
                        self.assertEqual(
                            summary["multiplicities"], spec.multiplicities
                        )
                        self.assertEqual(
                            summary["active_repeated_multiplicities"],
                            spec.active_repeated_multiplicities,
                        )
                        self.assertEqual(
                            summary["active_unique"], spec.active_unique
                        )
                        self.assertEqual(
                            summary["active_repeated_sources"],
                            tuple(
                                sorted(
                                    spec.active_repeated_sources,
                                    reverse=True,
                                )
                            ),
                        )
                        self.assertEqual(
                            summary["fragmented_repeated_sources"],
                            tuple(
                                sorted(
                                    spec.fragmented_repeated_sources,
                                    reverse=True,
                                )
                            ),
                        )
                        self.assertEqual(
                            summary["active_unique_motif_sizes"],
                            tuple(
                                sorted(
                                    spec.active_unique_motif_sizes
                                )
                            ),
                        )
                        self.assertTrue(summary["frames_complete"])
                        if spec.fragmented_repeated_sources:
                            self.assertTrue(
                                any(
                                    source_count > 1
                                    for source_count in summary[
                                        "source_counts"
                                    ].values()
                                )
                            )
                        else:
                            self.assertTrue(
                                all(
                                    source_count <= 1
                                    for source_count in summary[
                                        "source_counts"
                                    ].values()
                                )
                            )
                        self.assertEqual(
                            self.module.observe_overrides(grid),
                            {"scene_profile": profile},
                        )

    def test_default_bands_balance_linked_and_extrapolated_profiles(self) -> None:
        expected_profiles = {
            "easy": {
                "public_2x3_21111",
                "transpose_3x2_21111",
                "union_2x3_21111",
            },
            "medium": {
                "public_3x3_32211",
                "public_3x3_3222",
                "extrap_3x3_222111",
                "union_3x3_32211",
            },
            "hard": {
                "public_4x3_4221111",
                "public_4x4_5322211",
                "transpose_3x4_4221111",
                "extrap_4x4_4332211",
                "union_4x3_4221111",
            },
        }
        expected_motif_sizes = {
            "easy": {2, 5},
            "medium": {1, 2, 3, 5},
            "hard": {1, 2, 3, 4},
        }
        for band_index, band in enumerate(("easy", "medium", "hard")):
            profiles = Counter()
            motif_sizes = set()
            colors = set()
            linked = 0
            distinct = set()
            for index in range(400):
                grid = self.module.generate(
                    20_000 + index,
                    band_index * 10_000 + index,
                    difficulty=band,
                )
                profile = self.module.observe_overrides(grid)[
                    "scene_profile"
                ]
                summary = tile_summary(grid)
                profiles[profile] += 1
                motif_sizes.update(summary["motif_sizes"])
                colors.update(
                    value for row in grid for value in row if value
                )
                linked += profile in self.module.PUBLIC_PROFILES
                distinct.add(tuple(tuple(row) for row in grid))
            self.assertEqual(set(profiles), expected_profiles[band])
            self.assertEqual(motif_sizes, expected_motif_sizes[band])
            self.assertEqual(colors, set(range(1, 9)))
            self.assertGreaterEqual(linked, 90)
            self.assertLessEqual(linked, 180)
            self.assertGreaterEqual(len(distinct), 399)

    def test_multi_source_profile_requires_true_union(self) -> None:
        for band, profile in (
            ("easy", "union_2x3_21111"),
            ("medium", "union_3x3_32211"),
            ("hard", "union_4x3_4221111"),
        ):
            for seed in range(12):
                with self.subTest(band=band, seed=seed):
                    grid = self.module.generate(
                        91_000 + seed,
                        seed,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    summary = tile_summary(grid)
                    self.assertTrue(summary["fragmented_repeated_sources"])
                    expected = self.module.solve_python(grid)
                    self.assertNotEqual(
                        self.module.SEMANTIC_RIVALS["first_source_only"](grid),
                        expected,
                    )
                    self.assertNotEqual(
                        self.module.SEMANTIC_RIVALS["blank_targets_only"](grid),
                        expected,
                    )
                    self.assertTrue(
                        self.module.SEMANTIC_WITNESSES[
                            "multi_source_union_required"
                        ](grid)
                    )

    def test_declared_shortcuts_fit_canonical_but_generated_union_refutes_them(
        self,
    ) -> None:
        self.assertEqual(
            set(self.module.CANONICAL_SHORTCUTS),
            {"first_source_only", "blank_targets_only"},
        )
        for name, shortcut in self.module.CANONICAL_SHORTCUTS.items():
            for index, pair in enumerate(self.public_pairs):
                with self.subTest(shortcut=name, canonical_pair=index):
                    self.assertEqual(shortcut(pair["input"]), pair["output"])

        counterexample = self.module.generate(
            123,
            0,
            difficulty="easy",
            scene_profile="union_2x3_21111",
        )
        expected = self.module.solve_python(counterexample)
        for name, shortcut in self.module.CANONICAL_SHORTCUTS.items():
            with self.subTest(shortcut=name, generated_counterexample=True):
                self.assertNotEqual(shortcut(counterexample), expected)

    def test_every_three_default_draws_refute_union_shortcuts(self) -> None:
        for band in ("easy", "medium", "hard"):
            for start in range(12):
                demos = []
                for offset in range(3):
                    grid = self.module.generate(
                        72_001,
                        start + offset,
                        difficulty=band,
                    )
                    demos.append(
                        {"input": grid, "output": self.module.solve_python(grid)}
                    )
                query_grid = self.module.generate(
                    72_001,
                    start + 3,
                    difficulty=band,
                )
                query = {
                    "input": query_grid,
                    "output": self.module.solve_python(query_grid),
                }
                with self.subTest(band=band, start=start):
                    self.assertEqual(
                        self.module.lesson_identifiable(demos, query),
                        [],
                    )
                    for name, rival in self.module.LESSON_COMPETITORS.items():
                        self.assertFalse(
                            all(
                                rival(pair["input"]) == pair["output"]
                                for pair in demos
                            ),
                            name,
                        )

    def test_lesson_hook_reports_unresolved_union_shortcut(self) -> None:
        demos = []
        for sample_index, profile in enumerate(
            ("public_2x3_21111", "transpose_3x2_21111", "public_2x3_21111")
        ):
            grid = self.module.generate(
                44_000 + sample_index,
                100 + sample_index,
                difficulty="easy",
                scene_profile=profile,
            )
            demos.append(
                {"input": grid, "output": self.module.solve_python(grid)}
            )
        query_grid = self.module.generate(
            44_999,
            103,
            difficulty="easy",
            scene_profile="union_2x3_21111",
        )
        reasons = self.module.lesson_identifiable(
            demos,
            {"input": query_grid, "output": self.module.solve_python(query_grid)},
        )
        self.assertIn(
            "unresolved answer-changing competitor: first_source_only",
            reasons,
        )
        self.assertIn(
            "unresolved answer-changing competitor: blank_targets_only",
            reasons,
        )

    def test_defaults_are_deterministic_fresh_and_rng_isolated(self) -> None:
        random.seed(20260719)
        state = random.getstate()
        for band in ("easy", "medium", "hard"):
            for seed in range(20):
                first = self.module.generate(seed, 7, difficulty=band)
                second = self.module.generate(seed, 7, difficulty=band)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertTrue(
                    all(a is not b for a, b in zip(first, second))
                )
                before = copy.deepcopy(first)
                output = self.module.solve_python(first)
                self.assertEqual(first, before)
                self.assertNotEqual(output, first)
                self.assertTrue(
                    all(a is not b for a, b in zip(first, output))
                )
        self.assertEqual(random.getstate(), state)

    def test_literal_public_inputs_are_not_replayed(self) -> None:
        for profile in self.module.SCENE_PROFILES:
            for seed in range(30):
                grid = self.module.generate(
                    seed,
                    50_000 + seed,
                    difficulty="medium",
                    scene_profile=profile,
                )
                self.assertNotIn(
                    json.dumps(grid, separators=(",", ":")),
                    self.unique_public_inputs,
                )

    def test_oracle_unions_source_offsets_and_preserves_input(self) -> None:
        grid = simple_two_tile_grid()
        before = copy.deepcopy(grid)
        output = self.module.solve_python(grid)
        self.assertEqual(grid, before)
        self.assertEqual(output[3][3], 2)
        self.assertEqual(output[3][9], 2)
        changed = [
            (row, col)
            for row in range(7)
            for col in range(13)
            if output[row][col] != grid[row][col]
        ]
        self.assertEqual(changed, [(3, 9)])

    def test_self_check_rejects_semantic_impostors(self) -> None:
        base = self.module.generate(
            17,
            5,
            scene_profile="public_2x3_21111",
        )
        color_nine = copy.deepcopy(base)
        source_color = color_nine[1][1]
        for row in range(1, 6):
            for col in range(1, 6):
                if color_nine[row][col] == source_color:
                    color_nine[row][col] = 9

        missing_frame = copy.deepcopy(base)
        missing_frame[1][1] = 0

        wrong_motif = copy.deepcopy(base)
        blank_start = next(
            (row, col)
            for row in range(1, len(base), 6)
            for col in range(1, len(base[0]), 6)
            if all(
                base[row + dr][col + dc] == 0
                for dr in range(1, 4)
                for dc in range(1, 4)
            )
        )
        wrong_motif[blank_start[0] + 1][blank_start[1] + 1] = (
            wrong_motif[blank_start[0]][blank_start[1]]
        )

        multiple_sources = copy.deepcopy(base)
        first_color = multiple_sources[1][1]
        matching_starts = [
            (row, col)
            for row in range(1, len(base), 6)
            for col in range(1, len(base[0]), 6)
            if base[row][col] == first_color
        ]
        if len(matching_starts) < 2:
            first_color = next(
                color
                for color, count in Counter(
                    base[row][col]
                    for row in range(1, len(base), 6)
                    for col in range(1, len(base[0]), 6)
                ).items()
                if count > 1
            )
            matching_starts = [
                (row, col)
                for row in range(1, len(base), 6)
                for col in range(1, len(base[0]), 6)
                if base[row][col] == first_color
            ]
        for row_start, col_start in matching_starts[:2]:
            multiple_sources[row_start + 2][col_start + 2] = first_color

        identity = copy.deepcopy(base)
        for row_start in range(1, len(identity), 6):
            for col_start in range(1, len(identity[0]), 6):
                for row in range(row_start + 1, row_start + 4):
                    for col in range(col_start + 1, col_start + 4):
                        identity[row][col] = 0

        wrong_tile_size = simple_two_tile_grid()
        impostors = {
            "color_nine": color_nine,
            "missing_frame": missing_frame,
            "wrong_motif": wrong_motif,
            "multiple_sources": multiple_sources,
            "identity": identity,
            "wrong_profile": wrong_tile_size,
        }
        for label, grid in impostors.items():
            with self.subTest(label=label):
                before = copy.deepcopy(grid)
                self.assertTrue(self.module.self_check(grid))
                self.assertEqual(self.module.observe_overrides(grid), {})
                self.assertEqual(grid, before)

    def test_unknown_controls_fail_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown override"):
            self.module.generate(0, 0, obsolete_texture="sparse")
        with self.assertRaisesRegex(ValueError, "invalid difficulty"):
            self.module.generate(0, 0, difficulty="expert")
        with self.assertRaises(ValueError):
            self.module.generate(0, 0, scene_profile="missing")

    def test_rule_hash_and_both_base_sources_match_canonical(self) -> None:
        programs = {row["program_solution"] for row in self.rows}
        self.assertEqual(len(programs), 1)
        program = programs.pop()
        digest = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()
        self.assertEqual(self.module.RULE_HASH, digest[:12])
        paths = (
            data_path(
                "base/solutions/training/42918530__4dd7720cba5f.json"
            ),
            data_path(
                "base/solutions/augmented/42918530__faf978157f30.json"
            ),
        )
        for path in paths:
            record = json.loads(path.read_text())
            # Selected authority must be byte-exact with canonical; raw_code is
            # an archival executable source whose textual divergence is lawful
            # (selected_synchronized_archival_divergent policy) — require only
            # that it exists.
            self.assertTrue(record["racket_target"]["raw_code"])
            self.assertEqual(record["racket_target"]["target_code"], program)
            self.assertEqual(
                record["primitive_metadata"]["primitive_chain"],
                [
                    "rows",
                    "cols",
                    "filter",
                    "all?",
                    "at",
                    "range",
                    "fst",
                    "third",
                    "flatmap",
                    "map",
                    "any?",
                    "snd",
                    "in-bounds?",
                    "reduce",
                    "set-cell",
                ],
            )


if __name__ == "__main__":
    unittest.main()
