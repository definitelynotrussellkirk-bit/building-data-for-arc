#!/usr/bin/env python3
"""Replay bounded teaching rivals for this task through protected Racket.

The original prototype checks only the opposite parent setting. This audit also
tries a depth limit learned from the demonstrations, frozen input parents, a
missing support gate, and an endpoint-only support shortcut. It retains exact
programs and labels for a rival that fits every demonstration but changes a
query. A passing audit concerns these finite rivals, not universal uniqueness.

On the legal binary palette, right-policy color is complement(left parent),
and left-policy color is complement(right parent), with BOTH support gates.
That simplification is answer-equivalent and is checked as a control. At width
30, a top-only seed can have at most 14 nonempty descendant rows: row r needs
r+1 active top-row ancestors at columns c-r,c-r+2,...,c+r.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root


TASK_ID = "f59691ac00f3"
HOME = Path(__file__).resolve().parent
RETAINED = (
    "generators/f59691ac00f3/workspace/parametric/evidence/reviewer-reported/"
    "2660d3ed32ee6cfc/parametric/f59691ac00f3-parent-choice-v1/private"
)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load same-task source: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_prototype = _load(HOME / "prototype.py", "_parent_choice_audit_prototype")


def _sha(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def selected_program(policy, *, root=None):
    return _prototype.materialize_rule(policy, root=root or find_root(__file__))


def _replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Expected one pinned Racket fragment: {old!r}")
    return source.replace(old, new, 1)


def _endpoint_program(policy):
    endpoint = "lp" if policy == "right" else "rp"
    return f"""(rule! (lambda (g)
      (let* ((h (rows g)) (w (cols g))
             (opp (lambda (v) (if (= v 2) 5 2))))
        (reduce (lambda (grid r)
          (reduce (lambda (g2 c)
            (if (zero? r) g2
              (let* ((lo (- c r)) (hi (+ c r)))
                (if (or (< lo 0) (>= hi w)) g2
                  (let* ((lp (at g 0 lo)) (rp (at g 0 hi)))
                    (if (or (= lp 7) (= rp 7)) g2
                      (set-cell g2 r c
                        (if (zero? (modulo r 2)) {endpoint} (opp {endpoint})))))))))
            grid (range 0 w)))
          g (range 0 h)))))"""


def rival_programs(program, *, depth_cap):
    """Build a finite, explicitly named set of executable rule hypotheses."""
    canonical = _prototype.restore_canonical(program)
    policy = "right" if program == canonical else "left"
    if type(depth_cap) is not int or not 0 <= depth_cap <= 29:
        raise ValueError("depth_cap must be an integer in 0..29")
    branch = (_prototype.CANONICAL_BRANCH if policy == "right"
              else _prototype.ALTERNATIVE_BRANCH)
    source_parent = "lp" if policy == "right" else "rp"
    equivalent = _replace_once(program, branch, f"(set-cell g2 r c (opp {source_parent}))")
    frozen = _replace_once(program, "(at g2 (- r 1) (- c 1))", "(at g (- r 1) (- c 1))")
    frozen = _replace_once(frozen, "(at g2 (- r 1) (+ c 1))", "(at g (- r 1) (+ c 1))")
    entries = [
        ("opposite_setting", selected_program("left" if policy == "right" else "right"),
         "Copy the other parent when active parents differ.", False),
        ("depth_cap", _replace_once(program, "(range 0 h)", f"(range 0 (min h {depth_cap + 1}))"),
         f"Stop after row {depth_cap}, the deepest active row visible in the demonstrations.", False),
        ("frozen_input_parents", frozen,
         "Read the original input above each cell, so generated rows do not feed later rows.", False),
        ("omit_opposite_support_gate", _replace_once(equivalent,
             "(or (= lp 7) (= rp 7))", f"(= {source_parent} 7)"),
         "Shift and complement the source-side parent without requiring the other parent.", False),
        ("endpoint_support_only", _endpoint_program(policy),
         "Use row-parity color from a top-row endpoint; require only the two outer ancestors, ignoring internal holes.", False),
        ("equivalent_complement", equivalent,
         "Binary answer-equivalent color simplification with both support gates retained.", True),
    ]
    return [dict(name=name, program=source, program_sha256=_sha(source),
                 description=description, answer_equivalent=equivalent)
            for name, source, description, equivalent in entries]


@contextmanager
def protected_evaluator(root):
    """Use the exact same protected execution path as native qualification."""
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
    runtime = Path(root).resolve() / "shared/runtime"
    with _local_imports(runtime, HOME):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            def execute(program, grid):
                return _grid(apply(program, _grid(grid)))
            yield execute, identity
        finally:
            bridge.close()


def _normalize_episode(episode, root):
    from arcpuzzles.parametric_worker import _grid
    settings = copy.deepcopy(episode.get("settings", episode.get("parameters")))
    if not isinstance(settings, dict) or set(settings) != {"different_parent"}:
        raise ValueError("Episode requires exactly one different_parent setting")
    program = selected_program(settings["different_parent"], root=root)
    supplied = episode.get("program", episode.get("program_solution", program))
    if supplied != program:
        raise ValueError("Episode program differs from its pinned setting")
    result = dict(seed=episode.get("seed"), settings=settings, program=program)
    for split in ("train", "test"):
        if not isinstance(episode.get(split), list) or not episode[split]:
            raise ValueError("Episode needs nonempty demonstrations and queries")
        result[split] = []
        for pair in episode[split]:
            grid = _grid(pair["input"])
            if any(value not in (2, 5, 7) for value in grid[0]) or any(
                value != 7 for row in grid[1:] for value in row
            ):
                raise ValueError("Audit requires the legal top-only {2,5,7} input grammar")
            result[split].append(dict(input=grid, output=_grid(pair["output"])))
    if "source_evidence" in episode:
        result["source_evidence"] = copy.deepcopy(episode["source_evidence"])
    return result


def retained_episodes(root):
    """Read only this task's two retained visible lessons and private labels."""
    root = Path(root).resolve()
    result = []
    for path in sorted((root / RETAINED).glob("episode-*.json")):
        episode = _normalize_episode(json.loads(path.read_text()), root)
        episode["source_evidence"] = dict(path=path.relative_to(root).as_posix(), sha256=_sha(path.read_bytes()))
        result.append(episode)
    if {row["seed"] for row in result} != {0, 1}:
        raise ValueError("Expected the two task-local retained episodes, seeds 0 and 1")
    return result


