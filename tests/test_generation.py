"""Reference execution must use the authority that was actually reviewed."""
import json
import shutil
import sys

import pytest

from arcpuzzles import Catalog, runtime


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_generation_ignores_stale_base_authority(monkeypatch):
    catalog = Catalog()
    original_prepare = runtime.prepare_runtime

    def stale_base(catalog, destination, task_id):
        receipt = original_prepare(catalog, destination, task_id)
        # Deliberately corrupt only the disposable archival authority. The
        # canonical program and reviewed source remain unchanged.
        changed = 0
        for path in (destination / "data/base/solutions").rglob("*.json"):
            row = json.loads(path.read_text())
            if row.get("task_id") == task_id:
                row["racket_target"] = {"target_code": "(rule! (lambda (g) g))"}
                path.write_text(json.dumps(row))
                changed += 1
        assert changed > 0
        return receipt

    monkeypatch.setattr(runtime, "prepare_runtime", stale_base)
    episode, = catalog.generate("6c68e1b008a5", seed=23, n_train=2, n_test=1)
    assert episode["executed_rule_hash"] == catalog.describe("6c68e1b008a5")["rule_hash"]
    assert episode["rule_source"] == "data/canonical/puzzles.jsonl"
    assert episode["provenance"]["approved"]
    assert len(episode["train"]) == 2 and len(episode["test"]) == 1
    assert all(pair["input"] != pair["output"] for pair in episode["train"] + episode["test"])


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_override_axes_and_sample_indices_are_executed_and_recorded():
    catalog = Catalog()
    options = dict(seed=31, sample_index=7, n_train=2, n_test=1,
                   difficulty="easy", overrides={"scene_profile": "match_2_single"})
    episode, = catalog.generate("6c68e1b008a5", **options)
    assert episode["sample_index"] == 7
    assert episode["sample_indices"] == [7, 8, 9]
    assert episode["provenance"]["overrides"] == options["overrides"]
    assert all(pair["output"] == [[0, 0, 8]] for pair in episode["train"] + episode["test"])
    with pytest.raises(ValueError, match="explicit"):
        catalog.generate("6c68e1b008a5", overrides={"seed": 3})


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
@pytest.mark.parametrize("identity,reason", [(False, "duplicate pair"), (True, "output_equals_input")])
def test_generic_worker_preserves_legacy_pair_admission(tmp_path, identity, reason):
    catalog = Catalog()
    task_id = "generic_dense_recolor_gen1"
    row = catalog.describe(task_id)
    stage = tmp_path / "runtime"
    runtime.prepare_runtime(catalog, stage, task_id)
    # Replace only a disposable fixture implementation, after staging. This
    # directly exercises the worker; production API additionally checks hashes.
    if identity:
        program = "(rule! (lambda (g) g))"
        train = [{"input": [[1, 0]], "output": [[1, 0]]}]
        test = [{"input": [[2, 0]], "output": [[2, 0]]}]
    else:
        program = "(rule! (flip-lr g))"
        train = test = [{"input": [[1, 0]], "output": [[0, 1]]}]
    task = {"program": program, "train": train, "test": test}
    (stage / row["runtime_generator"]).write_text(
        "def generate_task(seed, *, difficulty='medium'):\n    return " + repr(task) + "\n")
    request = {"task_id": task_id, "kind": "generic", "runtime_generator": row["runtime_generator"],
               "count": 1, "seed": 1, "difficulty": "medium", "n_train": 1, "n_test": 1}
    (stage / "request.json").write_text(json.dumps(request))
    result = runtime.run_process([sys.executable, "arcpuzzles_worker.py"], stage, timeout=20)
    assert result["exit_code"] != 0 and reason in result["stderr"]
