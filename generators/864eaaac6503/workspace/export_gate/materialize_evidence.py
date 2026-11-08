#!/usr/bin/env python3
"""Small authoring diagnostic: Racket-label two E witnesses, then screen final episodes."""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import sys

for parent in Path(__file__).resolve().parents:
    for runtime in (parent / "shared/runtime", parent):
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    else:
        continue
    break
from reviewer_support import canonical_pairs, find_root, load_selected_generator, normalize_grid
from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from final_episode_gate import screen_episode
ROOT = find_root(__file__)
TASK = "864eaaac6503"


def only_three_by_three(grid):
    """Candidate shortcut hypothesis; never a reference label generator."""
    return [list(row) for row in zip(*grid)][::-1] if len(grid) == len(grid[0]) == 3 else deepcopy(grid)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        parser.error("output directory must be new; existing evidence is source-bound")
    # Controlled authoring-time load only. The reusable gate imports no generator.
    generator, source, source_hash = load_selected_generator(TASK, root=ROOT)
    source_bytes = source.read_bytes()
    assert hashlib.sha256(source_bytes).hexdigest() == source_hash
    original = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    rows = []
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            rows.append(row)
    assert {row["program_solution"] for row in rows} == {"(rule! rotate-ccw)"}
    program = rows[0]["program_solution"]
    calls = [{"seed": 731, "sample_index": i, "difficulty": "easy"} for i in (1, 3)]
    inputs = [generator.generate(**call) for call in calls]
    assert inputs[0] != inputs[1]
    assert all((len(grid), len(grid[0])) != (3, 3) and not generator.self_check(grid) for grid in inputs)
    wrapper = "(define (rule! f) f)"
    installation = f"(define export-evidence-rule {program})"
    extended = []
    with RacketBridge() as bridge:
        bridge.eval_text(wrapper)
        bridge.eval_text(installation)
        for grid in inputs:
            bridge.define_grid("export-evidence-input", grid)
            output = normalize_grid(bridge.eval_text("(export-evidence-rule export-evidence-input)"))
            assert output != grid
            extended.append({"input": grid, "output": output})
    canonical = [{"input": pair["input"], "output": pair["output"]} for pair in original if pair["split"] == "train"]
    negative = {"intent": "teaching_negative", "diagnostic": True,
                "train": canonical[:3], "test": [extended[1]]}
    positive = {"intent": "teaching_positive", "diagnostic": True,
                "train": [canonical[0], canonical[1], extended[0]], "test": [extended[1]]}
    rationale = {"only_three_by_three": "This export deliberately includes the extended rotation domain, so a 3x3-only rotation shortcut is admissible as a competing hypothesis. Do not reuse this allowlist for an export whose lawful domain is restricted to 3x3."}
    rivals = {"only_three_by_three": only_three_by_three}
    verdicts = {name: {"current_partition": screen_episode(episode, rivals, rationale=rationale),
                       "all_query_rotations": screen_episode(episode, rivals, rationale=rationale, query_rotation=True)}
                for name, episode in (("teaching_negative", negative), ("teaching_positive", positive))}
    assert not verdicts["teaching_negative"]["current_partition"]["allowed"]
    assert not verdicts["teaching_negative"]["all_query_rotations"]["allowed"]
    assert verdicts["teaching_positive"]["current_partition"]["allowed"]
    assert verdicts["teaching_positive"]["all_query_rotations"]["allowed"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash, "source changed during evidence run"
    out.mkdir(parents=True)
    (out / "generator.snapshot.py").write_bytes(source_bytes)
    gate = Path(__file__).with_name("final_episode_gate.py")
    (out / "final_episode_gate.snapshot.py").write_bytes(gate.read_bytes())
    bridge_path = Path(sys.modules["arc_repl.racket_bridge"].__file__).resolve()
    evidence = {
        "schema": "final-episode-export-gate-diagnostic-v1",
        "status": "proposed finite rival screen; not production integration",
        "intent": "teaching_negative and teaching_positive diagnostics, not accidental solve attempts",
        "generator_source": str(source.relative_to(ROOT)), "generator_sha256": source_hash,
        "gate_sha256": hashlib.sha256(gate.read_bytes()).hexdigest(),
        "materializer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rule_text": program, "rule_text_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "rule_hash": hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12],
        "racket_wrapper": wrapper, "installation": installation,
        "bridge_sha256": hashlib.sha256(bridge_path.read_bytes()).hexdigest(),
        "prelude_sha256": hashlib.sha256((bridge_path.parent / "racket_prelude/arc-prelude.rkt").read_bytes()).hexdigest(),
        "runtime": racket_runtime_status(), "generated_calls": calls,
        "extended_witnesses": extended, "extended_witness_labels_executed_by_racket": 2,
        "negative_episode": negative, "positive_episode": positive,
        "verdicts": verdicts,
        "final_assembly_change": "Drop the first extended demonstration, replace it with canonical train[2], and retain the second extended query: the shortcut now survives all three demos.",
        "limits": ["Reference label correctness is a separate prerequisite, not certified by the pure rival gate.",
                   "Only the explicitly allowlisted only_three_by_three rival is screened here.",
                   "The positive uses two distinct extended reference-labelled pairs so every query rotation retains an informative demo.",
                   "A domain-restricted export can lawfully support narrower hypotheses; caller must justify each rival before screening.",
                   "No measured Qwen3.5-9B improvement, universal induction guarantee, production hook, or dataset approval is claimed."]}
    (out / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"out": str(out), "source_sha256": source_hash, "rule_hash": evidence["rule_hash"],
                      "racket_witnesses": 2, "negative_allowed": False, "positive_allowed": True,
                      "positive_query_rotations_passed": len(verdicts["teaching_positive"]["all_query_rotations"]["checks"])}, sort_keys=True))


if __name__ == "__main__":
    main()
