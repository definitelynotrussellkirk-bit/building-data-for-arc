"""Proposed task-local zero-count rule parameter; never a production rule API."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import shlex
import sys
import types

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator, normalize_grid

ROOT = find_root(__file__)
TASK = "520fe6e64fb6"
SETTINGS = (1, 2, 3)
DEFAULT = 1
ROW_TRIGGER = "(for/or ((cc (range 0 w))) (zero? (at g r cc)))"
COL_TRIGGER = "(for/or ((r (range 0 h))) (zero? (at g r cc)))"
LIMITATIONS = [
    "Proposed task-local prototype; no production parametric API, approval, or training admission.",
    "Finite evidence for the retained seeds and three declared threshold rivals; not universal rule identifiability.",
    "Teaching inputs require informative zero-count lines 0,1,2,3; this is narrower than the canonical input domain.",
    "Query rotations hold out each labeled pair; they do not assert spatial rotation equivariance of the canonical branch rule.",
    "The retained negative control is intentionally ambiguous and is not an accepted teaching episode.",
]


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def canonical_program():
    sources = set()
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK:
                    sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError("expected one exact canonical Racket authority for selected task")
    return sources.pop()


def program(min_zeros=DEFAULT):
    if type(min_zeros) is not int or min_zeros not in SETTINGS:
        raise ValueError(f"unsupported min_zeros: {min_zeros!r}; expected 1, 2, or 3")
    source = canonical_program()
    if source.count(ROW_TRIGGER) != 1 or source.count(COL_TRIGGER) != 1:
        raise ValueError("canonical zero-trigger sites changed; explicit review required")
    if min_zeros == DEFAULT:
        return source
    row_count = f"(>= (for/sum ((cc (range 0 w))) (if (zero? (at g r cc)) 1 0)) {min_zeros})"
    col_count = f"(>= (for/sum ((r (range 0 h))) (if (zero? (at g r cc)) 1 0)) {min_zeros})"
    return source.replace(ROW_TRIGGER, row_count).replace(COL_TRIGGER, col_count)


def execute(bridge, source, grid):
    """Run the existing normalizer and protected Racket bridge for every label."""
    if "scripts" not in sys.modules and (ROOT / "shared/tools").is_dir():
        scripts = types.ModuleType("scripts")
        scripts.__path__ = [str(ROOT / "shared/tools")]
        sys.modules["scripts"] = scripts
    from puzzle_generators.rule_wrap import wrap_rule
    grid = normalize_grid(grid)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    output = normalize_grid(bridge.eval_text(f"({wrap_rule(source)} {literal})"))
    if (len(output), len(output[0])) != (len(grid), len(grid[0])):
        raise ValueError("reference program changed the grid dimensions")
    return output


def choose_min_zeros(seed):
    """Select a hidden rule once, independently of scene draws."""
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    return random.Random(f"{TASK}:min-zeros-v1:{seed}").choice(SETTINGS)


def make_input(seed, sample_index):
    """Construct a scene with four informative zero-count lines, never labels."""
    rng = random.Random(f"{TASK}:threshold-scene-v1:{seed}:{sample_index}")
    top, height_a, height_b = rng.randint(1, 3), rng.randint(2, 3), rng.randint(2, 3)
    gap, left = rng.randint(4, 6), rng.randint(2, 4)
    width, span9, span7 = rng.randint(11, 15), rng.randint(3, 4), rng.randint(3, 5)
    lower = top + height_a + gap
    grid = [[6] * width for _ in range(lower + height_b + rng.randint(1, 3))]
    nine_first = sample_index % 4 < 2
    for color, row0, height in ((9 if nine_first else 7, top, height_a),
                                (7 if nine_first else 9, lower, height_b)):
        span = span9 if color == 9 else span7
        mode = (sample_index + color) % 3
        for r in range(row0, row0 + height):
            for c in range(left, left + span):
                corner = r in (row0, row0 + height - 1) and c in (left, left + span - 1)
                if mode == 1 and not corner:
                    continue
                if mode == 2 and r == row0 + 1 and c == left + 1 and height > 2:
                    continue
                grid[r][c] = color
    counts = [0, 1, 2, 3] + [rng.randrange(4) for _ in range(gap - 4)]
    rng.shuffle(counts)
    outside = [c for c in range(width) if not left <= c < left + span9]
    for row, count in zip(range(top + height_a, lower), counts):
        zero_columns = rng.sample(outside, count)
        if count == 3:
            zero_columns[-1] = left + span9 // 2
        for col in zero_columns:
            grid[row][col] = 0
        if count == 2:
            grid[row][left + span9 // 2] = rng.choice((1, 3, 4, 5, 8))
    grid[0][-1] = 0  # outside the between interval: preserved without triggering
    if sample_index % 2:
        grid = [list(row) for row in zip(*grid)]
        if sample_index % 4 == 3:
            # Shift only the 7 marker's rows: distinct minimum columns must
            # still select the horizontal branch even when rows do not align.
            sevens = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 7]
            for r, c in sevens:
                grid[r][c] = 6
            for r, c in sevens:
                grid[r + 1][c] = 7
    return grid


def outputs_for(bridge, grid, programs=None):
    programs = programs or {value: program(value) for value in SETTINGS}
    return {str(value): execute(bridge, programs[value], grid) for value in SETTINGS}


def identifiability(pairs, min_zeros):
    """Score executed threshold rivals under every leave-one-out query split."""
    if type(min_zeros) is not int or min_zeros not in SETTINGS:
        raise ValueError("min_zeros must be 1, 2, or 3")
    if len(pairs) < 2:
        raise ValueError("identifiability requires demonstrations and a query")
    rotations = []
    for query_index, query in enumerate(pairs):
        demos = [i for i in range(len(pairs)) if i != query_index]
        rivals = []
        for rival in SETTINGS:
            if rival == min_zeros:
                continue
            mismatches = [i for i in demos if pairs[i]["outputs"][str(rival)] != pairs[i]["outputs"][str(min_zeros)]]
            differs = query["outputs"][str(rival)] != query["outputs"][str(min_zeros)]
            status = "eliminated" if mismatches else "ambiguous" if differs else "survived_all"
            rivals.append({"min_zeros": rival, "demo_mismatches": mismatches,
                           "query_differs": differs, "status": status})
        rotations.append({"query_index": query_index, "demonstration_indices": demos,
                          "rivals": rivals})
    ambiguous = [row["query_index"] for row in rotations
                 if any(rival["status"] == "ambiguous" for rival in row["rivals"])]
    return {"production_query_index": len(pairs) - 1,
            "production_status": "ambiguous" if len(pairs) - 1 in ambiguous else "no_ambiguity_found",
            "rotation_status": "ambiguous" if ambiguous else "no_ambiguity_found",
            "ambiguous_query_indices": ambiguous, "rotations": rotations}


def build_episode(seed, bridge, min_zeros=None):
    chosen = choose_min_zeros(seed) if min_zeros is None else min_zeros
    programs = {value: program(value) for value in SETTINGS}
    program(chosen)  # strict validation before any scene is generated
    gen, _, _ = load_selected_generator(TASK, root=ROOT)
    pairs = []
    for index in range(4):
        grid = make_input(seed, index)
        errors = gen.self_check(grid)
        if errors:
            raise ValueError(f"prototype scene {index} failed selected self_check: {errors}")
        outputs = outputs_for(bridge, grid, programs)
        if len({encoded(output) for output in outputs.values()}) != len(SETTINGS):
            raise ValueError(f"prototype scene {index} does not distinguish all threshold rivals")
        pairs.append({"sample_index": index, "input": grid, "outputs": outputs})
    if len({encoded(pair["input"]) for pair in pairs}) != 4:
        raise ValueError("prototype episode contains repeated inputs")
    checks = identifiability(pairs, chosen)
    if checks["rotation_status"] != "no_ambiguity_found":
        raise ValueError("prototype episode has a measured parameter ambiguity")
    public = {"train": [{"input": pair["input"], "output": pair["outputs"][str(chosen)]}
                         for pair in pairs[:3]],
              "test": [{"input": pairs[3]["input"]}]}
    private = {"schema": "arc-task-local-threshold-prototype-v1", "status": "proposed prototype",
               "task_id": TASK, "seed": seed, "parameters": {"min_zeros": chosen},
               "reference_program": programs[chosen], "program_sha256": digest(programs[chosen]),
               "query_outputs": [pairs[3]["outputs"][str(chosen)]], "pairs": pairs,
               "identifiability": checks, "public_sha256": digest(encoded(public))}
    return public, private


def negative_control(seed, bridge):
    """Retain an actual unidentifiable episode to verify ambiguity reporting."""
    query = make_input(seed, 0)  # vertical scene: row counts are the relevant counts
    demo = [[6 if value == 0 and row.count(0) in (1, 2) else value for value in row]
            for row in query]
    demo_outputs, query_outputs = outputs_for(bridge, demo), outputs_for(bridge, query)
    pairs = [{"input": demo, "outputs": demo_outputs} for _ in range(3)]
    pairs.append({"input": query, "outputs": query_outputs})
    checks = identifiability(pairs, 2)
    if checks["production_status"] != "ambiguous":
        raise AssertionError("negative control did not expose the intended ambiguity")
    return {"status": "expected measured ambiguity; not an accepted teaching episode",
            "parameters": {"min_zeros": 2}, "seed": seed, "pairs": pairs,
            "identifiability": checks}


def default_parity(seed, bridge):
    gen, _, _ = load_selected_generator(TASK, root=ROOT)
    canonical, default = canonical_program(), program()
    records = []
    for pair in canonical_pairs(TASK, root=ROOT):
        actual = execute(bridge, default, pair["input"])
        records.append({"kind": "canonical_expected_label", "variant": pair["variant"],
                        "split": pair["split"], "pair_index": pair["pair_index"],
                        "input": pair["input"], "output": actual,
                        "expected_sha256": digest(encoded(pair["output"])),
                        "passed": actual == pair["output"]})
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(seed, index, difficulty=band, scene_profile=profile)
            errors = gen.self_check(grid)
            if errors:
                raise ValueError(f"selected generator produced invalid parity input: {errors}")
            expected = execute(bridge, canonical, grid)
            actual = execute(bridge, default, grid)
            records.append({"kind": "selected_generator_default_parity", "difficulty": band,
                            "scene_profile": profile, "sample_index": index, "input": grid,
                            "output": actual, "expected_sha256": digest(encoded(expected)),
                            "passed": actual == expected})
    if not all(record["passed"] for record in records):
        raise AssertionError("default canonical parity failed")
    return {"exact_canonical_bytes": default == canonical,
            "checked": len(records), "passed": sum(record["passed"] for record in records),
            "canonical_label_occurrences": sum(row["kind"] == "canonical_expected_label" for row in records),
            "selected_generator_inputs": sum(row["kind"] == "selected_generator_default_parity" for row in records),
            "unique_inputs": len({encoded(record["input"]) for record in records}), "cases": records}


def source_hashes():
    gen, selected, _ = load_selected_generator(TASK, root=ROOT)
    runtime = ROOT / "shared/runtime" if (ROOT / "shared/runtime").is_dir() else ROOT
    tools = ROOT / "shared/tools" if (ROOT / "shared/tools").is_dir() else ROOT / "scripts"
    home = ROOT / "generators" / TASK
    paths = [Path(__file__), Path(__file__).with_name("README.md"), selected,
             home / "tests/test_parametric_520fe6e64fb6.py", runtime / "reviewer_support.py",
             runtime / "arc_repl/racket_bridge.py", runtime / "arc_repl/racket_prelude/arc-prelude.rkt",
             runtime / "puzzle_generators/rule_wrap.py", tools / "comment_solutions.py"]
    return {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in paths}


def write_json(path, value):
    path.write_text(encoded(value) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--min-zeros", choices=("1", "2", "3", "auto", "all"), default="all")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=False)
    for directory in ("public", "private", "programs"):
        (args.out / directory).mkdir()
    receipt = {"schema": "arc-task-local-threshold-evidence-v1", "task_id": TASK,
               "status": "running", "seed": args.seed,
               "cwd": str(Path.cwd()), "command": shlex.join([sys.executable, *sys.argv]),
               "parameters": {"min_zeros": {"allowed": list(SETTINGS), "default": DEFAULT}},
               "source_sha256": source_hashes(), "limitations": LIMITATIONS,
               "episodes": []}
    try:
        from arc_repl.racket_bridge import RacketBridge
        programs = {setting: program(setting) for setting in SETTINGS}
        receipt["program_sha256"] = {str(setting): digest(source) for setting, source in programs.items()}
        for setting, source in programs.items():
            (args.out / "programs" / f"min-zeros-{setting}.rkt").write_text(source, encoding="utf-8")
        settings = SETTINGS if args.min_zeros == "all" else (choose_min_zeros(args.seed),) if args.min_zeros == "auto" else (int(args.min_zeros),)
        with RacketBridge() as bridge:
            receipt["runtime"] = bridge.runtime_identity
            parity = default_parity(args.seed, bridge)
            write_json(args.out / "private/default-parity.json", parity)
            receipt["default_parity"] = {key: value for key, value in parity.items() if key != "cases"}
            for setting in settings:
                public, private = build_episode(args.seed, bridge, setting)
                fingerprint = digest(encoded({"seed": args.seed, "challenge": public}))[:20]
                filename = f"episode-{fingerprint}.json"
                write_json(args.out / "public" / filename, public)
                write_json(args.out / "private" / filename, private)
                receipt["episodes"].append({"public": f"public/{filename}", "private": f"private/{filename}",
                                            "parameters": private["parameters"], "pairs": 4,
                                            "production_status": private["identifiability"]["production_status"],
                                            "rotation_status": private["identifiability"]["rotation_status"],
                                            "query_rotations": len(private["identifiability"]["rotations"]),
                                            "rival_checks": 8})
            control = negative_control(args.seed, bridge)
            write_json(args.out / "private/negative-control.json", control)
            receipt["negative_control"] = {"status": "expected measured ambiguity",
                                           "production_status": control["identifiability"]["production_status"],
                                           "ambiguous_rivals": 2}
        if source_hashes() != receipt["source_sha256"]:
            raise RuntimeError("source files changed during evidence generation; rerun against stable bytes")
        receipt["status"] = "passed prototype evidence"
    except Exception as exc:
        receipt["status"] = "failed prototype evidence"
        receipt["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        receipt["artifact_sha256"] = {str(path.relative_to(args.out)): digest(path.read_bytes())
                                      for path in sorted(args.out.rglob("*")) if path.is_file() and path.name != "receipt.json"}
        write_json(args.out / "receipt.json", receipt)
    print(encoded({"status": receipt["status"], "episodes": len(receipt["episodes"]),
                   "default_parity": receipt["default_parity"], "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
