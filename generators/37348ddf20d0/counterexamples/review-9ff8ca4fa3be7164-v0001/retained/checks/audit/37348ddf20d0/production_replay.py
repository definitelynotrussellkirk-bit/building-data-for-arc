"""Replay the retained candidate through the public production materializer."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from adversarial_probe import TASK, EXPECTED_SOURCE, component_manhattan, changed_cells


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path[:0] = [str(root / "src"), str(root / "shared/runtime")]
    from arcpuzzles import Catalog
    from reviewer_support import load_selected_generator
    gen, _, sha = load_selected_generator(TASK, root=root)
    assert sha == EXPECTED_SOURCE
    candidate = json.loads(args.candidate.read_text())
    settings = candidate["candidate_search"]
    assert settings["assembly"] == "ordered_five_demos_one_query"
    payload = {
        "schema": "37348ddf20d0-production-replay-v1", "task_id": TASK,
        "generator_sha256": sha,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "candidate_sha256": hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
        "invocation": {"argv": sys.argv, "cwd": str(Path.cwd()), "python": sys.executable},
    }
    try:
        episodes = Catalog(root).generate(
            TASK, count=1, seed=settings["seed"], sample_index=0,
            difficulty=settings["difficulty"], n_train=5, n_test=1,
            reference="canonical", allow_unapproved=True, timeout=180,
        )
    except Exception as exc:
        payload["failure"] = {"type": type(exc).__name__, "message": str(exc),
                              "run": getattr(exc, "run", None)}
        args.out.write_text(json.dumps(payload, indent=2) + "\n")
        raise
    episode = episodes[0]
    pairs = episode["train"] + episode["test"]
    fits = [component_manhattan(p["input"]) == p["output"] for p in pairs]
    difference = changed_cells(pairs[-1]["output"], component_manhattan(pairs[-1]["input"]))
    payload.update(
        episode=episode,
        matches_retained_pairs=pairs == candidate["lesson"]["pairs"],
        rival_demo_fit=fits[:-1], rival_query_fit=fits[-1],
        query_difference=difference,
        declared_hook=gen.lesson_identifiable(episode["train"], episode["test"][0]),
    )
    payload["reproduced"] = all(fits[:-1]) and not fits[-1] and payload["matches_retained_pairs"]
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({key: payload[key] for key in (
        "reproduced", "matches_retained_pairs", "rival_demo_fit", "rival_query_fit", "declared_hook"
    )}))
    print(json.dumps({"lesson_check": episode.get("lesson_check"),
                      "sampling": episode.get("sampling"),
                      "query_difference": difference}))
    return 0 if payload["reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
