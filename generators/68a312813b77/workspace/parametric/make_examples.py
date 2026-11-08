"""Execute all declared native settings and export private labels with isolated turns.

These task-local examples remain owner-pending. Protected reference execution
checks labels and finite setting identification; it does not grant acceptance
or training admission.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = HERE.parents[1].name
PROMOTION_PATH = HERE / "promotion.json"

for source in (REPO / "src", REPO / "shared/runtime"):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

from arcpuzzles.parametric_promotion import settings_space
from arcpuzzles.parametric_worker import evaluate_contract


def _exporter():
    """Load this task's transport code without a generic module-name cache."""
    path = HERE / "export.py"
    spec = importlib.util.spec_from_file_location(f"_{TASK_ID}_native_export", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load exporter from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_examples(
    out_dir: str | Path, *, seed: int = 0, demos: int = 3, queries: int = 4
) -> dict[str, Any]:
    """Replay every declared setting through protected Racket, then export.

    Identical seeds/counts are passed to every setting. The native worker
    independently executes each declared program on demonstrations and checks
    all selected query labels before any public or private file is written.
    """
    destination = Path(out_dir)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
    for name, value in (("demos", demos), ("queries", queries)):
        lower, upper = contract["limits"][name]
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError(f"{name} must be an exact integer in {lower}..{upper}")
    jobs = [
        {"seed": seed, "settings": setting, "demos": demos, "queries": queries}
        for setting in settings_space(contract)
    ]
    execution = evaluate_contract(REPO, TASK_ID, contract, jobs)
    identity = execution.get("racket", {})
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise ValueError("example export requires live protected Racket execution")

    episodes = []
    for episode, certificate in zip(execution["episodes"], execution["checks"], strict=True):
        episodes.append(
            {
                **episode,
                "reference": "protected_racket_pending_acceptance",
                "private": {
                    "racket": identity,
                    "demo_only_certificate": certificate,
                    "native_acceptance": "owner_pending",
                    "training_admitted": False,
                    # The native worker deliberately normalizes away adapter
                    # metadata. Retain this task's pinned inspiration privately.
                    "authoring_focus": {
                        "source_task_id": "7666fa5d",
                        "source_split": "evaluation",
                        "challenge_sha256": "1b19ed6f202f6b9addff88314b0697b2752f581a55994c0339948f7cf3f8cd6d",
                        "relationship_verified": False,
                        "training_admitted": False,
                    },
                },
            }
        )
    report = _exporter().write_batch(episodes, destination)
    return {
        **report,
        "task_id": TASK_ID,
        "settings": [job["settings"] for job in jobs],
        "demos": demos,
        "queries": queries,
        "racket": identity,
        "racket_evaluations": execution["racket_evaluations"],
        "native_acceptance": "owner_pending",
        "training_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args()
    report = build_examples(args.out, seed=args.seed, demos=args.demos, queries=args.queries)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
