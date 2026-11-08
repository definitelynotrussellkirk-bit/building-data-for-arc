"""Proposed episode-level first/last overlay priority for ed860c0a9107.

This task-local authoring tool does not register a production generator, change
canonical authority, or grant approval. All labels are executed by Racket.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)


TASK_ID = "ed860c0a9107"
PROTOTYPE_VERSION = "1.0.0"
PRIORITIES = ("first", "last")
DEFAULT_PRIORITY = "first"
HOST_BINDINGS = ("(define h (rows g))", "(define w (cols g))")


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_rule(root):
    programs = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID and row.get("program_solution"):
                    programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("the prototype requires one exact canonical authority")
    return programs.pop()


def select_priority(seed, priority=DEFAULT_PRIORITY):
    """Choose once per episode; input sampling never depends on this choice."""
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer, not bool/float/string")
    if priority == "sample":
        key = f"{TASK_ID}:priority:v1:{seed}".encode("ascii")
        return PRIORITIES[hashlib.sha256(key).digest()[0] % len(PRIORITIES)]
    if priority not in PRIORITIES:
        raise ValueError("priority must be 'first', 'last', or 'sample'")
    return priority


def materialize_rule(priority=DEFAULT_PRIORITY, *, root=None):
    """Return exact canonical text or its single, explicit priority mutation."""
    if priority not in PRIORITIES:
        raise ValueError("materialized priority must be 'first' or 'last'")
    root = find_root(__file__) if root is None else Path(root)
    source = canonical_rule(root)
    if priority == "first":
        return source
    needle = "(find-first (lambda (obj) (visible? (local-at obj r c))) boxes)"
    if source.count(needle) != 1:
        raise ValueError("canonical overlay changed; review the prototype mutation")
    replacement = "(find-first (lambda (obj) (visible? (local-at obj r c))) (reverse boxes))"
    return source.replace(needle, replacement)


def executed_expression(program):
    """Remove only the documented marker around this task's trusted body form."""
    source = program.strip()
    if not source.startswith("(rule!\n") or not source.endswith(")"):
        raise ValueError("expected this task's materialized (rule! BODY) program")
    return source[len("(rule!"):-1].strip()


def apply_rule(bridge, program, grid):
    """Execute a materialized rule using only public RacketBridge methods.

    The canonical rule is the documented body form of rule!: g/h/w are bound by
    its host. The raw-expression bridge does not provide the marker, so remove
    only its outer wrapper; retain the authored source and executed body hashes
    separately. No new macro or sandbox capability is needed.
    """
    bridge.define_grid("g", normalize_grid(grid))
    for binding in HOST_BINDINGS:
        bridge.eval_text(binding)
    return normalize_grid(bridge.eval_text(executed_expression(program)))


def assess_role_rotations(pairs, predictions):
    """Enumerate every leave-one-out query and its exact parameter rivals."""
    if len(pairs) < 2:
        raise ValueError("identifiability requires a demonstration and a query")
    if set(predictions) != set(PRIORITIES):
        raise ValueError("predictions must cover the exact declared priorities")
    if any(len(outputs) != len(pairs) for outputs in predictions.values()):
        raise ValueError("prediction count must equal the labeled pair count")
    checks = []
    for query_index in range(len(pairs)):
        demos = [index for index in range(len(pairs)) if index != query_index]
        witnesses = {
            priority: [
                index for index in demos
                if predictions[priority][index] != pairs[index]["output"]
            ]
            for priority in PRIORITIES
        }
        checks.append({
            "query_index": query_index,
            "demonstration_indices": demos,
            "consistent_priorities": [p for p in PRIORITIES if not witnesses[p]],
            "refuted_priorities": {p: indices for p, indices in witnesses.items() if indices},
            "query_priorities_disagree": predictions["first"][query_index] != predictions["last"][query_index],
        })
    return checks


