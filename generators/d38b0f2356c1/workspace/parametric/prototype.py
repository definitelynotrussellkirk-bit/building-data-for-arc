"""Marker-color parametric prototype for d38b0f2356c1.

The canonical setting chooses the unique 3x3 block without cyan(8).  The
alternate setting chooses the unique block without maroon(9).  Inputs are
setting-neutral: every generated grid has exactly one block missing each marker,
so demonstrations must reveal which absence rule is active.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import shutil
import tempfile
from typing import Any

from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ID = "d38b0f2356c1"
SCHEMA = "arcpuzzles-parametric-prototype-v1"
MARKER_COLORS = (8, 9)
HERE = Path(__file__).resolve().parent

CANONICAL_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (tmpl (reduce (lambda (acc ci)
                                (if acc
                                    acc
                                    (reduce (lambda (acc2 cj)
                                              (if acc2
                                                  acc2
                                                  (let ((r0 (* ci 4))
                                                        (c0 (* cj 4)))
                                                    (if (for/or ((lr (range 0 3)))
                                                                (for/or ((lc (range 0 3)))
                                                                        (= (at g
                                                                               (+ r0 lr)
                                                                               (+ c0 lc))
                                                                           8)))
                                                        #f
                                                        (list r0 c0)))))
                                            #f
                                            (range 0 3))))
                              #f
                              (range 0 3)))
                (tr (fst tmpl))
                (tc (snd tmpl)))
           (build-grid h
                       w
                       (r c)
                       (if (or (= r 3) (= r 7) (= c 3) (= c 7))
                           5
                           (at g (+ tr (floor (/ r 4))) (+ tc (floor (/ c 4)))))))))"""

_BLOCK_STARTS = (0, 4, 8)
_FILL_COLORS = (1, 2, 3, 4, 6, 7)


def _integer(value: object, name: str, lo: int, hi: int) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in [{lo}, {hi}]")
    return value


def _marker(settings: object) -> int:
    if type(settings) is not dict or set(settings) != {"marker_color"}:
        raise ValueError("settings must contain exactly marker_color")
    marker = settings["marker_color"]
    if type(marker) is not int or marker not in MARKER_COLORS:
        raise ValueError(f"marker_color must be one of {MARKER_COLORS}")
    return marker


def program(settings: object) -> str:
    marker = _marker(settings)
    if marker == 8:
        return CANONICAL_PROGRAM
    needle = "                                                                           8)))"
    if CANONICAL_PROGRAM.count(needle) != 1:
        raise RuntimeError("canonical marker literal not found exactly once")
    return CANONICAL_PROGRAM.replace(
        needle, f"                                                                           {marker})))"
    )


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


