"""Bind the final question answer to one already Racket-labelled census pair."""
from __future__ import annotations
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
REPO = WORK / "repo"
TASK = "274345a1792c"
EXPECTED = "3bbaba80d999266c004e3bd4fd823e0694b419bcd7c9046cf1d0332645376dd9"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def grid_hash(grid):
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def report(name):
    path = WORK / "checks" / name
    if not path.exists():
        path = Path(str(path) + ".gz")
    raw = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
    return json.loads(raw), digest(raw)


def main():
    source = REPO / "generators" / TASK / "generator.py"
    assert digest(source.read_bytes()) == EXPECTED
    sys.path.insert(0, str(REPO / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("final_question_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    from reviewer_support import canonical_pairs
    pairs = canonical_pairs(TASK, root=REPO)
    fits = {name: {"matches": sum(rival(p["input"]) == p["output"] for p in pairs), "pairs": len(pairs)}
            for name, rival in gen.CANONICAL_SHORTCUTS.items()}
    assert all(row == {"matches": 5, "pairs": 5} for row in fits.values())
    census, census_sha = report("lesson-census-final.json")
    distribution, distribution_sha = report("distribution-final-source.json")
    assert census["generator_sha256"] == distribution["after"]["generator_sha256"] == EXPECTED
    lesson = census["lessons"][0]
    sampled = next(row for row in lesson["instance"]["sampling"]["accepted_pairs"]
                   if row["split"] == "train" and row["pair_index"] == 1)
    pair = lesson["instance"]["train"][1]
    grid, output = pair["input"], pair["output"]
    call = {"seed": lesson["seed"], "sample_index": sampled["sample_index"],
            "difficulty": lesson["band"], "overrides": {}}
    actual = gen.generate(call["seed"], call["sample_index"], difficulty=call["difficulty"])
    assert actual == grid and grid_hash(grid) == sampled["input_sha256"]
    assert gen.self_check(grid) == []
    rival = gen.CANONICAL_SHORTCUTS["once_per_code"](grid)
    differences = [[r, c, output[r][c], rival[r][c]] for r in range(len(grid))
                   for c in range(len(grid[0])) if output[r][c] != rival[r][c]]
    assert differences
    old = json.loads((HERE / "evidence.json").read_text())
    compact = old["examples"][0]["input"] if "examples" in old else old["cases"][0]["input"]
    compact_errors = gen.self_check(compact)
    assert compact_errors == []
    witness = {"schema": "arcpuzzles-final-question-witness-v1", "task_id": TASK,
               "generator_sha256": EXPECTED, "rule_hash": census["declared_rule_hash"],
               "rule_callable_sha256": census["rule_callable_sha256"],
               "source_rule_sha256": census["rule_source_sha256"],
               "label_provenance": "Actual retained public Racket lesson-census output; this probe does not relabel.",
               "census_file": "checks/lesson-census-final.json.gz", "census_uncompressed_sha256": census_sha,
               "census_pair_json_pointer": "/lessons/0/instance/train/1",
               "census_sampling_json_pointer": "/lessons/0/instance/sampling/accepted_pairs/1",
               "census_lesson_rival_verdict": lesson["rivals"]["CANONICAL_SHORTCUTS:once_per_code"],
               "generate_call": call, "matches_retained_generated_input": True,
               "dimensions": {"input": [len(grid), len(grid[0])], "output": [len(output), len(output[0])]},
               "input_sha256": grid_hash(grid), "output_sha256": grid_hash(output),
               "input": grid, "actual_racket_output": output, "rival_name": "once_per_code",
               "rival_output": rival, "differences_r_c_actual_rival": differences,
               "validator_messages": [], "compact_handcrafted_final_validator_messages": compact_errors,
               "canonical_shortcuts_iterated": fits,
               "distinct_lesson_rivals": sorted(gen.LESSON_COMPETITORS),
               "distribution_file": "checks/distribution-final-source.json.gz",
               "distribution_uncompressed_sha256": distribution_sha,
               "distribution_sampling": distribution["sampling"], "distribution_summary": distribution["after"]["summary"],
               "census_summary": census["summary"], "census_sampler": census["sampler"],
               "census_execution": {k:v for k,v in census["execution"].items() if k not in {"stdout", "stderr"}},
               "probe_argv": sys.argv, "probe_cwd": str(Path.cwd()), "probe_sha256": digest(Path(__file__).read_bytes())}
    (HERE / "final-question-witness.json").write_text(json.dumps(witness, indent=2) + "\n")
    print(json.dumps({k:witness[k] for k in ("generator_sha256", "generate_call", "dimensions", "input_sha256",
                                            "output_sha256", "differences_r_c_actual_rival", "canonical_shortcuts_iterated")}, indent=2))


if __name__ == "__main__":
    main()