def generate_episode(seed, *, priority=DEFAULT_PRIORITY, difficulty="medium", root=None, bridge=None):
    """Produce three labeled demonstrations and one labeled private query."""
    root = find_root(__file__) if root is None else Path(root)
    if bridge is None:
        with RacketBridge(timeout=10.0) as owned_bridge:
            return generate_episode(seed, priority=priority, difficulty=difficulty,
                                    root=root, bridge=owned_bridge)
    chosen = select_priority(seed, priority)
    generator, _source, source_hash = load_selected_generator(TASK_ID, root=root)
    inputs = [generator.generate(seed, index, difficulty=difficulty) for index in range(4)]
    for grid in inputs:
        findings = generator.self_check(grid)
        if findings:
            raise ValueError(f"selected sampler produced an invalid input: {findings}")
    programs = {p: materialize_rule(p, root=root) for p in PRIORITIES}
    predictions = {
        p: [apply_rule(bridge, programs[p], grid) for grid in inputs]
        for p in PRIORITIES
    }
    pairs = [
        {"input": grid, "output": output}
        for grid, output in zip(inputs, predictions[chosen])
    ]
    rotations = assess_role_rotations(pairs, predictions)
    if any(check["consistent_priorities"] != [chosen] for check in rotations):
        raise ValueError("episode demonstrations do not identify the chosen priority in every query role")
    return {
        "schema": "ed860c0a9107-parametric-prototype-episode-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "difficulty": difficulty,
        "parameter_selection": "seeded" if priority == "sample" else "explicit",
        "parameters": {"priority": chosen},
        "parameter_domain": {"priority": list(PRIORITIES)},
        "generator_sha256": source_hash,
        "prototype_sha256": file_sha256(__file__),
        "program": programs[chosen],
        "program_sha256": sha256_text(programs[chosen]),
        "executed_expression": executed_expression(programs[chosen]),
        "executed_expression_sha256": sha256_text(executed_expression(programs[chosen])),
        "train": pairs[:3],
        "test": pairs[3:],
        "parameter_predictions": predictions,
        "role_rotations": rotations,
    }


def public_challenge(episode):
    """Allowlist the model-visible payload; no seed, rule, parameter or answer."""
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def rotate_grid(grid, quarter_turns):
    result = [list(row) for row in grid]
    for _ in range(quarter_turns % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def write_episode(out, episode):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / "challenge.json", public_challenge(episode))
    write_json(out / "private.json", episode)
    (out / "rule.rkt").write_text(episode["program"], encoding="utf-8")
    (out / "executed-body.rkt").write_text(episode["executed_expression"], encoding="utf-8")


def source_bindings(root):
    _gen, source, source_hash = load_selected_generator(TASK_ID, root=root)
    prototype = Path(__file__).resolve()
    source_files = [prototype, prototype.with_name("README.md")]
    tests = prototype.parents[2] / "tests/test_parametric_ed860c0a9107.py"
    if tests.is_file():
        source_files.append(tests)
    source_hashes = {
        str(path.relative_to(root)): file_sha256(path) for path in source_files if path.is_file()
    }
    source_hashes[str(source.relative_to(root))] = source_hash
    rule = canonical_rule(root)
    runtime = racket_runtime_status()
    bridge_source = Path(sys.modules[RacketBridge.__module__].__file__)
    return {
        "files": source_hashes,
        "canonical_program_sha256": sha256_text(rule),
        "canonical_normalized_rule_hash": sha256_text(" ".join(rule.split()))[:12],
        "canonical_ledger_sha256": file_sha256(canonical_path(root)),
        "host_grid_binding": "RacketBridge.define_grid('g', input)",
        "host_bindings": list(HOST_BINDINGS),
        "wrapper_handling": "remove only outer (rule! BODY) marker before public eval_text",
        "bridge_source_sha256": file_sha256(bridge_source),
        "prelude_source_sha256": file_sha256(runtime["prelude_path"]),
        "runtime": runtime,
    }