def _block(grid: list[list[int]], index: int) -> list[list[int]]:
    br = _BLOCK_STARTS[index // 3]
    bc = _BLOCK_STARTS[index % 3]
    return [row[bc : bc + 3] for row in grid[br : br + 3]]


def _selected_index(grid: list[list[int]], marker_color: int) -> int:
    matches = [
        index
        for index in range(9)
        if all(value != marker_color for row in _block(grid, index) for value in row)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one block without marker {marker_color}; got {matches}"
        )
    return matches[0]


def transform(grid: list[list[int]], *, marker_color: int = 8) -> list[list[int]]:
    _grid_check(grid)
    if len(grid) != 11 or len(grid[0]) != 11:
        raise ValueError("marker lattice must be exactly 11x11")
    if type(marker_color) is not int or marker_color not in MARKER_COLORS:
        raise ValueError(f"marker_color must be one of {MARKER_COLORS}")
    source = _block(grid, _selected_index(grid, marker_color))
    return [
        [
            5
            if row in (3, 7) or col in (3, 7)
            else source[row // 4][col // 4]
            for col in range(11)
        ]
        for row in range(11)
    ]


def _rng(seed: int, index: int, stream: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{index}|{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def sample_input(seed: int, index: int) -> list[list[int]]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    index = _integer(index, "index", 0, 2**31 - 1)
    selector = _rng(seed, index, "selector")
    missing8 = selector.randrange(9)
    missing9 = selector.randrange(8)
    if missing9 >= missing8:
        missing9 += 1

    grid = [[0 for _ in range(11)] for _ in range(11)]
    for sep in (3, 7):
        for col in range(11):
            grid[sep][col] = 5
        for row in range(11):
            grid[row][sep] = 5

    for block_index in range(9):
        rng = _rng(seed, index, f"block-{block_index}")
        positions = [(row, col) for row in range(3) for col in range(3)]
        rng.shuffle(positions)
        values: dict[tuple[int, int], int] = {}
        cursor = 0
        if block_index != missing8:
            values[positions[cursor]] = 8
            cursor += 1
        if block_index != missing9:
            values[positions[cursor]] = 9
            cursor += 1
        filler_count = 2 + ((seed + index + block_index) % 4)
        for offset in range(filler_count):
            if cursor >= len(positions):
                break
            values[positions[cursor]] = _FILL_COLORS[
                (index + block_index + offset + rng.randrange(len(_FILL_COLORS)))
                % len(_FILL_COLORS)
            ]
            cursor += 1
        br = _BLOCK_STARTS[block_index // 3]
        bc = _BLOCK_STARTS[block_index % 3]
        for (row, col), value in values.items():
            grid[br + row][bc + col] = value

    if _selected_index(grid, 8) == _selected_index(grid, 9):
        raise RuntimeError("marker settings unexpectedly select the same block")
    return grid


def _pair(grid: list[list[int]], marker_color: int) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": transform(grid, marker_color=marker_color)}


def sample_episode(
    seed: int,
    *,
    marker_color: int = 8,
    n_demo: int = 3,
    n_query: int = 4,
) -> dict[str, Any]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    marker_color = _integer(marker_color, "marker_color", 0, 9)
    if marker_color not in MARKER_COLORS:
        raise ValueError(f"marker_color must be one of {MARKER_COLORS}")
    n_demo = _integer(n_demo, "n_demo", 2, 6)
    n_query = _integer(n_query, "n_query", 1, 4)
    train = [_pair(sample_input(seed, index), marker_color) for index in range(n_demo)]
    test = [
        _pair(sample_input(seed, 100 + index), marker_color)
        for index in range(n_query)
    ]
    all_inputs = [pair["input"] for pair in train + test]
    keys = {json.dumps(grid, separators=(",", ":")) for grid in all_inputs}
    if len(keys) != len(all_inputs):
        raise RuntimeError("episode contains duplicate inputs")
    episode = {
        "train": train,
        "test": test,
        "program_solution": program({"marker_color": marker_color}),
        "parameters": {"marker_color": marker_color},
        "seed": seed,
    }
    certificate = lesson_certificate(episode)
    if certificate["survivors"] != [marker_color]:
        raise RuntimeError(f"demonstrations do not identify marker setting: {certificate}")
    return episode


def lesson_certificate(episode: dict[str, Any]) -> dict[str, Any]:
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    survivors = []
    for marker in MARKER_COLORS:
        try:
            fits = all(
                transform(pair["input"], marker_color=marker) == pair["output"]
                for pair in train
            )
        except (KeyError, TypeError, ValueError):
            fits = False
        if fits:
            survivors.append(marker)
    query_agreement = []
    for pair in test:
        predictions = {
            json.dumps(transform(pair["input"], marker_color=marker), separators=(",", ":"))
            for marker in survivors
        }
        query_agreement.append(len(predictions) <= 1)
    return {
        "family": "marker_color",
        "survivors": survivors,
        "identifiable": len(survivors) == 1,
        "query_agreement": query_agreement,
        "uses_query_outputs": False,
    }


def first_turn(episode: dict[str, Any]) -> dict[str, Any]:
    return json.loads(
        public_challenge_bytes(
            {"train": episode["train"], "test": episode["test"][:1]}
        )
    )


def generate(seed: int, settings: object, demos: int, queries: int) -> dict[str, Any]:
    marker = _marker(settings)
    episode = sample_episode(
        seed, marker_color=marker, n_demo=demos, n_query=queries
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
    marker_color: int = 8,
    n_demo: int = 3,
    n_query: int = 4,
    bridge: Any | None = None,
) -> dict[str, Any]:
    if bridge is None:
        from arc_repl.racket_bridge import RacketBridge

        with RacketBridge(timeout=15) as owned:
            return generate_episode(
                seed,
                marker_color=marker_color,
                n_demo=n_demo,
                n_query=n_query,
                bridge=owned,
            )
    episode = sample_episode(
        seed, marker_color=marker_color, n_demo=n_demo, n_query=n_query
    )
    for pair in episode["train"] + episode["test"]:
        for candidate in MARKER_COLORS:
            actual = racket_label(
                bridge, program({"marker_color": candidate}), pair["input"]
            )
            expected = transform(pair["input"], marker_color=candidate)
            if actual != expected:
                raise ValueError("Racket/Python marker prediction mismatch")
            if candidate == marker_color:
                pair["output"] = actual
    racket_program = episode.pop("program_solution")
    episode.update(
        schema=SCHEMA,
        task_id=TASK_ID,
        status="proposed",
        training_admitted=False,
        parameters={"marker_color": marker_color},
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
    stage = Path(tempfile.mkdtemp(prefix=".d38-marker-stage-", dir=out.parent))
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
        marker = _marker(params)
        seed = _integer(episode.get("seed"), "seed", 0, 2**63 - 1)
        del seed
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
            or certificate["survivors"] != [marker]
            or not certificate["identifiable"]
        ):
            raise ValueError("invalid demonstration-only certificate")
        for pair in all_pairs:
            for candidate in MARKER_COLORS:
                actual = racket_label(
                    bridge, program({"marker_color": candidate}), pair["input"]
                )
                if actual != transform(pair["input"], marker_color=candidate):
                    raise ValueError("Racket/Python prediction mismatch")
                if candidate == marker and actual != pair["output"]:
                    raise ValueError("stored label disagrees with Racket")
        labeled_pairs += len(all_pairs)
        queries += n_query
        rows.append(
            {
                "public_id": public_id,
                "marker_color": marker,
                "demos": n_demo,
                "queries": n_query,
                "query_shapes": [
                    [len(pair["input"]), len(pair["input"][0])]
                    for pair in episode["test"]
                ],
                "survivors": certificate["survivors"],
            }
        )
    return {
        "status": "passed",
        "episodes": len(ids),
        "labeled_pairs": labeled_pairs,
        "queries": queries,
        "racket_parameter_replays": len(MARKER_COLORS) * labeled_pairs,
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
    build.add_argument("--marker", choices=("all", "8", "9"), default="all")
    build.add_argument("--out", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("out", type=Path)
    args = parser.parse_args(argv)
    if args.command == "verify":
        print(json.dumps(verify_batch(args.out), sort_keys=True))
        return 0
    from arc_repl.racket_bridge import RacketBridge

    markers = MARKER_COLORS if args.marker == "all" else (int(args.marker),)
    with RacketBridge(timeout=15) as bridge:
        episodes = [
            generate_episode(
                args.seed,
                marker_color=marker,
                n_demo=args.demos,
                n_query=args.queries,
                bridge=bridge,
            )
            for marker in markers
        ]
        write_batch(episodes, args.out)
        print(json.dumps(verify_batch(args.out, bridge=bridge), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
