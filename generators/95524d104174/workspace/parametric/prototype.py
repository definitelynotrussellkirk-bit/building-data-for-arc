"""Proposed, task-local frame-color episodes; labels come only from Racket."""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import re
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (canonical_pairs, canonical_path, find_root, normalize_grid,
                              public_challenge_bytes, public_challenge_id)

TASK_ID = "95524d104174"
FRAME_COLORS = (4, 2, 8)
DEFAULT_FRAME_COLOR = 4


def sha256(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


@lru_cache(maxsize=4)
def canonical_rule(*, root=None):
    root = find_root(__file__) if root is None else Path(root)
    sources = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if TASK_ID in line:
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    sources.append(row["program_solution"])
    if len(sources) != 1:
        raise ValueError("The prototype requires one exact selected canonical rule.")
    return sources[0]


def instantiate_rule(frame_color=DEFAULT_FRAME_COLOR, *, root=None):
    if type(frame_color) is not int or frame_color not in FRAME_COLORS:
        raise ValueError(f"frame_color must be one of {FRAME_COLORS}, as a Python int")
    source = canonical_rule(root=root)
    # In this exact authority the standalone literal is the cellmap's paint color.
    # Keep the entire canonical source unchanged for the original setting.
    pattern = r"(?m)^([ \t]*)4([ \t]*)$"
    changed, count = re.subn(pattern, lambda m: m[1] + str(frame_color) + m[2], source)
    if count != 1:
        raise ValueError("Canonical frame-color site changed; reassess the prototype.")
    return changed


def evaluate(bridge, program, grid):
    grid = normalize_grid(grid)
    # This authority is already a native Racket lambda, including its h/w binds.
    # The public helper removes only its REPL registration wrapper.
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)"):
        raise ValueError("Expected the selected task's native Racket lambda.")
    datum = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


def choose_frame_color(seed):
    if type(seed) is not int:
        raise ValueError("seed must be a Python int")
    return FRAME_COLORS[seed % len(FRAME_COLORS)]


def generate_inputs(seed):
    choose_frame_color(seed)  # Validate without sharing the input RNG with the rule.
    rng = random.Random(f"{TASK_ID}:frame-color-inputs:{seed}")
    inputs = []
    for index in range(4):
        h, w = rng.randint(5, 12), rng.randint(5, 12)
        if index == 0 and h == w:
            w = 5 + (w - 4) % 8
        row, col = rng.randint(1, h - 2), rng.randint(1, w - 2)
        vertical, horizontal = rng.sample(range(1, 10), 2)
        grid = [[0] * w for _ in range(h)]
        for r in range(h):
            grid[r][col] = vertical
        grid[row] = [horizontal] * w
        grid[row][col] = vertical if index % 2 == 0 else horizontal
        inputs.append(grid)
    return inputs


def make_episode(bridge, seed, *, frame_color=None):
    chosen = choose_frame_color(seed) if frame_color is None else frame_color
    program = instantiate_rule(chosen)
    return {
        "seed": seed,
        "parameters": {"frame_color": chosen},
        "parameter_choice": "seed_modulo_three" if frame_color is None else "explicit_once_per_episode",
        "racket_program": program,
        "racket_sha256": sha256(program),
        "pairs": [{"input": grid, "output": evaluate(bridge, program, grid)}
                  for grid in generate_inputs(seed)],
    }


def public_challenge(episode):
    return json.loads(public_challenge_bytes({"train": episode["pairs"][:3],
                     "test": [{"input": episode["pairs"][3]["input"]}]}))


