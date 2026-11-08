#!/usr/bin/env python3
"""Proposed four-setting reflection/join family, isolated from canonical code."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
from dataclasses import asdict, dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import sys

from racket_episode import JSON_HASH_ALGORITHM, RacketOracle, json_hash, public_challenge, score_episode, text_hash, validate_grid


TASK_ID = "d89cff1052a2"
VERSION = "0.1.0-prototype"
AXES = ("vertical", "horizontal")
ORDERS = ("reflected_first", "original_first")


@dataclass(frozen=True)
class Setting:
    axis: str = "vertical"
    order: str = "reflected_first"

    def __post_init__(self):
        if self.axis not in AXES or self.order not in ORDERS:
            raise ValueError(f"axis must be one of {AXES}; order must be one of {ORDERS}")

    @property
    def key(self):
        return f"{self.axis}__{self.order}"


DEFAULT = Setting()
ALL_SETTINGS = tuple(Setting(axis, order) for axis in AXES for order in ORDERS)


def _rng(seed: int, purpose: str) -> random.Random:
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer, not bool")
    digest = text_hash(f"{TASK_ID}/{VERSION}/{seed}/{purpose}")
    return random.Random(int(digest, 16))


def sample_setting(seed: int) -> Setting:
    """Draw once before the episode; no pair function resamples the rule."""
    return _rng(seed, "episode-parameters").choice(ALL_SETTINGS)


def program_for(setting: Setting = DEFAULT) -> str:
    if not isinstance(setting, Setting):
        raise TypeError("setting must be a Setting")
    concat, reflect = ("vconcat", "flip-ud") if setting.axis == "vertical" else ("hconcat", "flip-lr")
    pieces = [f"({reflect} g)", "g"]
    if setting.order == "original_first":
        pieces.reverse()
    return f"(rule! ({concat} {' '.join(pieces)}))"


def programs() -> dict[str, str]:
    return {setting.key: program_for(setting) for setting in ALL_SETTINGS}


def validate_input(grid: list, setting: Setting = DEFAULT) -> None:
    validate_grid(grid)
    max_height, max_width = (15, 30) if setting.axis == "vertical" else (30, 15)
    if not (3 <= len(grid) <= max_height and 3 <= len(grid[0]) <= max_width):
        raise ValueError(f"input dimensions must be 3..{max_height} by 3..{max_width} for {setting.axis}")
    counts = Counter(value for row in grid for value in row)
    if not 2 <= len(counts) <= 4 or min(counts.values()) < 2:
        raise ValueError("input requires 2..4 colours, each used at least twice")


def draw_input(seed: int, pair_index: int, height: int, width: int, *, palette_size: int = 2) -> list:
    """Deterministic inputs with visible reflection about both axes.

    The same seed/index/shape gives the same input under every setting. This
    common support lets every declared parameter rival execute lawfully on all
    ordinary episode pairs. Symmetric lawful inputs are retained as diagnostics.
    """
    if type(pair_index) is not int or pair_index < 0:
        raise ValueError("pair_index must be a nonnegative literal integer")
    if any(type(value) is not int for value in (height, width, palette_size)):
        raise TypeError("dimensions and palette_size must be literal integers")
    if not (3 <= height <= 30 and 3 <= width <= 30 and 2 <= palette_size <= 4):
        raise ValueError("dimensions must be 3..30 and palette_size 2..4")
    rng = _rng(seed, f"input/{pair_index}/{height}/{width}/{palette_size}")
    palette = rng.sample(range(10), palette_size)
    for _ in range(128):
        values = palette * 2 + [rng.choice(palette) for _ in range(height * width - 2 * palette_size)]
        rng.shuffle(values)
        grid = [values[row * width:(row + 1) * width] for row in range(height)]
        if grid != list(reversed(grid)) and any(row != row[::-1] for row in grid):
            return grid
    raise RuntimeError("could not draw an asymmetric input within the bounded attempt budget")


def generate_episode(seed: int, *, setting: Setting = DEFAULT, oracle: RacketOracle) -> dict:
    """Three small demos and one larger query, all labelled by one fixed rule."""
    _rng(seed, "validate-seed")
    program = program_for(setting)
    shapes = ((3, 4, 2), (4, 7, 3), (6, 5, 4), (15, 15, 4))
    pairs = []
    for index, (height, width, palette_size) in enumerate(shapes):
        grid = draw_input(seed, index, height, width, palette_size=palette_size)
        validate_input(grid, setting)
        pairs.append({"input": grid, "output": oracle.label(program, grid)})
    return {
        "schema": "d89cff1052a2-parametric-episode-v1",
        "json_hash_algorithm": JSON_HASH_ALGORITHM,
        "task_id": TASK_ID,
        "original_task": "training:4c4377d9",
        "version": VERSION,
        "approval_status": "unapproved_prototype",
        "seed": seed,
        "parameters": asdict(setting),
        "program": program,
        "program_sha256": text_hash(program),
        "label_backend": "racket",
        "pair_input_sha256": [json_hash(pair["input"]) for pair in pairs],
        "train": pairs[:3],
        "test": pairs[3:],
    }


def ambiguity_fixture(axis: str, *, oracle: RacketOracle) -> dict:
    """A diagnostic counterexample, deliberately outside the ordinary sampler."""
    setting = Setting(axis, "reflected_first")
    symmetric = [
        [[1, 2, 1], [2, 1, 2], [1, 2, 1]],
        [[3, 3, 4, 4, 3, 3], [4, 3, 3, 3, 3, 4], [3, 3, 4, 4, 3, 3]],
        [[5, 6, 6, 5], [6, 5, 5, 6], [6, 5, 5, 6], [5, 6, 6, 5]],
    ]
    query = [[1, 1, 2], [1, 2, 1], [2, 2, 1]]
    inputs = symmetric + [query]
    for grid in inputs:
        validate_input(grid, setting)
    pairs = [{"input": grid, "output": oracle.label(program_for(setting), grid)} for grid in inputs]
    episode = {"train": pairs[:3], "test": pairs[3:]}
    return {
        "kind": "deliberate_diagnostic_ambiguity_fixture_not_a_solve_attempt",
        "parameters": asdict(setting),
        "program": program_for(setting),
        "program_sha256": text_hash(program_for(setting)),
        "episode": episode,
        "audit": score_episode(episode, programs(), setting.key, oracle=oracle),
    }


def repository_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "shared/data/canonical/puzzles.jsonl").is_file():
            return candidate
    raise FileNotFoundError("prototype must be inside its own repository or copied task-test runtime")


@lru_cache(maxsize=1)
def canonical_context() -> dict:
    from reviewer_support import canonical_pairs

    root = repository_root()
    ledger = root / "shared/data/canonical/puzzles.jsonl"
    rows = []
    with ledger.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    sources = {row["program_solution"] for row in rows}
    if len(sources) != 1:
        raise ValueError("expected one unmodified selected canonical program")
    program = sources.pop()
    return {
        "program": program,
        "program_sha256": text_hash(program),
        "canonical_ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
        "pairs": canonical_pairs(TASK_ID, root=root),
    }


def source_hashes() -> dict[str, str]:
    root = repository_root()
    home = Path(__file__).resolve().parent
    files = [path for path in home.iterdir() if path.is_file() and path.suffix in (".py", ".md")]
    files.extend((root / f"generators/{TASK_ID}/generator.py", root / f"generators/{TASK_ID}/tests/test_parametric.py"))
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(files)}


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def materialize_evidence(destination: Path, *, seeds: list[int]) -> dict:
    """Emit complete source-bound evidence; never overwrite an existing run."""
    destination = Path(destination)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("supply a nonempty list of distinct integer seeds")
    for seed in seeds:
        _rng(seed, "validate-seed")
    destination.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": "d89cff1052a2-parametric-evidence-v1",
        "json_hash_algorithm": JSON_HASH_ALGORITHM,
        "status": "incomplete",
        "approval_status": "unapproved_prototype",
        "task_id": TASK_ID,
        "version": VERSION,
        "parameters": {"axis": list(AXES), "order": list(ORDERS), "default": asdict(DEFAULT)},
        "input_bounds": {"vertical": [3, 15, 3, 30], "horizontal": [3, 30, 3, 15]},
        "source_sha256": source_hashes(),
        "seeds": seeds,
        "command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "programs": {}, "episodes": [], "diagnostics": [], "boundaries": [],
        "limitations": [
            "Finite selected seeds and the declared four parameter settings only; not a proof against arbitrary rival programs.",
            "Ordinary episodes use common 3..15 by 3..15 support, including a larger 15x15 query; maximum axis-specific inputs are separate boundary probes.",
            "Ordinary inputs are asymmetric on both axes; symmetric lawful inputs are covered by canonical data and deliberately ambiguous diagnostics.",
            "The prototype is proposed and unapproved. It does not alter canonical generation, rule authority, runtime interfaces, or training admission.",
        ],
    }
    _write_json(destination / "report.json", report)
    with RacketOracle() as oracle:
        report["runtime"] = oracle.runtime_identity
        candidate_programs = programs()
        for setting in ALL_SETTINGS:
            relative = f"private/programs/{setting.key}.rkt"
            path = destination / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(candidate_programs[setting.key])
            report["programs"][setting.key] = {"path": relative, "sha256": text_hash(candidate_programs[setting.key])}
        canonical = canonical_context()
        canonical_checks = [{"input": pair["input"], "expected": pair["output"],
                             "executed": oracle.label(program_for(DEFAULT), pair["input"])}
                            for pair in canonical["pairs"]]
        report["canonical"] = {
            "exact_program_match": program_for(DEFAULT) == canonical["program"],
            "program_sha256": canonical["program_sha256"],
            "ledger_sha256": canonical["canonical_ledger_sha256"],
            "passed": all(pair["expected"] == pair["executed"] for pair in canonical_checks),
            "pair_count": len(canonical_checks),
            "pairs": canonical_checks,
        }
        for seed in seeds:
            for setting in ALL_SETTINGS:
                episode = generate_episode(seed, setting=setting, oracle=oracle)
                audit = score_episode(episode, candidate_programs, setting.key, oracle=oracle)
                number = len(report["episodes"])
                name = f"episode-{number:04d}"
                public_path, private_path, audit_path = f"public/{name}.json", f"private/episodes/{name}.json", f"private/audits/{name}.json"
                public = public_challenge(episode)
                _write_json(destination / public_path, public)
                _write_json(destination / private_path, episode)
                _write_json(destination / audit_path, audit)
                report["episodes"].append({
                    "seed": seed, "parameters": asdict(setting),
                    "public_path": public_path, "private_path": private_path, "audit_path": audit_path,
                    "public_sha256": json_hash(public), "episode_sha256": json_hash(episode), "audit_sha256": json_hash(audit),
                    "file_sha256": {name: hashlib.sha256((destination / relative).read_bytes()).hexdigest()
                                    for name, relative in (("public", public_path), ("episode", private_path), ("audit", audit_path))},
                    "status": audit["status"], "parameters_identified": audit["parameters_identified"],
                    "rotations": len(audit["rotations"]),
                    "input_shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["train"] + episode["test"]],
                })
        witness = [[1, 1, 2], [1, 2, 1], [2, 2, 1]]
        outputs = {name: oracle.label(program, witness) for name, program in candidate_programs.items()}
        report["distinguishing_input"] = {"input": witness, "outputs": outputs, "distinct_outputs": len({json_hash(value) for value in outputs.values()})}
        for setting in ALL_SETTINGS:
            height, width = (15, 30) if setting.axis == "vertical" else (30, 15)
            grid = draw_input(101, 8, height, width, palette_size=4)
            validate_input(grid, setting)
            output = oracle.label(program_for(setting), grid)
            report["boundaries"].append({"parameters": asdict(setting), "seed": 101, "pair_index": 8,
                                         "input": grid, "output": output, "input_sha256": json_hash(grid),
                                         "output_shape": [len(output), len(output[0])]})
        for axis in AXES:
            fixture = ambiguity_fixture(axis, oracle=oracle)
            relative = f"private/diagnostics/{axis}-symmetric-demos.json"
            _write_json(destination / relative, fixture)
            report["diagnostics"].append({"path": relative, "sha256": json_hash(fixture), "axis": axis,
                                          "file_sha256": hashlib.sha256((destination / relative).read_bytes()).hexdigest(),
                                          "status": fixture["audit"]["status"],
                                          "ambiguous_rotations": sum(row["status"] == "ambiguous" for row in fixture["audit"]["rotations"])})
        report["racket_executions"] = oracle.executions
    report["summary"] = {
        "episode_count": len(report["episodes"]),
        "rotation_count": sum(row["rotations"] for row in report["episodes"]),
        "ambiguous_episodes": sum(row["status"] == "ambiguous" for row in report["episodes"]),
        "error_episodes": sum(row["status"] == "error" for row in report["episodes"]),
        "all_parameter_rivals_refuted": all(row["parameters_identified"] for row in report["episodes"]),
        "diagnostic_ambiguity_fixtures_detected": sum(row["status"] == "ambiguous" for row in report["diagnostics"]),
    }
    report["status"] = "pass" if (
        report["canonical"]["exact_program_match"] and report["canonical"]["passed"]
        and report["summary"]["all_parameter_rivals_refuted"]
        and not report["summary"]["ambiguous_episodes"] and not report["summary"]["error_episodes"]
        and report["distinguishing_input"]["distinct_outputs"] == 4
        and report["summary"]["diagnostic_ambiguity_fixtures_detected"] == 2
        and all(row["output_shape"] == [30, 30] for row in report["boundaries"])
    ) else "fail"
    _write_json(destination / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    evidence = sub.add_parser("evidence", help="materialize all four settings, rival audits, and diagnostics")
    evidence.add_argument("--out", type=Path, required=True)
    evidence.add_argument("--seeds", type=int, nargs="+", default=[0, 17, 20261022])
    episode = sub.add_parser("episode", help="materialize one proposed episode")
    episode.add_argument("--out", type=Path, required=True)
    episode.add_argument("--seed", type=int, default=17)
    episode.add_argument("--axis", choices=AXES, default=None)
    episode.add_argument("--order", choices=ORDERS, default=None)
    episode.add_argument("--sample-parameters", action="store_true")
    args = parser.parse_args(argv)
    if args.action == "evidence":
        report = materialize_evidence(args.out, seeds=args.seeds)
        print(json.dumps({"status": report["status"], "out": str(args.out), **report["summary"]}, sort_keys=True))
        return 0 if report["status"] == "pass" else 1
    if args.sample_parameters and (args.axis is not None or args.order is not None):
        parser.error("--sample-parameters cannot be combined with fixed --axis or --order")
    setting = sample_setting(args.seed) if args.sample_parameters else Setting(args.axis or DEFAULT.axis, args.order or DEFAULT.order)
    args.out.mkdir(parents=True, exist_ok=False)
    with RacketOracle() as oracle:
        value = generate_episode(args.seed, setting=setting, oracle=oracle)
        audit = score_episode(value, programs(), setting.key, oracle=oracle)
        _write_json(args.out / "private/episode.json", value)
        _write_json(args.out / "private/audit.json", audit)
        _write_json(args.out / "private/provenance.json", {"source_sha256": source_hashes(), "runtime": oracle.runtime_identity,
                                                        "command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]}})
        program_path = args.out / "private/program.rkt"
        program_path.write_text(value["program"])
        _write_json(args.out / "public/challenge.json", public_challenge(value))
    print(json.dumps({"status": audit["status"], "parameters_identified": audit["parameters_identified"], "out": str(args.out)}, sort_keys=True))
    return 0 if audit["status"] == "no_ambiguity_found" and audit["parameters_identified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
