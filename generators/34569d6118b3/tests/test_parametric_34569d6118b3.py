"""Task-local proposed variants; these tests do not certify canonical approval."""
from __future__ import annotations

import copy
from contextlib import ExitStack
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

CASE = unittest.TestCase()


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO = TASK_ROOT.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
PROTOTYPE = TASK_ROOT / "workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location("parametric_34569d6118b3", PROTOTYPE)
P = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = P
SPEC.loader.exec_module(P)


def witness():
    return [
        [1, 0, 2, 0, 5, 5, 5, 0, 5, 5, 5],
        [0, 0, 0, 0, 5, 0, 0, 0, 0, 5, 0],
        [0, 0, 0, 0, 5, 5, 0, 0, 0, 0, 5],
        [0] * 11,
        [0, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0],
    ]


def frozen(grid):
    return tuple(map(tuple, grid))


def private_example(setting=P.DEFAULT_SETTING):
    inputs = P.sample_inputs(42426, demo_count=1, query_count=1)
    program = P.reference_program(setting)
    return {
        "train": [{"input": grid, "output": P.python_mirror(grid, setting)}
                  for grid in inputs["train_inputs"]],
        "test": [{"input": grid, "output": P.python_mirror(grid, setting)}
                 for grid in inputs["test_inputs"]],
        "seed": 42426,
        "parameters": setting.as_dict(),
        "reference_program": program,
        "reference_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "status": "synthetic_writer_unit_fixture_not_execution_evidence",
    }


def test_canonical_default_is_exact_original_text_and_variants_are_surgical():
    with (REPO / "shared/data/canonical/puzzles.jsonl").open() as handle:
        rows = [json.loads(line) for line in handle]
    canonical = [row["program_solution"] for row in rows if row.get("task_id") == P.TASK_ID]
    assert canonical and len(set(canonical)) == 1
    assert P.reference_program(P.DEFAULT_SETTING) == canonical[0]
    assert hashlib.sha256(canonical[0].encode()).hexdigest() == P.CANONICAL_SHA256
    assert len({P.reference_program(setting) for setting in P.ALL_SETTINGS}) == 4
    assert P.reference_program(P.Settings("reverse", False)) == canonical[0].replace(
        "(list-ref template-mats i)",
        "(list-ref template-mats (- (length template-mats) 1 i))",
    )
    assert P.reference_program(P.Settings("forward", True)) == canonical[0].replace(
        "(list-ref (list-ref template tr) tc)",
        "(list-ref (list-ref template tr) (- tmpl-w 1 tc))",
    )


def test_lawful_witness_distinguishes_every_setting_and_default_matches_generator():
    grid = witness()
    assert not P.GENERATOR._parse_scene(grid)["errors"]
    assert len({frozen(P.python_mirror(grid, setting)) for setting in P.ALL_SETTINGS}) == 4
    assert P.python_mirror(grid, P.DEFAULT_SETTING) == P.GENERATOR.rule_mirror(grid)
    for setting in P.ALL_SETTINGS:
        demos = [{"input": grid, "output": P.python_mirror(grid, setting)}]
        assert P.surviving_settings(demos) == (setting,)


def test_compact_masks_are_ambiguous_and_query_answers_cannot_resolve_them():
    grid = P.GENERATOR.generate(7, 0, scene_profile="compact_two_color")
    demos = [{"input": grid, "output": P.python_mirror(grid, P.DEFAULT_SETTING)}]
    assert set(P.surviving_settings(demos)) == {
        P.DEFAULT_SETTING, P.Settings("reverse", True),
    }
    result = P.check_query_identifiability(demos, [witness()])
    assert len(result["survivors"]) == 2
    assert result["queries"][0]["identifiable"] is False
    # The checker accepts query inputs only, and never reads a hidden output.
    demos_with_private_noise = copy.deepcopy(demos)
    demos_with_private_noise[0]["query_answer"] = P.python_mirror(witness(), P.DEFAULT_SETTING)
    assert P.check_query_identifiability(demos_with_private_noise, [witness()]) == result


