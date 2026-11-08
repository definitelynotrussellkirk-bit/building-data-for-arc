"""Proposed, opt-in hole-ranking episodes; never a production/admission API.

Run through ``review.py run`` so the packet supplies its own Racket and imports.
Only public/ is model-visible. All settings, labels and certificates are private.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import shutil
import sys
import tempfile

from reviewer_support import (
    canonical_path, find_root, public_challenge_bytes, public_challenge_id,
)


TASK_ID = "581bb11ff645"
PARENT_TASK_ID = "42a15761"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
SETTINGS = tuple(
    {"count_mode": mode, "direction": direction}
    for mode in ("cells", "components")
    for direction in ("ascending", "descending")
)
RIVALS = tuple(f"{s['count_mode']}/{s['direction']}" for s in SETTINGS) + (
    "components8/ascending", "components8/descending", "identity", "reverse_groups",
)
SCHEMA = "581bb11ff645-parametric-episode-v1"


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _parameters(count_mode, direction):
    if type(count_mode) is not str or count_mode not in ("cells", "components"):
        raise ValueError("count_mode must be cells or components")
    if type(direction) is not str or direction not in ("ascending", "descending"):
        raise ValueError("direction must be ascending or descending")
    return {"count_mode": count_mode, "direction": direction}


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def canonical_program():
    """Return the exact unmodified canonical program, requiring one authority."""
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("expected one unambiguous canonical program")
    return programs.pop()


def materialize_program(*, count_mode="cells", direction="ascending"):
    _parameters(count_mode, direction)
    if count_mode == "cells" and direction == "ascending":
        return canonical_program()
    return (HERE.joinpath("rule_template.rkt").read_text(encoding="utf-8")
            .replace("__COUNT_MODE__", "'" + count_mode)
            .replace("__DIRECTION__", "'" + direction))


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or cell not in (0, 2) for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with literal zero/red (2) cells")
    return grid


def _bounds(grid):
    _grid(grid)
    groups, start = [], None
    for col in range(len(grid[0])):
        red = any(row[col] == 2 for row in grid)
        if red and start is None:
            start = col
        elif not red and start is not None:
            groups.append((start, col))
            start = None
    if start is not None:
        groups.append((start, len(grid[0])))
    if not 3 <= len(groups) <= 5:
        raise ValueError("require three through five red column groups")
    if (groups[0][0] != 0 or groups[-1][1] != len(grid[0])
            or any(right[0] - left[1] != 1 for left, right in zip(groups, groups[1:]))
            or len({end - begin for begin, end in groups}) != 1):
        raise ValueError("require equal-width groups, single separators, and no outer padding")
    return groups


def _component_count(cells, connectivity=4):
    remaining = set(cells)
    count = 0
    steps = ((1, 0), (-1, 0), (0, 1), (0, -1))
    if connectivity == 8:
        steps += ((1, 1), (1, -1), (-1, 1), (-1, -1))
    while remaining:
        count += 1
        frontier = [remaining.pop()]
        while frontier:
            row, col = frontier.pop()
            for dr, dc in steps:
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    frontier.append(neighbor)
    return count


def _scores(grid, groups, mode):
    scores = []
    for start, end in groups:
        zeros = {(r, c) for r, row in enumerate(grid)
                 for c in range(start, end) if row[c] == 0}
        scores.append(len(zeros) if mode == "cells" else
                      _component_count(zeros, 8 if mode == "components8" else 4))
    return scores


def _copy_groups(grid, groups, order):
    result = [[0] * len(grid[0]) for _ in grid]
    for (destination, _), index in zip(groups, order):
        start, end = groups[index]
        for r, row in enumerate(grid):
            result[r][destination:destination + end - start] = row[start:end]
    return result


def transform(grid, *, count_mode="cells", direction="ascending"):
    """Independent Python mirror. Zero components use 4-neighbor connectivity.

    Counts include zeros on group edges. Equal scores retain input order.
    """
    _parameters(count_mode, direction)
    groups = _bounds(grid)
    scores = _scores(grid, groups, count_mode)
    order = sorted(range(len(groups)), key=lambda i: scores[i],
                   reverse=direction == "descending")
    return _copy_groups(grid, groups, order)


def _predict(grid, rival):
    groups = _bounds(grid)
    if rival == "identity":
        return copy.deepcopy(grid)
    if rival == "reverse_groups":
        return _copy_groups(grid, groups, range(len(groups) - 1, -1, -1))
    mode, direction = rival.split("/")
    scores = _scores(grid, groups, mode)
    return _copy_groups(grid, groups, sorted(range(len(groups)), key=lambda i: scores[i],
                                            reverse=direction == "descending"))


def lesson_certificate(challenge):
    """Fit only demonstrations; compare surviving predictions on query INPUTS.

    No query answer, private setting, seed, program or supplied certificate is
    consulted. An empty version space is a failure, never a vacuous success.
    This finite declared-rival certificate does not prove universal uniqueness.
    """
    # The shared projector is the single boundary removing all private fields.
    visible = json.loads(public_challenge_bytes(challenge))
    for pair in visible["train"]:
        _bounds(pair["input"])
        _grid(pair["output"])
    for pair in visible["test"]:
        _bounds(pair["input"])
    witnesses, survivors = {}, []
    for rival in RIVALS:
        mismatch = next((i for i, pair in enumerate(visible["train"])
                         if _predict(pair["input"], rival) != pair["output"]), None)
        if mismatch is None:
            survivors.append(rival)
        else:
            witnesses[rival] = mismatch
    queries = []
    for i, pair in enumerate(visible["test"]):
        predictions = [{"rival": rival, "output": _predict(pair["input"], rival)}
                       for rival in survivors]
        identifiable = bool(predictions) and len({
            _json_bytes(p["output"]) for p in predictions}) == 1
        queries.append({"query_index": i, "identifiable": identifiable,
                        "survivor_predictions": predictions})
    return {"schema": "declared-rival-lesson-v1", "rivals": list(RIVALS),
            "survivors": survivors, "elimination_demo_indices": witnesses,
            "queries": queries,
            "identifiable": bool(survivors) and all(q["identifiable"] for q in queries),
            "scope": "eight declared rivals; demonstrations only; no training admission"}


def _input(rng, *, count, block_width, height):
    """Bounded rejection over genuine hole geometry, not public fixture replay."""
    cells = [(r, c) for r in range(1, height - 1)
             for c in range(1, block_width - 1)]
    for _ in range(512):
        blocks, pixel_scores, region_scores = [], set(), set()
        for _group in range(count):
            for _ in range(128):
                holes = set(rng.sample(cells, rng.randint(1, len(cells) - 1)))
                pixels, regions = len(holes), _component_count(holes)
                if pixels in pixel_scores or regions in region_scores:
                    continue
                block = [[2] * block_width for _ in range(height)]
                for r, c in holes:
                    block[r][c] = 0
                blocks.append(block)
                pixel_scores.add(pixels)
                region_scores.add(regions)
                break
            else:
                break
        if len(blocks) != count:
            continue
        grid = []
        for r in range(height):
            row = []
            for i, block in enumerate(blocks):
                if i:
                    row.append(0)
                row.extend(block[r])
            grid.append(row)
        outputs = [_json_bytes(transform(grid, **setting)) for setting in SETTINGS]
        if len(set(outputs)) == 4 and _json_bytes(grid) not in outputs:
            return grid
    raise RuntimeError("bounded input sampler exhausted; no partial episode returned")


def _racket_label(bridge, program, grid):
    from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper

    _bounds(grid)
    # Both retained authorities are full Racket lambdas with explicit h/w.
    # Do not pretend this restricted authoring helper accepts arbitrary DSL.
    body = strip_rule_wrapper(strip_line_comments(program))
    if not body.lstrip().startswith("(lambda"):
        raise ValueError("this prototype requires a self-contained Racket lambda")
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    output = bridge.eval_text(f"({body} {literal})")
    _grid(output)
    return output


def source_bindings():
    paths = {
        "prototype": Path(__file__).resolve(),
        "rule_template": HERE / "rule_template.rkt",
        "canonical_ledger": canonical_path(ROOT),
        "production_generator": ROOT / "generators" / TASK_ID / "generator.py",
    }
    return {key: {"path": str(path.relative_to(ROOT)), "sha256": _hash(path.read_bytes())}
            for key, path in paths.items()}


def generate_episode(seed, *, count_mode="cells", direction="ascending",
                     n_demo=3, n_query=4, bridge=None):
    params = _parameters(count_mode, direction)
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(n_demo, "n_demo", 1, 16)
    _integer(n_query, "n_query", 1, 16)
    if bridge is None:
        from arc_repl.racket_bridge import RacketBridge
        with RacketBridge(timeout=10) as owned:
            return generate_episode(seed, **params, n_demo=n_demo, n_query=n_query, bridge=owned)
    rng = random.Random(seed)
    selected = f"{count_mode}/{direction}"
    program = materialize_program(**params)
    seen, train, test = set(), [], []
    for i in range(n_demo + n_query):
        is_demo = i < n_demo
        # Broad queries include 21x29 and 30x29; equal slots cannot form width30.
        shapes = ((3, 5, 11), (4, 5, 13), (5, 5, 15)) if is_demo else (
            (3, 3, 9), (4, 4, 13), (5, 5, 21), (5, 5, 30))
        count, block_width, height = shapes[(i if is_demo else i - n_demo) % len(shapes)]
        for _ in range(256):
            grid = _input(rng, count=count, block_width=block_width, height=height)
            key = _json_bytes(grid)
            if key in seen:
                continue
            expected = transform(grid, **params)
            # First demo witnesses every declared incorrect hypothesis.
            if i == 0 and any(_predict(grid, rival) == expected
                              for rival in RIVALS if rival != selected):
                continue
            actual = _racket_label(bridge, program, grid)
            if actual != expected:
                raise ValueError("Racket/Python disagreement; episode not emitted")
            seen.add(key)
            (train if is_demo else test).append({"input": grid, "output": actual})
            break
        else:
            raise RuntimeError("bounded episode sampler exhausted; no partial episode returned")
    episode = {"schema": SCHEMA, "task_id": TASK_ID, "parent_task_id": PARENT_TASK_ID,
               "status": "proposed", "training_admitted": False, "seed": seed,
               "parameters": params, "program": program,
               "program_sha256": _hash(program.encode("utf-8")),
               "source_bindings": source_bindings(), "train": train, "test": test}
    certificate = lesson_certificate(episode)
    if certificate["survivors"] != [selected] or not certificate["identifiable"]:
        raise ValueError("demonstrations do not establish the requested query behavior")
    episode["certificate"] = certificate
    return episode


def write_batch(episodes, out):
    """Serialize a batch with public-only content identities; reject duplicates.

    This writer is not a label validator. Use verify_batch to replay the exact
    files, check private provenance, and validate their Racket labels.
    """
    episodes = list(episodes)
    if not episodes:
        raise ValueError("cannot export an empty batch")
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    payloads = {}
    for episode in episodes:
        raw = public_challenge_bytes(episode)
        public_id = public_challenge_id(episode)
        if public_id in payloads:
            raise ValueError("duplicate visible payload in batch")
        payloads[public_id] = (raw, _json_bytes(episode))
    index = {"schema": "public-challenge-batch-v1", "public_ids": sorted(payloads)}
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".hole-rank-stage-", dir=out.parent))
    try:
        (stage / "public").mkdir()
        (stage / "private").mkdir()
        for public_id in index["public_ids"]:
            public, private = payloads[public_id]
            (stage / "public" / (public_id + ".json")).write_bytes(public)
            (stage / "private" / (public_id + ".json")).write_bytes(private)
        (stage / "index.json").write_bytes(_json_bytes(index))
        if out.exists() or out.is_symlink():
            raise FileExistsError(out)
        stage.rename(out)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return index


def verify_batch(out, *, bridge=None):
    """Replay serialized files, including every parameter prediction per input.

    Verifies exact visible bytes/IDs, private source/program identity, distinct
    inputs, every selected label, and the demonstration-only certificate.
    """
    from arc_repl.racket_bridge import RacketBridge

    out = Path(out)
    if bridge is None:
        with RacketBridge(timeout=10) as owned:
            return verify_batch(out, bridge=owned)
    index = json.loads((out / "index.json").read_bytes())
    ids = index.get("public_ids")
    if (index.get("schema") != "public-challenge-batch-v1" or type(ids) is not list
            or not ids or any(type(i) is not str or len(i) != 64
                              or any(c not in "0123456789abcdef" for c in i) for i in ids)
            or ids != sorted(set(ids))):
        raise ValueError("invalid or unsorted public ID index")
    expected_files = {"index.json"} | {
        f"{kind}/{public_id}.json" for kind in ("public", "private") for public_id in ids}
    actual_files = set()
    for path in out.rglob("*"):
        if path.is_symlink():
            raise ValueError("symlinks are not permitted in an export")
        if path.is_file():
            actual_files.add(path.relative_to(out).as_posix())
    if expected_files != actual_files:
        raise ValueError("export inventory does not match its index")
    pairs, queries, rows = 0, 0, []
    programs = [(setting, materialize_program(**setting)) for setting in SETTINGS]
    current_sources = source_bindings()
    for public_id in ids:
        raw = (out / "public" / (public_id + ".json")).read_bytes()
        private = json.loads((out / "private" / (public_id + ".json")).read_bytes())
        if raw != public_challenge_bytes(private) or _hash(raw) != public_id:
            raise ValueError("visible bytes or public identity mismatch")
        if (private.get("schema") != SCHEMA or private.get("task_id") != TASK_ID
                or private.get("parent_task_id") != PARENT_TASK_ID
                or private.get("status") != "proposed"
                or private.get("training_admitted") is not False
                or private.get("source_bindings") != current_sources):
            raise ValueError("private status or exact-source binding mismatch")
        params = private.get("parameters")
        if type(params) is not dict or set(params) != {"count_mode", "direction"}:
            raise ValueError("invalid private parameter fields")
        _parameters(**params)
        _integer(private.get("seed"), "seed", 0, 2**63 - 1)
        program = materialize_program(**params)
        if (private.get("program") != program
                or private.get("program_sha256") != _hash(program.encode("utf-8"))):
            raise ValueError("private program identity mismatch")
        all_pairs = private["train"] + private["test"]
        _integer(len(private["train"]), "n_demo", 1, 16)
        _integer(len(private["test"]), "n_query", 1, 16)
        for pair in all_pairs:
            # Python equality aliases False/0 and integer/equivalent float.
            # Stored private answers need the same exact-color contract as
            # public grids before any semantic comparison can be trusted.
            _grid(pair.get("output"))
        if len({_json_bytes(p["input"]) for p in all_pairs}) != len(all_pairs):
            raise ValueError("duplicate input across demonstrations and queries")
        certificate = lesson_certificate(private)
        selected = f"{params['count_mode']}/{params['direction']}"
        if (_json_bytes(private.get("certificate")) != _json_bytes(certificate)
                or not certificate["identifiable"]
                or certificate["survivors"] != [selected]):
            raise ValueError("invalid or ambiguous demonstration-only certificate")
        for pair in all_pairs:
            for setting, candidate in programs:
                label = _racket_label(bridge, candidate, pair["input"])
                if label != transform(pair["input"], **setting):
                    raise ValueError("Racket/Python rival prediction mismatch")
                if setting == params and label != pair.get("output"):
                    raise ValueError("stored label differs from the executed Racket rule")
        pairs += len(all_pairs)
        queries += len(private["test"])
        rows.append({"public_id": public_id, "parameters": params,
                     "program_sha256": private["program_sha256"],
                     "demo_count": len(private["train"]), "query_count": len(private["test"]),
                     "query_shapes": [[len(p["input"]), len(p["input"][0])] for p in private["test"]],
                     "survivors": certificate["survivors"]})
    return {"status": "passed", "episodes": len(ids), "labeled_pairs": pairs,
            "queries": queries, "racket_parameter_replays": pairs * len(SETTINGS),
            "source_bindings": current_sources, "rows": rows,
            "scope": "proposed variants; eight declared rivals, not all possible rules",
            "training_admitted": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate")
    generate.add_argument("--seed", type=int, default=42)
    generate.add_argument("--count-mode", choices=("cells", "components"), default="cells")
    generate.add_argument("--direction", choices=("ascending", "descending"), default="ascending")
    generate.add_argument("--all-settings", action="store_true")
    generate.add_argument("--n-demo", type=int, default=3)
    generate.add_argument("--n-query", type=int, default=4)
    generate.add_argument("--out", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("path", type=Path)
    verify.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    if args.command == "generate":
        from arc_repl.racket_bridge import RacketBridge
        selected = SETTINGS if args.all_settings else ({
            "count_mode": args.count_mode, "direction": args.direction},)
        with RacketBridge(timeout=10) as bridge:
            episodes = [generate_episode(args.seed, **setting, n_demo=args.n_demo,
                                         n_query=args.n_query, bridge=bridge) for setting in selected]
        result = write_batch(episodes, args.out)
        print(json.dumps({"status": "written", "episodes": len(result["public_ids"]),
                          "out": str(args.out), "label_status": "Racket checked at generation"}))
    else:
        result = verify_batch(args.path)
        if args.report:
            if args.report.exists():
                raise FileExistsError(args.report)
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_bytes(_json_bytes(result))
        print(json.dumps({k: v for k, v in result.items() if k not in {"rows", "source_bindings"}}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError) as error:
        print(f"parametric prototype: {error}", file=sys.stderr)
        raise SystemExit(2)
