#!/usr/bin/env python3
"""Build source-bound causal and learnability evidence for 2fb0197be694."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
from arcpuzzles.review_sequential_replay import replay_witness

TASK_ID = "2fb0197be694"
ROOT = find_root(__file__)
CHECK = ROOT.parent / "checks" / TASK_ID
QUAL = CHECK / "qualification"
OUT = CHECK / "causal-self-audit"
CANON = ((2, 0), (0, 2), (1, 1), (2, 2))
ORIENTATIONS = {
    ((-1, 0), (0, 1)), ((-1, 0), (0, -1)),
    ((1, 0), (0, 1)), ((1, 0), (0, -1)),
    ((0, 1), (-1, 0)), ((0, 1), (1, 0)),
    ((0, -1), (-1, 0)), ((0, -1), (1, 0)),
}


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def one(grid, color):
    found = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if len(found) != 1:
        raise ValueError(f"expected one marker {color}, got {found}")
    return found[0]


def bits(grid):
    origin = one(grid, 2)
    x = one(grid, 3)
    y = one(grid, 4)
    vx = (x[0] - origin[0], x[1] - origin[1])
    vy = (y[0] - origin[0], y[1] - origin[1])
    if (vx, vy) not in ORIENTATIONS:
        raise ValueError(f"bad frame vectors {(vx, vy)}")
    result = []
    for u, v in CANON:
        row = origin[0] + u * vx[0] + v * vy[0]
        col = origin[1] + u * vx[1] + v * vy[1]
        result.append(int(grid[row][col] == 8))
    return tuple(result)


def direct(v): return tuple(v)

def running(v):
    state = 0
    out = []
    for bit in v:
        state ^= bit
        out.append(state)
    return tuple(out)


def reverse_direct(v): return tuple(reversed(v))

def suffix_parity(v):
    state = 0
    out = [0, 0, 0, 0]
    for index in range(3, -1, -1):
        state ^= v[index]
        out[index] = state
    return tuple(out)


def adjacent_xor(v): return (v[0], v[0] ^ v[1], v[1] ^ v[2], v[2] ^ v[3])

def count_prefix(v): return tuple(int(index < sum(v)) for index in range(4))

def count_suffix(v): return tuple(int(index >= 4 - sum(v)) for index in range(4))

def global_parity(v): return (sum(v) % 2,) * 4

def swap_axes(v): return (v[1], v[0], v[2], v[3])


def as_grid(v): return [[8 if bit else 0 for bit in v]]


def main() -> int:
    qualification = json.loads((QUAL / "qualification.json").read_text())
    execution = json.loads((QUAL / "execution.json").read_text())
    if execution.get("racket", {}).get("protected") is not True:
        raise ValueError("qualification is not protected-Racket evidence")

    transforms = {
        "direct": direct,
        "running_parity": running,
        "reverse_direct": reverse_direct,
        "suffix_parity": suffix_parity,
        "adjacent_xor": adjacent_xor,
        "count_prefix": count_prefix,
        "count_suffix": count_suffix,
        "global_parity": global_parity,
        "swap_axis_offsets": swap_axes,
    }
    episode_reports = []
    findings = []
    for episode in execution["episodes"]:
        chosen = episode["settings"]["encoding"]
        demo_bits = [bits(pair["input"]) for pair in episode["train"]]
        query_bits = [bits(pair["input"]) for pair in episode["test"]]
        candidates = {}
        for name, transform in transforms.items():
            fits = all(as_grid(transform(value)) == pair["output"]
                       for value, pair in zip(demo_bits, episode["train"]))
            disagreements = [
                index for index, (value, pair) in enumerate(zip(query_bits, episode["test"]))
                if as_grid(transform(value)) != pair["output"]
            ]
            candidates[name] = {"fits_all_demos": fits, "query_disagreements": disagreements}
            if name != chosen and fits and disagreements:
                findings.append({"settings": episode["settings"], "seed": episode["seed"],
                                 "rival": name, "query_disagreements": disagreements})
        fixed = episode["train"][0]["output"]
        fixed_fits = all(pair["output"] == fixed for pair in episode["train"])
        fixed_disagreements = [index for index, pair in enumerate(episode["test"])
                               if pair["output"] != fixed]
        candidates["fixed_first_demo_output"] = {
            "fits_all_demos": fixed_fits,
            "query_disagreements": fixed_disagreements,
        }
        if fixed_fits and fixed_disagreements:
            findings.append({"settings": episode["settings"], "seed": episode["seed"],
                             "rival": "fixed_first_demo_output",
                             "query_disagreements": fixed_disagreements})
        survivors = [name for name, row in candidates.items() if row["fits_all_demos"]]
        if survivors != [chosen]:
            raise ValueError(f"unexpected finite survivors for {chosen}: {survivors}")
        episode_reports.append({
            "settings": episode["settings"],
            "seed": episode["seed"],
            "program_sha256": episode["program_sha256"],
            "demo_occupancy_bits": [list(value) for value in demo_bits],
            "query_occupancy_bits": [list(value) for value in query_bits],
            "candidates": candidates,
            "survivors": survivors,
        })

    audit = {
        "schema": "arcpuzzles-visible-demo-self-audit-v1",
        "task_id": TASK_ID,
        "source_binding": qualification["source_binding"],
        "qualification_execution_sha256": hashlib.sha256((QUAL / "execution.json").read_bytes()).hexdigest(),
        "racket": execution["racket"],
        "scope": {
            "episodes": len(episode_reports),
            "settings": ["direct", "running_parity"],
            "seeds": sorted({row["seed"] for row in episode_reports}),
            "rivals": list(transforms) + ["fixed_first_demo_output"],
            "question": "Can a declared wrong rule fit every visible demonstration yet disagree on a query?",
        },
        "episodes": episode_reports,
        "findings": findings,
        "result": "finding" if findings else "no_surviving_wrong_rule_in_finite_scope",
        "limits": "Finite declared-rival audit over the four qualified episodes; not a uniqueness proof against arbitrary programs.",
    }
    dump(OUT / "visible-demo-self-audit.json", audit)
    if findings:
        raise ValueError(f"visible-demo shortcut findings require repair: {findings}")

    running_episodes = [ep for ep in execution["episodes"]
                        if ep["settings"] == {"encoding": "running_parity"}]
    cases = []
    runtime = ROOT / "shared" / "runtime"
    with _local_imports(runtime, runtime):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for episode, query_index in zip(running_episodes, (0, 2)):
                pair = episode["test"][query_index]
                source = episode["program"]
                needle = "(p0 b0)"
                if source.count(needle) != 1:
                    raise ValueError("qualified running-parity source changed")
                counterfactual = source.replace(
                    needle, "(p0 (remainder (+ b0 1) 2))"
                )
                actual = apply(source, pair["input"])
                alternative = apply(counterfactual, pair["input"])
                if actual != pair["output"] or actual == alternative:
                    raise ValueError("causal witness execution did not match qualification/change output")
                recovered = bits(pair["input"])
                cases.append({
                    "input": pair["input"],
                    "settings": episode["settings"],
                    "intermediate_value": {
                        "occupancy_bits": list(recovered),
                        "running_parity": list(running(recovered)),
                        "ablated_value": [1 - recovered[0], *recovered[1:]],
                    },
                    "program": source,
                    "output": actual,
                    "counterfactual_program": counterfactual,
                    "counterfactual_output": alternative,
                    "ablation": "wrong_intermediate",
                })
        finally:
            bridge.close()
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise ValueError("causal builder did not use protected Racket")

    descriptions = {
        "step_a": "Infer the directed 2/3/4 local frame and read the four color-8 occupancy bits at offsets (2,0), (0,2), (1,1), and (2,2).",
        "intermediate": "The input-dependent four-bit occupancy vector in canonical local-coordinate order.",
        "step_b": "For encoding=running_parity, fold that vector left-to-right so each output bit is the XOR of the current occupancy bit and the preceding parity state, then render 1 as color 8.",
        "why_b_depends_on_a": "The parity state and every rendered cell are determined by the recovered occupancy vector; changing one recovered bit changes the fold and final strip, while the frame orientation decides which physical cells supply those bits.",
    }
    witness = {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "source_binding": qualification["source_binding"],
        **descriptions,
        "racket": {"backend": "racket", "protected": True},
        "cases": cases,
        "limits": "Two bounded wrong-intermediate cases from qualified settings; this is causal evidence, not universal depth proof.",
    }
    witness_path = OUT / "sequential-dependency-witness.json"
    dump(witness_path, witness)
    replay = replay_witness(ROOT, witness)
    dump(OUT / "sequential-dependency-replay.json", replay)

    summary = {
        "schema": "arcpuzzles-parametric-main-evidence-summary-v1",
        "task_id": TASK_ID,
        "qualification_jobs": len(execution["episodes"]),
        "qualification_racket_evaluations": execution["racket_evaluations"],
        "self_audit_episodes": len(episode_reports),
        "self_audit_rivals": len(audit["scope"]["rivals"]),
        "self_audit_findings": len(findings),
        "causal_cases": len(cases),
        "causal_replay_evaluations": replay["evaluations"],
        "source_binding": qualification["source_binding"],
    }
    dump(OUT / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