def analyze_episode(bridge, episode):
    pairs = episode["pairs"]
    chosen = episode["parameters"]["frame_color"]
    alternatives = {}
    for color in FRAME_COLORS:
        if color != chosen:
            program = instantiate_rule(color)
            alternatives[str(color)] = [evaluate(bridge, program, pair["input"]) for pair in pairs]

    def score(query):
        demonstrations = [i for i in range(4) if i != query]
        rivals = []
        for color, outputs in alternatives.items():
            refutations = [i for i in demonstrations if outputs[i] != pairs[i]["output"]]
            rivals.append({
                "name": f"frame_color={color}", "parameters": {"frame_color": int(color)},
                "refuting_demonstration_indices": refutations,
                "fits_demonstrations": not refutations,
                "query_differs": outputs[query] != pairs[query]["output"],
            })
        ambiguous = any(r["fits_demonstrations"] and r["query_differs"] for r in rivals)
        return {"query_index": query, "demonstration_indices": demonstrations,
                "rivals": rivals, "status": "ambiguous" if ambiguous else "no_ambiguity_found"}

    return {"production": score(3), "rotations": [score(i) for i in range(4)],
            "counterfactual_outputs": alternatives}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def materialize(out, *, seed=0, bridge=None):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    report = {
        "schema": "95524d104174-frame-color-prototype-v1", "status": "incomplete",
        "scope": "proposed task-local extension; not a canonical rule change or production approval",
        "parameter_spec": {"frame_color": {"allowed": list(FRAME_COLORS), "original_default": 4}},
        "choice_policy": "One value per episode: [4,2,8][seed % 3]; three consecutive seeds cover all settings.",
        "lesson_policy": "Three demonstrations followed by one query; also test all four single-query rotations.",
        "input_domain": "5..12 rows/columns, zero background, two distinct nonzero full crossing lines, interior crossing; either line may own the center. Line colors may equal frame_color.",
        "limitations": "Three seeds and two declared color rivals per episode only. The input sampler is a bounded cross-only subset, not the selected production generator. No production parametric API or approval is added.",
        "source_hashes": {"prototype.py": sha256(Path(__file__).read_bytes()),
                          "canonical_racket": sha256(canonical_rule(root=root))},
        "invocation": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "canonical_checks": [], "episodes": [],
    }
    try:
        with (nullcontext(bridge) if bridge is not None else RacketBridge()) as active:
            report["runtime"] = {"python": sys.version, "racket_version": active.eval_text("(version)"),
                                 "bridge_sha256": sha256(Path(sys.modules[RacketBridge.__module__].__file__).read_bytes()),
                                 "prelude_sha256": sha256(Path(active.prelude_path).read_bytes())}
            for color in FRAME_COLORS:
                path = out / "private" / "rules" / f"frame-{color}.rkt"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(instantiate_rule(color), encoding="utf-8")
            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = evaluate(active, instantiate_rule(4), pair["input"])
                report["canonical_checks"].append({
                    "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
                    "input": pair["input"], "expected": pair["output"], "actual": actual,
                    "passed": actual == pair["output"],
                })
            all_inputs = set()
            for index in range(3):
                episode = make_episode(active, seed + index)
                scores = analyze_episode(active, episode)
                public = public_challenge(episode)
                public_path = f"public/{public_challenge_id(public)}.json"
                private_path = f"private/episode-{index + 1:03d}.json"
                (out / public_path).parent.mkdir(parents=True, exist_ok=True)
                (out / public_path).write_bytes(public_challenge_bytes(public))
                write_json(out / private_path, {**episode, "rival_checks": scores})
                report["episodes"].append({
                    "seed": episode["seed"], "parameters": episode["parameters"],
                    "racket_sha256": episode["racket_sha256"],
                    "public_path": public_path, "private_path": private_path,
                    "production": scores["production"], "rotations": scores["rotations"],
                })
                all_inputs.update(json.dumps(p["input"], separators=(",", ":")) for p in episode["pairs"])
                if episode["parameters"]["frame_color"] == 4:
                    report["setting_witness"] = {
                        "input": episode["pairs"][0]["input"],
                        "outputs": {"4": episode["pairs"][0]["output"],
                                    **{c: grids[0] for c, grids in scores["counterfactual_outputs"].items()}},
                        "racket_hashes": {str(c): sha256(instantiate_rule(c)) for c in FRAME_COLORS},
                    }
            production_ambiguities = sum(e["production"]["status"] == "ambiguous" for e in report["episodes"])
            rotation_ambiguities = sum(r["status"] == "ambiguous" for e in report["episodes"] for r in e["rotations"])
            passed = sum(c["passed"] for c in report["canonical_checks"])
            report["counts"] = {
                "canonical_labels_checked": len(report["canonical_checks"]), "canonical_labels_passed": passed,
                "episodes": 3, "demonstrations": 9, "queries": 3,
                "episode_labels": 12, "counterfactual_labels": 24,
                "production_ambiguities": production_ambiguities, "rotation_ambiguities": rotation_ambiguities,
                "query_rotations": 12, "unique_episode_inputs": len(all_inputs),
            }
            report["status"] = ("no_ambiguity_found" if passed == len(report["canonical_checks"])
                                and not production_ambiguities and not rotation_ambiguities else "failed")
            report["files"] = {str(path.relative_to(out)): {"sha256": sha256(path.read_bytes()), "bytes": path.stat().st_size}
                               for path in sorted(out.rglob("*")) if path.is_file()}
    except Exception as exc:
        report["status"] = "error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        write_json(out / "report.json", report)
        raise
    write_json(out / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0, help="First of three consecutive episode seeds")
    parser.add_argument("--out", type=Path, required=True, help="New evidence directory; never overwritten")
    args = parser.parse_args(argv)
    report = materialize(args.out, seed=args.seed)
    print(json.dumps({"status": report["status"], "counts": report["counts"],
                      "report": str(args.out / "report.json")}, sort_keys=True))
    return int(report["status"] != "no_ambiguity_found")


if __name__ == "__main__":
    raise SystemExit(main())
