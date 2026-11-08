"""Source-bound, finite-rival audit and public export for this native adapter.

Run from any directory, using a new destination each time::

    python3 /path/to/parametric/audit_native.py --out /path/to/new-audit

In an extracted review packet, run from the packet directory so its wrapper
configures the bundled Racket binary::

    WORK/.venv/bin/python review.py run python3 \
        generators/c9034f0626e0/workspace/parametric/audit_native.py \
        --out ../checks/c9034f0626e0/new-audit

The same-checkout protected Racket evaluator checks every sampled label. All
candidate programs see demonstrations before any surviving candidate sees a
query. Survivors and disagreements are observations about this finite bank,
never a claim of universal uniqueness. This tool changes no admission state.

Only individual files beneath public/ are model-visible. Private manifests
contain settings, exact labels, source snapshots, query ordering and results.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager, redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
TASK_ID = "c9034f0626e0"
MODES = ("period2", "period3", "ray_size")
SEEDS = (0, 17, 44)
SOURCE_NAMES = ("native.py", "adapter.py", "ray_component.rkt", "prototype.py",
                "promotion.json", "audit_native.py", "test_native_audit.py", "rivals.py")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def prepare_output(path):
    """Reserve a never-used output directory; do not overwrite earlier evidence."""
    path = Path(path).absolute()
    path.mkdir(parents=True, exist_ok=False)
    for relative in ("private/source", "private/programs", "private/episodes", "private/witnesses", "public/full", "public/turns"):
        (path / relative).mkdir(parents=True, exist_ok=False)
    return path


def write_new(path, data):
    """Deduplicate identical content IDs without replacing any differing file."""
    try:
        with path.open("xb") as handle:
            handle.write(data)
    except FileExistsError:
        if path.read_bytes() != data:
            raise ValueError(f"existing output has different bytes: {path}")


def exact_module(path, prefix):
    path = Path(path)
    if path.is_symlink() or path.resolve() != path or not path.is_file():
        raise ValueError(f"module must be a regular exact-path source: {path}")
    name = prefix + sha256(str(path).encode())
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load exact source {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@contextmanager
def same_checkout():
    """Use this task's adapter and this checkout's runtime, regardless of cwd."""
    runtime = ROOT / "shared/runtime"
    before = list(sys.path)
    sys.path.insert(0, str(ROOT / "src"))
    try:
        worker = importlib.import_module("arcpuzzles.parametric_worker")
        if Path(worker.__file__).resolve() != ROOT / "src/arcpuzzles/parametric_worker.py":
            raise ValueError("arcpuzzles.parametric_worker came from another checkout")
        with worker._local_imports(runtime, HOME):
            adapter = exact_module(HOME / "adapter.py", "_native_audit_adapter_")
            support = exact_module(runtime / "reviewer_support.py", "_native_audit_support_")
            yield adapter, worker, support, runtime
    finally:
        sys.path[:] = before


def replace_once(source, needle, replacement):
    """Fail closed if a source change invalidates a named rival mutation."""
    count = source.count(needle)
    if count != 1:
        raise ValueError(f"rival mutation needs exactly one occurrence, found {count}: {needle}")
    return source.replace(needle, replacement, 1)


def rival_programs(adapter, chosen):
    programs = {mode: adapter.program({"lattice_rule": mode}) for mode in MODES}
    ray = programs["ray_size"]
    period = "(period (if (= (remainder (length selected-cells) 2) 0) 2 3))"
    programs["ray_reversed_parity"] = replace_once(
        ray, period, "(period (if (= (remainder (length selected-cells) 2) 0) 3 2))")
    programs["ray_eight_connectivity"] = replace_once(ray,
        "(connected-region g mr hit-col (lambda (r c v) (= v 5)) 4)",
        "(connected-region g mr hit-col (lambda (r c v) (= v 5)) 8)")
    counts = {
        "ray_horizontal_count": """(if hit-col
            (let loop ((c hit-col) (n 0))
              (if (and (< c w) (= (at g mr c) 5))
                  (loop (+ c 1) (+ n 1)) n)) 0)""",
        "ray_east_gray_count": "(for/sum ((c (range (+ mc 1) w))) (if (= (at g mr c) 5) 1 0))",
        "total_gray_count": "(for*/sum ((r (range 0 h)) (c (range 0 w))) (if (= (at g r c) 5) 1 0))",
        "component_bbox_area": """(if (null? selected-cells) 0
            (let ((bb (bbox-of-cells selected-cells)))
              (* (+ 1 (- (third bb) (first bb)))
                 (+ 1 (- (fourth bb) (second bb))))))""",
    }
    for name, count in counts.items():
        programs[name] = replace_once(ray, "(length selected-cells)", count)
    actual = programs[chosen]
    p = "period" if chosen == "ray_size" else chosen[-1]
    row, col = f"(= (remainder r {p}) rp)", f"(= (remainder c {p}) cp)"
    programs[f"{chosen}_row_only"] = replace_once(actual, col, "#t")
    programs[f"{chosen}_column_only"] = replace_once(actual, row, "#t")
    programs[f"{chosen}_sum_residue"] = replace_once(replace_once(actual, row,
        f"(= (remainder (+ r c) {p}) (remainder (+ mr mc) {p}))"), col, "#t")
    programs[f"{chosen}_overwrite_gray"] = replace_once(actual, "(zero? (at g r c))",
        "(or (zero? (at g r c)) (= (at g r c) 5))")
    return programs


def audit_predictions(episode, candidates, chosen, execute):
    """Keep execution errors, label failures and finite ambiguity distinct."""
    names = [chosen] + [name for name in candidates if name != chosen]
    result = {"rivals": {}, "surviving_rivals": [], "ambiguous_rivals": [],
              "failures": [], "actual_predictions": {}, "survivor_query_predictions": {}}
    demos = {}

    def prediction(name, pair, split, index):
        try:
            return execute(candidates[name], pair["input"],
                           ("actual_" if name == chosen else "rival_") + split)
        except Exception as exc:
            result["failures"].append({"kind": "execution_error", "candidate": name,
                "split": split, "index": index, "error": type(exc).__name__, "message": str(exc)})
            return None

    # Stage 1: every candidate sees all demonstrations. No query runs here.
    for name in names:
        demos[name] = [prediction(name, pair, "train", i)
                       for i, pair in enumerate(episode["train"])]
    actual_demos = demos[chosen]
    result["actual_predictions"]["train"] = actual_demos
    for i, (observed, pair) in enumerate(zip(actual_demos, episode["train"])):
        if observed is not None and observed != pair["output"]:
            result["failures"].append({"kind": "reference_label_mismatch", "split": "train", "index": i})
    if any(grid is None for grid in actual_demos):
        # An unavailable authority cannot support a rival rejection or survival.
        for name in names:
            result["rivals"][name] = {"demo_status": "authority_failed", "query_status": "not_run_authority_failed"}
        return result

    survivors = []
    for name in names:
        errors = any(grid is None for grid in demos[name])
        mismatches = [i for i, (grid, exact) in enumerate(zip(demos[name], actual_demos))
                      if grid is not None and grid != exact]
        survives = not errors and not mismatches
        result["rivals"][name] = {"demo_status": "execution_error" if errors else "survives" if survives else "rejected",
            "demo_mismatch_indices": mismatches,
            "query_status": "pending" if survives else "not_run_demo_error" if errors else "not_run_demo_rejected"}
        if survives:
            survivors.append(name)
            if name != chosen:
                result["surviving_rivals"].append(name)

    # Stage 2: evaluate queries only for complete demonstration survivors.
    outputs = {name: [prediction(name, pair, "test", i) for i, pair in enumerate(episode["test"])]
               for name in survivors}
    actual_queries = outputs[chosen]
    result["actual_predictions"]["test"] = actual_queries
    for i, (observed, pair) in enumerate(zip(actual_queries, episode["test"])):
        if observed is not None and observed != pair["output"]:
            result["failures"].append({"kind": "reference_label_mismatch", "split": "test", "index": i})
    for name, grids in outputs.items():
        errors = any(grid is None for grid in grids) or any(grid is None for grid in actual_queries)
        mismatches = [i for i, (grid, exact) in enumerate(zip(grids, actual_queries))
                      if grid is not None and exact is not None and grid != exact]
        result["rivals"][name].update({"query_status": "execution_error" if errors else
            "disagrees" if mismatches else "agrees_on_checked_queries", "query_mismatch_indices": mismatches})
        if name != chosen:
            result["survivor_query_predictions"][name] = grids
            if mismatches:
                result["ambiguous_rivals"].append(name)
    return result


def ambiguity_witnesses(episode, result, candidates, chosen):
    """Retain each survivor's first disagreement with the full teaching lesson.

    This removes unrelated queries; it does not claim a minimized grid or a
    minimal demonstration subset. Both programs and both outputs are private.
    """
    witnesses = []
    for name in result["ambiguous_rivals"]:
        index = result["rivals"][name]["query_mismatch_indices"][0]
        witnesses.append({"rival": name, "query_index": index,
            "witness_kind": "all_demonstrations_plus_one_disagreeing_query",
            "visible": {"train": deepcopy(episode["train"]),
                        "test": [{"input": deepcopy(episode["test"][index]["input"])}]},
            "actual_output": deepcopy(result["actual_predictions"]["test"][index]),
            "rival_output": deepcopy(result["survivor_query_predictions"][name][index]),
            "actual_program": candidates[chosen], "rival_program": candidates[name],
            "actual_program_sha256": sha256(candidates[chosen].encode()),
            "rival_program_sha256": sha256(candidates[name].encode())})
    return witnesses


def check_public_projection(adapter, support, episode, seed, mode, demos, generate=None):
    generate = adapter.generate if generate is None else generate
    visible = adapter.public_challenge(episode)
    payload = support.public_challenge_bytes(visible)
    if support.public_challenge_id(visible) != sha256(payload):
        raise ValueError("public content ID does not bind the exact exported bytes")
    if payload != support.public_challenge_bytes(episode):
        raise ValueError("adapter public projection changes visible episode content")
    private = deepcopy(episode)
    for key in list(private):
        if key not in ("train", "test"):
            private[key] = {"private": "changed"}
    private["future_query_count"] = 999
    private["private_metadata"] = {"seed": -999, "settings": "changed"}
    for pair in private["train"]:
        pair["private_pair_metadata"] = "changed"
    for pair in private["test"]:
        pair["output"] = [[9]]
        pair["private_pair_metadata"] = "changed"
    invariant = payload == support.public_challenge_bytes(adapter.public_challenge(private))
    future_invariant = True
    for i in range(len(episode["test"])):
        one = adapter.public_challenge(episode, i)
        encoded = support.public_challenge_bytes(one)
        expected = {"train": deepcopy(episode["train"]), "test": [{"input": deepcopy(episode["test"][i]["input"])}]}
        if encoded != support.public_challenge_bytes(expected):
            raise ValueError("single-query export includes something other than the indexed query")
        parsed = json.loads(encoded)
        if (set(parsed) != {"train", "test"} or len(parsed["test"]) != 1
                or set(parsed["test"][0]) != {"input"}
                or any(set(pair) != {"input", "output"} for pair in parsed["train"])):
            raise ValueError("single-query bytes contain private fields or count hints")
        truncated = deepcopy(episode)
        truncated["test"] = truncated["test"][:i + 1]
        perturbed = deepcopy(private)
        for pair in perturbed["test"][i + 1:]:
            pair["input"] = [[8]]
        future_invariant &= encoded == support.public_challenge_bytes(adapter.public_challenge(truncated, i))
        future_invariant &= encoded == support.public_challenge_bytes(adapter.public_challenge(perturbed, i))
    short = generate(seed, {"lattice_rule": mode}, demos, 1)
    long = episode if len(episode["test"]) == 4 else generate(seed, {"lattice_rule": mode}, demos, 4)
    same_first = (support.public_challenge_bytes(adapter.public_challenge(short, 0)) ==
                  support.public_challenge_bytes(adapter.public_challenge(long, 0)))
    checks = {"private_metadata_invariant": invariant,
              "future_queries_invariant": future_invariant,
              "query1_single_vs_four_exact_bytes": same_first}
    if not all(checks.values()):
        raise ValueError(f"public projection invariant failed: {checks}")
    return checks


def export_episode(out, support, adapter, episode):
    exports = {"turns": []}
    if len(episode["test"]) == 4:
        challenge = adapter.public_challenge(episode)
        content_id = support.public_challenge_id(challenge)
        relative = f"public/full/{content_id}.json"
        write_new(out / relative, support.public_challenge_bytes(challenge))
        exports["full"] = {"path": relative, "public_challenge_id": content_id}
    for index in range(len(episode["test"])):
        challenge = adapter.public_challenge(episode, index)
        content_id = support.public_challenge_id(challenge)
        relative = f"public/turns/{content_id}.json"
        write_new(out / relative, support.public_challenge_bytes(challenge))
        exports["turns"].append({"query_index": index, "path": relative, "public_challenge_id": content_id})
    return exports


def sample_stats(episode, exact):
    result = []
    for split in ("train", "test"):
        for index, pair in enumerate(episode[split]):
            output = exact.get(split, [None] * len(episode[split]))[index]
            if output is None:
                continue
            grid = pair["input"]
            result.append({"split": split, "height": len(grid), "width": len(grid[0]),
                "changed_cells": sum(a != b for x, y in zip(grid, output) for a, b in zip(x, y))})
    return result


def summarize_stats(rows):
    if not rows:
        return {"pair_count": 0}
    return {"pair_count": len(rows), "split_counts": dict(Counter(row["split"] for row in rows)),
        "dimensions": {key: {"min": min(row[key] for row in rows), "max": max(row[key] for row in rows)}
                       for key in ("height", "width")},
        "shapes": sorted({(row["height"], row["width"]) for row in rows}),
        "changed_cells": {"min": min(row["changed_cells"] for row in rows),
                          "max": max(row["changed_cells"] for row in rows),
                          "total": sum(row["changed_cells"] for row in rows)}}


def jobs():
    for mode in MODES:
        for seed in SEEDS:
            yield {"kind": "primary", "seed": seed, "mode": mode, "demos": 3, "queries": 4}
            yield {"kind": "minimum_count", "seed": seed, "mode": mode, "demos": 2, "queries": 4}
        yield {"kind": "maximum_count", "seed": 0, "mode": mode, "demos": 6, "queries": 4}


def run_audit(out):
    out = prepare_output(out)
    report = {"schema": "c9034-native-finite-audit-v1", "task_id": TASK_ID,
        "started_utc": datetime.now(timezone.utc).isoformat(), "status": "running",
        "scope": "Finite sampled execution and public-projection checks; no universal uniqueness or admission conclusion.",
        "source_files": {}, "jobs_planned": list(jobs()), "episodes": [], "failures": [],
        "racket_call_counts": {"attempted": 0, "returned": 0, "failed": 0, "by_phase": {}},
        "generation_call_count": 0}
    stats = {mode: [] for mode in MODES}
    try:
        for name in SOURCE_NAMES:
            source = HOME / name
            if not source.is_file() and name in ("test_native_audit.py", "rivals.py"):
                continue
            data = source.read_bytes()
            write_new(out / "private/source" / name, data)
            report["source_files"][name] = {"path": str(source.relative_to(ROOT)), "sha256": sha256(data)}
        with same_checkout() as (adapter, worker, support, runtime):
            if tuple(adapter.MODES) != MODES:
                raise ValueError("adapter mode declaration differs from the audit's finite scope")
            report["runtime_sources"] = {str(path.relative_to(ROOT)): sha256(path.read_bytes()) for path in
                (ROOT / "src/arcpuzzles/parametric_worker.py", runtime / "reviewer_support.py")}
            apply, identity, bridge = worker._real_evaluator(runtime)
            report["racket_runtime_identity"] = identity
            try:
                counts = report["racket_call_counts"]

                def generate(*args):
                    report["generation_call_count"] += 1
                    return adapter.generate(*args)

                def execute(program, grid, phase):
                    counts["attempted"] += 1
                    counts["by_phase"][phase] = counts["by_phase"].get(phase, 0) + 1
                    try:
                        output = worker._grid(apply(program, deepcopy(grid)))
                        if len(output) != len(grid) or len(output[0]) != len(grid[0]):
                            raise ValueError("candidate changed grid dimensions")
                    except Exception:
                        counts["failed"] += 1
                        raise
                    counts["returned"] += 1
                    return output

                for index, job in enumerate(report["jobs_planned"]):
                    row = {"index": index, **job}
                    report["episodes"].append(row)
                    mode = job["mode"]
                    private = None
                    try:
                        episode = generate(job["seed"], {"lattice_rule": mode}, job["demos"], job["queries"])
                        private = {"job": job, "claimed_episode": episode}
                        if episode.get("program_solution") != adapter.program({"lattice_rule": mode}):
                            raise ValueError("generated source differs from program(settings)")
                        if episode.get("settings") != {"lattice_rule": mode}:
                            raise ValueError("generated private settings differ from the requested settings")
                        for split, count in (("train", job["demos"]), ("test", job["queries"])):
                            if type(episode.get(split)) is not list or len(episode[split]) != count:
                                raise ValueError(f"requested {split} count was not honored")
                            for pair in episode[split]:
                                worker._grid(pair["input"])
                                worker._grid(pair["output"])
                        inputs = [json.dumps(pair["input"]) for split in ("train", "test") for pair in episode[split]]
                        if len(inputs) != len(set(inputs)):
                            raise ValueError("episode contains duplicate demonstration/query inputs")
                        candidates = rival_programs(adapter, mode)
                        program_files = {}
                        for name, source in candidates.items():
                            digest = sha256(source.encode())
                            relative = f"private/programs/{digest}.rkt"
                            write_new(out / relative, source.encode())
                            program_files[name] = {"sha256": digest, "path": relative}
                        result = audit_predictions(episode, candidates, mode, execute)
                        private.update({"programs": program_files, "execution": result})
                        row["programs"] = program_files
                        row["rivals"] = result["rivals"]
                        row["surviving_rivals"] = result["surviving_rivals"]
                        row["ambiguous_rivals"] = result["ambiguous_rivals"]
                        row["failures"] = result["failures"]
                        row["status"] = "failed" if result["failures"] else "finite_ambiguity" if result["ambiguous_rivals"] else "checked"
                        report["failures"].extend({"episode_index": index, **failure} for failure in result["failures"])
                        measurements = sample_stats(episode, result["actual_predictions"])
                        stats[mode].extend(measurements)
                        row["stats"] = summarize_stats(measurements)
                        row["public_checks"] = check_public_projection(adapter, support, episode,
                            job["seed"], mode, job["demos"], generate=generate)
                        if not result["failures"]:
                            row["exports"] = export_episode(out, support, adapter, episode)
                            private["exports"] = row["exports"]
                            row["witnesses"] = []
                            for witness in ambiguity_witnesses(episode, result, candidates, mode):
                                relative = f"private/witnesses/{index:03d}-{witness['rival']}.json"
                                write_new(out / relative, json_bytes({"job": job, **witness}))
                                row["witnesses"].append(relative)
                    except Exception as exc:
                        failure = {"episode_index": index, "kind": "episode_error", "error": type(exc).__name__, "message": str(exc)}
                        row["status"] = "failed"
                        row.setdefault("failures", []).append(failure)
                        report["failures"].append(failure)
                    finally:
                        if private is not None:
                            relative = f"private/episodes/{index:03d}.json"
                            row["private_episode"] = relative
                            private["audit_status"] = row["status"]
                            private["audit_failures"] = row.get("failures", [])
                            write_new(out / relative, json_bytes(private))
            finally:
                bridge.close()
    except Exception as exc:
        report["failures"].append({"kind": "audit_error", "error": type(exc).__name__, "message": str(exc)})
    finally:
        for name, source in report["source_files"].items():
            try:
                final_hash = sha256((HOME / name).read_bytes())
            except OSError:
                final_hash = None
            source["unchanged_during_audit"] = final_hash == source["sha256"]
            if not source["unchanged_during_audit"]:
                report["failures"].append({"kind": "source_changed_during_audit", "source": name, "final_sha256": final_hash})
        report["per_setting_stats"] = {mode: summarize_stats(rows) for mode, rows in stats.items()}
        report["episode_count"] = len(report["episodes"])
        report["finite_ambiguity_episode_count"] = sum(bool(row.get("ambiguous_rivals")) for row in report["episodes"])
        report["surviving_rival_episode_count"] = sum(bool(row.get("surviving_rivals")) for row in report["episodes"])
        report["status"] = ("failed" if report["failures"] else "completed_with_finite_ambiguities"
                            if report["finite_ambiguity_episode_count"] else "completed_no_observed_finite_ambiguity")
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        write_new(out / "private/report.json", json_bytes(report))
    return out, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="new output directory; existing paths are refused")
    args = parser.parse_args(argv)
    try:
        with redirect_stdout(sys.stderr):
            out, report = run_audit(args.out)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": type(exc).__name__, "message": str(exc)}))
        return 1
    print(json.dumps({"status": report["status"], "report": str(out / "private/report.json"),
        "episodes": report["episode_count"], "racket_calls": report["racket_call_counts"]["attempted"],
        "finite_ambiguity_episodes": report["finite_ambiguity_episode_count"], "failures": len(report["failures"])}))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
