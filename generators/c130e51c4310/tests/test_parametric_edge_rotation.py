from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random
import unittest

from reviewer_support import canonical_path, find_root


TASK_ID = "c130e51c4310"
ROOT = find_root(__file__)
MODULE_PATH = (
    ROOT
    / "generators"
    / TASK_ID
    / "workspace"
    / "parametric"
    / "edge_rotation.py"
)
SPEC = importlib.util.spec_from_file_location(
    "c130e51c4310_edge_rotation_test_subject", MODULE_PATH
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {MODULE_PATH}")
edge_rotation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(edge_rotation)


def canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID and row.get("source") == "training":
            return row["program_solution"]
    raise RuntimeError("canonical c130e51c4310 row not found")


def grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def fixture(mask: tuple[str, ...]) -> list[list[int]]:
    """Hand-written frame with a cue wholly below it."""
    grid = [[7 for _ in range(10)] for _ in range(10)]
    for row in range(1, 6):
        for col in range(1, 7):
            if row in (1, 5) or col in (1, 6):
                grid[row][col] = 6
    for drow, values in enumerate(mask):
        for dcol, value in enumerate(values):
            if value == "1":
                grid[6 + drow][5 + dcol] = 5
    return grid


def erased_fixture(mask: tuple[str, ...]) -> list[list[int]]:
    output = fixture(mask)
    for row in range(6, 6 + len(mask)):
        for col in range(5, 5 + len(mask[0])):
            if output[row][col] == 5:
                output[row][col] = 7
    return output


def expected_single_top(mask: tuple[str, ...], target_edge: int) -> list[list[int]]:
    """Literal expected edge order: top, right, bottom, left."""
    output = erased_fixture(mask)
    target_cells = (
        [(2, col) for col in range(2, 6)],
        [(row, 5) for row in range(2, 5)],
        [(4, col) for col in range(2, 6)],
        [(row, 2) for row in range(2, 5)],
    )[target_edge]
    for row, col in target_cells:
        output[row][col] = 5
    return output


def bbox_for_color(grid: list[list[int]], color: int) -> tuple[int, int, int, int]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


class EdgeRotationCoreTests(unittest.TestCase):
    def test_default_program_is_exact_canonical_authority(self):
        self.assertEqual(
            edge_rotation.program({"edge_shift": 0}), canonical_program()
        )

    def test_single_top_edge_rotates_clockwise_to_each_frame_edge(self):
        mask = ("1111", "0100", "0100")
        source = fixture(mask)
        before = copy.deepcopy(source)
        for shift in range(4):
            with self.subTest(shift=shift):
                self.assertEqual(
                    edge_rotation.transform(source, {"edge_shift": shift}),
                    expected_single_top(mask, shift),
                )
                self.assertEqual(source, before)

    def test_all_edges_fill_the_whole_frame_interior_for_every_shift(self):
        mask = ("1111", "1001", "1111")
        expected = erased_fixture(mask)
        for row in range(2, 5):
            for col in range(2, 6):
                expected[row][col] = 5
        for shift in range(4):
            with self.subTest(shift=shift):
                self.assertEqual(
                    edge_rotation.transform(
                        fixture(mask), {"edge_shift": shift}
                    ),
                    expected,
                )

    def test_settings_counts_and_seed_require_exact_bounded_integers(self):
        invalid_settings = (
            None,
            {},
            {"edge_shift": 0, "extra": 1},
            {"edge_shift": True},
            {"edge_shift": 1.0},
            {"edge_shift": -1},
            {"edge_shift": 4},
        )
        for settings in invalid_settings:
            with self.subTest(settings=settings):
                with self.assertRaises(ValueError):
                    edge_rotation.program(settings)
        for kwargs in (
            {"seed": True},
            {"seed": 2**63},
            {"demos": True},
            {"demos": 1},
            {"demos": 7},
            {"queries": True},
            {"queries": 0},
            {"queries": 5},
        ):
            call = {
                "seed": 0,
                "settings": {"edge_shift": 0},
                "demos": 3,
                "queries": 4,
            }
            call.update(kwargs)
            with self.subTest(call=call):
                with self.assertRaises(ValueError):
                    edge_rotation.generate(**call)

    def test_same_seed_and_counts_use_identical_inputs_for_all_settings(self):
        episodes = [
            edge_rotation.generate(
                23, {"edge_shift": shift}, demos=3, queries=4
            )
            for shift in range(4)
        ]
        expected = [
            grid_key(pair["input"])
            for pair in episodes[0]["train"] + episodes[0]["test"]
        ]
        for episode in episodes[1:]:
            self.assertEqual(
                [
                    grid_key(pair["input"])
                    for pair in episode["train"] + episode["test"]
                ],
                expected,
            )

    def test_two_and_six_demo_episodes_are_exact_and_identifying(self):
        for demos in (2, 6):
            for shift in range(4):
                with self.subTest(demos=demos, shift=shift):
                    episode = edge_rotation.generate(
                        41, {"edge_shift": shift}, demos=demos, queries=4
                    )
                    self.assertEqual(len(episode["train"]), demos)
                    self.assertEqual(len(episode["test"]), 4)
                    certificate = edge_rotation.certify(episode)
                    self.assertEqual(
                        certificate["survivors"], [{"edge_shift": shift}]
                    )
                    inputs = [
                        grid_key(pair["input"])
                        for pair in episode["train"] + episode["test"]
                    ]
                    self.assertEqual(len(inputs), len(set(inputs)))

    def test_query_prefix_is_demo_count_independent_and_has_real_30x30_case(self):
        short = edge_rotation.generate(
            59, {"edge_shift": 2}, demos=2, queries=4
        )
        long = edge_rotation.generate(
            59, {"edge_shift": 2}, demos=6, queries=4
        )
        self.assertEqual(
            [pair["input"] for pair in short["test"]],
            [pair["input"] for pair in long["test"]],
        )
        self.assertEqual(
            [(len(p["input"]), len(p["input"][0])) for p in short["test"]],
            [(14, 17), (18, 22), (24, 27), (30, 30)],
        )
        grid = short["test"][3]["input"]
        frame_bbox = bbox_for_color(grid, 6)
        cue_color = next(
            value for row in grid for value in row if value not in (6, 7)
        )
        cue_bbox = bbox_for_color(grid, cue_color)
        self.assertGreaterEqual(frame_bbox[2] - frame_bbox[0] + 1, 16)
        self.assertGreaterEqual(frame_bbox[3] - frame_bbox[1] + 1, 18)
        self.assertGreaterEqual(cue_bbox[2] - cue_bbox[0] + 1, 7)
        self.assertGreaterEqual(cue_bbox[3] - cue_bbox[1] + 1, 9)
        self.assertTrue(
            any(
                row in (0, 29) or col in (0, 29)
                for row, values in enumerate(grid)
                for col, value in enumerate(values)
                if value == cue_color
            )
        )

    def test_generation_is_deterministic_fresh_and_global_rng_pure(self):
        state = random.getstate()
        first = edge_rotation.generate(
            -7, {"edge_shift": 3}, demos=3, queries=4
        )
        second = edge_rotation.generate(
            -7, {"edge_shift": 3}, demos=3, queries=4
        )
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first["train"][0]["input"], second["train"][0]["input"])
        first["train"][0]["input"][0][0] = 9
        self.assertNotEqual(first, second)
        self.assertEqual(random.getstate(), state)

    def test_first_model_turn_is_query_count_independent_and_masked(self):
        one = edge_rotation.generate(
            71, {"edge_shift": 1}, demos=3, queries=1
        )
        four = edge_rotation.generate(
            71, {"edge_shift": 1}, demos=3, queries=4
        )
        one_bytes = edge_rotation.model_turn_bytes(one, 0)
        four_bytes = edge_rotation.model_turn_bytes(four, 0)
        self.assertEqual(one_bytes, four_bytes)
        visible = json.loads(one_bytes)
        self.assertEqual(set(visible), {"train", "test"})
        self.assertEqual(len(visible["test"]), 1)
        self.assertEqual(set(visible["test"][0]), {"input"})
        self.assertNotIn("settings", one_bytes.decode("utf-8"))
        self.assertNotIn("program", one_bytes.decode("utf-8"))
        self.assertNotIn("queries", one_bytes.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()


class EdgeRotationExportTests(unittest.TestCase):
    def load_adapter(self):
        path = MODULE_PATH.with_name("adapter.py")
        spec = importlib.util.spec_from_file_location(
            "c130e51c4310_edge_rotation_adapter_test_subject", path
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_adapter_loads_the_exact_adjacent_core_and_minimal_contract(self):
        adapter = self.load_adapter()
        self.assertEqual(Path(adapter._prototype.__file__).resolve(), MODULE_PATH)
        self.assertEqual(
            adapter.program({"edge_shift": 3}),
            edge_rotation.program({"edge_shift": 3}),
        )
        episode = adapter.generate(5, {"edge_shift": 2}, 2, 1)
        self.assertEqual(set(episode), {"train", "test", "program_solution"})
        self.assertEqual(len(episode["train"]), 2)
        self.assertEqual(len(episode["test"]), 1)

    def test_promotion_contract_names_the_four_settings_and_count_limits(self):
        path = MODULE_PATH.with_name("promotion.json")
        contract = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(contract["schema"], "arcpuzzles-parametric-adapter-v1")
        self.assertEqual(
            contract["adapter"],
            "generators/c130e51c4310/workspace/parametric/adapter.py",
        )
        self.assertEqual(contract["parameters"], {"edge_shift": [0, 1, 2, 3]})
        self.assertEqual(contract["default"], {"edge_shift": 0})
        self.assertEqual(contract["limits"], {"demos": [2, 6], "queries": [1, 4]})
        self.assertIn(
            "generators/c130e51c4310/workspace/parametric/edge_rotation.py",
            contract["resources"],
        )

    def test_writer_refuses_existing_and_duplicate_public_roots_before_writing(self):
        import tempfile

        episode = edge_rotation.generate(
            101, {"edge_shift": 1}, demos=3, queries=4
        )
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent)
            existing = root / "existing"
            existing.mkdir()
            with self.assertRaises(FileExistsError):
                edge_rotation.write_batch([episode], existing)
            self.assertEqual(list(existing.iterdir()), [])

            duplicate = root / "duplicate"
            with self.assertRaises(ValueError):
                edge_rotation.write_batch([episode, copy.deepcopy(episode)], duplicate)
            self.assertFalse(duplicate.exists())

            private_variant = copy.deepcopy(episode)
            private_variant["seed"] = 999
            private_duplicate = root / "private-duplicate"
            with self.assertRaisesRegex(ValueError, "distinct"):
                edge_rotation.write_batch(
                    [episode, private_variant], private_duplicate
                )
            self.assertFalse(private_duplicate.exists())

    def test_public_bytes_ignore_private_mutations_and_hide_query_outputs(self):
        import tempfile

        episode = edge_rotation.generate(
            103, {"edge_shift": 2}, demos=3, queries=4
        )
        mutated = copy.deepcopy(episode)
        mutated["settings"] = {"edge_shift": 0}
        mutated["seed"] = 999
        mutated["program_solution"] = "private replacement"
        mutated["program_sha256"] = "0" * 64
        mutated["certificate"] = {"private": True}
        mutated["test"][0]["output"][0][0] = (
            mutated["test"][0]["output"][0][0] + 1
        ) % 10

        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent)
            first = root / "first"
            second = root / "second"
            one_manifest = edge_rotation.write_batch([episode], first)
            two_manifest = edge_rotation.write_batch([mutated], second)
            self.assertEqual(
                one_manifest["public_ids"], two_manifest["public_ids"]
            )
            self.assertEqual(
                (first / "public.jsonl").read_bytes(),
                (second / "public.jsonl").read_bytes(),
            )
            public_id = one_manifest["public_ids"][0]
            visible = json.loads(
                (first / "public" / f"{public_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(set(visible), {"train", "test"})
            self.assertTrue(all(set(pair) == {"input"} for pair in visible["test"]))
            public_text = (first / "public.jsonl").read_text(encoding="utf-8")
            for forbidden in (
                "edge_shift",
                "program_solution",
                "certificate",
                "program_sha256",
                '"seed"',
            ):
                self.assertNotIn(forbidden, public_text)

    def test_certificate_rejects_duplicate_wrong_and_underidentifying_episodes(self):
        episode = edge_rotation.generate(
            107, {"edge_shift": 3}, demos=3, queries=4
        )

        duplicate = copy.deepcopy(episode)
        duplicate["test"][1]["input"] = copy.deepcopy(
            duplicate["test"][0]["input"]
        )
        with self.assertRaisesRegex(ValueError, "distinct"):
            edge_rotation.certify(duplicate)

        wrong = copy.deepcopy(episode)
        wrong["test"][0]["output"][0][0] = (
            wrong["test"][0]["output"][0][0] + 1
        ) % 10
        with self.assertRaisesRegex(ValueError, "query output"):
            edge_rotation.certify(wrong)

        ambiguous = copy.deepcopy(episode)
        all_edges = copy.deepcopy(episode["train"][1]["input"])
        cue_color = next(
            value for row in all_edges for value in row if value not in (6, 7)
        )
        replacement = 9 if cue_color != 9 else 8
        recolored = [
            [replacement if value == cue_color else value for value in row]
            for row in all_edges
        ]
        chosen = ambiguous["settings"]
        ambiguous["train"] = [
            {"input": all_edges, "output": edge_rotation.transform(all_edges, chosen)},
            {"input": recolored, "output": edge_rotation.transform(recolored, chosen)},
        ]
        with self.assertRaisesRegex(ValueError, "uniquely identify"):
            edge_rotation.certify(ambiguous)

    def test_later_model_turn_is_prefix_stable_and_reveals_only_current_input(self):
        two = edge_rotation.generate(
            109, {"edge_shift": 1}, demos=3, queries=2
        )
        four = edge_rotation.generate(
            109, {"edge_shift": 1}, demos=3, queries=4
        )
        second_two = edge_rotation.model_turn_bytes(two, 1)
        second_four = edge_rotation.model_turn_bytes(four, 1)
        self.assertEqual(second_two, second_four)
        visible = json.loads(second_four)
        self.assertEqual(visible, {"test": [{"input": four["test"][1]["input"]}]})
        self.assertNotEqual(
            visible["test"][0]["input"], four["test"][2]["input"]
        )
        serialized = second_four.decode("utf-8")
        self.assertNotIn("settings", serialized)
        self.assertNotIn("query_index", serialized)
        self.assertNotIn("queries", serialized)
