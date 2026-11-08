"""Bounded independent semantics and demonstration-first adversarial review.

Run through the packet's review.py run wrapper. This checks a declared finite
bank; absence of findings is not universal identifiability or owner acceptance.
The Python sweep expands coverage cheaply. Retained protected-Racket checks
are the authority for every claim labeled Racket in the report.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
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


SETTINGS = ({"bridge_mode": "ignore"}, {"bridge_mode": "merge"})
DEFAULT_SEEDS = (0, 1, 7, 17, 42, 99, 101, 31337)
DEFAULT_RACKET_SEEDS = (0, 17)


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def source_files():
    paths = [TASK / "generator.py", *(HOME.glob("*.py")), *(HOME.glob("*.rkt"))]
    paths += [p for p in (HOME / "promotion.json",) if p.exists()]
    paths += sorted((TASK / "tests").glob("test_parametric*.py"))
    return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(set(paths))}


def prototype():
    spec = importlib.util.spec_from_file_location("_audit_6afe10b621e4_family", HOME / "prototype.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_program():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as stream:
        for line in stream:
            row = json.loads(line)
            if row["task_id"] == "6afe10b621e4":
                return row["program_solution"]
    raise ValueError("Canonical authority row missing")


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
    bank = [("declared:" + other["bridge_mode"], family.program(other),
             lambda grid, other=other: rivals.reference(grid, other)) for other in SETTINGS]
    bank += [(name, rivals.program(settings, name),
              lambda grid, name=name: rivals.predict(grid, settings, name)) for name in rivals.RIVALS]
    return bank


def fit_on_demos(apply, candidate, train, oracle=None):
    """Fit on demonstrations only; all errors propagate and fail the audit."""
    outputs = []
    rejected = []
    for i, pair in enumerate(train):
        output = apply(candidate, pair["input"])
        if oracle is not None and output != oracle(pair["input"]):
            raise AssertionError("Independent Python/Racket rival meaning mismatch")
        outputs.append(output)
        if output != pair["output"]:
            rejected.append(i)
    return {"survives_demonstrations": not rejected,
            "rejected_by_demo_indices": rejected, "demo_outputs": outputs}


def validate_episode(family, episode, seed, settings, demos):
    assert len(episode["train"]) == demos and len(episode["test"]) == 4
    assert episode["program_solution"] == family.program(settings)
    pairs = episode["train"] + episode["test"]
    assert len({packed(p["input"]) for p in pairs}) == len(pairs), "Non-novel query/demo input"
    for pair in pairs:
        _grid(pair["input"])
        assert _grid(pair["output"]) == rivals.reference(pair["input"], settings)
        for mode in ("ignore", "merge"):
            groups = rivals.components(rivals.preprocess(pair["input"], mode))
            for color in (2, 3):
                sizes = sorted((o.size for o in groups if o.color == color), reverse=True)
                assert len(sizes) >= 2, "Fewer than two removable candidates for a source color"
                assert sizes[0] > sizes[1], "Reference maximum is tied"
    first_two = [rivals.facts(p["input"]) for p in episode["train"][:2]]
    assert any(row["two_red_fragments_overtake_original_winner"] for row in first_two), "First two demos lack causal bridge reversal"
    assert any(row["standalone_8_wins_after_merge"] for row in first_two), "First two demos lack standalone-8 control"
    return first_two


def python_audit(family, seeds):
    result = {"scope": "Independent Python mirror only; protected subset reported separately.",
              "seeds": list(seeds), "demo_counts": list(range(2, 7)), "queries": 4,
              "episodes": [], "findings": [], "label_count": 0}
    input_banks = {}
    dimensions, content_counts, content_spans, red_counts, green_counts = [], [], [], [], []
    query_shape_counts = Counter()
    for seed in seeds:
        for settings in SETTINGS:
            base = None
            for demos in range(2, 7):
                episode = family.generate(seed, settings, demos=demos, queries=4)
                teaching_facts = validate_episode(family, episode, seed, settings, demos)
                result["label_count"] += demos + 4
                inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
                bank_key = seed, demos
                if bank_key in input_banks:
                    assert inputs == input_banks[bank_key], "Input distribution reveals setting"
                input_banks[bank_key] = inputs
                if base is None:
                    base = episode
                else:
                    assert episode["train"][:2] == base["train"][:2], "First two demos change with requested count"
                    assert episode["test"] == base["test"], "Query stream depends on requested demo count"
                fitted = []
                # The entire candidate-fitting pass precedes any query prediction.
                for name, program, oracle in candidate_bank(family, settings):
                    rejected = [i for i, pair in enumerate(episode["train"])
                                if oracle(pair["input"]) != pair["output"]]
                    fitted.append((name, program, oracle, rejected))
                rows = []
                for name, program, oracle, rejected in fitted:
                    survives_two = not any(i < 2 for i in rejected)
                    disagreement = None
                    if survives_two:
                        disagreement = [i for i, pair in enumerate(episode["test"])
                                        if oracle(pair["input"]) != pair["output"]]
                        if disagreement:
                            result["findings"].append({"seed": seed, "settings": settings,
                                "demos": demos, "hypothesis": name, "query_indices": disagreement,
                                "fits_first_two": True, "fits_all_demos": not rejected})
                    rows.append({"name": name, "first_two_demo_fit": survives_two,
                                 "all_demo_fit": not rejected, "rejected_by_demo_indices": rejected,
                                 "query_disagreement_indices": disagreement})
                result["episodes"].append({"seed": seed, "settings": settings, "demos": demos,
                    "fit_frozen_before_query": True, "first_two_teaching_facts": teaching_facts,
                    "hypotheses": rows, "input_sha256": [sha(packed(g)) for g in inputs]})
                if demos == 2 and settings["bridge_mode"] == "ignore":
                    for split in ("train", "test"):
                        for pair in episode[split]:
                            f = rivals.facts(pair["input"])
                            dimensions.append(f["shape"])
                            content_counts.append(f["nonzero_cells"])
                            content_spans.append(f["content_span"])
                            red_counts.append(sum(o["color"] == 2 for o in f["original_components"]))
                            green_counts.append(sum(o["color"] == 3 for o in f["original_components"]))
                            if split == "test":
                                query_shape_counts[tuple(f["shape"])] += 1
    assert family.program(SETTINGS[0]) == canonical_program(), "Default source is not canonical bytes"
    result["matched_inputs_across_settings"] = True
    result["first_two_demos_and_queries_independent_of_demo_count"] = True
    result["exact_canonical_default"] = True
    result["coverage"] = {
        "dimensions": sorted(set(map(tuple, dimensions))),
        "nonzero_cells_range": [min(content_counts), max(content_counts)],
        "content_spans": sorted(set(map(tuple, content_spans))),
        "original_red_component_count_range": [min(red_counts), max(red_counts)],
        "green_component_count_range": [min(green_counts), max(green_counts)],
        "query_shape_counts": {f"{h}x{w}": count for (h, w), count in sorted(query_shape_counts.items())},
        "max_canvas_30x30_seen": (30, 30) in query_shape_counts,
    }
    return result


def protected_audit(family, seeds, demos_values, *, controls_only=False):
    report = {"seeds": list(seeds), "demo_counts": list(demos_values), "queries": 4,
              "episodes": [], "findings": [], "programs": {}, "semantic_controls": [],
              "reference_label_count": 0}
    with _local_imports(RUNTIME, HOME):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        evaluator = CachedEvaluator(apply)
        report["racket"] = identity
        try:
            # Independently authored small scenes exercise ties and the intended
            # meanings of all candidates before any generated-lesson claim.
            for settings in SETTINGS:
                for fixture_name, grid in rivals.fixtures().items():
                    labels = {}
                    for name in ("reference", *rivals.RIVALS):
                        program = rivals.program(settings, name)
                        program_hash = sha(program.encode())
                        report["programs"][program_hash] = program
                        expected = rivals.predict(grid, settings, name)
                        actual = evaluator(program, grid)
                        assert actual == expected, ("Semantic-control mismatch", settings, fixture_name, name)
                        labels[name] = {"program_sha256": program_hash, "output": actual}
                    report["semantic_controls"].append({"name": fixture_name, "settings": settings,
                        "input": grid, "labels": labels})
            if not controls_only:
                for seed in seeds:
                    for settings in SETTINGS:
                        for demos in demos_values:
                            episode = family.generate(seed, settings, demos=demos, queries=4)
                            validate_episode(family, episode, seed, settings, demos)
                            selected = family.program(settings)
                            selected_hash = sha(selected.encode())
                            report["programs"][selected_hash] = selected
                            for pair in episode["train"] + episode["test"]:
                                actual = evaluator(selected, pair["input"])
                                assert actual == pair["output"] == rivals.reference(pair["input"], settings)
                                report["reference_label_count"] += 1
                            fitted = []
                            # Only first two visible demos are used to fit. This
                            # gives exactly the supported minimum teaching budget.
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
                                    fit["query_outputs"] = outputs
                                    difference = [i for i, (out, pair) in enumerate(zip(outputs, episode["test"]))
                                                  if out != pair["output"]]
                                    fit["query_disagreement_indices"] = difference
                                    if difference:
                                        report["findings"].append({"seed": seed, "settings": settings,
                                            "demos": demos, "hypothesis": name, "query_indices": difference,
                                            "minimal_train": episode["train"][:2],
                                            "query": episode["test"][difference[0]],
                                            "program": selected, "rival_program": candidate,
                                            "rival_query_output": outputs[difference[0]]})
                                rows.append(fit)
                            report["episodes"].append({"seed": seed, "settings": settings, "demos": demos,
                                "program_sha256": selected_hash, "fit_frozen_before_query": True,
                                "fit_demo_count": 2, "train": episode["train"], "test": episode["test"],
                                "scene_facts": {split: [rivals.facts(p["input"]) for p in episode[split]]
                                                for split in ("train", "test")}, "hypotheses": rows})
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
    report = {"schema": "6afe10b621e4-independent-finite-self-review-v1", "status": "running",
        "source_files_sha256": binding, "rivals": rivals.DESCRIPTIONS,
        "training_admitted": False, "owner_accepted": False, "visibility": "controller_private",
        "limits": "Finite declared rivals and seeds only; no proof of unique inferability. Python-only cases are not Racket execution evidence.",
        "command_argv": sys.argv}
    error = None
    try:
        family = None if args.controls_only else prototype()
        if not args.controls_only:
            report["python"] = python_audit(family, args.seeds)
        if not args.python_only:
            report["protected"] = protected_audit(family, args.racket_seeds, args.racket_demos,
                                                   controls_only=args.controls_only)
        assert source_files() == binding, "Task sources changed during self-review; rerun against stable source"
        findings = sum(len(report.get(section, {}).get("findings", [])) for section in ("python", "protected"))
        report["finding_count"] = findings
        report["status"] = "findings" if findings else "no_issue_in_finite_scope"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = type(exc).__name__ + ": " + str(exc)
        error = exc
    out.parent.mkdir(parents=True, exist_ok=True)
    # Exact grids are retained privately; compact JSON avoids multiplying the
    # transport size with whitespace for every repeated candidate prediction.
    out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"status": report["status"], "out": str(out),
        "finding_count": report.get("finding_count"),
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
    parser.add_argument("--racket-demos", type=int, nargs="+", default=(2, 6))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--python-only", action="store_true")
    group.add_argument("--controls-only", action="store_true")
    args = parser.parse_args()
    raise SystemExit(0 if run(args) else 1)
