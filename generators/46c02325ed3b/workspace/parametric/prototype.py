"""Spread-policy parametric prototype for 46c02325ed3b.

The canonical setting spreads water in both directions whenever the inward path
hits a cyan wall.  The alternate setting keeps only the geometric right-hand
branch relative to gravity.  Inputs are setting-neutral: every generated wall
layout exposes reachable holes on both sides, so demonstrations—not generation
metadata—identify the active policy.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import random
import shutil
import tempfile
from typing import Any

from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ID = "46c02325ed3b"
SCHEMA = "arcpuzzles-parametric-prototype-v1"
SPREAD_POLICIES = ("both", "right_hand_only")
HERE = Path(__file__).resolve().parent
_QUERY_SHAPES = ((10, 10), (14, 17), (18, 18), (30, 30))
_EDGES = ("top", "bottom", "left", "right")

CANONICAL_PROGRAM = """(rule! (lambda (g)
  (let* ((H (rows g)) (W (cols g))
         (srcs (find-color g 2))
         (s (first srcs)) (sr (first s)) (sc (second s)))
    (define water (make-hash))
    (define (inb? r c) (and (>= r 0) (< r H) (>= c 0) (< c W)))
    (define (wall? r c) (and (inb? r c) (= (cell-at g r c) 8)))
    (define (wet? r c) (hash-ref water (cons r c) #f))
    ;; gravity dir (dr dc) flows inward from source edge; perpendicular (pr pc) is spread axis
    (define dr (cond ((= sr 0) 1) ((= sr (- H 1)) -1) (else 0)))
    (define dc (cond ((= sc 0) 1) ((= sc (- W 1)) -1) (else 0)))
    (define pr (if (= dr 0) 1 0))
    (define pc (if (= dr 0) 0 1))
    (define (flow r c)
      (when (and (inb? r c) (not (wall? r c)) (not (wet? r c)))
        (hash-set! water (cons r c) #t)
        (let ((nr (+ r dr)) (nc (+ c dc)))
          (cond
            ((not (inb? nr nc)) (void))
            ((not (wall? nr nc)) (flow nr nc))
            (else (side r c pr pc) (side r c (- 0 pr) (- 0 pc)))))))
    (define (side r c ur uc)
      (let ((nr (+ r ur)) (nc (+ c uc)))
        (when (and (inb? nr nc) (not (wall? nr nc)) (not (wet? nr nc)))
          (hash-set! water (cons nr nc) #t)
          (let ((br (+ nr dr)) (bc (+ nc dc)))
            (cond
              ((not (inb? br bc)) (void))
              ((not (wall? br bc)) (flow br bc))
              (else (side nr nc ur uc)))))))
    (hash-set! water (cons sr sc) #t)
    (let ((nr (+ sr dr)) (nc (+ sc dc)))
      (cond
        ((not (inb? nr nc)) (void))
        ((not (wall? nr nc)) (flow nr nc))
        (else (side sr sc pr pc) (side sr sc (- 0 pr) (- 0 pc)))))
    (grid-from-fn H W (lambda (r c)
      (if (hash-ref water (cons r c) #f) 2 (cell-at g r c)))))))"""


def _right_only_program() -> str:
    replacements = (
        (
            "    (define pr (if (= dr 0) 1 0))\n"
            "    (define pc (if (= dr 0) 0 1))",
            "    ;; geometric right-hand direction relative to gravity\n"
            "    (define rr dc)\n"
            "    (define rc (- 0 dr))",
        ),
        (
            "(else (side r c pr pc) (side r c (- 0 pr) (- 0 pc)))",
            "(else (side r c rr rc))",
        ),
        (
            "(else (side sr sc pr pc) (side sr sc (- 0 pr) (- 0 pc)))",
            "(else (side sr sc rr rc))",
        ),
    )
    text = CANONICAL_PROGRAM
    for old, new in replacements:
        if text.count(old) != 1:
            raise RuntimeError(f"alternate-program replacement is not unique: {old!r}")
        text = text.replace(old, new)
    return text


RIGHT_ONLY_PROGRAM = _right_only_program()


def _integer(value: object, name: str, lo: int, hi: int) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in [{lo}, {hi}]")
    return value


def _policy(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"spread_policy"}:
        raise ValueError("settings must contain exactly spread_policy")
    policy = settings["spread_policy"]
    if type(policy) is not str or policy not in SPREAD_POLICIES:
        raise ValueError(f"spread_policy must be one of {SPREAD_POLICIES}")
    return policy


def program(settings: object) -> str:
    return CANONICAL_PROGRAM if _policy(settings) == "both" else RIGHT_ONLY_PROGRAM


def _grid_check(grid: object) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def _source(grid: list[list[int]]) -> tuple[int, int, int, int, str]:
    h, w = len(grid), len(grid[0])
    sources = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if len(sources) != 1:
        raise ValueError("expected exactly one red source")
    sr, sc = sources[0]
    memberships = [
        (name, dr, dc)
        for name, condition, dr, dc in (
            ("top", sr == 0, 1, 0),
            ("bottom", sr == h - 1, -1, 0),
            ("left", sc == 0, 0, 1),
            ("right", sc == w - 1, 0, -1),
        )
        if condition
    ]
    if len(memberships) != 1:
        raise ValueError("source must lie on exactly one non-corner edge")
    edge, dr, dc = memberships[0]
    return sr, sc, dr, dc, edge


def transform(grid: list[list[int]], *, spread_policy: str = "both") -> list[list[int]]:
    _grid_check(grid)
    if type(spread_policy) is not str or spread_policy not in SPREAD_POLICIES:
        raise ValueError(f"spread_policy must be one of {SPREAD_POLICIES}")
    sr, sc, dr, dc, _ = _source(grid)
    h, w = len(grid), len(grid[0])
    water: set[tuple[int, int]] = {(sr, sc)}
    canonical_side = (0, 1) if dr else (1, 0)
    right_side = (dc, -dr)

    def in_bounds(row: int, col: int) -> bool:
        return 0 <= row < h and 0 <= col < w

    def wall(row: int, col: int) -> bool:
        return in_bounds(row, col) and grid[row][col] == 8

    def side(row: int, col: int, step_row: int, step_col: int) -> None:
        next_row, next_col = row + step_row, col + step_col
        if (
            not in_bounds(next_row, next_col)
            or wall(next_row, next_col)
            or (next_row, next_col) in water
        ):
            return
        water.add((next_row, next_col))
        below_row, below_col = next_row + dr, next_col + dc
        if not in_bounds(below_row, below_col):
            return
        if not wall(below_row, below_col):
            flow(below_row, below_col)
        else:
            side(next_row, next_col, step_row, step_col)

    def spread(row: int, col: int) -> None:
        if spread_policy == "both":
            pr, pc = canonical_side
            side(row, col, pr, pc)
            side(row, col, -pr, -pc)
        else:
            side(row, col, *right_side)

    def flow(row: int, col: int) -> None:
        if not in_bounds(row, col) or wall(row, col) or (row, col) in water:
            return
        water.add((row, col))
        next_row, next_col = row + dr, col + dc
        if not in_bounds(next_row, next_col):
            return
        if wall(next_row, next_col):
            spread(row, col)
        else:
            flow(next_row, next_col)

    next_row, next_col = sr + dr, sc + dc
    if in_bounds(next_row, next_col):
        if wall(next_row, next_col):
            spread(sr, sc)
        else:
            flow(next_row, next_col)

    output = [row[:] for row in grid]
    for row, col in water:
        output[row][col] = 2
    return output


def _rng(seed: int, index: int, stream: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{index}|{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def _top_layout(seed: int, index: int, height: int, width: int, n_walls: int) -> list[list[int]]:
    rng = _rng(seed, index, "layout")
    max_offset = n_walls + 1
    source_col = rng.choice(list(range(max_offset + 1, width - max_offset - 1)))
    candidates = [
        combo
        for combo in itertools.combinations(range(2, height - 2), n_walls)
        if all(right - left >= 2 for left, right in zip(combo, combo[1:]))
    ]
    if not candidates:
        raise RuntimeError("shape cannot realize requested walls")
    wall_positions = list(rng.choice(candidates))
    offset_start = rng.choice((1, 2))
    grid = [[0 for _ in range(width)] for _ in range(height)]
    grid[0][source_col] = 2
    for wall_index, row in enumerate(wall_positions):
        offset = offset_start + wall_index
        holes = {source_col - offset, source_col + offset}
        for col in range(width):
            if col not in holes:
                grid[row][col] = 8
    return grid


def sample_input(seed: int, index: int) -> list[list[int]]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    index = _integer(index, "index", 0, 2**31 - 1)
    desired_h, desired_w = _QUERY_SHAPES[index % len(_QUERY_SHAPES)]
    edge = _EDGES[index % len(_EDGES)]
    n_walls = 2 + (index % 4)
    if edge in ("left", "right"):
        base_h, base_w = desired_w, desired_h
    else:
        base_h, base_w = desired_h, desired_w
    grid = _top_layout(seed, index, base_h, base_w, n_walls)
    if edge == "bottom":
        grid = _rotate_180(grid)
    elif edge == "left":
        grid = _rotate_ccw(grid)
    elif edge == "right":
        grid = _rotate_cw(grid)
    if (len(grid), len(grid[0])) != (desired_h, desired_w):
        raise RuntimeError("rotation changed the requested shape")
    if transform(grid, spread_policy="both") == transform(
        grid, spread_policy="right_hand_only"
    ):
        raise RuntimeError("sample does not distinguish spread policies")
    return grid


def _pair(grid: list[list[int]], spread_policy: str) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": transform(grid, spread_policy=spread_policy)}


def sample_episode(
    seed: int,
    *,
    spread_policy: str = "both",
    n_demo: int = 3,
    n_query: int = 4,
) -> dict[str, Any]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    if type(spread_policy) is not str or spread_policy not in SPREAD_POLICIES:
        raise ValueError(f"spread_policy must be one of {SPREAD_POLICIES}")
    n_demo = _integer(n_demo, "n_demo", 2, 6)
    n_query = _integer(n_query, "n_query", 1, 4)
    train = [_pair(sample_input(seed, index), spread_policy) for index in range(n_demo)]
    test = [
        _pair(sample_input(seed, 100 + index), spread_policy)
        for index in range(n_query)
    ]
    all_inputs = [pair["input"] for pair in train + test]
    keys = {json.dumps(grid, separators=(",", ":")) for grid in all_inputs}
    if len(keys) != len(all_inputs):
        raise RuntimeError("episode contains duplicate inputs")
    episode = {
        "train": train,
        "test": test,
        "program_solution": program({"spread_policy": spread_policy}),
        "parameters": {"spread_policy": spread_policy},
        "seed": seed,
    }
    certificate = lesson_certificate(episode)
    if certificate["survivors"] != [spread_policy]:
        raise RuntimeError(f"demonstrations do not identify spread policy: {certificate}")
    return episode


def lesson_certificate(episode: dict[str, Any]) -> dict[str, Any]:
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    survivors = []
    for policy in SPREAD_POLICIES:
        try:
            fits = all(
                transform(pair["input"], spread_policy=policy) == pair["output"]
                for pair in train
            )
        except (KeyError, TypeError, ValueError):
            fits = False
        if fits:
            survivors.append(policy)
    query_agreement = []
    for pair in test:
        predictions = {
            json.dumps(transform(pair["input"], spread_policy=policy), separators=(",", ":"))
            for policy in survivors
        }
        query_agreement.append(len(predictions) <= 1)
    return {
        "family": "spread_policy",
        "survivors": survivors,
        "identifiable": len(survivors) == 1,
        "query_agreement": query_agreement,
        "uses_query_outputs": False,
    }


def first_turn(episode: dict[str, Any]) -> dict[str, Any]:
    return json.loads(
        public_challenge_bytes({"train": episode["train"], "test": episode["test"][:1]})
    )


def generate(seed: int, settings: object, demos: int, queries: int) -> dict[str, Any]:
    policy = _policy(settings)
    episode = sample_episode(
        seed, spread_policy=policy, n_demo=demos, n_query=queries
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode()


def source_bindings() -> dict[str, str]:
    relative = ("prototype.py", "adapter.py", "promotion.json", "README.md")
    result = {name: _sha((HERE / name).read_bytes()) for name in relative}
    result["../../generator.py"] = _sha((HERE.parent.parent / "generator.py").read_bytes())
    return result


def racket_label(bridge: Any, racket_program: str, grid: list[list[int]]) -> list[list[int]]:
    from puzzle_generators.rule_wrap import wrap_rule

    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    result = bridge.eval_text(f"({wrap_rule(racket_program)} {literal})")
    _grid_check(result)
    return result


def _runtime_identity(bridge: Any) -> dict[str, Any]:
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise ValueError("runtime must be a protected Racket backend")
    return {
        key: value
        for key, value in identity.items()
        if key in ("schema", "backend", "protected") or key.endswith("_sha256")
    }


def generate_episode(
    seed: int,
    *,
    spread_policy: str = "both",
    n_demo: int = 3,
    n_query: int = 4,
    bridge: Any | None = None,
) -> dict[str, Any]:
    if bridge is None:
        from arc_repl.racket_bridge import RacketBridge

        with RacketBridge(timeout=15) as owned:
            return generate_episode(
                seed,
                spread_policy=spread_policy,
                n_demo=n_demo,
                n_query=n_query,
                bridge=owned,
            )
    episode = sample_episode(
        seed, spread_policy=spread_policy, n_demo=n_demo, n_query=n_query
    )
    for pair in episode["train"] + episode["test"]:
        for candidate in SPREAD_POLICIES:
            actual = racket_label(
                bridge, program({"spread_policy": candidate}), pair["input"]
            )
            expected = transform(pair["input"], spread_policy=candidate)
            if actual != expected:
                raise ValueError("Racket/Python spread prediction mismatch")
            if candidate == spread_policy:
                pair["output"] = actual
    racket_program = episode.pop("program_solution")
    episode.update(
        schema=SCHEMA,
        task_id=TASK_ID,
        status="proposed",
        training_admitted=False,
        parameters={"spread_policy": spread_policy},
        source_bindings=source_bindings(),
        program=racket_program,
        program_sha256=_sha(racket_program.encode()),
        racket=_runtime_identity(bridge),
        certificate=lesson_certificate(episode),
    )
    return episode


def write_batch(episodes: list[dict[str, Any]], out: str | Path) -> dict[str, Any]:
    episodes = list(episodes)
    if not episodes:
        raise ValueError("empty batch")
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    payloads: dict[str, tuple[bytes, bytes]] = {}
    for episode in episodes:
        public = public_challenge_bytes(episode)
        public_id = public_challenge_id(episode)
        if public_id in payloads:
            raise ValueError("duplicate public payload")
        payloads[public_id] = (public, _json_bytes(episode))
    index = {"schema": "public-challenge-batch-v1", "public_ids": sorted(payloads)}
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".46c-spread-stage-", dir=out.parent))
    try:
        (stage / "public").mkdir()
        (stage / "private").mkdir()
        for public_id in index["public_ids"]:
            public, private = payloads[public_id]
            (stage / "public" / f"{public_id}.json").write_bytes(public)
            (stage / "private" / f"{public_id}.json").write_bytes(private)
        (stage / "index.json").write_bytes(_json_bytes(index))
        if out.exists() or out.is_symlink():
            raise FileExistsError(out)
        stage.rename(out)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return index


def verify_batch(out: str | Path, *, bridge: Any | None = None) -> dict[str, Any]:
    if bridge is None:
        from arc_repl.racket_bridge import RacketBridge

        with RacketBridge(timeout=15) as owned:
            return verify_batch(out, bridge=owned)
    out = Path(out)
    if out.is_symlink():
        raise ValueError("export cannot be a symlink")
    index = json.loads((out / "index.json").read_bytes())
    ids = index.get("public_ids")
    if (
        set(index) != {"schema", "public_ids"}
        or index.get("schema") != "public-challenge-batch-v1"
        or type(ids) is not list
        or not ids
        or ids != sorted(set(ids))
        or any(
            type(value) is not str
            or len(value) != 64
            or any(char not in "0123456789abcdef" for char in value)
            for value in ids
        )
    ):
        raise ValueError("invalid public index")
    expected_files = {"index.json"} | {
        f"{kind}/{public_id}.json"
        for public_id in ids
        for kind in ("public", "private")
    }
    actual_files: set[str] = set()
    directories: set[str] = set()
    for path in out.rglob("*"):
        if path.is_symlink():
            raise ValueError("export contains a symlink")
        relative = path.relative_to(out).as_posix()
        if path.is_file():
            actual_files.add(relative)
        elif path.is_dir():
            directories.add(relative)
        else:
            raise ValueError("export contains a special file")
    if actual_files != expected_files or directories != {"public", "private"}:
        raise ValueError("export inventory differs from public index")

    current_runtime = _runtime_identity(bridge)
    labeled_pairs = 0
    queries = 0
    rows = []
    for public_id in ids:
        public = (out / "public" / f"{public_id}.json").read_bytes()
        episode = json.loads((out / "private" / f"{public_id}.json").read_bytes())
        if public != public_challenge_bytes(episode) or _sha(public) != public_id:
            raise ValueError("public bytes or visible identity mismatch")
        if (
            episode.get("schema") != SCHEMA
            or episode.get("task_id") != TASK_ID
            or episode.get("status") != "proposed"
            or episode.get("training_admitted") is not False
            or episode.get("source_bindings") != source_bindings()
        ):
            raise ValueError("private status or source binding mismatch")
        if episode.get("racket") != current_runtime:
            raise ValueError("stored runtime identity differs from current protected Racket runtime")
        params = episode.get("parameters")
        policy = _policy(params)
        _integer(episode.get("seed"), "seed", 0, 2**63 - 1)
        n_demo = _integer(len(episode.get("train", [])), "n_demo", 2, 6)
        n_query = _integer(len(episode.get("test", [])), "n_query", 1, 4)
        racket_program = program(params)
        if (
            episode.get("program") != racket_program
            or episode.get("program_sha256") != _sha(racket_program.encode())
        ):
            raise ValueError("private program identity mismatch")
        all_pairs = episode["train"] + episode["test"]
        if len({_json_bytes(pair["input"]) for pair in all_pairs}) != len(all_pairs):
            raise ValueError("duplicate input")
        for pair in all_pairs:
            _grid_check(pair.get("input"))
            _grid_check(pair.get("output"))
        certificate = lesson_certificate(episode)
        if (
            episode.get("certificate") != certificate
            or certificate["survivors"] != [policy]
            or not certificate["identifiable"]
        ):
            raise ValueError("invalid demonstration-only certificate")
        for pair in all_pairs:
            for candidate in SPREAD_POLICIES:
                actual = racket_label(
                    bridge, program({"spread_policy": candidate}), pair["input"]
                )
                if actual != transform(pair["input"], spread_policy=candidate):
                    raise ValueError("Racket/Python prediction mismatch")
                if candidate == policy and actual != pair["output"]:
                    raise ValueError("stored label disagrees with Racket")
        labeled_pairs += len(all_pairs)
        queries += n_query
        rows.append(
            {
                "public_id": public_id,
                "spread_policy": policy,
                "demos": n_demo,
                "queries": n_query,
                "query_shapes": [
                    [len(pair["input"]), len(pair["input"][0])]
                    for pair in episode["test"]
                ],
                "source_edges": [_source(pair["input"])[4] for pair in episode["test"]],
                "survivors": certificate["survivors"],
            }
        )
    return {
        "status": "passed",
        "episodes": len(ids),
        "labeled_pairs": labeled_pairs,
        "queries": queries,
        "racket_parameter_replays": len(SPREAD_POLICIES) * labeled_pairs,
        "rows": rows,
        "source_bindings": source_bindings(),
        "training_admitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--seed", type=int, default=17)
    build.add_argument("--demos", type=int, default=3)
    build.add_argument("--queries", type=int, default=4)
    build.add_argument(
        "--policy", choices=("all", *SPREAD_POLICIES), default="all"
    )
    build.add_argument("--out", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("out", type=Path)
    args = parser.parse_args(argv)
    if args.command == "verify":
        print(json.dumps(verify_batch(args.out), sort_keys=True))
        return 0
    from arc_repl.racket_bridge import RacketBridge

    policies = SPREAD_POLICIES if args.policy == "all" else (args.policy,)
    with RacketBridge(timeout=15) as bridge:
        episodes = [
            generate_episode(
                args.seed,
                spread_policy=policy,
                n_demo=args.demos,
                n_query=args.queries,
                bridge=bridge,
            )
            for policy in policies
        ]
        write_batch(episodes, args.out)
        print(json.dumps(verify_batch(args.out, bridge=bridge), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
