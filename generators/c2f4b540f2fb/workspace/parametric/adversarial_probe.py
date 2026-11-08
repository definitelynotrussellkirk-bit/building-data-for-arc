#!/usr/bin/env python3
"""Bounded protected-Racket adversarial review for the local-tier family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def _load():
    path = HERE / "prototype.py"
    name = "_c2f4b540f2fb_probe_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


P = _load()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RacketRunner:
    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule

        self._wrap_rule = wrap_rule
        self.bridge = RacketBridge(max_calls_before_restart=512)
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("protected Racket backend required")
        self.cache: dict[str, str] = {}
        self.evaluations = 0
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        if source not in self.cache:
            self.cache[source] = self._wrap_rule(source)
        literal = "'(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in grid
        ) + ")"
        self.evaluations += 1
        return self.bridge.eval_text(f"({self.cache[source]} {literal})")

    def __exit__(self, *exc):
        self.bridge.close()


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _selected_signature(grid, setting):
    info = P.analyze(grid)
    return tuple(P._selected(info["motif"], setting))


def _expect_reject(label: str, action, rejected: list[str]) -> None:
    try:
        action()
    except (ValueError, TypeError, RuntimeError):
        rejected.append(label)
    else:
        raise AssertionError(f"tamper was accepted: {label}")


def run(min_seeds: list[int], max_seed: int) -> dict[str, Any]:
    settings = [dict(row) for row in P.SETTINGS]
    minimum_records = []
    maximum_records = []
    matched_input_checks = 0
    racket_cases = 0
    teaching_profiles: dict[str, set[str]] = {json.dumps(s, sort_keys=True): set() for s in settings}
    fixed_slot_intermediates: dict[str, set[str]] = {json.dumps(s, sort_keys=True): set() for s in settings}
    nuisance_candidates: dict[tuple[str, str], list[dict[str, Any]]] = {}

    with RacketRunner() as execute:
        for seed in min_seeds:
            episodes = [P.generate(seed, setting, 2, 4) for setting in settings]
            input_banks = [[P.grid_digest(grid) for grid in _inputs(ep)] for ep in episodes]
            if any(bank != input_banks[0] for bank in input_banks[1:]):
                raise AssertionError(f"setting-dependent input sampler at seed {seed}")
            matched_input_checks += len(settings) - 1
            for setting, episode in zip(settings, episodes):
                certificate = P.certify(episode, execute)
                if certificate["survivors"] != [setting]:
                    raise AssertionError("minimum lesson did not identify the setting")
                racket_cases += len(episode["train"]) * len(settings) + len(episode["test"])
                profiles = [P.scene_profile(pair["input"]) for pair in episode["train"] + episode["test"]]
                final = profiles[-1]
                if final["size"] != [30, 30] or final["occupied_quadrants"] != [0, 1, 2, 3]:
                    raise AssertionError("30x30 stress scene lacks full-canvas spread")
                if final["nonzero_count"] < 35 or not final["touches_boundary"]:
                    raise AssertionError("30x30 stress scene is not substantive/boundary-touching")
                key = json.dumps(setting, sort_keys=True)
                for pair in episode["train"]:
                    teaching_profiles[key].add(json.dumps(_selected_signature(pair["input"], setting)))
                fixed_slot_intermediates[key].add(json.dumps(_selected_signature(episode["test"][0]["input"], setting)))
                minimum_records.append({
                    "seed": seed,
                    "settings": setting,
                    "input_hashes": input_banks[0],
                    "survivors": certificate["survivors"],
                    "extra_refutations": certificate["extra_refutations"],
                    "query_profiles": profiles[-4:],
                })

        for setting in settings:
            episode = P.generate(max_seed, setting, 6, 4)
            certificate = P.certify(episode, execute)
            if certificate["survivors"] != [setting]:
                raise AssertionError("six-demo lesson did not identify the setting")
            racket_cases += len(episode["train"]) * len(settings) + len(episode["test"])
            maximum_records.append({
                "seed": max_seed,
                "settings": setting,
                "counts": {"demos": len(episode["train"]), "queries": len(episode["test"])},
                "survivors": certificate["survivors"],
                "max_demo_profile": P.scene_profile(episode["train"][-1]["input"]),
            })

        # Directly compare every declared program on one shared 30x30 input.
        shared = P.generate(min_seeds[0], settings[0], 2, 4)["test"][-1]["input"]
        outputs = []
        for setting in settings:
            actual = execute(P.program(setting), shared)
            expected = P.transform(shared, setting)
            if actual != expected:
                raise AssertionError("Python mirror differs from protected Racket")
            outputs.append(P.grid_digest(actual))
        racket_cases += len(settings)
        if len(set(outputs)) != len(settings):
            raise AssertionError("shared 30x30 control does not distinguish all settings")

        # Search a larger Python-only pool for crossed controls. The scene slot
        # fixes dimensions/profile position; selected intermediates must still vary.
        for seed in range(96):
            episode = P.generate(seed, settings[0], 2, 4)
            grid = episode["test"][0]["input"]
            profile = P.scene_profile(grid)
            for setting in settings:
                skey = json.dumps(setting, sort_keys=True)
                signature = json.dumps(_selected_signature(grid, setting))
                fixed_slot_intermediates[skey].add(signature)
                nuisance_key = (skey, signature)
                nuisance_candidates.setdefault(nuisance_key, []).append({
                    "seed": seed,
                    "source_basis": profile["source_basis"],
                    "target_basis": profile["target_basis"],
                    "input_sha256": P.grid_digest(grid),
                })

        if any(len(values) < 3 for values in fixed_slot_intermediates.values()):
            raise AssertionError("fixed-slot controls do not vary the intended intermediate")

        nuisance_witnesses = []
        for (setting_key, signature), rows in nuisance_candidates.items():
            for i, left in enumerate(rows):
                for right in rows[i + 1:]:
                    if (left["source_basis"], left["target_basis"]) != (
                        right["source_basis"], right["target_basis"]
                    ):
                        nuisance_witnesses.append({
                            "settings": json.loads(setting_key),
                            "intermediate": json.loads(signature),
                            "left": left,
                            "right": right,
                        })
                        break
                if nuisance_witnesses and nuisance_witnesses[-1]["settings"] == json.loads(setting_key):
                    break
        covered = {json.dumps(row["settings"], sort_keys=True) for row in nuisance_witnesses}
        if covered != set(teaching_profiles):
            raise AssertionError("could not vary frame nuisance while holding each intermediate fixed")

        # Certificate/export-adjacent negative probes.
        rejected: list[str] = []
        clean = P.generate(min_seeds[0], settings[0], 2, 4)
        duplicate = copy.deepcopy(clean)
        duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
        _expect_reject("duplicate_input", lambda: P.certify(duplicate), rejected)
        missing_query = copy.deepcopy(clean)
        missing_query["test"].pop()
        _expect_reject("wrong_query_count", lambda: P.certify(missing_query), rejected)
        forged = copy.deepcopy(clean)
        forged["train"][0]["output"] = copy.deepcopy(forged["train"][0]["input"])
        _expect_reject("forged_demo_label", lambda: P.certify(forged), rejected)
        _expect_reject("boolean_seed", lambda: P.generate(True, settings[0], 2, 4), rejected)
        _expect_reject("boolean_demo_count", lambda: P.generate(1, settings[0], True, 4), rejected)
        _expect_reject("undeclared_setting", lambda: P.generate(1, {"axis": "x", "extreme": "max"}, 2, 4), rejected)

        identity = {key: self_value for key, self_value in execute.identity.items()
                    if key in {"schema", "backend", "protected", "binary_sha256", "prelude_sha256",
                               "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256"}}
        evaluations = execute.evaluations

    source_files = [HERE / "prototype.py", HERE / "adapter.py", HERE / "promotion.json", HERE / "canonical.rkt"]
    return {
        "schema": "c2f4b540f2fb-parametric-adversarial-v1",
        "status": "passed",
        "task_id": P.TASK_ID,
        "scope": {
            "minimum_demo_seeds": min_seeds,
            "maximum_demo_seed": max_seed,
            "settings": settings,
            "declared_shortcuts": list(P.EXTRA_RIVALS),
            "cross_control_search_seeds": [0, 95],
            "finite_limit": "Bounded settings/seeds/rivals; not a proof against every conceivable program.",
        },
        "checks": {
            "minimum_episodes": len(minimum_records),
            "maximum_episodes": len(maximum_records),
            "matched_input_comparisons": matched_input_checks,
            "protected_racket_evaluations": evaluations,
            "expected_racket_case_floor": racket_cases,
            "minimum_records": minimum_records,
            "maximum_records": maximum_records,
            "fixed_slot_intermediate_counts": {key: len(values) for key, values in fixed_slot_intermediates.items()},
            "fixed_intermediate_varied_nuisance": nuisance_witnesses[:8],
            "negative_probes_rejected": rejected,
        },
        "racket": identity,
        "source_sha256": {str(path.relative_to(REPO)): _sha(path) for path in source_files},
        "remaining_failures": [],
        "owner_acceptance": "not_performed",
        "training_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--max-seed", type=int, default=63)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    seeds = args.seeds or [0, 1, 17]
    if len(set(seeds)) != len(seeds) or any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError("--seed values must be distinct nonnegative integers")
    report = run(seeds, args.max_seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    args.out.write_bytes(_json_bytes(report))
    print(json.dumps({
        "status": report["status"],
        "minimum_episodes": report["checks"]["minimum_episodes"],
        "maximum_episodes": report["checks"]["maximum_episodes"],
        "protected_racket_evaluations": report["checks"]["protected_racket_evaluations"],
        "negative_probes_rejected": report["checks"]["negative_probes_rejected"],
        "out": str(args.out.resolve()),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
