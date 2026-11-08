"""Prototype-only checks; canonical generator repair coverage lives elsewhere."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from reviewer_support import find_root

ROOT = find_root(__file__)
PROTOTYPE = ROOT / "generators/a0fcc6f3396e/workspace/parametric/prototype.py"


def load_prototype():
    assert PROTOTYPE.is_file(), "The runnable task-local parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("a0fcc6f3396e_parametric", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ParametricPrototypeTests(unittest.TestCase):
    def test_cli_refuses_existing_evidence_without_modifying_it(self):
        load_prototype()
        with tempfile.TemporaryDirectory(prefix="a0fcc6f3396e-evidence-preservation-") as temp:
            output = Path(temp)
            sentinel = output / "retained-evidence.txt"
            sentinel.write_text("previous evidence\n", encoding="utf-8")
            before = {str(path.relative_to(output)): path.read_bytes()
                      for path in output.rglob("*") if path.is_file()}
            attempt = subprocess.run([sys.executable, str(PROTOTYPE), "--out", str(output)],
                                     capture_output=True, text=True, timeout=20)
            assert attempt.returncode != 0
            assert "FileExistsError" in attempt.stderr
            after = {str(path.relative_to(output)): path.read_bytes()
                     for path in output.rglob("*") if path.is_file()}
            assert after == before, "A refused CLI run changed previously retained evidence"

    def test_default_preserves_exact_authority_and_rejects_undeclared_colors(self):
        prototype = load_prototype()
        canonical = prototype.canonical_source(ROOT)
        assert prototype.materialize_program(canonical, 8) == canonical
        assert prototype.materialize_program(canonical, 3) != canonical
        for invalid in (True, 3.0, "3", 0, 2, 9, None):
            with self.assertRaises(ValueError):
                prototype.materialize_program(canonical, invalid)

    def test_seeded_episode_inputs_are_lawful_unique_and_cover_odd_positions(self):
        prototype = load_prototype()
        episodes = [prototype.episode_inputs(seed) for seed in (0, 1)]
        assert {episode["parameters"]["output_color"] for episode in episodes} == {3, 8}
        for seed, episode in zip((0, 1), episodes):
            assert episode == prototype.episode_inputs(seed)
            inputs = episode["inputs"]
            assert len(inputs) == 4
            assert len({json.dumps(grid) for grid in inputs}) == 4
            odd_positions = []
            for grid in inputs:
                h, w = len(grid), len(grid[0])
                assert 1 <= h <= 30 and 1 <= w <= 30
                assert all(len(row) == w for row in grid)
                assert all(type(c) is int and c in (0, 2, 9) for row in grid for c in row)
                seams = [c for c in range(w) if all(row[c] == 9 for row in grid)]
                assert len(seams) == 2
                dimensions = []
                bounds = [-1, *seams, w]
                for left, right in zip(bounds, bounds[1:]):
                    cells = [(r, c) for r, row in enumerate(grid)
                             for c in range(left + 1, right) if row[c]]
                    assert len(cells) == 4
                    rs, cs = {r for r, _ in cells}, {c for _, c in cells}
                    assert len(rs) == len(cs) == 2
                    assert set(cells) == {(r, c) for r in rs for c in cs}
                    dimensions.append((max(rs) - min(rs) + 1, max(cs) - min(cs) + 1))
                counts = Counter(dimensions)
                assert sorted(counts.values()) == [1, 2]
                odd_positions.append(next(i for i, shape in enumerate(dimensions) if counts[shape] == 1))
            assert set(odd_positions[:3]) == {0, 1, 2}

    def test_partial_setting_coverage_preserves_receipts_without_a_pass(self):
        prototype = load_prototype()

        def synthetic_label_results(root, output, request):
            # Isolate the real evidence writer and verdict from costly runtime
            # staging. These explicit test doubles do not test Racket semantics;
            # the separate executed-label regression owns that responsibility.
            canonical = {f"canonical:{i}": pair["output"] for i, pair in enumerate(
                prototype.canonical_pairs(prototype.TASK_ID, root=root, labeled_only=True))}
            programs = {}
            for setting, source in request["programs"].items():
                outputs = {name: canonical[name] if setting == "8" and name in canonical
                           else [[int(setting)]] for name in request["inputs"]}
                programs[setting] = {
                    "outputs": outputs, "program_sha256": prototype.text_sha256(source),
                    "callable": "synthetic-test-response; no Racket execution",
                    "callable_sha256": prototype.text_sha256("synthetic-test-response; no Racket execution")}
            return {"programs": programs, "evaluation_count": 0,
                    "runtime_identity": {"kind": "synthetic_test_double", "executed": False}}

        for seed, chosen, missing in ((0, 3, 8), (1, 8, 3)):
            with self.subTest(seed=seed), tempfile.TemporaryDirectory(
                    prefix="a0fcc6f3396e-partial-evidence-") as temp:
                evidence = Path(temp) / "parametric"
                with patch.object(prototype, "execute_labels", side_effect=synthetic_label_results):
                    report = prototype.write_evidence(evidence, seeds=(seed,), root=ROOT)
                assert report["canonical_parity"]["passed"]
                assert report["settings_witness"]["outputs_differ"]
                assert report["settings_covered"] == [chosen]
                assert not report["episodes"][0]["declared_parameter_ambiguity"]
                public = json.loads((evidence / report["episodes"][0]["public_path"]).read_text())
                private = json.loads((evidence / report["episodes"][0]["private_path"]).read_text())
                assert len(public["train"]) == 3 and len(public["test"]) == 1
                assert private["parameters"]["output_color"] == chosen
                assert len(private["test_outputs"]) == 1
                assert report["status"] == "prototype_partial"
                assert report["missing_episode_settings"] == [missing]
                retained = json.loads((evidence / "result.json").read_text())
                assert retained["status"] == "prototype_partial"
                assert retained["missing_episode_settings"] == [missing]

    def test_executed_racket_labels_distinguish_settings_and_keep_queries_private(self):
        prototype = load_prototype()
        with tempfile.TemporaryDirectory(prefix="a0fcc6f3396e-parametric-test-") as temp:
            evidence = Path(temp) / "parametric"
            report = prototype.write_evidence(evidence, seeds=(0, 1), root=ROOT)
            assert report["status"] == "prototype_passed"
            assert report["canonical_parity"]["passed"]
            assert report["canonical_parity"]["labeled_pairs"] == 3
            assert report["settings_witness"]["outputs_differ"]
            assert report["settings_covered"] == [3, 8]
            assert report["missing_episode_settings"] == []
            assert report["racket_evaluation_count"] == 24
            for episode in report["episodes"]:
                public = json.loads((evidence / episode["public_path"]).read_text())
                private = json.loads((evidence / episode["private_path"]).read_text())
                assert set(public) == {"train", "test"}
                assert len(public["train"]) == 3 and len(public["test"]) == 1
                assert all(set(pair) == {"input", "output"} for pair in public["train"])
                assert all(set(pair) == {"input"} for pair in public["test"])
                chosen = private["parameters"]["output_color"]
                assert len(private["test_outputs"]) == 1
                assert private["program_sha256"] == prototype.text_sha256(private["program"])
                for pair in public["train"]:
                    assert {cell for row in pair["output"] for cell in row} == {chosen}
                assert {cell for row in private["test_outputs"][0] for cell in row} == {chosen}
                assert private["rivals"][str(chosen)]["status"] == "survived_all"
                rival = 3 if chosen == 8 else 8
                assert private["rivals"][str(rival)]["status"] == "refuted_by_demonstrations"
                assert private["rivals"][str(rival)]["demonstration_mismatch_indices"] == [0, 1, 2]
                assert not private["declared_parameter_ambiguity"]
            with self.assertRaises(FileExistsError):
                prototype.write_evidence(evidence, seeds=(0, 1), root=ROOT)


if __name__ == "__main__":
    unittest.main()
