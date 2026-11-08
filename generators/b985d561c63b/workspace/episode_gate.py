"""Check a retained labeled episode against the selected finite rival set.

From the review packet root (the wrapper changes the child cwd to repo)::

    python3 run_with_racket.py python3 \
        generators/b985d561c63b/workspace/episode_gate.py \
        --generator generators/b985d561c63b/generator.py \
        --episode ../checks/final_probe_final/short_lesson.json \
        --out ../checks/episode_gate/short.json

Exit 0: no surviving declared rival disagrees with any query label.
Exit 1: at least one rival fits every demo and disagrees with a query label.
Exit 2: malformed/unlabeled episode, source-binding failure, or invalid rival.

This checker uses supplied labels and recorded source provenance. It does not
rerun Racket, create labels, verify that the supplied labels were executed, grant
approval, or establish identifiability beyond the actual declared finite rivals.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


class EpisodeError(ValueError):
    """The episode cannot be assessed under the source-bound contract."""


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def grid_hash(grid):
    return sha256_bytes(json.dumps(grid, separators=(",", ":")).encode())


def rule_hash(source):
    return sha256_bytes(" ".join(source.split()).encode())[:12]


def require(condition, message):
    if not condition:
        raise EpisodeError(message)


def validate_grid(grid, label):
    require(isinstance(grid, list) and bool(grid), f"{label}: expected a nonempty grid")
    require(all(isinstance(row, list) and bool(row) for row in grid), f"{label}: malformed grid rows")
    width = len(grid[0])
    require(len(grid) <= 30 and width <= 30 and all(len(row) == width for row in grid),
            f"{label}: ragged or oversized grid")
    require(all(type(value) is int and 0 <= value <= 9 for row in grid for value in row),
            f"{label}: cells must be integer ARC colors 0..9")


def find_canonical(generator_path, explicit=None):
    if explicit is not None:
        return Path(explicit).resolve()
    for parent in generator_path.parents:
        for relative in ("shared/data/canonical/puzzles.jsonl", "data/canonical/puzzles.jsonl"):
            candidate = parent / relative
            if candidate.is_file():
                return candidate
    raise EpisodeError("Cannot locate the selected canonical ledger; pass --canonical")


def load_selection(generator_path, canonical_path=None):
    """Load actual declarations and bind them to the selected canonical source."""
    generator_path = Path(generator_path).resolve()
    source_bytes = generator_path.read_bytes()
    generator_sha256 = sha256_bytes(source_bytes)
    for parent in generator_path.parents:
        for relative in ("shared/runtime", "."):
            runtime = parent / relative
            if (runtime / "puzzle_generators/base.py").is_file():
                sys.path.insert(0, str(runtime))
                break
        else:
            continue
        break
    spec = importlib.util.spec_from_file_location("episode_gate_generator_" + generator_sha256[:12], generator_path)
    require(spec is not None and spec.loader is not None, "Cannot load selected generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    task_id = getattr(module, "TASK_ID", None)
    require(isinstance(task_id, str) and bool(task_id), "Selected generator has no TASK_ID")
    canonical_path = find_canonical(generator_path, canonical_path)
    sources = []
    with canonical_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == task_id and isinstance(row.get("program_solution"), str):
                if row["program_solution"].strip():
                    sources.append(row["program_solution"])
    require(bool(sources), f"No canonical rule source for {task_id}")
    require(len({rule_hash(source) for source in sources}) == 1, "Selected canonical rule is ambiguous")
    selected_rule_hash = rule_hash(sources[0])
    require(getattr(module, "RULE_HASH", None) == selected_rule_hash,
            "Selected generator RULE_HASH does not match the selected canonical source")
    rivals, declarations = {}, {}
    for field in ("LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        declared = getattr(module, field, None)
        require(isinstance(declared, dict) and bool(declared), f"Missing nonempty {field} declaration")
        require(all(isinstance(name, str) and name and callable(fn) for name, fn in declared.items()),
                f"Malformed {field} declaration")
        declarations[field] = sorted(declared)
        for name, fn in declared.items():
            require(name not in rivals or rivals[name] is fn,
                    f"Conflicting rival definitions use the same name: {name}")
            rivals[name] = fn
    return {"module": module, "rivals": rivals, "declarations": declarations,
            "task_id": task_id, "generator_path": str(generator_path),
            "generator_sha256": generator_sha256, "canonical_path": str(canonical_path),
            "rule_hash": selected_rule_hash, "rule_source_sha256": sha256_bytes(sources[0].encode())}


def validate_episode(episode, selection):
    require(isinstance(episode, dict), "Episode must be a JSON object")
    require(episode.get("task_id") == selection["task_id"], "Episode task_id does not match selected task")
    provenance = episode.get("provenance")
    require(isinstance(provenance, dict), "Missing episode provenance")
    require(provenance.get("generator_sha256") == selection["generator_sha256"],
            "Episode provenance generator_sha256 does not match selected generator bytes")
    require(provenance.get("reference") == "canonical", "Episode must use the canonical reference")
    for field, value in (("provenance.rule_hash", provenance.get("rule_hash")),
                         ("executed_rule_hash", episode.get("executed_rule_hash")),
                         ("provenance.catalog_rule_hash", provenance.get("catalog_rule_hash"))):
        require(value == selection["rule_hash"], f"{field} does not match selected canonical rule_hash")
    program = episode.get("program")
    require(isinstance(program, str) and bool(program.strip()), "Missing episode canonical program source")
    require(rule_hash(program) == selection["rule_hash"], "Episode program source differs from selected canonical rule")
    require(episode.get("rule_task_id", selection["task_id"]) == selection["task_id"],
            "Episode rule_task_id differs from selected task")
    pair_count = 0
    for split in ("train", "test"):
        pairs = episode.get(split)
        require(isinstance(pairs, list) and bool(pairs), f"Episode needs a nonempty labeled {split} split")
        for index, pair in enumerate(pairs):
            require(isinstance(pair, dict), f"{split}[{index}] must be a labeled pair")
            require("input" in pair and "output" in pair, f"{split}[{index}] is unlabeled; input and output are required")
            validate_grid(pair["input"], f"{split}[{index}].input")
            validate_grid(pair["output"], f"{split}[{index}].output")
            pair_count += 1
    indices = episode.get("sample_indices")
    require(isinstance(indices, list) and len(indices) == pair_count,
            "sample_indices must retain one generator index for every demo and query")
    require(all(type(index) is int and index >= 0 for index in indices)
            and all(a < b for a, b in zip(indices, indices[1:])),
            "sample_indices must be increasing nonnegative integers")
    require(type(episode.get("seed")) is int, "Episode must retain its integer seed")
    require(sha256_bytes(Path(selection["generator_path"]).read_bytes()) == selection["generator_sha256"],
            "Selected generator changed after its declarations were loaded")


def prediction(name, fn, grid):
    supplied = deepcopy(grid)
    try:
        result = fn(supplied)
    except Exception as exc:
        raise EpisodeError(f"Rival {name} raised {type(exc).__name__}: {exc}") from exc
    require(supplied == grid, f"Rival {name} mutated its input")
    validate_grid(result, f"rival {name} prediction")
    return result


def assess_episode(episode, selection):
    """Assess supplied labels; return a JSON-ready receipt and documented status."""
    report = {
        "schema": "task-episode-finite-rival-gate-v1", "task_id": selection["task_id"],
        "scope": "Finite actual declared rivals, using supplied labels and recorded source provenance; no Racket reexecution, label certification, full-identifiability proof, or approval grant.",
        "racket_reexecuted": False, "grants_approval": False,
        "sources": {key: selection[key] for key in ("generator_path", "generator_sha256", "canonical_path", "rule_hash", "rule_source_sha256")},
        "declarations": selection["declarations"], "errors": [], "rivals": {}, "queries": [],
    }
    try:
        validate_episode(episode, selection)
        demos, queries, indices = episode["train"], episode["test"], episode["sample_indices"]
        report["episode"] = {"seed": episode["seed"], "sample_indices": indices,
            "difficulty": episode["provenance"].get("difficulty"),
            "n_train": len(demos), "n_test": len(queries)}
        survivors = []
        for name, fn in sorted(selection["rivals"].items()):
            matched = [prediction(name, fn, demo["input"]) == demo["output"] for demo in demos]
            eliminated = [index for index, match in enumerate(matched) if not match]
            report["rivals"][name] = {
                "demo_matches": matched, "survives_all_demos": not eliminated,
                "refuting_demo_indices": eliminated,
                "refuting_sample_indices": [indices[index] for index in eliminated],
            }
            if not eliminated:
                survivors.append(name)
        ambiguity = False
        for query_index, query in enumerate(queries):
            equivalent, disagreements = [], {}
            for name in survivors:
                actual = prediction(name, selection["rivals"][name], query["input"])
                if actual == query["output"]:
                    equivalent.append(name)
                else:
                    disagreements[name] = actual
            row = {"query_index": query_index, "sample_index": indices[len(demos) + query_index],
                   "input_sha256": grid_hash(query["input"]), "label_sha256": grid_hash(query["output"]),
                   "surviving_rivals": list(survivors), "answer_equivalent_survivors": equivalent,
                   "disagreeing_rivals": sorted(disagreements)}
            if disagreements:
                ambiguity = True
                row["counterexample"] = {"input": query["input"], "supplied_reference_output": query["output"],
                                         "rival_outputs": disagreements}
            report["queries"].append(row)
        report["status"] = "ambiguous" if ambiguity else "pass"
        report["exit_code"] = 1 if ambiguity else 0
    except (EpisodeError, KeyError, TypeError, ValueError) as exc:
        report["status"] = "malformed_or_unbound"
        report["exit_code"] = 2
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", required=True, type=Path)
    parser.add_argument("--canonical", type=Path, help="optional explicit canonical ledger for a relocated runtime")
    parser.add_argument("--episode", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output receipt already exists; choose a new path")
    report = {"schema": "task-episode-finite-rival-gate-v1", "status": "malformed_or_unbound",
              "exit_code": 2, "errors": []}
    try:
        selection = load_selection(args.generator, args.canonical)
        episode_bytes = args.episode.read_bytes()
        report = assess_episode(json.loads(episode_bytes), selection)
        report["episode_file"] = str(args.episode.resolve())
        report["episode_file_sha256"] = sha256_bytes(episode_bytes)
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    report["command"] = sys.argv
    report["working_directory"] = str(Path.cwd())
    report["checker_sha256"] = sha256_bytes(Path(__file__).read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "exit_code", "errors")}, sort_keys=True))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
