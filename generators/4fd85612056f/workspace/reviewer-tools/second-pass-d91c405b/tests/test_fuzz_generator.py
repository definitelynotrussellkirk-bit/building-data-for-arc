from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve()
PACKAGE = HERE.parents[2]
TOOL = HERE.parents[1] / "fuzz_generator.py"
GENERATOR = PACKAGE / "solve/source/generator.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("fuzz_generator", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FuzzGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()

    def test_quick_structural_fuzz_is_clean(self):
        report = self.tool.run_fuzz(
            GENERATOR,
            default_seed_count=3,
            default_index_count=12,
            override_seed_count=1,
            schedule_seed_count=3,
        )
        self.assertEqual(report["issues"], [])
        self.assertEqual(report["default_cases"], 3 * 12 * 4)
        self.assertEqual(report["legal_override_cases"], 1 * 4 * 4 * 4 * 4 * 2)
        self.assertEqual(report["lesson_query_cases"], 3 * 4 * 10 * 5)

    def test_mutated_decoy_shape_is_detected(self):
        text = GENERATOR.read_text()
        old = """_HEAVY_DECOY = (\n    (0, 0), (0, 1), (0, 2),\n    (1, 0), (1, 1), (1, 2), (1, 3),\n)"""
        new = """_HEAVY_DECOY = (\n    (0, 0), (0, 1), (0, 2), (0, 3),\n    (1, 0), (1, 1), (1, 2), (1, 3),\n)"""
        self.assertIn(old, text)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "generator.py"
            path.write_text(text.replace(old, new))
            report = self.tool.run_fuzz(
                path,
                default_seed_count=1,
                default_index_count=6,
                override_seed_count=0,
                schedule_seed_count=0,
            )
        self.assertTrue(report["issues"])
        self.assertTrue(any("first_nonrectangular" in str(issue) for issue in report["issues"]))


if __name__ == "__main__":
    unittest.main()