def test_sampling_defaults_distinctness_rejections_and_independent_counts():
    sample = P.sample_inputs(42426)
    assert len(sample["train_inputs"]) == 3 and len(sample["test_inputs"]) == 4
    all_inputs = sample["train_inputs"] + sample["test_inputs"]
    assert len({frozen(grid) for grid in all_inputs}) == 7
    assert len({frozen(P.python_mirror(all_inputs[0], setting)) for setting in P.ALL_SETTINGS}) == 4
    assert sample["rejections"][0]["reason"] == "ambiguous_first_demonstration"
    assert sample == P.sample_inputs(42426)
    changed = P.sample_inputs(42426, demo_count=1, query_count=4)
    assert (len(changed["train_inputs"]), len(changed["test_inputs"])) == (1, 4)
    wide = P.sample_inputs(42426, demo_count=4, query_count=1)
    assert (len(wide["train_inputs"]), len(wide["test_inputs"])) == (4, 1)


def test_bounded_duplicate_sampling_fails_without_short_batch():
    fixed = P.GENERATOR.generate(7, 0, scene_profile="three_color_square")
    assert len({frozen(P.python_mirror(fixed, setting)) for setting in P.ALL_SETTINGS}) == 4
    with patch.object(P.GENERATOR, "generate", lambda *args, **kwargs: copy.deepcopy(fixed)):
        with CASE.assertRaisesRegex(P.SamplingError, "requested 2 distinct inputs") as caught:
            P.sample_inputs(7, demo_count=1, query_count=1, max_attempts=3)
    assert caught.exception.rejections[-1]["reason"] == "duplicate_input"


def test_invalid_counts_fail_closed():
    for kwargs in ({"demo_count": 0}, {"query_count": 0}, {"demo_count": True},
                   {"query_count": 33}, {"max_attempts": 1}):
        with CASE.assertRaises(ValueError):
            P.sample_inputs(7, **kwargs)


def test_invalid_settings_fail_closed():
    for order, mirror in (("random", False), ("forward", 1), ("forward", "false")):
        with CASE.assertRaises(ValueError):
            P.Settings(order, mirror)


def test_public_bytes_and_name_ignore_private_metadata_and_query_answers(tmp_path):
    episode = private_example()
    altered = copy.deepcopy(episode)
    altered.update(seed=-999, parameters={"secret": "do-not-export"}, reference_program="PRIVATE")
    altered["test"][0]["output"] = [[9]]
    assert P.public_challenge_id(altered) == P.public_challenge_id(episode)
    assert P.public_challenge_bytes(altered) == P.public_challenge_bytes(episode)
    P.write_export(tmp_path / "export", [episode])
    public = tmp_path / "export/public"
    identifier = P.public_challenge_id(episode)
    assert sorted(path.name for path in public.iterdir()) == [identifier + ".json", "index.json"]
    actual = (public / (identifier + ".json")).read_bytes()
    assert actual == P.public_challenge_bytes(episode)
    assert hashlib.sha256(actual).hexdigest() == identifier
    payload = json.loads(actual)
    assert set(payload) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in payload["train"])
    assert all(set(pair) == {"input"} for pair in payload["test"])
    assert json.loads((public / "index.json").read_text()) == [identifier]
    private = tmp_path / "export/private"
    assert (private / "references" / (episode["reference_sha256"] + ".rkt")).read_bytes() == episode["reference_program"].encode()


def test_duplicate_projection_rejected_before_any_destination_or_stage(tmp_path):
    episode = private_example()
    duplicate = copy.deepcopy(episode)
    duplicate["seed"] = 987
    duplicate["test"][0]["output"] = [[8]]
    with CASE.assertRaisesRegex(ValueError, "duplicate public challenge"):
        P.write_export(tmp_path / "export", [episode, duplicate])
    assert not list(tmp_path.iterdir())


def test_existing_destination_is_never_overwritten(tmp_path):
    out = tmp_path / "export"
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("predecessor")
    with CASE.assertRaises(FileExistsError):
        P.write_export(out, [private_example()])
    assert sentinel.read_text() == "predecessor"
    assert list(out.iterdir()) == [sentinel]