def collect_evidence(out, *, root):
    """Bounded authored evidence: six episodes, eight canonical rows, 16 probes."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    sources_before = source_bindings(root)
    generator, _path, _digest = load_selected_generator(TASK_ID, root=root)
    programs = {p: materialize_rule(p, root=root) for p in PRIORITIES}
    rules_dir = out / "rules"
    rules_dir.mkdir()
    for p, program in programs.items():
        (rules_dir / f"{p}.rkt").write_text(program, encoding="utf-8")
        (rules_dir / f"{p}-executed-body.rkt").write_text(executed_expression(program), encoding="utf-8")
    episode_index = []
    with RacketBridge(timeout=10.0) as bridge:
        canonical = []
        canonical_inputs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
        for pair in canonical_inputs:
            outputs = {p: apply_rule(bridge, programs[p], pair["input"]) for p in PRIORITIES}
            canonical.append({**pair, "executed_outputs": outputs,
                              "default_matches_label": outputs["first"] == pair["output"],
                              "alternative_matches_label": outputs["last"] == pair["output"]})
        write_json(out / "canonical.json", canonical)
        canonical_predictions = {
            p: [row["executed_outputs"][p] for row in canonical[:4]] for p in PRIORITIES
        }
        negative = assess_role_rotations(canonical[:4], canonical_predictions)
        write_json(out / "canonical-only-ambiguity.json", negative)

        generated = []
        for band in ("easy", "medium", "hard"):
            for index in range(4):
                seed = 20261100 + index
                grid = generator.generate(seed, index, difficulty=band)
                outputs = {p: apply_rule(bridge, programs[p], grid) for p in PRIORITIES}
                generated.append({"seed": seed, "sample_index": index, "difficulty": band,
                                  "overrides": {}, "input": grid, "executed_outputs": outputs,
                                  "default_matches_canonical_mirror": outputs["first"] == generator.rule_mirror(grid),
                                  "settings_differ": outputs["first"] != outputs["last"]})
        for index, values in enumerate(((14, 14, 4, 5, 5), (14, 22, 3, 2, 5),
                                        (22, 14, 2, 5, 2), (22, 22, 4, 2, 2))):
            overrides = dict(zip(("grid_h", "grid_w", "n_containers", "box_h", "box_w"), values))
            seed = 20261200 + index
            grid = generator.generate(seed, index, difficulty="hard", **overrides)
            outputs = {p: apply_rule(bridge, programs[p], grid) for p in PRIORITIES}
            generated.append({"seed": seed, "sample_index": index, "difficulty": "hard",
                              "overrides": overrides, "input": grid, "executed_outputs": outputs,
                              "default_matches_canonical_mirror": outputs["first"] == generator.rule_mirror(grid),
                              "settings_differ": outputs["first"] != outputs["last"]})
        write_json(out / "generated-probes.json", generated)

        for priority in PRIORITIES:
            for index, band in enumerate(("easy", "medium", "hard")):
                seed = 20261020 + index
                episode = generate_episode(seed, priority=priority, difficulty=band,
                                           root=root, bridge=bridge)
                relative = f"episodes/{len(episode_index):04d}"
                write_episode(out / relative, episode)
                episode_index.append({"path": relative, "seed": seed, "difficulty": band,
                                      "parameters": episode["parameters"],
                                      "program_sha256": episode["program_sha256"],
                                      "role_rotations": episode["role_rotations"]})

        # Quarter-turns change row-major order, so reexecute both rules instead
        # of assuming that rotating a previous answer preserves its label.
        conflict = [[9] * 14 for _ in range(14)]
        for top, left, color in ((2, 2, 1), (8, 8, 2)):
            for row in range(2):
                for col in range(2):
                    conflict[top + row][left + col] = color if row == col == 0 else 0
        spatial = []
        for turns in range(4):
            grid = rotate_grid(conflict, turns)
            outputs = {p: apply_rule(bridge, programs[p], grid) for p in PRIORITIES}
            spatial.append({"quarter_turns_clockwise": turns, "input": grid,
                            "self_check": generator.self_check(grid), "executed_outputs": outputs,
                            "settings_differ": outputs["first"] != outputs["last"]})
        write_json(out / "lawful-conflict-spatial-rotations.json", spatial)

    sources_after = source_bindings(root)
    if sources_after != sources_before:
        raise RuntimeError("source changed during evidence collection; retain and rerun in a fresh directory")
    summary = {
        "schema": "ed860c0a9107-parametric-prototype-evidence-v1", "status": "prototype",
        "sources": sources_before,
        "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
        "parameter": {"name": "priority", "allowed": list(PRIORITIES), "default": DEFAULT_PRIORITY},
        "programs": {
            p: {"path": f"rules/{p}.rkt", "sha256": sha256_text(programs[p]),
                "executed_expression_path": f"rules/{p}-executed-body.rkt",
                "executed_expression_sha256": sha256_text(executed_expression(programs[p]))}
            for p in PRIORITIES
        },
        "canonical_labeled_records": len(canonical),
        "canonical_unique_inputs": len({json.dumps(row["input"]) for row in canonical}),
        "canonical_default_matches": sum(row["default_matches_label"] for row in canonical),
        "canonical_alternative_matches": sum(row["alternative_matches_label"] for row in canonical),
        "canonical_ambiguous_role_rotations": sum(len(row["consistent_priorities"]) > 1 for row in negative),
        "generated_probes": len(generated),
        "generated_default_matches_canonical_mirror": sum(row["default_matches_canonical_mirror"] for row in generated),
        "generated_setting_disagreements": sum(row["settings_differ"] for row in generated),
        "episode_count": len(episode_index), "episode_pairs": len(episode_index) * 4,
        "episode_role_rotations": sum(len(row["role_rotations"]) for row in episode_index),
        "identified_episode_role_rotations": sum(
            check["consistent_priorities"] == [row["parameters"]["priority"]]
            for row in episode_index for check in row["role_rotations"]
        ),
        "spatial_rotation_conflicts": sum(row["settings_differ"] for row in spatial),
        "racket_label_executions": len(canonical) * 2 + len(generated) * 2 + len(episode_index) * 8 + len(spatial) * 2,
        "episodes": episode_index,
        "limitations": [
            "Prototype only; canonical production API, rule, and approvals remain unchanged.",
            "Eight canonical labeled records contain four unique inputs; all also fit last priority.",
            "Identifiability excludes only the two declared priority settings, not all possible programs.",
            "Episode rotations are exhaustive leave-one-out query roles; spatial rotations are a separate four-case lawful witness probe.",
            "The prototype inherits the selected input sampler's size, palette, payload, and placement support.",
            "No full Cartesian-product or universal seed coverage is claimed.",
        ],
    }
    checks = {
        "canonical_default": summary["canonical_default_matches"] == 8,
        "known_canonical_ambiguity_retained": summary["canonical_ambiguous_role_rotations"] == 4,
        "generated_default_parity": summary["generated_default_matches_canonical_mirror"] == 16,
        "generated_alternative_changes_outputs": summary["generated_setting_disagreements"] == 16,
        "all_episode_query_roles_identifiable": summary["identified_episode_role_rotations"] == 24,
        "spatial_witness_is_lawful": all(not row["self_check"] for row in spatial),
        "spatial_witness_separates_both_settings": summary["spatial_rotation_conflicts"] == 4,
    }
    summary["checks"] = checks
    summary["passed"] = all(checks.values())
    write_json(out / "summary.json", summary)
    files = sorted(path for path in out.rglob("*") if path.is_file())
    write_json(out / "files.json", {str(path.relative_to(out)): file_sha256(path) for path in files})
    if not summary["passed"]:
        raise AssertionError(f"bounded prototype evidence failed: {checks}")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    episode = commands.add_parser("episode", help="emit one complete private/public episode")
    episode.add_argument("--seed", type=int, required=True)
    episode.add_argument("--priority", choices=(*PRIORITIES, "sample"), default=DEFAULT_PRIORITY)
    episode.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    episode.add_argument("--out", type=Path, required=True)
    evidence = commands.add_parser("evidence", help="collect the bounded two-setting Racket evidence")
    evidence.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    root = find_root(__file__)
    if args.command == "episode":
        data = generate_episode(args.seed, priority=args.priority, difficulty=args.difficulty, root=root)
        write_episode(args.out, data)
        print(json.dumps({"status": "prototype", "out": str(args.out), "parameters": data["parameters"],
                          "train_pairs": 3, "test_pairs": 1, "identified_role_rotations": 4}))
    else:
        summary = collect_evidence(args.out, root=root)
        print(json.dumps({key: value for key, value in summary.items()
                          if key not in ("sources", "episodes", "limitations", "programs")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
