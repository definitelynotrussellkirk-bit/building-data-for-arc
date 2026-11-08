"""Reusable bounded structural and public-projection audit for 6145142974ff."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_6145142974ff_audit_prototype_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prototype = _load_prototype()
SCHEMA = "arcpuzzles-parametric-self-audit-v1"
SETTINGS = ({"finish": "canonical"}, {"finish": "bridge_matches"})
DEMO_COUNTS = tuple(range(2, 7))


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def structural_audit(seed_count: int = 16) -> dict[str, Any]:
    if type(seed_count) is not int or not 1 <= seed_count <= 10_000:
        raise ValueError("seed_count must be an exact integer in 1..10000")

    failures: list[dict[str, Any]] = []
    episodes = matched = certificates = public_checks = stress_checks = prefix_checks = 0
    visible_pairs = 0
    survivor_rows: list[dict[str, Any]] = []

    for seed in range(seed_count):
        for demos in DEMO_COUNTS:
            generated: dict[str, dict[str, Any]] = {}
            for settings in SETTINGS:
                finish = settings["finish"]
                context = {"seed": seed, "demos": demos, "finish": finish}
                try:
                    episode = prototype.generate(seed, settings, demos=demos, queries=4)
                    generated[finish] = episode
                    episodes += 1
                    pairs = episode["train"] + episode["test"]
                    visible_pairs += len(pairs)
                    if len(episode["train"]) != demos or len(episode["test"]) != 4:
                        raise AssertionError("requested counts were not exact")
                    frozen = [_freeze(pair["input"]) for pair in pairs]
                    if len(frozen) != len(set(frozen)):
                        raise AssertionError("episode contains duplicate inputs")

                    certificate = prototype.teaching_certificate(
                        episode["train"], [pair["input"] for pair in episode["test"]]
                    )
                    certificates += 1
                    survivor_rows.append(
                        {
                            **context,
                            "survivors": certificate["survivors"],
                            "harmful_query_survivors": certificate["harmful_query_survivors"],
                        }
                    )
                    if certificate["survivors"] != [finish]:
                        raise AssertionError(f"finite survivors were {certificate['survivors']}")
                    if certificate["harmful_query_survivors"]:
                        raise AssertionError(
                            "harmful query survivors: "
                            + ", ".join(certificate["harmful_query_survivors"])
                        )

                    short = prototype.generate(seed, settings, demos=2, queries=4)
                    one = prototype.generate(seed, settings, demos=demos, queries=1)
                    if episode["train"][:2] != short["train"]:
                        raise AssertionError("demonstration prefix depends on requested count")
                    if episode["test"][:1] != one["test"]:
                        raise AssertionError("first query depends on requested query count")
                    if prototype.public_turn_bytes(episode, 0) != prototype.public_turn_bytes(one, 0):
                        raise AssertionError("first public turn differs from single-query use")
                    prefix_checks += 1

                    for query_index in range(4):
                        public = json.loads(prototype.public_turn_bytes(episode, query_index))
                        if set(public) != {"train", "test"}:
                            raise AssertionError("public payload has unexpected fields")
                        if len(public["test"]) != 1 or set(public["test"][0]) != {"input"}:
                            raise AssertionError("public payload leaks answers or future queries")
                        public_checks += 1

                    stress = episode["test"][3]["input"]
                    info = prototype.observe(stress)
                    if (len(stress), len(stress[0])) != (30, 30):
                        raise AssertionError("fourth query is not 30x30")
                    if info["matching_components"] < 6 or info["distractor_components"] < 4:
                        raise AssertionError("30x30 stress lacks object spread")
                    if info["colored_cells"] < 60 or info["boundary_contacts"] < 1:
                        raise AssertionError("30x30 stress lacks density or boundary contact")
                    if prototype.predict(stress, "canonical") == prototype.predict(stress, "bridge_matches"):
                        raise AssertionError("settings agree on 30x30 stress")
                    stress_checks += 1
                except Exception as exc:
                    failures.append({**context, "error": f"{type(exc).__name__}: {exc}"})

            if set(generated) == set(prototype.FINISHES):
                canonical = generated["canonical"]
                bridge = generated["bridge_matches"]
                left = [pair["input"] for pair in canonical["train"] + canonical["test"]]
                right = [pair["input"] for pair in bridge["train"] + bridge["test"]]
                if left != right:
                    failures.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "finish": "matched_inputs",
                            "error": "settings received different visible inputs",
                        }
                    )
                else:
                    matched += 1

    witness = prototype.causal_witness(seed=0)
    if witness["changed_cells"] <= 0:
        failures.append({"finish": "bridge_matches", "error": "causal witness did not change output"})

    return {
        "schema": SCHEMA,
        "task_id": prototype.TASK_ID,
        "seed_count": seed_count,
        "seed_range": [0, seed_count - 1],
        "settings": list(SETTINGS),
        "demo_counts": list(DEMO_COUNTS),
        "queries": 4,
        "episodes": episodes,
        "visible_pairs": visible_pairs,
        "matched_input_checks": matched,
        "finite_rival_certificates": certificates,
        "prefix_checks": prefix_checks,
        "public_turn_checks": public_checks,
        "stress_30x30_checks": stress_checks,
        "survivor_rows": survivor_rows,
        "causal_witness_summary": {
            "seed": witness["seed"],
            "changed_cells": witness["changed_cells"],
            "ablation": "wrong_intermediate",
        },
        "failures": failures,
        "scope": (
            "Bounded Python structural/count/prefix/public-projection and finite declared-rival audit. "
            "Protected Racket qualification and causal replay are separate evidence."
        ),
    }


def write_public_exports(output: str | Path, *, seed: int = 0, demos: int = 3) -> dict[str, Any]:
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"public output must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    identifiers: list[str] = []
    rows: list[dict[str, Any]] = []
    for settings in SETTINGS:
        episode = prototype.generate(seed, settings, demos=demos, queries=4)
        for query_index in range(4):
            payload = prototype.public_turn_bytes(episode, query_index)
            identifier = hashlib.sha256(payload).hexdigest()
            if identifier in identifiers:
                raise ValueError("duplicate visible public challenge")
            identifiers.append(identifier)
            path = output / f"{identifier}.json"
            path.write_bytes(payload)
            rows.append(
                {
                    "public_id": identifier,
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "query_index": query_index,
                    "private_setting": settings,
                }
            )
    return {
        "schema": "arcpuzzles-parametric-public-export-check-v1",
        "task_id": prototype.TASK_ID,
        "seed": seed,
        "demos": demos,
        "queries_per_setting": 4,
        "files": len(rows),
        "rows": rows,
        "scope": "Settings are retained only in this private audit index, never in public files or names.",
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--public-dir", type=Path, required=True)
    parser.add_argument("--seed-count", type=int, default=16)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--demos", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        report = structural_audit(args.seed_count)
        public = write_public_exports(args.public_dir, seed=args.seed, demos=args.demos)
        result = {**report, "public_export": public}
        _write_json(args.out, result)
        print(
            json.dumps(
                {
                    "task_id": prototype.TASK_ID,
                    "episodes": report["episodes"],
                    "finite_rival_certificates": report["finite_rival_certificates"],
                    "public_files": public["files"],
                    "failures": len(report["failures"]),
                    "out": str(args.out.resolve()),
                },
                sort_keys=True,
            )
        )
        return 0 if not report["failures"] else 1
    except Exception as exc:
        print(f"audit: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