def test_atomic_publish_refuses_a_concurrently_created_empty_destination(tmp_path):
    stage, destination = tmp_path / "stage", tmp_path / "destination"
    stage.mkdir()
    (stage / "sentinel.txt").write_text("staged")
    destination.mkdir()
    with CASE.assertRaises(FileExistsError):
        P._publish_no_replace(stage, destination)
    assert (stage / "sentinel.txt").read_text() == "staged"
    assert list(destination.iterdir()) == []


def test_oracle_validates_before_cached_or_uncached_execution():
    class NoExecution:
        def eval_text(self, expression):
            raise AssertionError("invalid inputs must never reach Racket")

    oracle = P.RacketOracle(NoExecution())
    valid = witness()
    oracle.cache[(P.DEFAULT_SETTING, frozen(valid))] = P.python_mirror(valid)
    for invalid in (True, 1.0, "1"):
        grid = copy.deepcopy(valid)
        grid[0][0] = invalid
        with CASE.assertRaises(ValueError):
            oracle.predict(grid)


def test_racket_witness_and_all_general_profile_boundaries(racket_bridge):
    oracle = P.RacketOracle(racket_bridge)
    grids = [witness()] + [P.GENERATOR.generate(17, index, scene_profile=profile)
                           for index, profile in enumerate(P.GENERATOR.GENERAL_PROFILES)]
    for grid in grids:
        for setting in P.ALL_SETTINGS:
            assert oracle.predict(grid, setting) == P.python_mirror(grid, setting)


def test_racket_episodes_all_settings_and_writer_regression(racket_bridge, tmp_path):
    episodes = [P.build_episode(42426, setting=setting, bridge=racket_bridge)
                for setting in P.ALL_SETTINGS]
    for setting, episode in zip(P.ALL_SETTINGS, episodes):
        assert episode["parameters"] == setting.as_dict()
        assert len(episode["train"]) == 3 and len(episode["test"]) == 4
        assert len({frozen(pair["input"]) for pair in episode["train"] + episode["test"]}) == 7
        assert episode["identifiability"]["survivors"] == [setting.as_dict()]
        assert all(row["identifiable"] for row in episode["identifiability"]["queries"])
        assert episode["verification"]["label_backend"] == "racket"
        assert episode["verification"]["executed_predictions"] == 28
        assert episode["reference_sha256"] == hashlib.sha256(episode["reference_program"].encode()).hexdigest()
    P.write_export(tmp_path / "export", list(reversed(episodes)))
    ids = sorted(P.public_challenge_id(episode) for episode in episodes)
    assert json.loads((tmp_path / "export/public/index.json").read_text()) == ids
    for episode in episodes:
        identifier = P.public_challenge_id(episode)
        assert (tmp_path / "export/public" / (identifier + ".json")).read_bytes() == P.public_challenge_bytes(episode)
    changed = P.build_episode(17, setting=P.Settings("reverse", True), demo_count=1,
                              query_count=4, bridge=racket_bridge)
    assert (len(changed["train"]), len(changed["test"])) == (1, 4)


def load_tests(loader, tests, pattern):
    """Keep the suite dependency-free while providing two explicit fixtures."""
    suite = unittest.TestSuite()
    for name, function in sorted(globals().items()):
        if not name.startswith("test_") or not callable(function):
            continue

        def run(function=function):
            arguments = inspect.signature(function).parameters
            with ExitStack() as stack:
                fixtures = {}
                if "tmp_path" in arguments:
                    fixtures["tmp_path"] = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="parametric-tests-")))
                if "racket_bridge" in arguments:
                    if not os.environ.get("RACKET_PATH") and not shutil.which("racket"):
                        raise unittest.SkipTest("Racket integration requires WORK/run_with_racket.py")
                    from arc_repl.racket_bridge import RacketBridge
                    fixtures["racket_bridge"] = stack.enter_context(RacketBridge(timeout=20.0))
                function(**fixtures)

        run.__name__ = name
        suite.addTest(unittest.FunctionTestCase(run, description=name))
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
