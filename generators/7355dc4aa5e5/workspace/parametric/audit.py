"""Bounded demo-first review using independent events and protected Racket.

Run through review.py run. Python expands the finite seed/count sweep; protected
Racket separately checks native programs and every authored rival's meaning.
This evidence confers neither owner acceptance nor training admission.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parent
TASK = HOME.parents[1]
ROOT = HOME.parents[3]
RUNTIME = ROOT / "shared/runtime"
sys.path[:0] = [str(HOME), str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
import rivals


SETTINGS = tuple({"diagonal_radius": r, "propagation_passes": p}
                 for r, p in itertools.product((1, 2), repeat=2))
DEFAULT_SEEDS = (0, 1, 7, 17, 42, 99, 101, 31337)
DEFAULT_RACKET_SEEDS = (0, 17)


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def source_files():
    paths = [TASK / "generator.py", *(HOME.glob("*.py")), *(HOME.glob("*.rkt"))]
    paths += [p for p in (HOME / "promotion.json",) if p.exists()]
    paths += sorted((TASK / "tests").glob("test_native*.py"))
    return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(set(paths))}


def load_family():
    spec = importlib.util.spec_from_file_location("_independent_7355dc4aa5e5_family", HOME / "family.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_program():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as stream:
        for line in stream:
            row = json.loads(line)
            if row["task_id"] == "7355dc4aa5e5":
                return row["program_solution"]
    raise ValueError("Canonical task authority is missing")


class CachedEvaluator:
    def __init__(self, apply):
        self.apply, self.cache = apply, {}
        self.requests = self.executions = 0

    def __call__(self, program, grid):
        self.requests += 1
        key = program, packed(grid)
        if key not in self.cache:
            self.executions += 1
            self.cache[key] = _grid(self.apply(program, deepcopy(grid)))
        return deepcopy(self.cache[key])


def candidate_bank(family, settings):
    bank = [(f"declared:r{other['diagonal_radius']}:p{other['propagation_passes']}", family.program(other),
             lambda grid, other=other: rivals.reference(grid, other)) for other in SETTINGS]
    bank += [(name, rivals.program(settings, name),
              lambda grid, name=name: rivals.predict(grid, settings, name)) for name in rivals.RIVALS]
    return bank


def fit_on_demos(apply, candidate, train, oracle=None):
    """No query data enters fitting; execution errors are fatal, never refutations."""
    outputs, rejected = [], []
    for index, pair in enumerate(train):
        output = apply(candidate, pair["input"])
        if oracle is not None and output != oracle(pair["input"]):
            raise AssertionError("Independent Python/Racket meaning mismatch")
        outputs.append(output)
        if output != pair["output"]:
            rejected.append(index)
    return {"survives_demonstrations": not rejected, "rejected_by_demo_indices": rejected,
            "demo_outputs": outputs}


def validate_episode(family, episode, settings, demos):
    assert len(episode["train"]) == demos and len(episode["test"]) == 4
    assert episode["program_solution"] == family.program(settings)
    pairs = episode["train"] + episode["test"]
    assert len({packed(p["input"]) for p in pairs}) == len(pairs), "Repeated demo or query input"
    for pair in pairs:
        _grid(pair["input"])
        h, w = len(pair["input"]), len(pair["input"][0])
        assert 7 <= h <= 30 and 7 <= w <= 30
        assert 2 <= len(rivals.coordinates(pair["input"], 1)) <= 12
        rivals.background(pair["input"])
        assert _grid(pair["output"]) == rivals.reference(pair["input"], settings)
    facts = [rivals.facts(pair["input"]) for pair in episode["train"][:2]]
    for radius in (1, 2):
        assert any(f["radii"][str(radius)]["erased_diagonal_cells"] for f in facts), "No early causal stamp erasure"
        assert any(f["radii"][str(radius)]["clipped_marker_count"] for f in facts), "No early clipping control"
    assert any(f["shared_rows"] or f["shared_columns"] for f in facts), "No early shared-axis overwrite"
    return facts


def python_audit(family, seeds):
    report = {"scope": "Independent Python coordinate events only; protected subset separately recorded.",
              "seeds": list(seeds), "demo_counts": list(range(2, 7)), "queries": 4,
              "episodes": [], "findings": [], "label_count": 0}
    input_banks, dimensions, counts, spans, backgrounds = {}, set(), [], [], set()
    query_shapes = Counter()
    for seed in seeds:
        for settings in SETTINGS:
            baseline = None
            for demos in range(2, 7):
                episode = family.generate(seed, settings, demos=demos, queries=4)
                teaching = validate_episode(family, episode, settings, demos)
                report["label_count"] += demos + 4
                inputs = [p["input"] for p in episode["train"] + episode["test"]]
                key = seed, demos
                if key in input_banks:
                    assert inputs == input_banks[key], "Input distribution depends on setting"
                input_banks[key] = inputs
                if baseline is None:
                    baseline = episode
                else:
                    assert baseline["train"][:2] == episode["train"][:2], "First-two-demo stream changes with count"
                    assert baseline["test"] == episode["test"], "Query stream changes with demo count"
                fitted = []
                # Freeze every hypothesis's demo fit before evaluating any query.
                for name, program, oracle in candidate_bank(family, settings):
                    rejected = [i for i, pair in enumerate(episode["train"])
                                if oracle(pair["input"]) != pair["output"]]
                    fitted.append((name, oracle, rejected))
                rows = []
                for name, oracle, rejected in fitted:
                    fits_two = not any(index < 2 for index in rejected)
                    differences = None
                    if fits_two:
                        differences = [i for i, pair in enumerate(episode["test"])
                                       if oracle(pair["input"]) != pair["output"]]
                        if differences:
                            report["findings"].append({"seed": seed, "settings": settings, "demos": demos,
                                "hypothesis": name, "query_indices": differences,
                                "fits_first_two": True, "fits_all_demos": not rejected})
                    rows.append({"name": name, "first_two_demo_fit": fits_two,
                                 "all_demo_fit": not rejected, "rejected_by_demo_indices": rejected,
                                 "query_disagreement_indices": differences})
                report["episodes"].append({"seed": seed, "settings": settings, "demos": demos,
                    "fit_frozen_before_query": True, "fit_demo_count": 2,
                    "first_two_teaching_facts": teaching, "hypotheses": rows,
                    "input_sha256": [sha(packed(grid)) for grid in inputs]})
                if demos == 2 and settings == SETTINGS[0]:
                    for split in ("train", "test"):
                        for pair in episode[split]:
                            f = rivals.facts(pair["input"])
                            dimensions.add(tuple(f["shape"]))
                            counts.append(f["marker_count"])
                            spans.append(f["marker_span"])
                            backgrounds.add(f["background"])
                            if split == "test":
                                query_shapes[tuple(f["shape"])] += 1
    assert family.program(SETTINGS[0]) == canonical_program(), "Default program differs from canonical bytes"
    report.update({"matched_inputs_across_settings": True,
        "first_two_demos_and_queries_independent_of_demo_count": True, "exact_canonical_default": True,
        "coverage": {"dimensions": sorted(dimensions), "original_marker_count_range": [min(counts), max(counts)],
                     "backgrounds": sorted(backgrounds), "marker_spans": sorted(set(map(tuple, spans))),
                     "query_shape_counts": {f"{h}x{w}": n for (h, w), n in sorted(query_shapes.items())},
                     "max_canvas_30x30_seen": (30, 30) in query_shapes}})
    return report


def protected_audit(family, seeds, *, controls_only=False, smoke_only=False):
    report = {"seeds": list(seeds), "demo_counts": [3], "queries": 4, "episodes": [],
              "findings": [], "programs": {}, "semantic_controls": [], "reference_label_count": 0}
    with _local_imports(RUNTIME, HOME):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        evaluator = CachedEvaluator(apply)
        report["racket"] = identity
        try:
            fixtures = rivals.fixtures()
            if smoke_only:
                fixtures = dict(list(fixtures.items())[:1])
            for settings in SETTINGS:
                for fixture_name, grid in fixtures.items():
                    bank = [("native", family.program(settings), lambda g: rivals.reference(g, settings))]
                    if not smoke_only:
                        bank += [(name, rivals.program(settings, name),
                                  lambda g, name=name: rivals.predict(g, settings, name))
                                 for name in ("reference", *rivals.RIVALS)]
                    labels = {}
                    for name, program, oracle in bank:
                        phash = sha(program.encode())
                        report["programs"][phash] = program
                        actual = evaluator(program, grid)
                        assert actual == oracle(grid), ("Semantic-control mismatch", settings, fixture_name, name)
                        labels[name] = {"program_sha256": phash, "output": actual}
                    report["semantic_controls"].append({"name": fixture_name, "settings": settings,
                                                       "input": grid, "labels": labels})
            if not (controls_only or smoke_only):
                for seed in seeds:
                    for settings in SETTINGS:
                        episode = family.generate(seed, settings, demos=3, queries=4)
                        validate_episode(family, episode, settings, 3)
                        selected = family.program(settings)
                        selected_hash = sha(selected.encode())
                        report["programs"][selected_hash] = selected
                        for pair in episode["train"] + episode["test"]:
                            actual = evaluator(selected, pair["input"])
                            assert actual == pair["output"] == rivals.reference(pair["input"], settings)
                            report["reference_label_count"] += 1
                        fitted = []
                        for name, candidate, oracle in candidate_bank(family, settings):
                            phash = sha(candidate.encode())
                            report["programs"][phash] = candidate
                            fit = fit_on_demos(evaluator, candidate, episode["train"][:2], oracle)
                            fitted.append((name, candidate, oracle, {"name": name,
                                                                   "program_sha256": phash, **fit}))
                        rows = []
                        for name, candidate, oracle, fit in fitted:
                            fit["query_disagreement_indices"] = None
                            if fit["survives_demonstrations"]:
                                outputs = [evaluator(candidate, pair["input"]) for pair in episode["test"]]
                                assert outputs == [oracle(pair["input"]) for pair in episode["test"]]
                                difference = [i for i, (out, pair) in enumerate(zip(outputs, episode["test"]))
                                              if out != pair["output"]]
                                fit.update({"query_outputs": outputs, "query_disagreement_indices": difference})
                                if difference:
                                    report["findings"].append({"seed": seed, "settings": settings, "demos": 3,
                                        "hypothesis": name, "query_indices": difference,
                                        "minimal_train": episode["train"][:2], "query": episode["test"][difference[0]],
                                        "program": selected, "rival_program": candidate,
                                        "rival_query_output": outputs[difference[0]]})
                            rows.append(fit)
                        report["episodes"].append({"seed": seed, "settings": settings, "demos": 3,
                            "program_sha256": selected_hash, "fit_frozen_before_query": True, "fit_demo_count": 2,
                            "train": episode["train"], "test": episode["test"], "hypotheses": rows,
                            "scene_facts": {split: [rivals.facts(p["input"]) for p in episode[split]]
                                            for split in ("train", "test")}})
        finally:
            report["racket_executions"] = evaluator.executions
            report["racket_cache_hits"] = evaluator.requests - evaluator.executions
            bridge.close()
    return report


def run(args):
    out = Path(args.out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    binding = source_files()
    report = {"schema": "7355dc4aa5e5-independent-finite-self-review-v1", "status": "running",
              "source_files_sha256": binding, "rivals": rivals.DESCRIPTIONS,
              "training_admitted": False, "owner_accepted": False, "visibility": "controller_private",
              "limits": "Finite declared rivals and seeds only; no universal uniqueness. Python-only cases are not protected-Racket evidence.",
              "command_argv": sys.argv}
    error = None
    try:
        family = load_family()
        if not (args.controls_only or args.smoke_only):
            report["python"] = python_audit(family, args.seeds)
        if not args.python_only:
            report["protected"] = protected_audit(family, args.racket_seeds,
                controls_only=args.controls_only, smoke_only=args.smoke_only)
        assert source_files() == binding, "Task sources changed during review; rerun against stable sources"
        findings = sum(len(report.get(section, {}).get("findings", [])) for section in ("python", "protected"))
        report["finding_count"] = findings
        report["status"] = "findings" if findings else "no_issue_in_finite_scope"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = type(exc).__name__ + ": " + str(exc)
        error = exc
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"status": report["status"], "out": str(out), "finding_count": report.get("finding_count"),
        "python_episodes": len(report.get("python", {}).get("episodes", [])),
        "protected_episodes": len(report.get("protected", {}).get("episodes", [])),
        "racket_executions": report.get("protected", {}).get("racket_executions"),
        "error": report.get("error")}, sort_keys=True))
    if error is not None:
        raise error
    return report["finding_count"] == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=DEFAULT_SEEDS)
    parser.add_argument("--racket-seeds", type=int, nargs="+", default=DEFAULT_RACKET_SEEDS)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--python-only", action="store_true")
    group.add_argument("--controls-only", action="store_true")
    group.add_argument("--smoke-only", action="store_true")
    raise SystemExit(0 if run(parser.parse_args()) else 1)
