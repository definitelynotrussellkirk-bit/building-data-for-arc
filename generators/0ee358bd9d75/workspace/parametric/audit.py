"""Bounded, source-bound authoring census for the proposed frequency parameter."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (canonical_pairs, canonical_path, find_root, load_selected_generator,
                              public_challenge_bytes, public_challenge_id)


HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
_spec = importlib.util.spec_from_file_location("_frequency_prototype_audit", HERE / "prototype.py")
prototype = importlib.util.module_from_spec(_spec)
exec(compile((HERE / "prototype.py").read_bytes(), str(HERE / "prototype.py"), "exec"), prototype.__dict__)
DEFAULT_SEEDS = tuple(range(8)) + tuple(range(50000, 50008))


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def independent_oracle(grid, selection):
    """Validation only: independently count sections directly from input cells."""
    row_breaks = [-1, *[r for r, row in enumerate(grid) if all(v == 0 for v in row)], len(grid)]
    col_breaks = [-1, *[c for c in range(len(grid[0])) if all(row[c] == 0 for row in grid)], len(grid[0])]
    output = []
    for r0, r1 in zip(row_breaks, row_breaks[1:]):
        out_row = []
        for c0, c1 in zip(col_breaks, col_breaks[1:]):
            counts = Counter(grid[r][c] for r in range(r0 + 1, r1) for c in range(c0 + 1, c1) if grid[r][c])
            ordered = sorted(counts, key=counts.get, reverse=selection == "most_frequent")
            if not ordered or (len(ordered) > 1 and counts[ordered[0]] == counts[ordered[1]]):
                raise ValueError("independent oracle encountered an ambiguous extreme")
            out_row.append(ordered[0])
        output.append(out_row)
    return output


def source_hashes(generator_source, generator_hash):
    sources = [HERE / "prototype.py", HERE / "audit.py", HERE / "adapter.py", HERE / "promotion.json",
               *sorted((HERE / "programs").glob("*.rkt")),
               ROOT / "generators" / prototype.TASK_ID / "tests" / "test_parametric_extension.py",
               ROOT / "generators" / prototype.TASK_ID / "tests" / "test_parametric_counts.py",
               canonical_path(ROOT)]
    if (HERE / "README.md").is_file():
        sources.append(HERE / "README.md")
    result = {path.relative_to(ROOT).as_posix(): file_hash(path) for path in sources}
    result[generator_source.relative_to(ROOT).as_posix()] = generator_hash
    return result


def run_census(output, *, seeds=DEFAULT_SEEDS, bridge=None):
    """Execute all labels and check both settings on all four query rotations.

    Failures are retained in the report. A failed report is not approval and
    does not silently become a smaller successful census.
    """
    seeds = tuple(seeds)
    if not 1 <= len(seeds) <= 64 or any(type(seed) is not int for seed in seeds) or len(set(seeds)) != len(seeds):
        raise ValueError("provide 1..64 distinct integer seeds")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    private, public_dir = output / "private", output / "public"
    private.mkdir()
    public_dir.mkdir()
    own_bridge = bridge is None
    try:
        if own_bridge:
            bridge = RacketBridge()
        generator, generator_source, generator_hash = load_selected_generator(prototype.TASK_ID, root=ROOT)
        programs = {setting: prototype.materialize_program(setting) for setting in prototype.SELECTIONS}
        hashes = {setting: hashlib.sha256(program.encode()).hexdigest() for setting, program in programs.items()}
        failures = []
        counts = {"canonical_pairs": 0, "canonical_unique_inputs": 0, "generated_inputs": 0,
                  "generated_racket_labels": 0, "witness_racket_labels": 0, "rotations_checked": 0,
                  "ambiguous_rotations": 0, "oracle_mismatches": 0, "lawfulness_failures": 0,
                  "public_challenges_checked": 0}
        for setting, program in programs.items():
            path = private / "programs" / (setting + ".rkt")
            path.parent.mkdir(exist_ok=True)
            path.write_text(program, encoding="utf-8")
        canonical_programs = {variant["program_solution"] for variant in Catalog(ROOT).get(prototype.TASK_ID)["variants"]}
        identical_default = canonical_programs == {programs[prototype.DEFAULT_SELECTION]}
        if not identical_default:
            failures.append({"kind": "default_program_differs_from_canonical"})
        canonical = canonical_pairs(prototype.TASK_ID, root=ROOT)
        canonical_outputs = prototype.execute_program(programs[prototype.DEFAULT_SELECTION],
                                                       [pair["input"] for pair in canonical], bridge=bridge)
        canonical_rows = []
        for pair, actual in zip(canonical, canonical_outputs):
            row = {key: pair[key] for key in ("variant", "split", "pair_index")}
            row.update(input_sha256=prototype.digest(pair["input"]), expected=pair["output"], actual=actual,
                       matches=actual == pair["output"])
            canonical_rows.append(row)
            if not row["matches"]:
                failures.append({"kind": "canonical_mismatch", "pair": pair, "actual": actual})
        counts["canonical_pairs"] = len(canonical_rows)
        counts["canonical_unique_inputs"] = len({row["input_sha256"] for row in canonical_rows})
        write_json(private / "canonical-compatibility.json", {
            "default_program_is_byte_identical": identical_default,
            "canonical_normalized_rule_hash": hashlib.sha256(" ".join(programs[prototype.DEFAULT_SELECTION].split()).encode()).hexdigest()[:12],
            "program_sha256": hashes[prototype.DEFAULT_SELECTION], "pairs": canonical_rows,
        })

        witness = prototype.differing_witness()
        witness_info = prototype.validate_input(witness, require_mixed=True)
        witness_errors = generator.self_check(witness)
        witness_outputs = {setting: prototype.execute_program(program, [witness], bridge=bridge)[0]
                           for setting, program in programs.items()}
        counts["witness_racket_labels"] = len(programs)
        expected_witness = {"most_frequent": [[1, 3], [5, 7]], "least_frequent": [[2, 4], [6, 8]]}
        if witness_errors or witness_outputs != expected_witness:
            failures.append({"kind": "differing_witness_failure", "errors": witness_errors, "actual": witness_outputs})
        write_json(private / "differing-witness.json", {
            "input": witness, "input_sha256": prototype.digest(witness), "sections": witness_info["sections"],
            "canonical_generator_self_check": witness_errors, "program_sha256": hashes,
            "racket_outputs": witness_outputs, "expected_outputs": expected_witness,
        })

        records, sizes, section_color_counts = [], Counter(), Counter()
        episode_mapping = []
        auto_selections = Counter()
        for seed in seeds:
            inputs = prototype.sample_inputs(seed)
            episodes = {setting: prototype.generate_episode(seed, selection=setting, bridge=bridge)
                        for setting in programs}
            predictions = {setting: [pair["output"] for pair in episode["train"] + episode["test"]]
                           for setting, episode in episodes.items()}
            auto_setting = prototype.choose_selection(seed)
            auto_selections[auto_setting] += 1
            record = {"seed": seed, "automatic_episode_selection": auto_setting, "pairs": [], "rotations": []}
            counts["generated_inputs"] += len(inputs)
            counts["generated_racket_labels"] += len(inputs) * len(programs)
            for index, grid in enumerate(inputs):
                info = prototype.validate_input(grid, require_mixed=True)
                errors = generator.self_check(grid)
                if errors:
                    counts["lawfulness_failures"] += 1
                    failures.append({"kind": "canonical_input_lawfulness", "seed": seed,
                                     "pair_index": index, "input": grid, "errors": errors})
                size = (len(grid), len(grid[0]))
                sizes[size] += 1
                section_color_counts.update(len(section["counts"]) for section in info["sections"])
                comparisons = {}
                for setting in programs:
                    actual = predictions[setting][index]
                    expected = independent_oracle(grid, setting)
                    comparisons[setting] = actual == expected
                    if actual != expected:
                        counts["oracle_mismatches"] += 1
                        failures.append({"kind": "oracle_mismatch", "seed": seed, "pair_index": index,
                                         "selection": setting, "input": grid, "actual": actual, "expected": expected})
                record["pairs"].append({"pair_index": index, "input_sha256": prototype.digest(grid),
                                        "shape": list(size), "output_shape": info["output_shape"],
                                        "section_counts": [section["counts"] for section in info["sections"]],
                                        "outputs": {setting: predictions[setting][index] for setting in programs},
                                        "oracle_agreement": comparisons, "canonical_self_check": errors})
            for setting, episode in episodes.items():
                for query_index in range(4):
                    rotated = prototype.rotate_episode(episode, query_index)
                    demos = rotated["train_pair_indices"]
                    survivors = [candidate for candidate in programs if all(
                        predictions[candidate][index] == predictions[setting][index] for index in demos
                    )]
                    ambiguous = survivors != [setting]
                    counts["rotations_checked"] += 1
                    counts["ambiguous_rotations"] += ambiguous
                    if ambiguous:
                        failures.append({"kind": "ambiguous_demonstrations", "seed": seed, "selection": setting,
                                         "query_index": query_index, "survivors": survivors})
                    record["rotations"].append({"selection": setting, "query_pair_index": query_index,
                                               "train_pair_indices": demos, "surviving_settings": survivors,
                                               "rival_query_disagrees": all(
                                                   predictions[candidate][query_index] != predictions[setting][query_index]
                                                   for candidate in programs if candidate != setting)})
            if seed == seeds[0]:
                for index, (setting, episode) in enumerate(episodes.items()):
                    basename = f"episode-{index:03d}.json"
                    public = prototype.public_turn(episode)
                    if set(public) != {"train", "test"} or any(set(pair) != {"input"} for pair in public["test"]):
                        failures.append({"kind": "public_challenge_leak", "selection": setting})
                    public_name = public_challenge_id(public) + ".json"
                    write_json(private / "episodes" / basename, episode)
                    (public_dir / public_name).write_bytes(public_challenge_bytes(public))
                    episode_mapping.append({"selection": setting, "seed": seed,
                                            "private": "private/episodes/" + basename,
                                            "public": "public/" + public_name})
                    counts["public_challenges_checked"] += 1
            records.append(record)

        counts["total_racket_labels"] = counts["canonical_pairs"] + counts["witness_racket_labels"] + counts["generated_racket_labels"]
        limits = [
            "Prototype only; neither a production parametric API nor approval/training admission.",
            "Finite declared rivals: most_frequent and least_frequent; no universal lesson identifiability or model-success claim.",
            "Census seeds are exactly those recorded; four inputs per seed, three demos and one query, all four query holdouts.",
            "Generated sections use two or three nonzero colors with unique least and most frequencies; ties are excluded.",
            "Single-color canonical sections remain lawful but cannot alone identify this parameter; generated demos are all mixed.",
            "Grid dimensions 8..30, one to three full-zero divider rows and columns, section sides at least two.",
            "Only input sampling/proposed programs are added; the selected production generator and authoritative rule remain separate.",
            "Canonical compatibility covers eight ledger pairs (four unique inputs) plus literal default-program equality.",
        ]
        report = {"schema": "section-frequency-parametric-census-v1", "status": "passed" if not failures else "failed",
                  "scope": "prototype", "generator_id": prototype.TASK_ID, "family": prototype.FAMILY,
                  "seeds": list(seeds), "settings": list(programs), "default": prototype.DEFAULT_SELECTION,
                  "parameter_definition": "Select the unique extremal nonzero frequency independently in each zero-divider section.",
                  "program_sha256": hashes, "counts": counts, "automatic_selections": dict(auto_selections),
                  "sizes": [{"height": h, "width": w, "count": count} for (h, w), count in sorted(sizes.items())],
                  "exact_30_by_30_inputs": sizes[(30, 30)],
                  "inputs_with_side_over_20": sum(count for (h, w), count in sizes.items() if max(h, w) > 20),
                  "nonzero_colors_per_section": dict(section_color_counts), "failures": failures,
                  "limits": limits, "episodes": records}
        write_json(private / "census.json", report)
        manifest = {"schema": "section-frequency-parametric-evidence-v1", "status": report["status"],
                    "scope": "prototype", "source_hashes": source_hashes(generator_source, generator_hash),
                    "payload_argv": sys.argv, "program_sha256": hashes, "seeds": list(seeds),
                    "runtime": {"engine": "RacketBridge", "racket_binary_sha256": file_hash(bridge.racket_binary),
                                "prelude_sha256": file_hash(bridge.prelude_path)},
                    "public_delivery": "Only public/*.json; filenames hash exactly the visible first-turn bytes.",
                    "episode_mapping_private": episode_mapping,
                    "files": {path.relative_to(output).as_posix(): file_hash(path)
                              for path in sorted(output.rglob("*")) if path.is_file()}, "limits": limits}
        write_json(private / "manifest.json", manifest)
        return report
    except Exception as exc:
        write_json(private / "failure.json", {"status": "failed", "exception": type(exc).__name__,
                                                      "message": str(exc), "seeds": list(seeds), "payload_argv": sys.argv})
        raise
    finally:
        if own_bridge and bridge is not None:
            bridge.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS)
    args = parser.parse_args()
    report = run_census(args.out, seeds=args.seeds)
    print(json.dumps({"status": report["status"], "scope": "prototype", "counts": report["counts"],
                      "out": str(args.out), "failures": len(report["failures"])}, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
