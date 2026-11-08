"""One four-pair Racket-backed probe of the teaching hook's query labels."""
import argparse
import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = find_root(Path(__file__))
    gen, source_path, source_hash = load_selected_generator("067449d7a3b3", root=root)
    programs = {
        row["program_solution"]
        for line in canonical_path(root).read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == gen.TASK_ID
        and row.get("program_solution")
    }
    program, = programs
    assert hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12] == gen.RULE_HASH
    pairs = []
    with RacketBridge(timeout=15.0) as bridge:
        for index in range(4):
            grid = gen.generate(91, index)
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            output = bridge.eval_text(f"({wrap_rule(program)} {literal})")
            assert output == gen._mirror(grid), index
            pairs.append({"input": grid, "output": output})
        runtime = bridge.runtime_identity

    rotations = []
    for index, query in enumerate(pairs):
        demos = [pair for offset, pair in enumerate(pairs) if offset != index]
        assert gen.lesson_identifiable(demos, query) == []
        assert gen.lesson_identifiable(demos, {"input": query["input"]}) == []
        corrupt = [row[:] for row in query["output"]]
        corrupt[0][0] = (corrupt[0][0] + 1) % 10
        errors = gen.lesson_identifiable(demos, {**query, "output": corrupt})
        assert errors == ["query output disagrees with the intended rule"], errors
        assert gen.lesson_identifiable(demos, {**query, "output": None}) == errors
        rotations.append({"query_index": index, "correct_label": "accepted", "input_only": "accepted", "one_cell_corruption": errors, "null_label": errors})

    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == source_hash
    report = {
        "schema": "067449d7a3b3-query-label-probe-v1",
        "status": "pass", "generator_sha256": source_hash,
        "canonical_rule_hash": gen.RULE_HASH,
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "draw": {"seed": 91, "sample_indices": [0, 1, 2, 3], "difficulty": None},
        "racket_executions": 4, "runtime_identity": runtime,
        "rotations": rotations,
        "limits": ["One four-pair label-validation probe; no full battery or census", "Existing unresolved connectivity-teaching audit remains open", "Input-only hook queries remain supported"],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "racket_executions": 4, "rotations": len(rotations)}))


if __name__ == "__main__":
    main()
