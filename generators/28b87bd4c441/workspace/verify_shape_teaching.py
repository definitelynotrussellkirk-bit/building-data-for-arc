"""Bounded, source-bound verification of the repaired shape-teaching curriculum.

Run through the packet's review.py run wrapper, or in a prepared checkout:

    python generators/28b87bd4c441/workspace/verify_shape_teaching.py \
        --out var/checks/28b87bd4c441-shape-teaching --seed 17

The output directory must be new. Only public/<content-id>.json is a challenge
for a learner; private/ contains reference answers and authoring evidence.
This calls the public Catalog.apply API once, for exactly 55 inputs (maximum
64). It is a bounded repair check, not an all-seed or arbitrary-holdout proof.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

TASK = "28b87bd4c441"
EXPECTED_RULE_HASH = "0af5c7008ee7"
EXPECTED_CANONICAL_PROGRAM_SHA256 = "d488617f0f22d0115b860791a46ebdb0b32dd15c52cbbd12f0c2612c95addb7c"
DEMO_COUNT = 10
QUERY_COUNT = 4
QUERY_ATTEMPT_CAP = 32
APPLY_INPUT_CAP = 64
U5 = ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def write_json(path, value):
    path.write_bytes(json_bytes(value))


def selected_api():
    """Load public APIs from this file's own tree, independently of cwd."""
    for candidate in Path(__file__).resolve().parents:
        helper_dir = candidate / "shared/runtime"
        if (helper_dir / "reviewer_support.py").is_file():
            require((candidate / "src/arcpuzzles/__init__.py").is_file(),
                    "The selected checkout lacks its public arcpuzzles API")
            sys.path[:0] = [str(candidate / "src"), str(helper_dir)]
            break
    else:
        raise FileNotFoundError("No local ARCpuzzles checkout above this tool")
    from reviewer_support import (canonical_pairs, find_root,
                                  load_selected_generator,
                                  public_challenge_bytes, public_challenge_id)
    import arcpuzzles
    root = find_root(__file__)
    require(root == candidate, "Public helper selected a different source tree")
    require(Path(arcpuzzles.__file__).resolve().is_relative_to(root),
            "The public API was imported from another source tree")
    return (root, arcpuzzles.Catalog, canonical_pairs, load_selected_generator,
            public_challenge_bytes, public_challenge_id)


def visible_template(pair):
    """Infer a dimension/direction template from visible grids, not profiles."""
    grid, output = pair["input"], pair["output"]
    gray = [(r, c) for r, row in enumerate(grid)
            for c, color in enumerate(row) if color == 5]
    markers = [(r, c) for r, row in enumerate(grid)
               for c, color in enumerate(row) if color == 2]
    require(gray and len(markers) == 1, "Template witness needs one red marker and gray cells")
    mr, mc = markers[0]
    top, left = min(r for r, _ in gray), min(c for _, c in gray)
    sign = lambda value: (value > 0) - (value < 0)
    key = (len(grid), len(grid[0]), sign(mr - top), sign(mc - left))
    offsets = tuple((r - mr, c - mc) for r, row in enumerate(output)
                    for c, color in enumerate(row) if color == 5)
    return key, offsets


def template_conflicts(demos):
    """Retain concrete contradictions for templates ignoring the gray shape."""
    first, witnesses = {}, []
    for index, pair in enumerate(demos):
        key, offsets = visible_template(pair)
        if key not in first:
            first[key] = (index, offsets)
            continue
        first_index, first_offsets = first[key]
        if offsets != first_offsets:
            witnesses.append({
                "demo_indices": [first_index, index],
                "dimensions": list(key[:2]), "direction_signs": list(key[2:]),
                "output_offsets_from_red": [first_offsets, offsets],
                "offsets_only_in_first": sorted(set(first_offsets) - set(offsets)),
                "offsets_only_in_second": sorted(set(offsets) - set(first_offsets)),
            })
    require(any(w["dimensions"] == [12, 13] and w["direction_signs"] == [-1, 1]
                for w in witnesses),
            "No visible 12x13 up-right shape-template contradiction was found")
    return witnesses


