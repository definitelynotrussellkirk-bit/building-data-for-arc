"""Proposed one-step/cascading legend rewrite family for ``d3c9fc4479d8``.

The production generator and canonical Racket authority are unchanged.  This
module provides an opt-in task-local adapter, deterministic episode sampler,
protected-Racket evidence writer, and replay verifier.
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
from typing import Callable, Sequence

from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
TASK_ID = "d3c9fc4479d8"
SCHEMA = "legend-rewrite-mode-prototype-v1"
MODES = ("once", "cascade")
DEFAULT_MODE = "once"
CANONICAL_SHA256 = "895ca245d5158693234f5d28b1e08b79a881076b79634087f8864e89eec2e502"
QUERY_SHAPES = ((10, 12), (16, 20), (24, 24), (30, 30))
DEMO_SHAPES = ((8, 10), (10, 12), (12, 14), (14, 16), (16, 18), (18, 20))
RIVALS = (
    "once",
    "cascade",
    "identity",
    "reverse_once",
    "fixed_origin_once",
    "fixed_origin_cascade",
    "erase_unmapped_once",
    "erase_unmapped_cascade",
)


def json_bytes(value) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _exact_int(value, name: str, lo: int, hi: int) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    return value


def settings(mode: str) -> dict[str, str]:
    if type(mode) is not str or mode not in MODES:
        raise ValueError("mode must be once or cascade")
    return {"mode": mode}


def materialize_program(*, mode: str = DEFAULT_MODE) -> str:
    settings(mode)
    canonical = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    if sha(canonical.encode()) != CANONICAL_SHA256:
        raise ValueError("canonical.rkt differs from the selected canonical authority")
    if mode == "once":
        return canonical
    marker = "(hash-ref mapping v v)"
    if canonical.count(marker) != 1:
        raise ValueError("canonical legend application site changed")
    replacement = """(let loop ([value v] [seen '()])
          (if (or (member value seen) (not (hash-has-key? mapping value)))
              value
              (loop (hash-ref mapping value) (cons value seen))))"""
    return canonical.replace(marker, replacement)


def _rng(seed: int, purpose: str) -> random.Random:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    return random.Random(sha(f"{TASK_ID}|rewrite-v1|{seed}|{purpose}".encode()))


def _parse_pairs(grid: Sequence[Sequence[int]], *, fixed_origin: bool = False):
    row = grid[0]
    pairs: list[tuple[int, int]] = []
    if fixed_origin:
        starts = range(0, len(row) - 1, 2)
        for column in starts:
            left, right = int(row[column]), int(row[column + 1])
            if left != 0 and right != 0:
                pairs.append((left, right))
        return pairs
    column = 0
    while column + 1 < len(row):
        left, right = int(row[column]), int(row[column + 1])
        if left != 0 and right != 0:
            pairs.append((left, right))
            column += 2
        else:
            column += 1
    return pairs


def _mapped(value: int, mapping: dict[int, int], mode: str) -> int:
    if mode == "once":
        return mapping.get(value, value)
    seen: set[int] = set()
    while value in mapping and value not in seen:
        seen.add(value)
        value = mapping[value]
    return value


def _predict(
    grid: Sequence[Sequence[int]],
    *,
    mode: str,
    fixed_origin: bool = False,
    reverse: bool = False,
    erase_unmapped: bool = False,
) -> list[list[int]]:
    settings(mode)
    pairs = _parse_pairs(grid, fixed_origin=fixed_origin)
    mapping = {source: target for source, target in pairs}
    if reverse:
        mapping = {target: source for source, target in pairs}
    output: list[list[int]] = []
    for row in grid[1:]:
        result = []
        for raw in row:
            value = int(raw)
            if erase_unmapped and value != 0 and value not in mapping:
                result.append(0)
            else:
                result.append(_mapped(value, mapping, mode))
        output.append(result)
    return output


def transform(grid: Sequence[Sequence[int]], *, mode: str = DEFAULT_MODE) -> list[list[int]]:
    """Pure Python mirror used for sampling claims and finite rival checks."""
    return _predict(grid, mode=mode)


def _rival(name: str, grid: Sequence[Sequence[int]]) -> list[list[int]]:
    if name in MODES:
        return transform(grid, mode=name)
    if name == "identity":
        return [list(row) for row in grid[1:]]
    if name == "reverse_once":
        return _predict(grid, mode="once", reverse=True)
    if name == "fixed_origin_once":
        return _predict(grid, mode="once", fixed_origin=True)
    if name == "fixed_origin_cascade":
        return _predict(grid, mode="cascade", fixed_origin=True)
    if name == "erase_unmapped_once":
        return _predict(grid, mode="once", erase_unmapped=True)
    if name == "erase_unmapped_cascade":
        return _predict(grid, mode="cascade", erase_unmapped=True)
    raise ValueError(name)


def sample_input(
    seed: int,
    index: int,
    *,
    height: int,
    width: int,
    stream: str = "general",
) -> list[list[int]]:
    """Construct a dense lawful legend/body input with a visible mapping chain."""
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(index, "index", 0, 10**9)
    _exact_int(height, "height", 8, 30)
    _exact_int(width, "width", 8, 30)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be a nonempty string")
    rng = _rng(seed, f"{stream}:{index}:{height}x{width}")
    colors = list(range(1, 10))
    rng.shuffle(colors)
    a, b, c, d, e, neutral = colors[:6]
    pairs = ((a, b), (b, c), (d, e))
    offset = index % 2
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for pair_index, (source, target) in enumerate(pairs):
        column = offset + 2 * pair_index
        grid[0][column] = source
        grid[0][column + 1] = target

    palette = (a, b, d, neutral, c, e)
    phase = rng.randrange(97)
    for r in range(1, height):
        for col in range(width):
            code = (r * 11 + col * 7 + r * col + phase) % 12
            if code in (0, 5, 11):
                value = 0
            else:
                value = palette[(code + r + 2 * col) % len(palette)]
            grid[r][col] = value

    # Literal boundary witnesses ensure the chain affects the whole supported
    # shape range and that non-source controls survive both settings.
    grid[1][0] = a
    grid[1][-1] = neutral
    grid[-1][0] = b
    grid[-1][-1] = a
    grid[height // 2][width // 2] = d
    if transform(grid, mode="once") == transform(grid, mode="cascade"):
        raise RuntimeError("constructed input does not distinguish rewrite modes")
    return grid


def lesson_certificate(challenge: dict) -> dict:
    """Fit finite rivals to demonstrations only; query labels are projected out."""
    visible = json.loads(public_challenge_bytes(challenge))
    demos = visible["train"]
    survivors = [
        name
        for name in RIVALS
        if all(_rival(name, pair["input"]) == pair["output"] for pair in demos)
    ]
    agreement = []
    for pair in visible["test"]:
        predictions = [json_bytes(_rival(name, pair["input"])) for name in survivors]
        agreement.append(bool(predictions) and len(set(predictions)) == 1)
    return {
        "schema": "legend-rewrite-demo-certificate-v1",
        "survivors": survivors,
        "identifiable": len(survivors) == 1 and survivors[0] in MODES and all(agreement),
        "query_agreement": agreement,
        "scope": "eight declared one-step/cascade, placement, reversal, identity, and erasure rivals; not universal uniqueness",
    }


def _validate_request(seed: int, mode: str, n_demo: int, n_query: int) -> None:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    settings(mode)
    _exact_int(n_demo, "n_demo", 2, 6)
    _exact_int(n_query, "n_query", 1, 4)


def sample_episode(
    seed: int,
    *,
    mode: str = DEFAULT_MODE,
    n_demo: int = 3,
    n_query: int = 4,
) -> dict:
    """Return Python label claims; native qualification independently runs Racket."""
    _validate_request(seed, mode, n_demo, n_query)
    demos = [
        sample_input(seed, i, height=h, width=w, stream="demo")
        for i, (h, w) in enumerate(DEMO_SHAPES[:n_demo])
    ]
    queries = [
        sample_input(seed, i, height=h, width=w, stream="query")
        for i, (h, w) in enumerate(QUERY_SHAPES[:n_query])
    ]
    inputs = demos + queries
    if len({json_bytes(grid) for grid in inputs}) != len(inputs):
        raise RuntimeError("duplicate input; no partial episode")
    episode = {
        "train": [{"input": grid, "output": transform(grid, mode=mode)} for grid in demos],
        "test": [{"input": grid, "output": transform(grid, mode=mode)} for grid in queries],
        "program_solution": materialize_program(mode=mode),
    }
    certificate = lesson_certificate(episode)
    if certificate["survivors"] != [mode] or not certificate["identifiable"]:
        raise RuntimeError("demonstrations do not identify the selected mode")
    return episode


def first_turn(episode: dict) -> dict:
    """Visible one-query projection with no future inputs or count hints."""
    return json.loads(
        public_challenge_bytes({"train": episode["train"], "test": episode["test"][:1]})
    )


def grid_check(value) -> list[list[int]]:
    if type(value) is not list or not value or type(value[0]) is not list or not value[0]:
        raise ValueError("grid must contain nonempty rows of exact integer colors")
    width = len(value[0])
    if len(value) > 30 or width > 30:
        raise ValueError("grid exceeds 30x30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return value


def source_bindings() -> dict[str, str]:
    paths = ("prototype.py", "adapter.py", "promotion.json", "canonical.rkt", "README.md", "probe.py")
    sources = {name: sha((HERE / name).read_bytes()) for name in paths}
    sources["../../generator.py"] = sha((HERE.parent.parent / "generator.py").read_bytes())
    return sources


def racket_label(bridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    from puzzle_generators.rule_wrap import wrap_rule

    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    result = bridge.eval_text(f"({wrap_rule(program)} {literal})")
    return grid_check(result)


def runtime_identity(bridge) -> dict:
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise ValueError("retained examples require protected live Racket execution")
    return {
        key: value
        for key, value in identity.items()
        if key in ("schema", "backend", "protected") or key.endswith("_sha256")
    }


def generate_episode(
    seed: int,
    *,
    mode: str = DEFAULT_MODE,
    n_demo: int = 3,
    n_query: int = 4,
    bridge=None,
) -> dict:
    if bridge is None:
        from arc_repl.racket_bridge import RacketBridge

        with RacketBridge(timeout=20, startup_timeout=60) as owned:
            return generate_episode(
                seed, mode=mode, n_demo=n_demo, n_query=n_query, bridge=owned
            )
    episode = sample_episode(seed, mode=mode, n_demo=n_demo, n_query=n_query)
    for pair in episode["train"] + episode["test"]:
        for candidate in MODES:
            actual = racket_label(
                bridge, materialize_program(mode=candidate), pair["input"]
            )
            if actual != transform(pair["input"], mode=candidate):
                raise ValueError("Racket/Python parameter prediction mismatch")
            if candidate == mode:
                pair["output"] = actual
    program = episode.pop("program_solution")
    episode.update(
        schema=SCHEMA,
        task_id=TASK_ID,
        status="proposed",
        training_admitted=False,
        seed=seed,
        parameters=settings(mode),
        source_bindings=source_bindings(),
        program=program,
        program_sha256=sha(program.encode()),
        racket=runtime_identity(bridge),
        certificate=lesson_certificate(episode),
    )
    return episode


def write_batch(episodes, out: Path) -> dict:
    """Atomically write hash-named public challenges and private records."""
    episodes = list(episodes)
    if not episodes:
        raise ValueError("empty batch")
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    payloads: dict[str, tuple[bytes, bytes]] = {}
    for episode in episodes:
        raw = public_challenge_bytes(episode)
        public_id = public_challenge_id(episode)
        if public_id in payloads:
            raise ValueError("duplicate public payload")
        payloads[public_id] = (raw, json_bytes(episode))
    index = {"schema": "public-challenge-batch-v1", "public_ids": sorted(payloads)}
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".legend-stage-", dir=out.parent))
    try:
        (stage / "public").mkdir()
        (stage / "private").mkdir()
        for public_id in index["public_ids"]:
            public, private = payloads[public_id]
            (stage / "public" / f"{public_id}.json").write_bytes(public)
            (stage / "private" / f"{public_id}.json").write_bytes(private)
        (stage / "index.json").write_bytes(json_bytes(index))
        if out.exists() or out.is_symlink():
            raise FileExistsError(out)
        stage.rename(out)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return index


def verify_batch(out: Path, *, bridge=None) -> dict:
    """Replay source-bound programs and reject malformed or tampered exports."""
    if bridge is None:
        from arc_repl.racket_bridge import RacketBridge

        with RacketBridge(timeout=20, startup_timeout=60) as owned:
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
            type(item) is not str
            or len(item) != 64
            or any(char not in "0123456789abcdef" for char in item)
            for item in ids
        )
    ):
        raise ValueError("invalid public index")
    expected = {"index.json"} | {
        f"{kind}/{public_id}.json"
        for public_id in ids
        for kind in ("public", "private")
    }
    actual: set[str] = set()
    directories: set[str] = set()
    for path in out.rglob("*"):
        if path.is_symlink():
            raise ValueError("export contains a symlink")
        if path.is_file():
            actual.add(path.relative_to(out).as_posix())
        elif path.is_dir():
            directories.add(path.relative_to(out).as_posix())
        else:
            raise ValueError("export contains a special file")
    if actual != expected or directories != {"public", "private"}:
        raise ValueError("export inventory differs from public index")

    current_runtime = runtime_identity(bridge)
    pairs = queries = 0
    max_h = max_w = 0
    rows = []
    for public_id in ids:
        raw = (out / "public" / f"{public_id}.json").read_bytes()
        episode = json.loads((out / "private" / f"{public_id}.json").read_bytes())
        if raw != public_challenge_bytes(episode) or sha(raw) != public_id:
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
            raise ValueError("stored Racket runtime identity differs from current backend")
        params = episode.get("parameters")
        if type(params) is not dict or set(params) != {"mode"}:
            raise ValueError("invalid private parameters")
        mode = params["mode"]
        _validate_request(episode.get("seed"), mode, len(episode["train"]), len(episode["test"]))
        program = materialize_program(mode=mode)
        if episode.get("program") != program or episode.get("program_sha256") != sha(program.encode()):
            raise ValueError("private program identity mismatch")
        all_pairs = episode["train"] + episode["test"]
        if len({json_bytes(pair["input"]) for pair in all_pairs}) != len(all_pairs):
            raise ValueError("duplicate input")
        for pair in all_pairs:
            grid_check(pair.get("input"))
            grid_check(pair.get("output"))
            max_h = max(max_h, len(pair["input"]))
            max_w = max(max_w, len(pair["input"][0]))
        certificate = lesson_certificate(episode)
        if (
            json_bytes(episode.get("certificate")) != json_bytes(certificate)
            or certificate["survivors"] != [mode]
            or not certificate["identifiable"]
        ):
            raise ValueError("invalid demonstration-only certificate")
        for pair in all_pairs:
            for candidate in MODES:
                actual_label = racket_label(
                    bridge, materialize_program(mode=candidate), pair["input"]
                )
                if actual_label != transform(pair["input"], mode=candidate):
                    raise ValueError("Racket/Python prediction mismatch")
                if candidate == mode and actual_label != pair["output"]:
                    raise ValueError("stored label disagrees with Racket")
        pairs += len(all_pairs)
        queries += len(episode["test"])
        rows.append(
            {
                "public_id": public_id,
                "parameters": params,
                "demos": len(episode["train"]),
                "queries": len(episode["test"]),
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
        "labeled_pairs": pairs,
        "queries": queries,
        "racket_parameter_replays": len(MODES) * pairs,
        "max_shape": [max_h, max_w],
        "source_bindings": source_bindings(),
        "rows": rows,
        "training_admitted": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--seed", type=int, default=17)
    build.add_argument("--demos", type=int, default=3)
    build.add_argument("--queries", type=int, default=4)
    build.add_argument("--mode", choices=("all", *MODES), default="all")
    build.add_argument("--out", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("out", type=Path)
    args = parser.parse_args(argv)
    if args.command == "verify":
        print(json.dumps(verify_batch(args.out), sort_keys=True))
        return 0
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(timeout=20, startup_timeout=60) as bridge:
        modes = MODES if args.mode == "all" else (args.mode,)
        episodes = [
            generate_episode(
                args.seed, mode=mode, n_demo=args.demos, n_query=args.queries, bridge=bridge
            )
            for mode in modes
        ]
        write_batch(episodes, args.out)
        print(json.dumps(verify_batch(args.out, bridge=bridge), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
