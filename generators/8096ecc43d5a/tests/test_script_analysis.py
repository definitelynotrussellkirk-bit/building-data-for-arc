"""Independent authoring-tool checks, using recorded canonical labels only."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from reviewer_support import find_root, load_selected_generator


ROOT = find_root(__file__)
_, GENERATOR_SOURCE, _ = load_selected_generator("8096ecc43d5a", root=ROOT)


def selected_tool_path():
    direct = GENERATOR_SOURCE.parent / "workspace/analyze_script_maps.py"
    if direct.is_file():
        return direct
    manifest_path = ROOT / "RUNTIME_MANIFEST.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        library_path = "generators/8096ecc43d5a/workspace/analyze_script_maps.py"
        selected = [row for row in manifest.get("files", []) if row.get("library_path") == library_path]
        if len(selected) == 1:
            relative = Path(selected[0]["runtime_path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Unsafe authoring-tool runtime path")
            return ROOT / relative
    return direct  # The test reports a missing selected tool rather than guessing a sibling tree.


TOOL_PATH = selected_tool_path()
EXPECTED_MAPS = [
    (1, 4, 2, 6),  # CW, horizontal, half turn, vertical
    (1, 6, 0, 4),  # CW, vertical, identity, horizontal
    (3, 4, 0, 4),  # CCW, horizontal, identity, horizontal
    (3, 6, 2, 6),  # CCW, vertical, half turn, vertical
]


def singleton_fixture():
    """Four explicit labels on an asymmetric L; no generator/oracle import."""
    outputs = (
        [[8, 8], [8, 0], [8, 0]],
        [[0, 0, 8], [8, 8, 8]],
        [[8, 8, 8], [0, 0, 8]],
        [[8, 8, 8], [8, 0, 0]],
    )
    return [
        {
            "input": [[code, 0, 0], [0, 0, 0], [8, 0, 0], [8, 8, 8]],
            "output": output,
        }
        for code, output in enumerate(outputs, 1)
    ]


class ScriptMapAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = None

    def load_tool(self):
        self.assertTrue(TOOL_PATH.is_file(), "The script-map authoring tool is missing")
        if self.__class__.tool is None:
            spec = importlib.util.spec_from_file_location("task_script_map_analysis", TOOL_PATH)
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.__class__.tool = module
        return self.__class__.tool

    def test_asymmetric_singletons_identify_one_constant_map(self):
        tool = self.load_tool()
        self.assertEqual(tool.enumerate_fitting_maps(singleton_fixture()), [EXPECTED_MAPS[0]])

    def test_inconsistent_label_has_no_fitting_map(self):
        tool = self.load_tool()
        pairs = singleton_fixture()
        pairs[0]["output"] = [[8]]
        self.assertEqual(tool.enumerate_fitting_maps(pairs), [])

    def test_empty_population_does_not_become_vacuous_evidence(self):
        tool = self.load_tool()
        with self.assertRaisesRegex(ValueError, "labeled pair"):
            tool.enumerate_fitting_maps([])

    def test_codes_ignore_gaps_and_compose_in_order(self):
        tool = self.load_tool()
        grid = [[0, 2, 0, 1], [0, 0, 0, 0], [8, 0, 0, 0], [8, 8, 8, 0]]
        before = [row[:] for row in grid]
        self.assertEqual(tool.solve_mapping(grid, EXPECTED_MAPS[0]), [[8, 0], [8, 0], [8, 8]])
        self.assertEqual(grid, before)

    def test_recorded_canonical_labels_leave_exactly_four_maps(self):
        tool = self.load_tool()
        context = tool.read_context()
        self.assertEqual(len(context["pairs"]), 4)
        self.assertEqual(tool.enumerate_fitting_maps(context["pairs"]), EXPECTED_MAPS)
        self.assertEqual(context["identity"]["canonical_rule_hash"], "04788c0240d6")
        self.assertEqual(
            [(p["split"], p["pair_index"]) for p in context["pairs"]],
            [("train", 0), ("train", 1), ("train", 2), ("test", 0)],
        )

    def test_rich_pools_cover_all_three_nonzero_map_masks(self):
        tool = self.load_tool()
        result = tool.derive_rich_pools(EXPECTED_MAPS, min_length=4, max_length=6)
        pools = result["pools"]
        self.assertEqual(set(pools), {"011", "101", "110"})
        self.assertEqual({key: len(value) for key, value in pools.items()},
                         {"011": 14, "101": 153, "110": 153})
        representatives = {
            "011": [(3, 4, 1, 1, 1), (2, 2, 3, 4, 1)],
            "101": [(2, 2, 4, 1), (4, 1, 1, 1)],
            "110": [(2, 1, 1, 1), (2, 1, 3, 3)],
        }
        for mask, scripts in representatives.items():
            actual = {tuple(row["codes"]) for row in pools[mask]}
            self.assertTrue(set(scripts) <= actual)
        self.assertIn("first_three_only", result["required_rival_refutations"])
        self.assertIn("collapse_adjacent_codes", result["required_rival_refutations"])

    def test_cli_binds_sources_from_an_unrelated_working_directory(self):
        self.load_tool()
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "analysis.json"
            completed = subprocess.run(
                [sys.executable, str(TOOL_PATH), "--out", str(output)],
                cwd=temporary, text=True, capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["task_id"], "8096ecc43d5a")
        self.assertEqual(report["canonical_labeled_pairs"], 4)
        self.assertEqual(report["candidate_maps_examined"], 4096)
        self.assertEqual(report["fitting_map_count"], 4)
        self.assertFalse(report["reference_execution_performed"])
        self.assertEqual(len(report["source_identity"]["generator_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
