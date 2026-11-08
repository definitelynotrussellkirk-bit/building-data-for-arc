"""Replay bounded teaching evidence and export static one-query public views."""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
RANKINGS = ("perimeter", "normalized_top_edge")


def _load(path):
    body = path.read_bytes()
    name = "_ef03216cf2fa_" + path.stem + hashlib.sha256(body).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


@lru_cache(maxsize=1)
def _public_serializer():
    return _load(ROOT / "shared/runtime/reviewer_support.py").public_challenge_bytes


def public_view_bytes(episode, query_index):
    """Project one selected query; future queries and all private fields vanish."""
    if not isinstance(episode, dict) or type(episode.get("test")) is not list:
        raise ValueError("episode needs a test list")
    if type(query_index) is not int or not 0 <= query_index < len(episode["test"]):
        raise ValueError("query_index must be an exact integer within the test list")
    return _public_serializer()({"train": episode.get("train"),
                                 "test": [episode["test"][query_index]]})


def write_public_views(episodes, destination: Path) -> list[str]:
    """Write unique visible payloads, named only by their exact byte hashes."""
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    payloads = {}
    for episode in episodes:
        if not isinstance(episode, dict) or type(episode.get("test")) is not list or not episode["test"]:
            raise ValueError("episode needs nonempty test pairs")
        for index in range(len(episode["test"])):
            raw = public_view_bytes(episode, index)
            filename = hashlib.sha256(raw).hexdigest() + ".json"
            if filename in payloads:
                raise ValueError("duplicate public payload")
            payloads[filename] = raw
    if not payloads:
        raise ValueError("at least one public view is required")
    destination.mkdir(parents=True, exist_ok=False)
    for filename in sorted(payloads):
        with (destination / filename).open("xb") as handle:
            handle.write(payloads[filename])
    return sorted(payloads)


