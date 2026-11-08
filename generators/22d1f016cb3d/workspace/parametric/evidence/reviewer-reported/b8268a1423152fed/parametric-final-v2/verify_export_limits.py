"""Validate a fresh four-query export and one supported 32/32 boundary episode."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    started = time.monotonic()
    here = Path(__file__).resolve().parent
    root = find_root(__file__)
    source = root / "generators/22d1f016cb3d/workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("boundary_palette_limits", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = json.loads((here / "evidence.json").read_text())
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    assert report["prototype_source_sha256"] == source_sha
    verified = []
    for mode, setting in report["settings"].items():
        episode = setting["episode"]
        assert setting["actual_counts"] == {"n_train": 4, "n_test": 4}
        assert len(episode["train"]) == len(episode["test"]) == 4
        assert setting["distinct_input_count"] == 8
        assert setting["surviving_settings_from_demonstrations"] == [mode]
        assert len(setting["query_identifiability"]) == 4
        assert all(row["survivor_predictions_agree"] for row in setting["query_identifiability"])
        public_id = public_challenge_id(episode)
        payload = (here / "public" / f"{public_id}.json").read_bytes()
        assert payload == public_challenge_bytes(episode)
        assert hashlib.sha256(payload).hexdigest() == public_id
        assert set(json.loads(payload)) == {"train", "test"}
        changed = copy.deepcopy(episode)
        changed["seed"] += 123456
        changed["parameter"] = {"boundary_palette": "private_changed"}
        changed["selected_generator_sha256"] = "private_changed"
        for query in changed["test"]:
            query["output"] = [[9]]
            query["sample_index"] = -999
        assert public_challenge_bytes(changed) == payload
        assert public_challenge_id(changed) == public_id
        changed_visible = copy.deepcopy(episode)
        cell = changed_visible["train"][0]["output"][0][0]
        changed_visible["train"][0]["output"][0][0] = (cell + 1) % 10
        assert public_challenge_id(changed_visible) != public_id
        verified.append({"mode": mode, "public_id": public_id, "queries_verified": 4})
    ids = [row["public_id"] for row in report["public_exports"]]
    assert ids == sorted(ids) and len(set(ids)) == 2
    assert sorted(p.name for p in (here / "public").iterdir()) == [f"{key}.json" for key in ids]

    upper = module.build_episode(root=root, seed=19, n_train=32, n_test=32)
    pairs = upper["train"] + upper["test"]
    assert len(upper["train"]) == len(upper["test"]) == 32
    assert len({digest(pair["input"]) for pair in pairs}) == 64
    assert upper["label_source"] == "executed_racket"
    summary = {
        "schema": "arcpuzzles-boundary-palette-export-verification-v1",
        "status": "pass",
        "prototype_sha256": source_sha,
        "generator_sha256": upper["selected_generator_sha256"],
        "verified_public_episodes": verified,
        "public_identity_ignores_private_metadata_and_query_answers": True,
        "public_identity_changes_with_visible_demo_output": True,
        "upper_boundary": {
            "seed": 19, "n_train": 32, "n_test": 32,
            "distinct_inputs": 64, "label_source": upper["label_source"],
            "racket_sha256": upper["racket_sha256"],
            "sampling": upper["sampling"],
            "input_sha256": [digest(pair["input"]) for pair in pairs],
            "output_sha256": [digest(pair["output"]) for pair in pairs],
        },
        "execution": {"argv": sys.argv, "cwd": str(Path.cwd())},
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "limits": "One 32/32 episode; no claim of exhaustive seed support or production approval.",
    }
    (here / "count-boundaries.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "pass", "public_episodes": 2, "four_query_checks": 8,
                      "upper_boundary_distinct_racket_labels": 64}))


if __name__ == "__main__":
    main()