def boundary_grid(source, marker):
    """Construct U5 independently of the generator's placement/shape helpers."""
    grid = [[0] * 13 for _ in range(12)]
    for dr, dc in U5:
        grid[source[0] + dr][source[1] + dc] = 5
    require(grid[marker[0]][marker[1]] == 0, "Boundary marker overlaps the source")
    grid[marker[0]][marker[1]] = 2
    return grid


def verify(out, seed):
    (root, Catalog, canonical_pairs, load_selected_generator,
     public_challenge_bytes, public_challenge_id) = selected_api()
    gen, source_path, source_hash = load_selected_generator(TASK, root=root)
    source_bytes = source_path.read_bytes()
    require(digest(source_bytes) == source_hash, "Generator changed while loading")
    require(gen.RULE_HASH == EXPECTED_RULE_HASH, "Generator rule identity changed")
    require(gen.EXAMPLES_NEEDED == DEMO_COUNT and len(gen.PROFILE_NAMES) == DEMO_COUNT,
            "Expected the repaired ten-profile curriculum")
    require({"canonical_up_right_u5", "canonical_up_left_u5"} <= set(gen.PROFILE_NAMES),
            "The two required U5 profiles are missing")

    catalog = Catalog(root)
    authority = catalog.get(TASK)
    require(authority["generator_sha256"] == source_hash, "Catalog selected different source bytes")
    require(authority["rule_hash"] == EXPECTED_RULE_HASH, "Canonical normalized rule identity changed")
    variants = authority["variants"]
    require(len(variants) == 1, "Expected one canonical variant for the selected task")
    program = variants[0]["program_solution"]
    program_hash = digest(program.encode())
    require(program_hash == EXPECTED_CANONICAL_PROGRAM_SHA256,
            "The exact canonical program changed; review the authority before rerunning")
    canonical = canonical_pairs(TASK, root=root)
    require(len(canonical) == 4 and [p["split"] for p in canonical] == ["train"] * 3 + ["test"],
            "Expected the original three train labels and one test label")

    private = out / "private"
    private.mkdir()
    (private / "generator.py").write_bytes(source_bytes)
    (private / "canonical_program.rkt").write_text(program, encoding="utf-8")
    inputs, records = [], []

    def add(grid, kind, **metadata):
        errors = gen.self_check(grid, difficulty=metadata.get("difficulty"))
        require(errors == [], f"{kind} input failed generator validation: {errors}")
        profile = gen.observe_overrides(grid)["scene_profile"]
        index = len(inputs)
        inputs.append(grid)
        records.append({"index": index, "kind": kind, "profile": profile, **metadata})
        return index

    for pair in canonical:
        require(gen.strict_canonical_like(pair["input"]) == [], "Canonical input lost strict support")
        add(pair["input"], "canonical", variant=pair["variant"],
            split=pair["split"], pair_index=pair["pair_index"])
    require(records[3]["profile"] == "canonical_up_left_u5",
            "The original canonical test is outside the new sampled profile")

    def lesson(name, difficulty, n_queries):
        demo_indices, query_indices, skipped = [], [], []
        seen = set()
        for sample_index in range(DEMO_COUNT):
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            key = json_bytes(grid)
            require(key not in seen, f"{name} has duplicate demonstration inputs")
            seen.add(key)
            demo_indices.append(add(grid, name + "_demo", seed=seed,
                                    difficulty=difficulty, sample_index=sample_index))
        profiles = {records[i]["profile"] for i in demo_indices}
        require(profiles == set(gen.PROFILE_NAMES), f"{name} omits a scheduled profile")
        for sample_index in range(DEMO_COUNT, DEMO_COUNT + QUERY_ATTEMPT_CAP):
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            key = json_bytes(grid)
            if key in seen:
                skipped.append({"sample_index": sample_index, "reason": "duplicate_input",
                                "input_sha256": digest(key)})
                continue
            seen.add(key)
            query_indices.append(add(grid, name + "_query", seed=seed,
                                     difficulty=difficulty, sample_index=sample_index))
            if len(query_indices) == n_queries:
                break
        require(len(query_indices) == n_queries,
                f"{name} could not find {n_queries} distinct queries within {QUERY_ATTEMPT_CAP} draws")
        return {"name": name, "seed": seed, "difficulty": difficulty,
                "demo_indices": demo_indices, "query_indices": query_indices,
                "skipped_draws": skipped, "query_attempt_cap": QUERY_ATTEMPT_CAP}

    public_lesson = lesson("public", "medium", QUERY_COUNT)
    ordered = [lesson("ordered_" + band, band, 1) for band in ("easy", "medium", "hard")]
    edges = [
        ("up_right_extreme", "canonical_up_right_u5", (10, 0), (0, 10)),
        ("up_right_one_row", "canonical_up_right_u5", (10, 0), (9, 3)),
        ("up_left_extreme", "canonical_up_left_u5", (10, 10), (0, 0)),
        ("up_left_one_row", "canonical_up_left_u5", (10, 10), (9, 7)),
    ]
    for name, expected_profile, source, marker in edges:
        index = add(boundary_grid(source, marker), "boundary", name=name,
                    source_bbox_origin=source, marker=marker)
        require(records[index]["profile"] == expected_profile, f"Boundary case {name} has wrong profile")
    require(len(inputs) == 55 and len(inputs) <= APPLY_INPUT_CAP, "Unexpected reference batch size")
    write_json(private / "input_index.json", {"cases": records, "public_lesson": public_lesson,
                                              "ordered_lessons": ordered})
    write_json(private / "reference_inputs.json", {"inputs": inputs})

    # This public API supports check_generator_domain (see docs/verification.md
    # and Catalog.apply's documented options); no private runner is imported.
    applied = catalog.apply(TASK, inputs, reference="canonical", timeout=300,
                            check_generator_domain=True)
    write_json(private / "racket_apply.json", applied)
    require(applied["generator_sha256"] == source_hash, "Reference run used another generator")
    require(applied["rule_hash_matches_catalog"] is True, "Executed rule does not match catalog authority")
    require(applied["catalog_rule_hash"] == applied["executed_rule_hash"] == EXPECTED_RULE_HASH,
            "Reference run used another rule identity")
    require(isinstance(applied["rule_text_sha256"], str) and len(applied["rule_text_sha256"]) == 64,
            "Reference receipt lacks the exact executed text hash")
    results = applied["results"]
    require(len(results) == len(inputs), "Reference runner returned an incomplete batch")
    pairs = []
    for index, (grid, result) in enumerate(zip(inputs, results, strict=True)):
        require(result["input"] == grid, f"Reference input order changed at {index}")
        require(result["error"] is None and result["valid_output"] is True,
                f"Racket failed input {index}: {result}")
        require(result["generator_domain"] == {"status": "valid", "errors": []},
                f"Staged generator rejected input {index}: {result['generator_domain']}")
        require(result["output"] == gen.rule_mirror(grid), f"Racket/mirror mismatch at input {index}")
        if index < len(canonical):
            require(result["output"] == canonical[index]["output"],
                    f"Racket/original canonical label mismatch at input {index}")
        pairs.append({"input": grid, "output": result["output"]})

    lesson_checks = []
    for item in [public_lesson, *ordered]:
        demos = [pairs[i] for i in item["demo_indices"]]
        conflicts = template_conflicts(demos)
        for query_index in [*item["query_indices"], 3]:
            query = {"input": inputs[query_index]}
            require(gen.lesson_identifiable(demos, query) == [],
                    f"{item['name']} hook rejected query {query_index}")
            query["output"] = "deliberately invalid private label; must be ignored"
            require(gen.lesson_identifiable(demos, query) == [],
                    f"{item['name']} hook consulted a private query label")
        lesson_checks.append({**item, "template_conflicts": conflicts,
                              "accepted_queries": [*item["query_indices"], 3],
                              "private_query_labels_ignored": True})

    public_demos = [pairs[i] for i in public_lesson["demo_indices"]]
    malformed_checks = []
    for color, replacement in ((5, 5.0), (0, False)):
        altered = copy.deepcopy(public_demos)
        output = altered[0]["output"]
        r, c = next((r, c) for r, row in enumerate(output)
                    for c, value in enumerate(row) if value == color)
        output[r][c] = replacement
        reasons = gen.lesson_identifiable(altered, {"input": inputs[public_lesson["query_indices"][0]]})
        require(bool(reasons), f"Lesson hook accepted nonliteral label cell {replacement!r}")
        malformed_checks.append({"replacement_type": type(replacement).__name__, "reasons": reasons})

    challenge = {"train": public_demos,
                 "test": [{"input": inputs[i]} for i in public_lesson["query_indices"]]}
    visible_bytes = public_challenge_bytes(challenge)
    public_id = public_challenge_id(challenge)
    require(digest(visible_bytes) == public_id, "Public challenge content identity mismatch")
    require(len({json_bytes(p["input"]) for p in challenge["test"]}) == QUERY_COUNT,
            "Public query inputs are not distinct")
    require(digest(source_path.read_bytes()) == source_hash, "Generator changed during verification")
    require(digest(catalog.get(TASK)["variants"][0]["program_solution"].encode()) == program_hash,
            "Canonical program changed during verification")

    (out / "public").mkdir()
    public_path = Path("public") / (public_id + ".json")
    (out / public_path).write_bytes(visible_bytes)
    write_json(private / "query_labels.json", {"public_challenge_id": public_id,
        "test": [{"query_index": qi, "reference_case_index": index,
                  "input_sha256": results[index]["input_sha256"],
                  "output": results[index]["output"], "output_sha256": results[index]["output_sha256"]}
                 for qi, index in enumerate(public_lesson["query_indices"])]})
    write_json(private / "verification.json", {"lessons": lesson_checks,
        "nonliteral_demo_labels_rejected": malformed_checks,
        "canonical_test_profile": records[3]["profile"],
        "boundary_indices": [r["index"] for r in records if r["kind"] == "boundary"]})
    return {
        "generator_version": gen.VERSION, "generator_sha256": source_hash,
        "generator_relative_path": source_path.relative_to(root).as_posix(),
        "canonical_program_sha256": program_hash,
        "catalog_rule_hash": applied["catalog_rule_hash"],
        "executed_rule_hash": applied["executed_rule_hash"],
        "executed_rule_text_sha256": applied["rule_text_sha256"],
        "rule_hash_matches_catalog": applied["rule_hash_matches_catalog"],
        "public_challenge_id": public_id, "public_challenge": public_path.as_posix(),
        "public_demonstrations": DEMO_COUNT, "public_distinct_queries": QUERY_COUNT,
        "racket_inputs": len(inputs), "racket_vs_mirror_matches": len(inputs),
        "original_canonical_label_matches": len(canonical), "boundary_cases": len(edges),
        "ordered_difficulty_lessons": len(ordered), "visible_template_conflicts": len(lesson_checks),
        "catalog_approved_at_execution": applied["catalog_approved"],
        "scope": "One seed; 55 reference inputs, including repeated medium lesson inputs. "
                 "Ordered ten-demo lessons only; no arbitrary query-rotation or all-seed proof. "
                 "Labels are from canonical Racket; Python mirror is a comparison only. "
                 "No approval, audit disposition, or training admission is changed.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True, help="new output directory; never overwritten")
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    out = args.out.expanduser().absolute()
    if out.exists() or out.is_symlink():
        parser.error(f"refusing existing output path: {out}")
    try:
        out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error(f"refusing existing output path: {out}")
    receipt = {"schema": "shape-teaching-verification-v1", "task_id": TASK,
               "status": "running", "seed": args.seed,
               "tool_sha256": digest(Path(__file__).read_bytes()),
               "started_utc": datetime.now(timezone.utc).isoformat()}
    write_json(out / "receipt.json", receipt)
    try:
        receipt.update(verify(out, args.seed))
        receipt["status"] = "passed"
    except BaseException as exc:
        receipt["status"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
        receipt["error"] = {"type": type(exc).__name__, "message": str(exc)}
        if isinstance(getattr(exc, "run", None), dict):
            (out / "private").mkdir(exist_ok=True)
            write_json(out / "private/runtime_failure.json", exc.run)
        raise
    finally:
        receipt["finished_utc"] = datetime.now(timezone.utc).isoformat()
        receipt["artifacts"] = [{"path": path.relative_to(out).as_posix(),
                                 "sha256": digest(path.read_bytes()), "bytes": path.stat().st_size}
                                for path in sorted(out.rglob("*"))
                                if path.is_file() and path != out / "receipt.json"]
        write_json(out / "receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