def _write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def _source_hashes():
    return [{"path": (HOME / name).relative_to(ROOT).as_posix(),
             "sha256": hashlib.sha256((HOME / name).read_bytes()).hexdigest()}
            for name in ("prototype.py", "adapter.py", "promotion.json", "canonical.rkt", "check.py")]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append")
    parser.add_argument("--demos", type=int, default=3)
    args = parser.parse_args(argv)
    seeds = args.seed if args.seed is not None else [0, 17]
    if not 2 <= args.demos <= 6 or any(not 0 <= seed < 2**63 for seed in seeds) or len(set(seeds)) != len(seeds):
        parser.error("use 2..6 demos and distinct seeds in 0..2**63-1")
    if args.out.exists() or args.out.is_symlink():
        parser.error("output already exists; choose a new path")
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
    from arcpuzzles.parametric_worker import _grid
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    prototype = _load(HOME / "prototype.py")
    sources = _source_hashes()
    programs = {ranking: prototype.program({"ranking": ranking}) for ranking in RANKINGS}
    rivals = {ranking: {name: prototype.rival_program(ranking, name)
                       for name in prototype.rival_names()} for ranking in RANKINGS}
    report = {"schema": "ef03216cf2fa-parametric-check-v1", "task_id": "ef03216cf2fa",
              "command": [sys.executable, str(Path(__file__).resolve()), *(sys.argv[1:] if argv is None else argv)],
              "cwd": str(Path.cwd()), "sources": sources, "seeds": seeds,
              "demos": args.demos, "queries": 4, "episodes": [], "failures": [],
              "programs": {ranking: {"program": program, "sha256": hashlib.sha256(program.encode()).hexdigest(),
                  "rivals": {name: {"program": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}
                             for name, text in rivals[ranking].items()}} for ranking, program in programs.items()},
              "training_admitted": False, "owner_acceptance": "not_performed",
              "limits": "Finite authored rivals and sampled seeds only; public views are static projections, not a turn controller."}
    episodes, input_sets, cache, wrapped = [], {}, {}, {}
    evaluations = 0
    bridge = None
    try:
        bridge = RacketBridge()
        report["racket"] = dict(bridge.runtime_identity)
        if report["racket"].get("backend") != "racket" or report["racket"].get("protected") is not True:
            raise ValueError("a live protected Racket runtime is required")

        def execute(program, grid):
            nonlocal evaluations
            key = (program, json.dumps(_grid(grid), separators=(",", ":")))
            if key not in cache:
                if program not in wrapped:
                    wrapped[program] = wrap_rule(program)
                literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
                evaluations += 1
                cache[key] = _grid(bridge.eval_text(f"({wrapped[program]} {literal})"))
            return deepcopy(cache[key])

        for seed in seeds:
            for ranking in RANKINGS:
                row = {"seed": seed, "settings": {"ranking": ranking}, "status": "failed", "rivals": []}
                report["episodes"].append(row)
                try:
                    episode = deepcopy(prototype.generate(seed, row["settings"], args.demos, 4))
                    if episode.get("program_solution") != programs[ranking]:
                        raise ValueError("generated program differs from program(settings)")
                    if any(type(episode.get(split)) is not list or len(episode[split]) != count
                           for split, count in (("train", args.demos), ("test", 4))):
                        raise ValueError("independent demo/query counts were not met")
                    inputs = [json.dumps(_grid(pair["input"])) for split in ("train", "test") for pair in episode[split]]
                    if len(inputs) != len(set(inputs)):
                        raise ValueError("demonstration and query inputs must all be distinct")
                    if input_sets.setdefault(seed, inputs) != inputs:
                        raise ValueError("input sampling differs between settings for the same seed/counts")
                    row["pairs"] = []
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            actual = execute(programs[ranking], pair["input"])
                            if actual != _grid(pair["output"]):
                                raise ValueError(f"{split}[{index}] Python claim differs from protected Racket")
                            pair["output"] = actual
                            grid = pair["input"]
                            row["pairs"].append({"split": split, "index": index,
                                "input_shape": [len(grid), len(grid[0])], "output_shape": [len(actual), len(actual[0])],
                                "components": len(prototype.components(grid)),
                                "foreground_cells": sum(cell != 0 for line in grid for cell in line),
                                "occupied_rows": sum(any(line) for line in grid),
                                "occupied_columns": sum(any(line[c] for line in grid) for c in range(len(grid[0])))})
                    candidates = [("setting:" + name, text, name == ranking) for name, text in programs.items()]
                    candidates += [("rival:" + name, text, False) for name, text in rivals[ranking].items()]
                    for name, text, intended in candidates:
                        matches = [execute(text, pair["input"]) == pair["output"] for pair in episode["train"]]
                        row["rivals"].append({"name": name, "demo_matches": matches, "survives": all(matches),
                                              "first_refuting_demo": next((i for i, match in enumerate(matches) if not match), None)})
                        if intended != all(matches) or (not intended and all(matches[:2])):
                            raise ValueError(f"demonstrations do not distinguish {name} within their first two examples")
                    episode.update(task_id="ef03216cf2fa", seed=seed, settings=row["settings"])
                    episodes.append(episode)
                    row.update(status="passed", distinct_inputs=len(inputs), labels_checked=len(inputs),
                               selected_survivor=ranking, first_two_demos_refute_all_wrong_rivals=True)
                except Exception as error:
                    row["error"] = f"{type(error).__name__}: {error}"
                    report["failures"].append({"seed": seed, "settings": row["settings"], "error": row["error"]})
    except Exception as error:
        report["failures"].append({"error": f"{type(error).__name__}: {error}"})
    finally:
        if bridge is not None:
            bridge.close()
    if _source_hashes() != sources:
        report["failures"].append({"error": "source files changed during replay"})
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "private").mkdir()
    _write(args.out / "private/episodes.json", episodes)
    if not report["failures"]:
        try:
            report["public_files"] = write_public_views(episodes, args.out / "public")
        except Exception as error:
            report["failures"].append({"error": f"public export: {type(error).__name__}: {error}"})
    report.update(status="failed" if report["failures"] else "passed", racket_evaluations=evaluations,
                  attempted_episodes=len(seeds) * len(RANKINGS), successful_episodes=len(episodes),
                  failed_episodes=len(seeds) * len(RANKINGS) - len(episodes),
                  success_rate=len(episodes) / (len(seeds) * len(RANKINGS)))
    _write(args.out / "report.json", report)
    print(json.dumps({key: report[key] for key in ("status", "attempted_episodes", "successful_episodes", "racket_evaluations", "failures")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