def audit_episode(episode, *, execute, racket, root=None):
    """Check demos first; a surviving rule is a defect only if a query differs."""
    root = Path(root or find_root(__file__)).resolve()
    episode = _normalize_episode(episode, root)
    if racket.get("backend") != "racket" or racket.get("protected") is not True:
        raise ValueError("Self-audit evidence requires live protected Racket")
    pairs = [*episode["train"], *episode["test"]]
    for pair in pairs:
        if execute(episode["program"], pair["input"]) != pair["output"]:
            raise ValueError("Episode label differs from live selected Racket")
    depth = max((r for pair in episode["train"] for r, row in enumerate(pair["output"])
                 if any(value != 7 for value in row)), default=0)
    rivals = []
    for rival in rival_programs(episode["program"], depth_cap=depth):
        outputs = [execute(rival["program"], pair["input"]) for pair in episode["train"]]
        matches = [output == pair["output"] for pair, output in zip(episode["train"], outputs)]
        row = {**rival, "demonstration_matches": matches,
               "demonstration_outputs": outputs, "fits_all_demonstrations": all(matches),
               "query_differs": None, "counterexample": False}
        if all(matches) or rival["answer_equivalent"]:
            queries = [execute(rival["program"], pair["input"]) for pair in episode["test"]]
            differences = [output != pair["output"] for pair, output in zip(episode["test"], queries)]
            row.update(query_differs=differences, query_outputs=queries,
                       counterexample=all(matches) and any(differences))
            if rival["answer_equivalent"] and (not all(matches) or any(differences)):
                raise AssertionError("The binary complement equivalence was implemented incorrectly")
            if row["counterexample"]:
                index = next(i for i, differs in enumerate(differences) if differs)
                row["replay_case"] = dict(
                    settings=episode["settings"], program=episode["program"],
                    counterfactual_program=rival["program"], train=copy.deepcopy(episode["train"]),
                    demonstration_predictions=outputs, query_index=index,
                    query=copy.deepcopy(episode["test"][index]), counterfactual_output=queries[index],
                )
        else:
            row["refuting_demonstration_index"] = next(i for i, match in enumerate(matches) if not match)
        rivals.append(row)
    return dict(status="counterexample_found" if any(row["counterexample"] for row in rivals)
                else "no_counterexample_found", episode=episode, selected_labels_match=True,
                max_demonstration_depth=depth, rivals=rivals,
                limits="Only the explicitly materialized finite rivals were checked; this is not universal identification.")


def _source_files(root, *, native):
    relatives = ["generators/f59691ac00f3/generator.py",
                 "generators/f59691ac00f3/workspace/parametric/prototype.py",
                 "generators/f59691ac00f3/workspace/parametric/self_audit.py"]
    if native:
        relatives.append("generators/f59691ac00f3/workspace/parametric/adapter.py")
    return {relative: _sha((root / relative).read_bytes()) for relative in relatives}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("original", "native"))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    root = find_root(__file__)
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError("Choose a new audit output path")
    before = _source_files(root, native=args.mode == "native")
    if args.mode == "original":
        episodes = retained_episodes(root)
    else:
        adapter = _load(HOME / "adapter.py", "_parent_choice_self_audit_adapter")
        episodes = []
        for policy in ("right", "left"):
            settings = {"different_parent": policy}
            generated = adapter.generate(args.seed, settings, args.demos, args.queries)
            episodes.append({**generated, "seed": args.seed, "settings": settings})
    with protected_evaluator(root) as (execute, identity):
        results = [audit_episode(episode, execute=execute, racket=identity, root=root) for episode in episodes]
    if before != _source_files(root, native=args.mode == "native"):
        raise ValueError("Source files changed during audit; rerun against stable bytes")
    found = any(row["status"] == "counterexample_found" for row in results)
    report = dict(task_id=TASK_ID, mode=args.mode,
                  status="counterexample_found" if found else "no_counterexample_found",
                  source_files=before, racket=identity, episodes=results,
                  limits=["Finite rivals and recorded episodes only; no universal uniqueness claim.",
                          "Complement-of-source with both gates is answer-equivalent on {2,5}.",
                          "Top-only width<=30 implies maximum active descendant depth 14.",
                          "This audit does not grant native acceptance or training admission."])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(dict(status=report["status"], mode=args.mode, episodes=len(results),
                          output=str(args.out)), sort_keys=True))
    return 1 if args.mode == "native" and found else 0


if __name__ == "__main__":
    raise SystemExit(main())
