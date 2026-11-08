from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest

from reviewer_support import canonical_path, find_root

TASK = "b7e4aaffabac"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
PROTOTYPE_PATH = HOME / "prototype.py"
ADAPTER_PATH = HOME / "adapter.py"
PROMOTION_PATH = HOME / "promotion.json"
VERIFY_PATH = HOME / "verify.py"
GENERATOR = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def _load_exact(path: Path, label: str):
    body = path.read_bytes()
    name = f"_{TASK}_{label}_" + hashlib.sha256(str(path).encode() + body).hexdigest()
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


def _prototype():
    return _load_exact(PROTOTYPE_PATH, "prototype")


def _adapter():
    return _load_exact(ADAPTER_PATH, "adapter")


def _canonical_program() -> str:
    programs = {
        json.loads(line)["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("task_id") == TASK
    }
    if len(programs) != 1:
        raise AssertionError(f"expected one canonical program, found {len(programs)}")
    return next(iter(programs))


def _shape(grid):
    return len(grid), len(grid[0])


def _changed(before, after):
    return {
        (row, col)
        for row in range(len(before))
        for col in range(len(before[0]))
        if before[row][col] != after[row][col]
    }


class ParametricBridgeTests(unittest.TestCase):
    def test_contract_files_exist_and_default_program_is_exact_canonical(self):
        self.assertTrue(PROTOTYPE_PATH.is_file())
        self.assertTrue(ADAPTER_PATH.is_file())
        self.assertTrue(PROMOTION_PATH.is_file())
        prototype = _prototype()
        adapter = _adapter()
        contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["schema"], "arcpuzzles-parametric-adapter-v1")
        self.assertEqual(contract["parameters"], {"overlap_policy": ["trimmed", "full"]})
        self.assertEqual(contract["default"], {"overlap_policy": "trimmed"})
        self.assertEqual(contract["limits"], {"demos": [2, 6], "queries": [4, 4]})
        canonical = _canonical_program()
        self.assertEqual(prototype.canonical_program(), canonical)
        self.assertEqual(prototype.program_for("trimmed"), canonical)
        self.assertEqual(adapter.program({"overlap_policy": "trimmed"}), canonical)

    def test_full_program_changes_only_the_four_overlap_bounds(self):
        prototype = _prototype()
        canonical = prototype.program_for("trimmed")
        full = prototype.program_for("full")
        expected = canonical
        replacements = {
            "(lo (+ (max lr1 rr1) 1))": "(lo (max lr1 rr1))",
            "(hi (- (min lr2 rr2) 1))": "(hi (min lr2 rr2))",
            "(lo (+ (max tc1 bc1) 1))": "(lo (max tc1 bc1))",
            "(hi (- (min tc2 bc2) 1))": "(hi (min tc2 bc2))",
        }
        for old, new in replacements.items():
            self.assertEqual(expected.count(old), 1, old)
            expected = expected.replace(old, new, 1)
        self.assertEqual(full, expected)
        self.assertNotEqual(full, canonical)

    def test_counts_are_prefix_stable_inputs_are_matched_and_last_query_is_30x30(self):
        prototype = _prototype()
        adapter = _adapter()
        longest = prototype.build_claimed_episode(17, "trimmed", 6, 4)
        expected_queries = [pair["input"] for pair in longest["test"]]
        for demos in range(2, 7):
            trimmed = prototype.build_claimed_episode(17, "trimmed", demos, 4)
            full = prototype.build_claimed_episode(17, "full", demos, 4)
            adapted = adapter.generate(17, {"overlap_policy": "trimmed"}, demos, 4)
            self.assertEqual(len(trimmed["train"]), demos)
            self.assertEqual(len(trimmed["test"]), 4)
            self.assertEqual(trimmed["train"], longest["train"][:demos])
            self.assertEqual([pair["input"] for pair in trimmed["test"]], expected_queries)
            self.assertEqual(
                [pair["input"] for split in ("train", "test") for pair in trimmed[split]],
                [pair["input"] for split in ("train", "test") for pair in full[split]],
            )
            self.assertEqual(adapted["train"], trimmed["train"])
            self.assertEqual(adapted["test"], trimmed["test"])
            self.assertEqual(adapted["program_solution"], trimmed["program_solution"])
            all_inputs = [
                json.dumps(pair["input"], separators=(",", ":"))
                for split in ("train", "test")
                for pair in trimmed[split]
            ]
            self.assertEqual(len(all_inputs), len(set(all_inputs)))
            self.assertEqual(_shape(trimmed["test"][-1]["input"]), (30, 30))
            self.assertGreater(len(_changed(trimmed["test"][-1]["input"], trimmed["test"][-1]["output"])), 30)

    def test_minimum_demonstrations_identify_each_setting_and_cover_both_orientations(self):
        prototype = _prototype()
        for setting in prototype.ALLOWED_SETTINGS:
            episode = prototype.build_claimed_episode(0, setting, 2, 4)
            self.assertEqual(prototype.surviving_settings(episode["train"]), [setting])
            intermediates = [prototype.analyze_intermediate(pair["input"]) for pair in episode["train"]]
            self.assertEqual([row["orientation"] for row in intermediates], ["horizontal", "vertical"])
            self.assertTrue(any(row["offset"] for row in intermediates))
            self.assertTrue(any(row["edge_touch"] for row in intermediates))

    def test_python_semantics_match_claims_and_policy_delta_is_exact_raw_span_border(self):
        prototype = _prototype()
        for seed in (0, 1, 17, 2**63 - 1):
            trimmed = prototype.build_claimed_episode(seed, "trimmed", 6, 4)
            full = prototype.build_claimed_episode(seed, "full", 6, 4)
            for trim_pair, full_pair in zip(
                trimmed["train"] + trimmed["test"],
                full["train"] + full["test"],
            ):
                grid = trim_pair["input"]
                self.assertEqual(grid, full_pair["input"])
                self.assertEqual(trim_pair["output"], prototype.apply_python(grid, "trimmed"))
                self.assertEqual(full_pair["output"], prototype.apply_python(grid, "full"))
                info = prototype.analyze_intermediate(grid)
                trim_changed = _changed(grid, trim_pair["output"])
                full_changed = _changed(grid, full_pair["output"])
                self.assertEqual(trim_changed, set(map(tuple, info["trimmed_cells"])))
                self.assertEqual(full_changed, set(map(tuple, info["full_cells"])))
                self.assertTrue(trim_changed < full_changed)
                self.assertEqual(len(full_changed - trim_changed), 2 * info["gap"])
                self.assertEqual(GENERATOR.self_check(grid), [])
                self.assertIsNone(GENERATOR.canonical_profile_signature(grid))
                self.assertEqual(trim_pair["output"], GENERATOR.rule_mirror(grid))

    def test_visible_bytes_mask_settings_program_and_query_answers(self):
        prototype = _prototype()
        episode = prototype.build_claimed_episode(23, "full", 3, 4)
        visible = prototype.public_challenge(episode, query_indices=[0])
        self.assertEqual(set(visible), {"train", "test"})
        self.assertEqual(len(visible["train"]), 3)
        self.assertEqual(len(visible["test"]), 1)
        self.assertEqual(set(visible["test"][0]), {"input"})
        identifier = prototype.public_id(episode, query_indices=[0])
        mutated = deepcopy(episode)
        mutated["settings"] = {"overlap_policy": "trimmed"}
        mutated["program"] = "private mutation"
        mutated["program_solution"] = "private mutation"
        mutated["test"][0]["output"][0][0] = (mutated["test"][0]["output"][0][0] + 1) % 10
        self.assertEqual(prototype.public_id(mutated, query_indices=[0]), identifier)
        mutated["test"][0]["input"][0][0] = (mutated["test"][0]["input"][0][0] + 1) % 10
        self.assertNotEqual(prototype.public_id(mutated, query_indices=[0]), identifier)


    def test_orientation_shortcut_programs_are_source_guarded(self):
        prototype = _prototype()
        marker = "(define horizontal (or (< c2a c1b) (< c2b c1a)))"
        for setting in prototype.ALLOWED_SETTINGS:
            selected = prototype.program_for(setting)
            self.assertEqual(selected.count(marker), 1)
            horizontal = prototype.orientation_shortcut_program(setting, "horizontal")
            vertical = prototype.orientation_shortcut_program(setting, "vertical")
            self.assertEqual(horizontal, selected.replace(marker, "(define horizontal #t)", 1))
            self.assertEqual(vertical, selected.replace(marker, "(define horizontal #f)", 1))

    def test_verifier_materializes_protected_racket_evidence_and_rejects_shortcuts(self):
        self.assertTrue(VERIFY_PATH.is_file())
        verify = _load_exact(VERIFY_PATH, "verify")
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "evidence"
            report = verify.verify(seed=20261024, out_dir=out)
            self.assertEqual(report["schema"], "b7e4aaffabac-overlap-policy-verification-v1")
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["racket"]["backend"], "racket")
            self.assertIs(report["racket"]["protected"], True)
            self.assertEqual(report["counts"], {
                "settings": 2,
                "demonstrations_per_setting": 3,
                "queries_per_setting": 4,
                "boundary_demo_counts": [2, 6],
                "primary_racket_checked_pairs": 14,
                "boundary_racket_checked_pairs": 32,
                "racket_checked_pairs": 46,
                "racket_program_evaluations": 88,
            })
            self.assertEqual(
                {(row["setting"], row["demos"]) for row in report["boundary_replays"]},
                {(setting, demos) for setting in verify.prototype.ALLOWED_SETTINGS for demos in (2, 6)},
            )
            self.assertTrue(all(row["selected_racket_matches_all_claims"] for row in report["boundary_replays"]))
            self.assertTrue(all(row["declared_survivors_from_demos"] == [row["setting"]] for row in report["boundary_replays"]))
            self.assertEqual(report["maximum_query"]["shape"], [30, 30])
            self.assertTrue(report["maximum_query"]["selected_racket_matches_claim"])
            self.assertEqual({row["setting"] for row in report["settings"]}, set(verify.prototype.ALLOWED_SETTINGS))
            for row in report["settings"]:
                self.assertEqual(row["declared_survivors_from_demos"], [row["setting"]])
                by_name = {rival["name"]: rival for rival in row["rivals"]}
                self.assertTrue(by_name["alternate_setting"]["demo_mismatch_indices"])
                self.assertTrue(by_name["horizontal_only"]["demo_mismatch_indices"])
                self.assertTrue(by_name["vertical_only"]["demo_mismatch_indices"])
            self.assertEqual(len(report["public_challenges"]), 2)
            self.assertTrue((out / "private" / "verification.json").is_file())
            self.assertEqual(len(list((out / "public").glob("*.json"))), 2)
            with self.assertRaises(ValueError):
                verify.verify(seed=0, out_dir=out)

    def test_seed_settings_and_counts_fail_closed_with_bool_rejected(self):
        prototype = _prototype()
        adapter = _adapter()
        bad_settings = [
            None,
            {},
            {"overlap_policy": "bad"},
            {"overlap_policy": "trimmed", "extra": 1},
            {"overlap_policy": 1},
        ]
        for value in bad_settings:
            if value is None:
                self.assertEqual(prototype.validate_settings(value), "trimmed")
            else:
                with self.assertRaises(ValueError):
                    prototype.validate_settings(value)
        for seed in (-1, True, 2**63, 1.5, "0"):
            with self.assertRaises(ValueError):
                prototype.build_claimed_episode(seed, "trimmed", 2, 4)
        for demos in (1, 7, True, 2.0):
            with self.assertRaises(ValueError):
                prototype.build_claimed_episode(0, "trimmed", demos, 4)
        for queries in (0, 3, 5, True, 4.0):
            with self.assertRaises(ValueError):
                prototype.build_claimed_episode(0, "trimmed", 2, queries)
        with self.assertRaises(ValueError):
            adapter.generate(0, {"overlap_policy": "full"}, 2, 3)


if __name__ == "__main__":
    unittest.main()
