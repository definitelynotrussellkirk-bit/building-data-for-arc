"""Replayable bounded semantic, privacy, and protected-Racket audit.

Run through ``review.py run``.  The rival bank is finite and explicitly named;
passing is evidence against those shortcuts, not a universal uniqueness claim.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
ROOT = HOME.parents[1]
RIVALS = (
    "all_pairs",
    "convex_hull",
    "row_order",
    "seed_shadow",
    "no_shadow",
    "overwrite_shadow",
)

_spec = importlib.util.spec_from_file_location("_polygon_shadow_audit_adapter", HERE / "adapter.py")
a = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = a
_spec.loader.exec_module(a)


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _source_binding() -> list[dict[str, str]]:
    paths = [
        HOME / "generator.py",
        HOME / "reference.rkt",
        HOME / "tests/test_35ab12c3_native.py",
        HOME / "tests/test_35ab12c3_parametric.py",
        HERE / "adapter.py",
        HERE / "prototype.py",
        HERE / "canonical.rkt",
        HERE / "promotion.json",
        HERE / "audit.py",
    ]
    return [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in paths
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=32)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 256:
        raise ValueError("seeds must be in 1..256")
    args.out.mkdir(parents=True, exist_ok=False)

    from arcpuzzles.parametric_worker import _grid, _real_evaluator

    failures: list[object] = []
    counterexamples: dict[str, list[int]] = {}
    episodes = labeled_pairs = rival_checks = public_views = large_queries = 0
    racket_evaluations = 0
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        for seed in range(args.seeds):
            mode_queries: dict[str, list[object]] = {}
            for demos in (2, 3, 6):
                for mode in a.impl.EDGE_MODES:
                    episode = a.generate(seed, {"edge_mode": mode}, demos, 4)
                    episodes += 1
                    pairs = episode["train"] + episode["test"]
                    labeled_pairs += len(pairs)
                    inputs = [pair["input"] for pair in pairs]
                    if len({_digest(grid) for grid in inputs}) != len(inputs):
                        failures.append(["duplicate", seed, demos, mode])
                    queries_now = [pair["input"] for pair in episode["test"]]
                    previous = mode_queries.setdefault(mode, queries_now)
                    if previous != queries_now:
                        failures.append(["query-instability", seed, demos, mode])
                    large_queries += sum(len(pair["input"]) == 30 and len(pair["input"][0]) == 30 for pair in episode["test"])

                    views = a.impl.public_turns(episode, seed)
                    public_views += len(views)
                    if not all(
                        set(view) == {"train", "test"}
                        and len(view["test"]) == 1
                        and set(view["test"][0]) == {"input"}
                        for view in views
                    ):
                        failures.append(["public-shape", seed, demos, mode])
                    mutant = copy.deepcopy(episode)
                    mutant["program_solution"] = "PRIVATE CANARY"
                    for pair in mutant["test"]:
                        pair["output"] = [[9]]
                    if a.impl.public_turns(mutant, seed) != views:
                        failures.append(["privacy", seed, demos, mode])

                    for rival in RIVALS:
                        rival_checks += 1
                        fits = all(a.impl.solve(pair["input"], mode, rival) == pair["output"] for pair in episode["train"])
                        harms = any(a.impl.solve(pair["input"], mode, rival) != pair["output"] for pair in episode["test"])
                        if fits and harms:
                            failures.append(["harmful-rival", seed, demos, mode, rival])
                        if not fits:
                            counterexamples.setdefault(f"{mode}:{rival}", [seed, demos])

                    other = "orthogonal" if mode == "all_8" else "all_8"
                    if not any(a.impl.solve(pair["input"], other) != pair["output"] for pair in episode["train"]):
                        failures.append(["setting-not-taught", seed, demos, mode])

                    if seed in (0, min(17, args.seeds - 1)) and demos in (2, 6):
                        for pair in pairs:
                            actual = _grid(apply(episode["program_solution"], pair["input"]))
                            racket_evaluations += 1
                            if actual != pair["output"]:
                                failures.append(["racket-parity", seed, demos, mode])
    finally:
        bridge.close()

    report = {
        "schema": "public-parent-finite-audit-v1",
        "task_id": a.impl.TASK_ID,
        "status": "passed" if not failures else "failed",
        "seeds": list(range(args.seeds)),
        "demos": [2, 3, 6],
        "settings": list(a.impl.EDGE_MODES),
        "episodes": episodes,
        "labeled_pairs": labeled_pairs,
        "finite_rival_checks": rival_checks,
        "policies": list(RIVALS),
        "counterexample_seeds": counterexamples,
        "public_views": public_views,
        "protected_racket_evaluations": racket_evaluations,
        "racket": identity,
        "substantive_30x30_queries": large_queries,
        "source_binding": _source_binding(),
        "failures": failures,
        "limits": "Finite named rivals and bounded seeds, not universal uniqueness. Protected Racket validates selected labels; no owner acceptance or training admission.",
    }
    (args.out / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "episodes", "labeled_pairs", "finite_rival_checks", "protected_racket_evaluations", "failures")}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
