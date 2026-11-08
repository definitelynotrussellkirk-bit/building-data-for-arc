"""Regressions for the independent adversarial review's serialized mutations."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location("_marker_area_verifier_tests", SOURCE)
prototype = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)


class MarkerAreaVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = prototype.RacketRunner().__enter__()
        cls.episode = prototype.generate_verified(193, {"minimum_marker_area": 2},
                                                  demos=2, queries=1, runner=cls.runner)

    @classmethod
    def tearDownClass(cls):
        cls.runner.__exit__(None, None, None)

    def check_mutation_rejected(self, mutate):
        episode = copy.deepcopy(self.episode)
        mutate(episode)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "batch"
            prototype.write_batch([episode], out)
            with self.assertRaises(ValueError):
                prototype.verify_batch(out, self.runner)

    def test_certificate_rejects_float_and_boolean_integer_coercion(self):
        mutations = (
            lambda e: e["certificate"]["parameter_survivors"][0].update(minimum_marker_area=2.0),
            lambda e: e["certificate"].update(query_identifiable=[1]),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                self.check_mutation_rejected(mutate)

    def test_extra_empty_directories_reject(self):
        for name in ("public/private-parameter-is-two", "private/extra", "extra"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "batch"
                prototype.write_batch([self.episode], out)
                (out / name).mkdir()
                with self.assertRaises(ValueError):
                    prototype.verify_batch(out, self.runner)

    def test_source_binding_includes_executable_runtime_closure(self):
        bindings = prototype.source_bindings()
        required = {
            "shared/runtime/puzzle_generators/base.py",
            "shared/runtime/puzzle_generators/helpers/grid.py",
            "shared/tools/comment_solutions.py",
            "shared/runtime/arc_repl/racket_prelude/heightmap.rkt",
            "shared/runtime/arc_repl/racket_prelude/layers.rkt",
            "shared/runtime/arc_repl/racket_prelude/bank-helpers.rkt",
        }
        self.assertFalse(required - set(bindings), required - set(bindings))
        for path in (prototype.ROOT / "shared/runtime").rglob("*"):
            if path.is_file() and path.suffix in (".py", ".rkt"):
                self.assertIn(path.relative_to(prototype.ROOT).as_posix(), bindings)

    def test_recorded_seed_must_reproduce_the_inputs(self):
        self.check_mutation_rejected(lambda e: e.update(seed=194))

    def test_claimed_runtime_is_checked_without_binding_machine_paths(self):
        self.check_mutation_rejected(lambda e: e.update(runtime_identity={"backend": "python"}))
        moved = copy.deepcopy(self.episode)
        for key in moved["runtime_identity"]:
            if key.endswith("_path"):
                moved["runtime_identity"][key] = "/a/different/checkout/" + key
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "batch"
            prototype.write_batch([moved], out)
            self.assertEqual(prototype.verify_batch(out, self.runner)["status"], "passed")


if __name__ == "__main__":
    unittest.main()
