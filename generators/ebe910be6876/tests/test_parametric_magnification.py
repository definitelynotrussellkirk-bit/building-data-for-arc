from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest


from reviewer_support import canonical_path, find_root  # noqa: E402

ROOT = find_root(__file__)
TASK_DIR = ROOT / "generators" / "ebe910be6876"

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.rule_wrap import wrap_rule  # noqa: E402


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(
        TASK_DIR / "workspace" / "parametric" / "prototype.py",
        "test_parametric_ebe910be6876",
    )


def _adapter():
    return _load(
        TASK_DIR / "workspace" / "parametric" / "adapter.py",
        "test_adapter_ebe910be6876",
    )


def _generator():
    return _load(TASK_DIR / "generator.py", "test_generator_ebe910be6876_parametric")


def _verifier():
    return _load(
        TASK_DIR / "workspace" / "parametric" / "verify.py",
        "test_verify_ebe910be6876",
    )


def _literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _key(grid):
    return json.dumps(grid, separators=(",", ":"))


def _selected_canonical_program():
    programs = {
        row["program_solution"]
        for row in map(json.loads, canonical_path(ROOT).read_text().splitlines())
        if row.get("task_id") == "ebe910be6876"
    }
    if len(programs) != 1:
        raise AssertionError(f"expected one canonical program, found {len(programs)}")
    return programs.pop()


class ParametricClusterFinishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = RacketBridge()

    @classmethod
    def tearDownClass(cls):
        cls.bridge.close()

    def apply(self, program, grid):
        return self.bridge.eval_text(f"({wrap_rule(program)} {_literal(grid)})")

    def test_default_program_is_exact_canonical_and_python_matches_generator(self):
        """Catches canonical-byte drift or a Python default that stops mirroring it."""
        proto = _prototype()
        gen = _generator()
        canonical = (TASK_DIR / "workspace" / "parametric" / "canonical.rkt").read_text()
        self.assertEqual(proto.DEFAULT, {"finish": "expand_only"})
        self.assertEqual(proto.program(proto.DEFAULT), canonical)
        self.assertEqual(canonical, _selected_canonical_program())
        self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(), proto.CANONICAL_SHA256)
        grid = proto.sample_inputs(7, demos=2, queries=1)["train"][0]
        self.assertEqual(proto.solve(grid, finish="expand_only"), gen.rule_mirror(grid))

    def test_largest_cluster_finish_recolors_the_cluster_created_by_expansion(self):
        """Catches same-color grouping, input-space grouping, or wrong tile geometry."""
        proto = _prototype()
        grid = [[0] * 10 for _ in range(8)]
        for row, col, color in (
            (1, 1, 1), (1, 3, 2), (3, 1, 3),  # target: three touching tiles
            (5, 7, 4), (7, 7, 4),              # two-tile decoy
            (3, 9, 5),                         # singleton decoy
        ):
            grid[row][col] = color
        info = proto.intermediate(grid)
        out = proto.solve(grid, finish="mark_largest_cluster")
        expected_target = {
            (r, c)
            for r0, c0 in ((0, 0), (0, 4), (4, 0))
            for r in range(r0, r0 + 4)
            for c in range(c0, c0 + 4)
        }
        self.assertEqual(set(map(tuple, info["target_cells"])), expected_target)
        self.assertTrue(all(out[r][c] == 9 for r, c in expected_target))
        self.assertEqual(out[10][14], 4)
        self.assertEqual(out[6][18], 5)
        self.assertEqual((len(out), len(out[0])), (16, 20))

    def test_all_supported_counts_are_prefix_stable_and_queries_reach_30x30(self):
        """Catches coupled counts, query cloning, or loss of the maximum-size stress case."""
        proto = _prototype()
        small = proto.sample_inputs(19, demos=2, queries=1)
        full = proto.sample_inputs(19, demos=6, queries=4)
        self.assertEqual(small["train"], full["train"][:2])
        self.assertEqual(small["test"], full["test"][:1])
        all_inputs = full["train"] + full["test"]
        self.assertEqual(len({_key(grid) for grid in all_inputs}), 10)
        self.assertEqual((len(full["test"][3]), len(full["test"][3][0])), (15, 15))
        for finish in proto.FINISHES:
            episode = proto.generate(19, {"finish": finish}, 6, 4)
            self.assertEqual(len(episode["train"]), 6)
            self.assertEqual(len(episode["test"]), 4)
            self.assertEqual((len(episode["test"][3]["output"]), len(episode["test"][3]["output"][0])), (30, 30))

    def test_two_demonstrations_identify_both_declared_settings(self):
        """Catches minimum lessons whose visible labels cannot select the episode rule."""
        proto = _prototype()
        inputs = proto.sample_inputs(0, demos=2, queries=4)["train"]
        canonical = [proto.solve(grid, finish="expand_only") for grid in inputs]
        composed = [proto.solve(grid, finish="mark_largest_cluster") for grid in inputs]
        self.assertNotEqual(canonical, composed)
        for chosen, labels in (("expand_only", canonical), ("mark_largest_cluster", composed)):
            survivors = []
            for candidate in proto.FINISHES:
                outputs = [proto.solve(grid, finish=candidate) for grid in inputs]
                if outputs == labels:
                    survivors.append(candidate)
            self.assertEqual(survivors, [chosen])

    def test_minimum_lesson_refutes_every_declared_plausible_shortcut(self):
        """Catches a wrong rule that fits both visible demos but changes a query."""
        proto = _prototype()
        demos = proto.sample_inputs(0, demos=2, queries=4)["train"]
        intended = [proto.solve(grid, finish="mark_largest_cluster") for grid in demos]
        self.assertGreaterEqual(len(proto.RIVAL_NAMES), 4)
        for rival in proto.RIVAL_NAMES:
            with self.subTest(rival=rival):
                observed = [proto.rival_solve(grid, rival) for grid in demos]
                self.assertNotEqual(observed, intended)

    def test_public_turn_reveals_one_masked_query_and_no_total_count_hint(self):
        """Catches future-query leakage or a first turn that changes with query count."""
        proto = _prototype()
        one = proto.generate(23, {"finish": "mark_largest_cluster"}, 3, 1)
        many = proto.generate(23, {"finish": "mark_largest_cluster"}, 3, 4)
        first_one = proto.public_turn(one, 0)
        first_many = proto.public_turn(many, 0)
        self.assertEqual(first_one, first_many)
        self.assertEqual(set(first_one), {"train", "test"})
        self.assertEqual(len(first_one["test"]), 1)
        self.assertEqual(set(first_one["test"][0]), {"input"})
        self.assertTrue(all(set(pair) == {"input", "output"} for pair in first_one["train"]))
        self.assertNotIn("settings", json.dumps(first_one))
        self.assertNotIn("program_solution", json.dumps(first_one))

    def test_validation_rejects_bool_bad_counts_and_unknown_settings(self):
        """Catches Python bool-as-int coercion and undeclared API expansion."""
        proto = _prototype()
        for bad_seed in (True, -1, 1.5, "1"):
            with self.subTest(seed=bad_seed), self.assertRaises((TypeError, ValueError)):
                proto.sample_inputs(bad_seed, 2, 1)
        for demos in (1, 7, True, 2.0):
            with self.subTest(demos=demos), self.assertRaises((TypeError, ValueError)):
                proto.sample_inputs(0, demos, 1)
        for queries in (0, 5, True, 1.0):
            with self.subTest(queries=queries), self.assertRaises((TypeError, ValueError)):
                proto.sample_inputs(0, 2, queries)
        for settings in ({}, {"finish": "unknown"}, {"finish": "expand_only", "x": 1}, None):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                proto.program(settings)

    def test_native_adapter_exports_adjacent_program_and_generate(self):
        """Catches a stale or cross-task adapter import."""
        proto = _prototype()
        adapter = _adapter()
        settings = {"finish": "mark_largest_cluster"}
        self.assertEqual(adapter.program(settings), proto.program(settings))
        self.assertEqual(adapter.generate(17, settings, 2, 4), proto.generate(17, settings, 2, 4))

    def test_racket_matches_python_for_both_settings_and_exact_30x30_query(self):
        """Catches unsupported Racket syntax or Python-only labels at the stress boundary."""
        proto = _prototype()
        grid = proto.sample_inputs(17, demos=2, queries=4)["test"][3]
        for finish in proto.FINISHES:
            settings = {"finish": finish}
            with self.subTest(finish=finish):
                self.assertEqual(self.apply(proto.program(settings), grid), proto.solve(grid, finish=finish))


    def test_public_writer_emits_racket_backed_views_in_public_id_order(self):
        """Catches writes in private seed/setting order before visible IDs are sorted."""
        import sys
        import tempfile

        verifier = _verifier()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            opened = []

            def audit(event, args):
                if event != "open" or not args:
                    return
                try:
                    path = Path(args[0]).resolve()
                except (TypeError, OSError):
                    return
                mode = args[1] if len(args) > 1 else None
                if (
                    path.is_relative_to(root)
                    and path.name.startswith("challenge-")
                    and path.suffix == ".json"
                    and isinstance(mode, str)
                    and "w" in mode
                ):
                    opened.append(path.name)

            sys.addaudithook(audit)
            report = verifier.build_report(root, seeds=(17, 0))
            export = report["public_export"]
            expected_names = [f"challenge-{value}.json" for value in export["write_order"]]
            self.assertEqual(opened, expected_names)
            self.assertEqual(export["write_order"], sorted(export["write_order"]))
            self.assertEqual(len(opened), 16)
            self.assertEqual(
                sorted(path.name for path in (root / "public").iterdir()),
                expected_names,
            )

    def test_self_audit_tool_executes_racket_and_rejects_all_declared_rivals(self):
        """Catches a future audit that reports Python-only or lets a visible-demo shortcut survive."""
        import tempfile

        verifier = _verifier()
        with tempfile.TemporaryDirectory() as directory:
            report = verifier.build_report(Path(directory), seeds=(0,))
            self.assertEqual(report["schema"], "ebe910be6876-largest-cluster-self-audit-v1")
            self.assertTrue(report["racket"]["protected"])
            self.assertGreaterEqual(report["racket_evaluations"], 1)
            self.assertEqual(report["harmful_survivors"], [])
            self.assertTrue(report["all_python_racket_exact"])
            self.assertTrue(report["all_public_turns_masked"])
            self.assertTrue((Path(directory) / "self-audit.json").is_file())

    def test_wrong_input_component_counterfactual_changes_the_final_output(self):
        """Catches a cosmetic two-stage claim whose ablation leaves the answer unchanged."""
        proto = _prototype()
        grid = proto.sample_inputs(0, demos=2, queries=4)["train"][0]
        intended = self.apply(proto.program({"finish": "mark_largest_cluster"}), grid)
        counterfactual = self.apply(proto.counterfactual_program(), grid)
        self.assertEqual(intended, proto.solve(grid, finish="mark_largest_cluster"))
        self.assertEqual(counterfactual, proto.rival_solve(grid, "first_input_marker"))
        self.assertNotEqual(counterfactual, intended)


if __name__ == "__main__":
    unittest.main()
