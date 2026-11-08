"""Bounded protected-Racket learnability audit for the accepted cddbee92b2f3 native family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK_ID = "cddbee92b2f3"
SOURCE = REPO / f"generators/{TASK_ID}/generator.py"
PROTOTYPE = REPO / f"generators/{TASK_ID}/workspace/parametric/prototype.py"
EXPECTED_SOURCE_SHA256 = "bfe9b25b5a9c922d37e3751b38e61eea8071a051f3ec2af7eef2465e200edaff"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_prototype():
    spec = importlib.util.spec_from_file_location("_cdd_peer_probe", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    started = time.monotonic()
    source_sha = sha256(SOURCE)
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source drift: {source_sha}")
    p = load_prototype()
    jobs = []
    protected_evaluations = 0
    with p.RacketRunner() as execute:
        for seed in (0, 17):
            for demos in (2, 6):
                matched = {}
                for setting in p.SETTINGS:
                    episode = p.generate(seed, setting, demos=demos, queries=4)
                    certificate = p.certify(episode, execute)
                    protected_evaluations += demos + 4 + 2 * demos
                    key = setting["source_side"]
                    matched[key] = [pair["input"] for pair in episode["train"] + episode["test"]]
                    jobs.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "settings": setting,
                            "survivors": certificate["survivors"],
                            "shortcut_refutations": certificate["shortcut_refutations"],
                            "query_shapes": [
                                [len(pair["input"]), len(pair["input"][0])]
                                for pair in episode["test"]
                            ],
                        }
                    )
                if matched["left"] != matched["right"]:
                    raise RuntimeError("settings did not receive matched inputs")

    if not all(
        row["survivors"] == [row["settings"]]
        and all(row["shortcut_refutations"].values())
        and row["query_shapes"][-1] == [30, 30]
        for row in jobs
    ):
        raise RuntimeError("finite native-family audit failed")

    result = {
        "schema": "arcpuzzles-peer-adversarial-probe-v1",
        "task_id": TASK_ID,
        "status": "no_finding_bounded",
        "generator_sha256": source_sha,
        "prototype_sha256": sha256(PROTOTYPE),
        "scope": (
            "Both accepted source-side settings at seeds 0 and 17, with 2- and 6-demo boundaries, "
            "four matched queries, and protected-Racket certification against the alternate setting, "
            "mirror-both-sides, and move-instead-of-copy rivals."
        ),
        "jobs": jobs,
        "protected_racket_evaluations": protected_evaluations,
        "limits": "Finite declared rivals only; this is not a universal uniqueness proof or new owner acceptance.",
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }
    (HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "protected_racket_evaluations", "elapsed_seconds")}, sort_keys=True))


if __name__ == "__main__":
    main()
