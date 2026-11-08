#!/usr/bin/env python3
"""Bounded source-bound adversarial probes for the dafb4f819b93 prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

WORK = Path(__file__).resolve().parents[2]
REPO = WORK / "repo"
PROTOTYPE_PATH = REPO / "generators/dafb4f819b93/workspace/parametric/prototype.py"
VALID_TREE = WORK / "checks/parametric/dafb4f819b93-label-offset-v1"
OUTPUT = WORK / "checks/parametric/dafb4f819b93-adversarial.json"

sys.path.insert(0, str(REPO))
spec = importlib.util.spec_from_file_location("dafb4f819b93_parametric_probe", PROTOTYPE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load prototype")
prototype = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prototype)


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def refresh_manifest_entry(tree: Path, path: Path) -> None:
    manifest_path = tree / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    relative = path.relative_to(tree).as_posix()
    body = path.read_bytes()
    manifest["files"][relative] = {"bytes": len(body), "sha256": sha256_bytes(body)}
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def infer_attempt(seed: int, row: dict) -> int:
    target = (row["input_seed"], row["sample_index"])
    for attempt in range(32):
        if prototype._draw_coordinates(seed, row["slot"], attempt) == target:
            return attempt
    raise AssertionError("saved coordinates are outside the declared retry budget")


def sampler_probe() -> dict:
    started = time.monotonic()
    max_attempt = 0
    offsets = set()
    for seed in range(32):
        rows = prototype._episode_input_rows(seed, n_train=16, n_test=8, root=REPO)
        assert len(rows) == 24
        assert len({json.dumps(row["input"], separators=(",", ":")) for row in rows}) == 24
        assert {row["observed_axes"]["border_relation"] for row in rows} == {"matched", "different"}
        assert [row["slot"] for row in rows] == list(range(24))
        max_attempt = max(max_attempt, *(infer_attempt(seed, row) for row in rows))
        offsets.add(prototype.parameters_for_seed(seed)["label_offset"])

    # Force attempt-0 collisions after the first slot and prove the bounded retry path recovers.
    seed = 987654321
    original_loader = prototype.load_selected_generator
    base, source_path, source_sha = original_loader(prototype.TASK_ID, root=REPO)
    first_coordinates = {
        prototype._draw_coordinates(seed, slot, 0): slot for slot in range(7)
    }
    first_seed, first_index = prototype._draw_coordinates(seed, 0, 0)
    repeated = base.generate(
        first_seed,
        first_index,
        difficulty="easy",
        grid_n=8,
        n_colors=4,
        border_relation="matched",
    )

    class CollisionOnce:
        self_check = staticmethod(base.self_check)
        observe_overrides = staticmethod(base.observe_overrides)

        @staticmethod
        def generate(input_seed, sample_index, **kwargs):
            slot = first_coordinates.get((input_seed, sample_index))
            if slot is not None and slot > 0:
                return copy.deepcopy(repeated)
            return base.generate(input_seed, sample_index, **kwargs)

    prototype.load_selected_generator = lambda task_id, root: (CollisionOnce, source_path, source_sha)
    try:
        recovered = prototype._episode_input_rows(seed, n_train=3, n_test=4, root=REPO)
    finally:
        prototype.load_selected_generator = original_loader
    recovered_attempts = [infer_attempt(seed, row) for row in recovered]
    assert recovered_attempts == [0, 1, 1, 1, 1, 1, 1]
    assert len({json.dumps(row["input"], separators=(",", ":")) for row in recovered}) == 7

    try:
        prototype.episode_inputs(0, n_train=16, n_test=9, root=REPO)
    except ValueError:
        over_limit_rejected = True
    else:
        over_limit_rejected = False
    assert over_limit_rejected

    return {
        "status": "pass",
        "seed_range": [0, 31],
        "max_count_episode": {"demonstrations": 16, "queries": 8},
        "episodes_checked": 32,
        "inputs_checked": 768,
        "settings_seen": sorted(offsets),
        "natural_max_retry_attempt": max_attempt,
        "forced_collision_attempts": recovered_attempts,
        "over_limit_rejected": over_limit_rejected,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def verifier_probe() -> dict:
    from arc_repl.racket_bridge import RacketBridge

    started = time.monotonic()
    results = {}
    with tempfile.TemporaryDirectory(prefix="dafb4f819b93-adversarial-") as tmp, RacketBridge(max_calls_before_restart=64) as bridge:
        tmp_path = Path(tmp)

        output_tree = tmp_path / "tampered-output"
        shutil.copytree(VALID_TREE, output_tree)
        report = json.loads((output_tree / "report.json").read_text(encoding="utf-8"))
        private_path = output_tree / report["episodes"][0]["private_path"]
        private = json.loads(private_path.read_text(encoding="utf-8"))
        old = private["test"][0]["output"][0][0]
        private["test"][0]["output"][0][0] = (old + 1) % 10
        private_path.write_text(json.dumps(private, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        refresh_manifest_entry(output_tree, private_path)
        output_verification = prototype.verify_tree(output_tree, root=REPO, bridge=bridge)
        assert output_verification["status"] == "fail"
        assert any("Racket labels mismatch" in error for error in output_verification["errors"])
        results["recomputed_manifest_hidden_output_tamper"] = {
            "status": "rejected",
            "errors": output_verification["errors"],
        }

        public_tree = tmp_path / "tampered-public"
        shutil.copytree(VALID_TREE, public_tree)
        report = json.loads((public_tree / "report.json").read_text(encoding="utf-8"))
        public_path = public_tree / report["episodes"][0]["public_path"]
        public = json.loads(public_path.read_text(encoding="utf-8"))
        public["test"][0]["input"][0][0] = (public["test"][0]["input"][0][0] + 1) % 10
        public_path.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        refresh_manifest_entry(public_tree, public_path)
        public_verification = prototype.verify_tree(public_tree, root=REPO, bridge=bridge)
        assert public_verification["status"] == "fail"
        assert any("public/private projection mismatch" in error for error in public_verification["errors"])
        results["recomputed_manifest_public_tamper"] = {
            "status": "rejected",
            "errors": public_verification["errors"],
        }

        clean = prototype.verify_tree(VALID_TREE, root=REPO, bridge=bridge)
        assert clean["status"] == "pass"
        results["untampered_control"] = clean

    return {
        "status": "pass",
        "cases": results,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def main() -> None:
    started = time.monotonic()
    result = {
        "schema": "arcpuzzles-bounded-adversarial-probe-v1",
        "task_id": prototype.TASK_ID,
        "prototype_path": PROTOTYPE_PATH.relative_to(REPO).as_posix(),
        "prototype_sha256": sha256_bytes(PROTOTYPE_PATH.read_bytes()),
        "valid_tree": VALID_TREE.relative_to(WORK).as_posix(),
        "sampler_count_retry": sampler_probe(),
        "verifier_rejection": verifier_probe(),
    }
    result["status"] = "pass"
    result["elapsed_seconds"] = round(time.monotonic() - started, 3)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
