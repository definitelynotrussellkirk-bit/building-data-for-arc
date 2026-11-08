"""Reusable deterministic stress audit for the bbox-relay parametric family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
_PROTOTYPE_PATH = HERE / "prototype.py"
_SPEC = importlib.util.spec_from_file_location(
    "_arc_ebe355c22d70_parametric_audit_prototype", _PROTOTYPE_PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent parametric prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = prototype
_SPEC.loader.exec_module(prototype)

SCHEMA = "ebe355c22d70-bbox-relay-stress-v1"
DEMO_COUNTS = list(range(prototype.DEMO_LIMITS[0], prototype.DEMO_LIMITS[1] + 1))
MODES = [setting["mode"] for setting in prototype.SETTINGS]


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def stress(seed_count: int = 50) -> dict:
    """Sweep all modes/demo counts and return a machine-readable audit report.

    This is intentionally a Python-side structural and learnability stress test.
    Protected Racket execution remains the responsibility of qualification and
    the task-local bounded self-audit.
    """
    if type(seed_count) is not int or not 1 <= seed_count <= 10_000:
        raise ValueError("seed_count must be an exact integer in 1..10000")

    failures: list[dict] = []
    episode_count = 0
    visible_pairs = 0
    matched_input_checks = 0
    public_turn_checks = 0
    distinct_inputs_checked = 0
    certificate_checks = 0
    stress_query_checks = 0

    for seed in range(seed_count):
        for demos in DEMO_COUNTS:
            by_mode: dict[str, dict] = {}
            for mode in MODES:
                context = {"seed": seed, "demos": demos, "mode": mode}
                try:
                    episode = prototype.generate(
                        seed, {"mode": mode}, demos=demos, queries=prototype.QUERY_COUNT
                    )
                    by_mode[mode] = episode
                    episode_count += 1
                    pairs = episode["train"] + episode["test"]
                    visible_pairs += len(pairs)

                    frozen = [_freeze(pair["input"]) for pair in pairs]
                    if len(set(frozen)) != len(frozen):
                        raise AssertionError("episode contains duplicate inputs")
                    distinct_inputs_checked += len(frozen)

                    certificate = prototype.certify(episode)
                    if certificate["survivors"] != [{"mode": mode}]:
                        raise AssertionError("certificate did not retain exactly the chosen mode")
                    if not all(certificate["extra_refutations"].values()):
                        raise AssertionError("an authored rival has no demonstration refutation")
                    certificate_checks += 1

                    for query_index in range(prototype.QUERY_COUNT):
                        public = prototype.public_turn(episode, query_index)
                        if set(public) != {"train", "test"} or len(public["test"]) != 1:
                            raise AssertionError("public turn shape is invalid")
                        if set(public["test"][0]) != {"input"}:
                            raise AssertionError("public query leaks a non-input field")
                        if public["test"][0]["input"] != episode["test"][query_index]["input"]:
                            raise AssertionError("public turn selected the wrong query")
                        public_turn_checks += 1

                    stress_grid = episode["test"][3]["input"]
                    if (len(stress_grid), len(stress_grid[0])) != (30, 30):
                        raise AssertionError("fourth query is not 30x30")
                    stress_query_checks += 1
                except Exception as exc:  # keep the sweep informative after one failure
                    failures.append({**context, "error": f"{type(exc).__name__}: {exc}"})

            if set(by_mode) == set(MODES):
                canonical = by_mode[MODES[0]]["train"] + by_mode[MODES[0]]["test"]
                alternate = by_mode[MODES[1]]["train"] + by_mode[MODES[1]]["test"]
                if [pair["input"] for pair in canonical] != [pair["input"] for pair in alternate]:
                    failures.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "mode": "matched_inputs",
                            "error": "settings received different visible inputs",
                        }
                    )
                else:
                    matched_input_checks += 1

    return {
        "schema": SCHEMA,
        "task_id": prototype.TASK_ID,
        "seed_count": seed_count,
        "seed_range": [0, seed_count - 1],
        "modes": MODES,
        "demo_counts": DEMO_COUNTS,
        "queries_per_episode": prototype.QUERY_COUNT,
        "episodes": episode_count,
        "visible_pairs": visible_pairs,
        "matched_input_checks": matched_input_checks,
        "distinct_inputs_checked": distinct_inputs_checked,
        "certificate_checks": certificate_checks,
        "public_turn_checks": public_turn_checks,
        "stress_query_checks": stress_query_checks,
        "failures": failures,
        "scope": (
            "Python structural, matched-input, finite-rival and public-projection sweep; "
            "protected Racket execution is covered separately by retained qualification evidence."
        ),
        "source_sha256": {
            "audit.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            **prototype.source_hashes(),
        },
    }


def write_report(report: dict, destination: Path) -> None:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=50, help="number of seeds starting at zero")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = stress(seed_count=args.seeds)
    write_report(report, args.out)
    print(
        json.dumps(
            {
                "status": "pass" if not report["failures"] else "fail",
                "episodes": report["episodes"],
                "visible_pairs": report["visible_pairs"],
                "failures": len(report["failures"]),
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    if report["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
