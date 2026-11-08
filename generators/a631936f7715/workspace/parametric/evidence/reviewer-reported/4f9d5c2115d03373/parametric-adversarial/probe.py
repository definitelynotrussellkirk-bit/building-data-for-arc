#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile

from reviewer_support import find_root

TASK_ID = "a631936f7715"
ROOT = find_root(__file__)
PROTOTYPE = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    spec = importlib.util.spec_from_file_location("a631936f7715_adversarial", PROTOTYPE)
    if spec is None or spec.loader is None:
        raise RuntimeError("prototype loader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_failure(fn, expected):
    try:
        fn()
    except expected as exc:
        return type(exc).__name__
    raise AssertionError(f"expected {expected}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    proto = load_prototype()

    count_cases = ((1, 1), (3, 4), (4, 8))
    seeds = range(32)
    episodes_checked = 0
    pairs_checked = 0
    query_checks = 0
    public_mask_checks = 0
    max_pairs = 0

    retained = []
    for seed in seeds:
        for connectivity in proto.ALLOWED_CONNECTIVITIES:
            for n_train, n_test in count_cases:
                episode = proto.build_episode(
                    seed,
                    connectivity=connectivity,
                    n_train=n_train,
                    n_test=n_test,
                )
                assert proto.episode_errors(episode) == []
                pairs = episode["train"] + episode["test"]
                keys = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
                assert len(keys) == len(set(keys))
                assert episode["counts"] == {
                    "demonstrations": n_train,
                    "queries": n_test,
                }
                rival = 8 if connectivity == 4 else 4
                assert any(
                    proto.apply_python(pair["input"], rival) != pair["output"]
                    for pair in episode["train"]
                )
                for pair in episode["test"]:
                    assert proto.apply_python(pair["input"], rival) != pair["output"]
                    query_checks += 1
                episodes_checked += 1
                pairs_checked += len(pairs)
                max_pairs = max(max_pairs, len(pairs))
                if seed in (0, 31) and (n_train, n_test) == (3, 4):
                    changed = deepcopy(episode)
                    changed["seed"] = 999999
                    changed["parameters"] = {"component_connectivity": rival}
                    changed["program"] = "private-only replacement"
                    for pair in changed["test"]:
                        pair["output"] = [[9]]
                    assert proto.public_challenge_bytes(episode) == proto.public_challenge_bytes(changed)
                    assert proto.public_challenge_id(episode) == proto.public_challenge_id(changed)
                    public_mask_checks += 1
                if seed == 31 and (n_train, n_test) == (3, 4):
                    retained.append(episode)

    invalid_count_results = {}
    for field in ("n_train", "n_test"):
        for value in (0, -1, True, 1.5, "4", None):
            kwargs = {"connectivity": 4, "n_train": 3, "n_test": 4}
            kwargs[field] = value
            key = f"{field}={value!r}"
            invalid_count_results[key] = expect_failure(
                lambda kwargs=kwargs: proto.build_episode(17, **kwargs),
                (TypeError, ValueError),
            )

    duplicate_episode = deepcopy(retained[0])
    duplicate_episode["test"][0]["input"] = deepcopy(duplicate_episode["train"][0]["input"])
    duplicate_episode["test"][0]["output"] = proto.apply_python(
        duplicate_episode["test"][0]["input"],
        duplicate_episode["parameters"]["component_connectivity"],
    )
    duplicate_errors = proto.episode_errors(duplicate_episode)
    assert any("duplicate input" in error for error in duplicate_errors)

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        export = base / "export"
        manifest = proto.write_batch(list(reversed(retained)), export)
        ids = [row["public_id"] for row in manifest["episodes"]]
        assert ids == sorted(ids) and len(ids) == len(set(ids)) == 2
        public_records = []
        for row in manifest["episodes"]:
            path = export / row["public_path"]
            raw = path.read_bytes()
            assert path.parent.name == "public"
            assert re.fullmatch(r"[0-9a-f]{64}\.json", path.name)
            assert hashlib.sha256(raw).hexdigest() == row["public_id"]
            payload = json.loads(raw)
            assert all(set(pair) == {"input"} for pair in payload["test"])
            assert "component_connectivity" not in raw.decode()
            assert "program" not in raw.decode()
            public_records.append(
                {
                    "public_id": row["public_id"],
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            )

        duplicate_dir = base / "duplicate"
        duplicate_rejection = expect_failure(
            lambda: proto.write_batch([retained[0], deepcopy(retained[0])], duplicate_dir),
            ValueError,
        )
        assert not duplicate_dir.exists()

        corrupt = deepcopy(retained[0])
        corrupt["test"][0]["input"][0][0] = True
        corrupt_dir = base / "corrupt"
        corrupt_rejection = expect_failure(
            lambda: proto.write_batch([corrupt], corrupt_dir),
            ValueError,
        )
        assert not corrupt_dir.exists()

    report = {
        "schema": "a631936f7715-parametric-adversarial-v1",
        "status": "passed",
        "surfaces": [
            "sampler count boundaries and episode input uniqueness",
            "visible-content public IDs, private masking, and writer rejection paths",
        ],
        "bounded_scope": {
            "seeds": [0, 31],
            "seed_count": 32,
            "settings": list(proto.ALLOWED_CONNECTIVITIES),
            "count_cases": [
                {"demonstrations": train, "queries": test}
                for train, test in count_cases
            ],
            "episodes_checked": episodes_checked,
            "pairs_checked": pairs_checked,
            "query_identifiability_checks": query_checks,
            "private_mask_checks": public_mask_checks,
            "max_pairs_in_episode": max_pairs,
        },
        "invalid_count_rejections": invalid_count_results,
        "duplicate_episode_errors": duplicate_errors,
        "writer": {
            "public_records": public_records,
            "duplicate_visible_payload_rejection": duplicate_rejection,
            "non_arc_numeric_rejection": corrupt_rejection,
            "duplicate_output_created": False,
            "corrupt_output_created": False,
        },
        "finding": (
            "No issue found in the bounded 32-seed, two-setting, three-count-case pass. "
            "The writer rejected duplicate visible payloads and non-ARC numeric content before creating outputs."
        ),
        "limits": (
            "This bounded pass covers up to four demonstrations and eight queries at seeds 0..31; "
            "it does not prove collision-free sampling for arbitrary requested counts."
        ),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "out": str(out), "bounded_scope": report["bounded_scope"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
