#!/usr/bin/env python3
"""Bounded six-setting authoring probe; emits no production approvals."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import sys
import time
import traceback
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root

import prototype

HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def setting_key(setting: tuple[str, int]) -> str:
    return f"{setting[0]}-{setting[1]}"


class RecordingBridge:
    """Save successful and failed exact-expression bridge calls as they happen."""

    def __init__(self, bridge: Any, stream: Any):
        self.bridge = bridge
        self.stream = stream
        self.context: dict[str, Any] = {}
        self.count = 0
        self.context_count = 0

    def set_context(self, **context: Any) -> None:
        self.context = context
        self.context_count = 0

    def eval_text(self, expression: str) -> Any:
        self.count += 1
        started = time.monotonic()
        row = {
            "execution_index": self.count,
            "context_input_index": self.context_count,
            **self.context,
            "exact_expression": expression,
            "expression_sha256": text_sha256(expression),
        }
        self.context_count += 1
        try:
            output = self.bridge.eval_text(expression)
            row.update(status="passed", output=output)
            return output
        except Exception as exc:
            row.update(status="failed", error_type=type(exc).__name__, error=str(exc))
            raise
        finally:
            row["elapsed_seconds"] = round(time.monotonic() - started, 6)
            self.stream.write(json.dumps(row, sort_keys=True) + "\n")
            self.stream.flush()


def canonical_program(root: Path) -> str:
    programs = []
    with canonical_path(root).open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == prototype.TASK_ID:
                    programs.append(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"Expected one canonical program, found {len(programs)}")
    return programs[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--out", required=True, type=Path, help="New evidence directory; never overwritten")
    args = parser.parse_args()
    if args.seed_start < 0:
        parser.error("--seed-start must be nonnegative")
    args.out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    sources = [HERE / "prototype.py", HERE / "probe.py", HERE / "README.md",
               HERE.parents[1] / "tests/test_parametric_prototype.py"]
    report: dict[str, Any] = {
        "schema": "75ba893e1e36-parametric-probe-v1",
        "status": "running",
        "scope": "PROPOSED task-local prototype; no canonical production or approval change",
        "task_id": prototype.TASK_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "seed_start": args.seed_start,
        "seeds": list(range(args.seed_start, args.seed_start + 6)),
        "parameters": {
            "first_tile": list(prototype.FIRST_TILES),
            "tile_pairs": list(prototype.TILE_PAIRS),
            "original": {"first_tile": "mirror", "tile_pairs": 2},
            "selection": "SETTINGS[seed % 6], once for the whole episode",
            "input_seed": "seed // 6; shared within a six-seed comparison block",
            "input_constraints": "3x3; exactly colors 5/7/8; at least one asymmetric row",
            "output_constraints": "3 rows, width 6/12/18, all below 30",
        },
        "source_sha256": {str(path.relative_to(root)): sha256(path) for path in sources},
        "commands": {
            "outer_cwd": str(root.parent.parent),
            "outer_command": "python3 review.py run " + shlex.join(["python3", *sys.argv]),
            "payload_cwd": str(Path.cwd()),
            "payload_argv": [sys.executable, *sys.argv],
        },
        "execution_method": (
            "Exact emitted (rule! (lambda (g) ...)) bytes are embedded in an expression "
            "with a lexical identity binding for callable-form rule!; the returned "
            "lambda is applied by the included RacketBridge. No Python label mirror."
        ),
        "episodes": [],
        "failures": [],
        "limitations": [
            "Six settings and six seeds only; not a broad sampler or seed census.",
            "Authored teaching grids use fixed 3x3 geometry and palette 5/7/8.",
            "Identifiability is checked only against the five other declared settings per episode.",
            "Palindromic teaching grids are excluded because they cannot identify first_tile.",
            "Only the six closed-lambda programs are supported by the local registration wrapper.",
            "No production parametric API or variant approval is implemented or implied.",
        ],
    }
    report_path = args.out / "report.json"
    write_json(report_path, report)
    recorder = None
    try:
        authority = canonical_program(root)
        default_program = prototype.program_for(*prototype.DEFAULT_PARAMETERS)
        if authority != default_program:
            raise ValueError("Default emitted program is no longer byte-identical to canonical authority")
        report["canonical_authority"] = {
            "path": str(canonical_path(root).relative_to(root)),
            "ledger_sha256": sha256(canonical_path(root)),
            "program": authority,
            "program_sha256": text_sha256(authority),
            "default_program_byte_identical": True,
        }
        programs = {setting_key(setting): prototype.program_for(*setting) for setting in prototype.SETTINGS}
        for index, (key, program) in enumerate(programs.items()):
            program_path = args.out / "private/programs" / f"program-{index:02d}.rkt"
            program_path.parent.mkdir(parents=True, exist_ok=True)
            program_path.write_text(program, encoding="utf-8")
        report["programs"] = {
            key: {"source": program, "sha256": text_sha256(program),
                  "path": f"private/programs/program-{index:02d}.rkt"}
            for index, (key, program) in enumerate(programs.items())
        }
        with (args.out / "executions.jsonl").open("w", encoding="utf-8") as stream:
            with RacketBridge(timeout=10.0, startup_timeout=30.0) as bridge:
                report["racket_runtime"] = bridge.runtime_identity
                recorder = RecordingBridge(bridge, stream)
                for episode_index, seed in enumerate(report["seeds"]):
                    chosen = prototype.choose_parameters(seed)
                    chosen_key = setting_key(chosen)
                    recorder.set_context(purpose="selected_episode", seed=seed, setting=chosen_key,
                                         program_sha256=text_sha256(programs[chosen_key]))
                    episode = prototype.build_episode(seed, recorder)
                    episode["prototype_source_sha256"] = report["source_sha256"]
                    private_path = f"private/episode-{episode_index:02d}.json"
                    public_path = f"public/episode-{episode_index:02d}.json"
                    write_json(args.out / private_path, episode)
                    public = prototype.public_challenge(episode)
                    write_json(args.out / public_path, public)
                    all_pairs = episode["train"] + episode["test"]
                    predictions = {chosen_key: [pair["output"] for pair in all_pairs]}
                    rivals = []
                    for rival, program in programs.items():
                        if rival == chosen_key:
                            continue
                        recorder.set_context(purpose="parameter_rival", seed=seed,
                                             selected_setting=chosen_key, setting=rival,
                                             program_sha256=text_sha256(program))
                        predicted = [prototype.execute_program(recorder, program, pair["input"])
                                     for pair in all_pairs]
                        predictions[rival] = predicted
                        disagree = [index for index in range(3)
                                    if predicted[index] != all_pairs[index]["output"]]
                        query_disagrees = predicted[3] != all_pairs[3]["output"]
                        rivals.append({
                            "setting": rival, "demonstration_mismatch_indices": disagree,
                            "consistent_with_demonstrations": not disagree,
                            "query_disagrees": query_disagrees,
                            "ambiguous": not disagree and query_disagrees,
                            "racket_outputs": predicted,
                        })
                    survivors = [chosen_key] + [row["setting"] for row in rivals
                                                if row["consistent_with_demonstrations"]]
                    entry = {"seed": seed, "setting": chosen_key,
                             "public_path": public_path, "private_path": private_path,
                             "demonstrations": 3, "queries": 1,
                             "surviving_settings": survivors,
                             "identified_among_six": survivors == [chosen_key],
                             "rivals": rivals}
                    report["episodes"].append(entry)
                    if episode_index == 0:
                        witness_outputs = {key: outputs[0] for key, outputs in predictions.items()}
                        report["differing_lawful_witness"] = {
                            "input": all_pairs[0]["input"],
                            "lawful": True,
                            "outputs": witness_outputs,
                            "distinct_outputs": len({json.dumps(output) for output in witness_outputs.values()}),
                            "all_five_alternatives_differ_from_original": all(
                                output != witness_outputs[setting_key(prototype.DEFAULT_PARAMETERS)]
                                for key, output in witness_outputs.items()
                                if key != setting_key(prototype.DEFAULT_PARAMETERS)),
                            "execution_source": "selected_episode and parameter_rival calls for first retained seed",
                        }
                canonical_results = []
                for pair in canonical_pairs(prototype.TASK_ID, root=root, labeled_only=True):
                    identity = {name: pair[name] for name in ("variant", "split", "pair_index")}
                    recorder.set_context(purpose="canonical_authority", **identity,
                                         program_sha256=text_sha256(authority))
                    actual = prototype.execute_program(recorder, authority, pair["input"])
                    recorder.set_context(purpose="prototype_default_on_canonical", **identity,
                                         program_sha256=text_sha256(default_program))
                    default_actual = prototype.execute_program(recorder, default_program, pair["input"])
                    canonical_results.append({**identity, "input": pair["input"],
                                              "expected": pair["output"], "authority_output": actual,
                                              "default_output": default_actual,
                                              "agrees": actual == default_actual == pair["output"]})
                report["canonical_pairs"] = canonical_results
        if len(report["canonical_pairs"]) != 5 or not all(row["agrees"] for row in report["canonical_pairs"]):
            report["failures"].append("Default did not agree with all five canonical labeled pairs")
        if not all(row["identified_among_six"] for row in report["episodes"]):
            report["failures"].append("At least one retained episode is not identified among six settings")
        if report["differing_lawful_witness"]["distinct_outputs"] != 6:
            report["failures"].append("The retained lawful witness does not distinguish all six settings")
        report["counts"] = {
            "settings": len(programs), "episodes": len(report["episodes"]),
            "train_pairs": 18, "query_pairs": 6, "canonical_pairs": len(report["canonical_pairs"]),
            "declared_rival_checks": sum(len(row["rivals"]) for row in report["episodes"]),
            "identified_episodes": sum(row["identified_among_six"] for row in report["episodes"]),
            "ambiguous_rivals": sum(rival["ambiguous"] for row in report["episodes"] for rival in row["rivals"]),
            "racket_grid_executions": recorder.count,
            "max_output_width": max(len(pair["output"][0]) for episode_index in range(6)
                                    for pair in json.loads((args.out / f"private/episode-{episode_index:02d}.json").read_text())["train"]),
        }
        report["status"] = "failed" if report["failures"] else "passed"
    except Exception as exc:
        report["status"] = "failed"
        report["failures"].append({"error_type": type(exc).__name__, "message": str(exc),
                                   "traceback": traceback.format_exc()})
    finally:
        report["completed_racket_calls"] = recorder.count if recorder is not None else 0
        report["artifact_sha256"] = {
            str(path.relative_to(args.out)): sha256(path)
            for path in sorted(args.out.rglob("*")) if path.is_file() and path != report_path
        }
        write_json(report_path, report)
    print(json.dumps({"status": report["status"], "report": str(report_path),
                      "counts": report.get("counts"), "failures": report["failures"]}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
