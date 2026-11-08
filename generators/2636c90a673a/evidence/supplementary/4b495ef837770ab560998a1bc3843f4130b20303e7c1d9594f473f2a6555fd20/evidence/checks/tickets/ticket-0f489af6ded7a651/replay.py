"""Exactly one source/asset-bound replay of the pinned existing audit witness."""
from __future__ import annotations
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def sha(data):
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid):
    return sha(json.dumps(grid, separators=(",", ":")).encode())


def frequency_rival(grid):
    """Exact rival from the pinned audit; the old 3,000-draw loop is not run."""
    counts = Counter(value for value in grid[0] if value != 0)
    if max(counts.values()) == 3:
        candidates = [value for value, count in counts.items() if count == 2]
        marker = min(candidates) if candidates else min(counts, key=lambda value: (-counts[value], value))
    else:
        marker = min(counts, key=lambda value: (-counts[value], value))
    keep = [col for col, value in enumerate(grid[0]) if value == marker]
    return [[row[col] for col in keep] for row in grid[1:]], marker, keep


def main():
    started = time.monotonic()
    ticket = next(t for t in json.loads((WORK / "AUDIT_ASSIGNMENT.json").read_text())["tickets"]
                  if t["ticket_id"] == "ticket-0f489af6ded7a651")
    source = WORK / ticket["source"]["path"]
    assert sha(source.read_bytes()) == ticket["generator_sha256"] == ticket["audited_generator_sha256"]
    index_path = WORK / ticket["audit_index"]["path"]
    manifest_path = WORK / ticket["assets_manifest"]["path"]
    assert sha(index_path.read_bytes()) == ticket["audit_index"]["sha256"]
    assert sha(manifest_path.read_bytes()) == ticket["assets_manifest"]["sha256"]
    record = next(a for a in json.loads(index_path.read_text())["audits"]
                  if a["return_id"] == ticket["audit_return_id"])
    assert sha(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()) == ticket["audit_record_sha256"]
    manifest = json.loads(manifest_path.read_text())
    selected_names = {"2636c90a673a-counterexample-input.json", "2636c90a673a-counterexample-racket.json",
                      "2636c90a673a-probe.json", "probe_2636c90a673a.py"}
    files, identity = {}, []
    for entry in manifest["files"]:
        name = Path(entry["path"]).name
        if name in selected_names:
            path = REPO / entry["path"]
            data = path.read_bytes()
            assert len(data) == entry["bytes"] and sha(data) == entry["sha256"]
            files[name] = path
            identity.append({"path": entry["path"], "sha256": entry["sha256"], "bytes": len(data)})
    assert set(files) == selected_names
    prior = json.loads(files["2636c90a673a-probe.json"].read_text())
    case = prior["counterexample"]
    old_racket = json.loads(files["2636c90a673a-counterexample-racket.json"].read_text())
    input_grid = json.loads(files["2636c90a673a-counterexample-input.json"].read_text())["input"]
    spec = importlib.util.spec_from_file_location("audit_replay_peer", source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    actual_input = generator.generate(case["seed"], case["sample_index"],
                                      difficulty=case["difficulty"], **case["overrides"])
    assert actual_input == input_grid == case["input"]
    validation = generator.self_check(actual_input, difficulty=case["difficulty"],
                                      meta={"overrides": case["overrides"]})
    assert validation == case["self_check"] == []
    assert generator.observe_overrides(actual_input)["n_keep"] == 3
    rules = set()
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == ticket["rule_task_id"]:
            rules.add(row["program_solution"])
    assert len(rules) == 1
    rule = rules.pop()
    wrapped = wrap_rule(rule)
    executed_rule_hash = sha(" ".join(rule.split()).encode())[:12]
    assert executed_rule_hash == ticket["rule_hash"] == old_racket["executed_rule_hash"]
    with RacketBridge(timeout=20.0) as bridge:
        bridge.eval_text(f"(define replay_rule {wrapped})")
        bridge.define_grid("replay_input", actual_input)
        output = bridge.eval_text("(replay_rule replay_input)")
        racket_binary = bridge.racket_binary
    rival, chosen_color, chosen_columns = frequency_rival(actual_input)
    expected = [[row[col] for col in (1, 2, 7)] for row in actual_input[1:]]
    assert output == expected == old_racket["results"][0]["output"] == case["truth"]
    assert rival == case["schedule_frequency_rival"] and rival != output
    assert chosen_color == 3 and chosen_columns == [0, 3, 5, 6]
    assert [len(output), len(output[0])] == [5, 3]
    assert [len(rival), len(rival[0])] == [5, 4]
    assert Counter(actual_input[0]) == {1: 3, 2: 1, 3: 4}
    assert sha(source.read_bytes()) == ticket["generator_sha256"]
    elapsed = time.monotonic() - started
    assert elapsed <= 120
    result = {"schema": "bounded-existing-audit-replay-v1", "ticket_id": ticket["ticket_id"],
              "type": ticket["type"], "task_id": ticket["task_id"],
              "audit_return_id": ticket["audit_return_id"], "assignment_seed": ticket["seed"],
              "seed_use": "The assignment seed selects the ticket; replay parameters are the pinned existing witness.",
              "generator_sha256": ticket["generator_sha256"],
              "audit_record_sha256": ticket["audit_record_sha256"],
              "audit_index_sha256": ticket["audit_index"]["sha256"],
              "assets_manifest_sha256": ticket["assets_manifest"]["sha256"],
              "verified_selected_assets": identity,
              "normalized_rule_hash": executed_rule_hash,
              "raw_program_solution_sha256": sha(rule.encode()), "wrapped_callable_sha256": sha(wrapped.encode()),
              "racket_binary": racket_binary, "racket_wrapper_sha256": sha(Path(racket_binary).read_bytes()),
              "script_sha256": sha(Path(__file__).read_bytes()),
              "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
              "probe_elapsed_seconds": elapsed, "targeted_probes": 1, "racket_applications": 1,
              "seed": case["seed"], "sample_index": case["sample_index"], "difficulty": case["difficulty"],
              "overrides": case["overrides"], "input": actual_input, "self_check": validation,
              "header_counts": dict(Counter(actual_input[0])), "output": output, "rival_output": rival,
              "input_sha256": grid_hash(actual_input), "output_sha256": grid_hash(output),
              "rival_output_sha256": grid_hash(rival), "authority_output_shape": [5, 3],
              "rival_output_shape": [5, 4], "bounded_witness_reproduced": True,
              "retained_input_reproduced": True, "retained_racket_output_reproduced": True,
              "default_draw_census": {"rerun": False, "retained_reported_draws": prior["default_draws"],
                                      "retained_reported_matches": prior["schedule_frequency_matches"]},
              "scope": "Only the pinned separating override witness was replayed; no peer battery or broad census.",
              "audit_disposition_changed": False, "peer_source_changed": False}
    (HERE / "replay.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"bounded_witness_reproduced": True, "source_sha256": result["generator_sha256"],
                      "rule_hash": executed_rule_hash, "self_check": validation,
                      "header_counts": result["header_counts"], "authority_shape": [5, 3],
                      "rival_shape": [5, 4], "racket_applications": 1,
                      "probe_seconds": elapsed, "default_census_rerun": False}))


if __name__ == "__main__":
    main()
