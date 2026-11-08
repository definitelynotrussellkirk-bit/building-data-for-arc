"""Proposed room compression with an episode-fixed minimum marker area.

The canonical generator and rule remain unchanged. Inputs are independent of
the private setting; the CLI and verifier execute the exact Racket programs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import shutil
import tempfile

from reviewer_support import (
    canonical_path, find_root, load_selected_generator,
    public_challenge_bytes, public_challenge_id,
)

TASK_ID = "36b22ff07a2e"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
SETTINGS = tuple({"minimum_marker_area": value} for value in (1, 2, 4))
SCHEMA = "36b22ff07a2e-marker-area-proposal-v1"
RIVALS = (
    "marker_width", "marker_height", "strict_greater", "room_area",
    "global_color_area", "empty_zero", "transpose",
)


def _bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"minimum_marker_area"}:
        raise ValueError("settings require exactly minimum_marker_area")
    value = settings["minimum_marker_area"]
    if type(value) is not int or value not in (1, 2, 4):
        raise ValueError("minimum_marker_area must be an exact integer: 1, 2 or 4")
    return {"minimum_marker_area": value}


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must contain rectangular, exact integer ARC colors")


@lru_cache(maxsize=1)
def _generator():
    return load_selected_generator(TASK_ID, root=ROOT)[0]


def canonical_program():
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("expected one unambiguous canonical program")
    return programs.pop()


def program(settings):
    minimum = _settings(settings)["minimum_marker_area"]
    source = canonical_program()
    if minimum == 1:
        return source  # The default is the exact canonical string, not a rewrite.
    anchor = "(null? non-bg-cells)"
    if source.count(anchor) != 1:
        raise ValueError("canonical marker branch changed; review required")
    return source.replace(anchor, f"(< (length non-bg-cells) {minimum})")


def _facts(grid):
    _grid(grid)
    analysis = _generator()._analysis(grid)
    if analysis["errors"]:
        raise ValueError("outside room grammar: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    background = facts["background_color"]
    for room in facts["room_records"]:
        top, left, bottom, right = room["bbox"]
        cells = [(r, c) for r in range(top, bottom + 1)
                 for c in range(left, right + 1) if grid[r][c] != background]
        room["marker_height"] = max((r for r, _ in cells), default=-1) - min(
            (r for r, _ in cells), default=0) + 1
        room["marker_width"] = max((c for _, c in cells), default=-1) - min(
            (c for _, c in cells), default=0) + 1
    return facts


def _matrix(facts, keep, *, fallback=None):
    background = facts["background_color"] if fallback is None else fallback
    records = facts["room_records"]
    rows = sorted({r["bbox"][0] for r in records})
    cols = sorted({r["bbox"][1] for r in records})
    lookup = {(r["bbox"][0], r["bbox"][1]): r for r in records}
    return [[record["marker"] if record["marker_size"] and keep(record) else background
             for c in cols for record in (lookup[(r, c)],)] for r in rows]


def transform(grid, settings):
    minimum = _settings(settings)["minimum_marker_area"]
    return _matrix(_facts(grid), lambda room: room["marker_size"] >= minimum)


def _predictions(grid, settings):
    minimum = _settings(settings)["minimum_marker_area"]
    facts = _facts(grid)
    area = lambda room: room["marker_size"] >= minimum
    totals = Counter()
    for room in facts["room_records"]:
        if room["marker_size"]:
            totals[room["marker"]] += room["marker_size"]
    chosen = _matrix(facts, area)
    return {
        "parameters": [_matrix(facts, lambda room, t=s["minimum_marker_area"]:
                               room["marker_size"] >= t) for s in SETTINGS],
        "rivals": {
            "marker_width": _matrix(facts, lambda room: room["marker_width"] >= minimum),
            "marker_height": _matrix(facts, lambda room: room["marker_height"] >= minimum),
            "strict_greater": _matrix(facts, lambda room: room["marker_size"] > minimum),
            "room_area": _matrix(facts, lambda room: room["height"] * room["width"] >= minimum),
            "global_color_area": _matrix(facts, lambda room: totals[room["marker"]] >= minimum),
            "empty_zero": _matrix(facts, area, fallback=0),
            "transpose": [list(row) for row in zip(*chosen)],
        },
    }


def lesson_certificate(challenge, settings):
    """Fit rivals using only demos; query answers are deliberately never read."""
    chosen = _settings(settings)
    visible = json.loads(public_challenge_bytes(challenge))
    demo_predictions = [_predictions(p["input"], chosen) for p in visible["train"]]
    parameter_indices = [i for i in range(len(SETTINGS))
                         if all(pred["parameters"][i] == pair["output"]
                                for pred, pair in zip(demo_predictions, visible["train"]))]
    rival_survivors = [name for name in RIVALS
                      if all(pred["rivals"][name] == pair["output"]
                             for pred, pair in zip(demo_predictions, visible["train"]))]
    eliminations = {}
    for name in RIVALS:
        mismatch = next((i for i, (pred, pair) in enumerate(zip(demo_predictions, visible["train"]))
                         if pred["rivals"][name] != pair["output"]), None)
        if mismatch is not None:
            eliminations[name] = mismatch
    identifiable = []
    selected_index = list(SETTINGS).index(chosen)
    for query in visible["test"]:
        predictions = _predictions(query["input"], chosen)
        reference = predictions["parameters"][selected_index]
        survivors = [predictions["parameters"][i] for i in parameter_indices]
        survivors.extend(predictions["rivals"][name] for name in rival_survivors)
        identifiable.append(selected_index in parameter_indices and bool(survivors)
                            and all(output == reference for output in survivors))
    return {
        "schema": "room-marker-declared-rivals-v1",
        "parameter_survivors": [dict(SETTINGS[i]) for i in parameter_indices],
        "rival_survivors": rival_survivors,
        "elimination_demo_indices": eliminations,
        "query_identifiable": identifiable,
        "scope": "three area settings and seven named shortcuts; demos only; no universal uniqueness claim",
    }


def _rng(seed, stream, index):
    return random.Random(int(_sha(_bytes([TASK_ID, seed, stream, index])), 16))


def _scene(seed, index, *, query=False):
    # None of these choices depends on the hidden minimum-marker-area setting.
    rng = _rng(seed, "input", index)
    shape = (("2x3", "3x2", "3x3", "3x3") if query else ("2x3", "3x2"))[index % (4 if query else 2)]
    background = (seed % 10 + 3 * (index % 10)) % 10
    frame = rng.choice([c for c in range(10) if c != background])
    grid = _generator().generate(seed, index, difficulty="hard", lattice_shape=shape,
                                 scene_profile="dense_varied", background_color=background,
                                 frame_color=frame)
    facts = _facts(grid)
    marked = [room for room in facts["room_records"] if room["marker_size"]]
    rng.shuffle(marked)
    # Areas 1,2,2,3,4 teach all boundaries and both thin-marker orientations.
    shapes = [(1, 1), (1, 2), (2, 1), rng.choice(((1, 3), (3, 1))), (2, 2)]
    for i, room in enumerate(marked):
        top, left, bottom, right = room["bbox"]
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                grid[r][c] = background
        height, width = shapes[i] if i < len(shapes) else rng.choice(shapes)
        marker_top = rng.randint(top, bottom - height + 1)
        marker_left = rng.randint(left, right - width + 1)
        # A low-area repeated color defeats global-per-color area at thresholds 2/4.
        color = marked[0]["marker"] if index % 2 == 0 and i == 3 else room["marker"]
        for r in range(marker_top, marker_top + height):
            for c in range(marker_left, marker_left + width):
                grid[r][c] = color
    _facts(grid)
    return grid


def sample_inputs(seed, demos=2, queries=4):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 8)
    _integer(queries, "queries", 1, 8)
    seen, train, test = set(), [], []
    for count, query, destination in ((demos, False, train), (queries, True, test)):
        for i in range(count):
            for retry in range(32):
                # Demo and query streams have independent, stable count prefixes.
                index = (1024 if query else 0) + i + retry * 16
                grid = _scene(seed, index, query=query)
                key = _sha(_bytes(grid))
                if key not in seen:
                    seen.add(key)
                    destination.append(grid)
                    break
            else:
                raise ValueError("distinct-input budget exhausted; no partial episode")
    return train, test


def source_bindings():
    paths = {HERE / "prototype.py", HERE / "adapter.py", HERE / "promotion.json",
             ROOT / "generators" / TASK_ID / "generator.py", canonical_path(ROOT),
             ROOT / "shared/tools/comment_solutions.py"}
    # Bind transitive local helpers and every Racket prelude, not just entrypoints.
    paths.update(p for p in (ROOT / "shared/runtime").rglob("*")
                 if p.is_file() and p.suffix in (".py", ".rkt"))
    if any(p.is_symlink() or not p.resolve().is_relative_to(ROOT) for p in paths):
        raise ValueError("source dependency escapes its checkout")
    return {p.relative_to(ROOT).as_posix(): _sha(p.read_bytes()) for p in sorted(paths)}


def _validate_pairs(episode):
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    seen = set()
    for name, low, high in (("train", 2, 8), ("test", 1, 8)):
        pairs = episode.get(name)
        if type(pairs) is not list or not low <= len(pairs) <= high:
            raise ValueError(f"{name} count must be in {low}..{high}")
        for pair in pairs:
            if type(pair) is not dict or "input" not in pair or "output" not in pair:
                raise ValueError("private pairs require input and output")
            _grid(pair["input"])
            _grid(pair["output"])
            key = _sha(_bytes(pair["input"]))
            if key in seen:
                raise ValueError("episode inputs must all be distinct")
            seen.add(key)


def generate(seed, settings, demos=2, queries=4):
    """Adapter proposal. Returned Python labels require independent execution."""
    chosen = _settings(settings)
    train, test = sample_inputs(seed, demos, queries)
    source = program(chosen)
    episode = {
        "schema": SCHEMA, "task_id": TASK_ID, "parent_family": "training:ac6f9922",
        "status": "proposed", "training_admitted": False, "seed": seed,
        "settings": chosen, "program_solution": source,
        "program_sha256": _sha(source.encode("utf-8")), "source_bindings": source_bindings(),
        "train": [{"input": grid, "output": transform(grid, chosen)} for grid in train],
        "test": [{"input": grid, "output": transform(grid, chosen)} for grid in test],
    }
    certificate = lesson_certificate(episode, chosen)
    if certificate["parameter_survivors"] != [chosen] or not all(certificate["query_identifiable"]):
        raise ValueError("demonstrations do not identify every requested query")
    episode["certificate"] = certificate
    return episode


class RacketRunner:
    """Protected live Racket with a per-run exact-program/input cache."""
    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge
        self.bridge = RacketBridge(timeout=15)
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket is required")
        self.cache = {}
        return self

    def __call__(self, source, grid):
        from puzzle_generators.rule_wrap import wrap_rule
        _grid(grid)
        key = (source, _bytes(grid))
        if key not in self.cache:
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            output = self.bridge.eval_text(f"({wrap_rule(source)} {literal})")
            _grid(output)
            self.cache[key] = _bytes(output)
        return json.loads(self.cache[key])

    def __exit__(self, *exc):
        self.bridge.close()


def verify_episode(episode, runner):
    _validate_pairs(episode)
    chosen = _settings(episode.get("settings"))
    _integer(episode.get("seed"), "seed", 0, 2**63 - 1)
    if (episode.get("schema") != SCHEMA or episode.get("task_id") != TASK_ID
            or episode.get("parent_family") != "training:ac6f9922"
            or episode.get("status") != "proposed" or episode.get("training_admitted") is not False):
        raise ValueError("episode identity or admission status changed")
    source = program(chosen)
    if (episode.get("program_solution") != source
            or episode.get("program_sha256") != _sha(source.encode("utf-8"))
            or episode.get("source_bindings") != source_bindings()):
        raise ValueError("episode program/source identity mismatch")
    train, test = sample_inputs(episode["seed"], len(episode["train"]), len(episode["test"]))
    if train != [p["input"] for p in episode["train"]] or test != [p["input"] for p in episode["test"]]:
        raise ValueError("recorded seed/counts do not reproduce the inputs")
    if "runtime_identity" in episode:
        stored, current = episode["runtime_identity"], runner.identity
        if type(stored) is not dict or type(current) is not dict:
            raise ValueError("invalid runtime identity")
        # Relocation changes paths; executable hashes and protection properties do not.
        portable = lambda value: {k: v for k, v in value.items() if not k.endswith("_path")}
        if _bytes(portable(stored)) != _bytes(portable(current)):
            raise ValueError("stored runtime identity differs from live Racket")
    for setting in SETTINGS:
        reference = program(setting)
        for pair in episode["train"] + episode["test"]:
            actual = runner(reference, pair["input"])
            if actual != transform(pair["input"], setting):
                raise ValueError("Racket/Python parameter disagreement")
            if setting == chosen and actual != pair["output"]:
                raise ValueError("stored label disagrees with Racket")
    certificate = lesson_certificate(episode, chosen)
    if (certificate["parameter_survivors"] != [chosen]
            or not all(certificate["query_identifiable"])
            or _bytes(episode.get("certificate")) != _bytes(certificate)):
        raise ValueError("invalid demonstration-only lesson certificate")
    return {"pairs": len(episode["train"]) + len(episode["test"]),
            "queries": len(episode["test"]), "settings_checked": len(SETTINGS)}


def generate_verified(seed, settings, demos=2, queries=4, *, runner=None):
    if runner is None:
        with RacketRunner() as live:
            return generate_verified(seed, settings, demos, queries, runner=live)
    episode = generate(seed, settings, demos, queries)
    verify_episode(episode, runner)
    # Store the executed values; Python is never an unchecked label fallback.
    for pair in episode["train"] + episode["test"]:
        pair["output"] = runner(episode["program_solution"], pair["input"])
    episode["runtime_identity"] = runner.identity
    return episode


def write_batch(episodes, out):
    """Write projections, not label approval. Public names depend only on visible bytes."""
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    payloads = {}
    for episode in episodes:
        _validate_pairs(episode)
        visible = public_challenge_bytes(episode)
        public_id = public_challenge_id(episode)
        if public_id in payloads:
            raise ValueError("duplicate visible challenge")
        payloads[public_id] = (visible, _bytes(episode))
    if not payloads:
        raise ValueError("batch must contain an episode")
    manifest = {"schema": "room-marker-public-batch-v1", "public_ids": sorted(payloads)}
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".room-marker-stage-", dir=out.parent))
    try:
        (stage / "public").mkdir()
        (stage / "private").mkdir()
        for public_id in manifest["public_ids"]:
            public, private = payloads[public_id]
            (stage / "public" / f"{public_id}.json").write_bytes(public)
            (stage / "private" / f"{public_id}.json").write_bytes(private)
        (stage / "index.json").write_bytes(_bytes(manifest))
        if out.exists() or out.is_symlink():
            raise FileExistsError(out)
        stage.rename(out)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return manifest


def verify_batch(out, runner=None):
    out = Path(out)
    try:
        if out.is_symlink():
            raise ValueError("symlink export root is not permitted")
        index = json.loads((out / "index.json").read_bytes())
        if type(index) is not dict:
            raise ValueError("public ID index must be an object")
        ids = index.get("public_ids")
        if (index.get("schema") != "room-marker-public-batch-v1" or type(ids) is not list
                or not ids or any(type(i) is not str or len(i) != 64
                                 or any(c not in "0123456789abcdef" for c in i) for i in ids)
                or ids != sorted(set(ids))):
            raise ValueError("invalid public ID index")
        expected = {"index.json"} | {f"{kind}/{i}.json" for i in ids for kind in ("public", "private")}
        actual, directories = set(), set()
        for path in out.rglob("*"):
            if path.is_symlink():
                raise ValueError("symlinks are not permitted in an export")
            if path.is_file():
                actual.add(path.relative_to(out).as_posix())
            elif path.is_dir():
                directories.add(path.relative_to(out).as_posix())
            else:
                raise ValueError("unsupported filesystem entry in export")
        if actual != expected or directories != {"public", "private"}:
            raise ValueError("export inventory mismatch")
        episodes = []
        for public_id in ids:
            visible = (out / "public" / f"{public_id}.json").read_bytes()
            episode = json.loads((out / "private" / f"{public_id}.json").read_bytes())
            _validate_pairs(episode)
            if visible != public_challenge_bytes(episode) or _sha(visible) != public_id:
                raise ValueError("public bytes or identity mismatch")
            episodes.append(episode)
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError(f"malformed export: {error}") from error
    if runner is None:
        with RacketRunner() as live:
            return _verify_loaded(episodes, live)
    return _verify_loaded(episodes, runner)


def _verify_loaded(episodes, runner):
    counts = [verify_episode(episode, runner) for episode in episodes]
    return {"status": "passed", "episodes": len(episodes),
            "pairs": sum(row["pairs"] for row in counts),
            "queries": sum(row["queries"] for row in counts),
            "parameter_settings": len(SETTINGS), "training_admitted": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--seed", type=int, action="append")
    build.add_argument("--minimum-marker-area", type=int, choices=(1, 2, 4))
    build.add_argument("--demos", type=int, default=2)
    build.add_argument("--queries", type=int, default=4)
    build.add_argument("--out", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    if args.command == "verify":
        result = verify_batch(args.path)
    else:
        settings = SETTINGS if args.minimum_marker_area is None else ({"minimum_marker_area": args.minimum_marker_area},)
        with RacketRunner() as runner:
            episodes = [generate_verified(seed, setting, args.demos, args.queries, runner=runner)
                        for seed in (args.seed or [0, 17]) for setting in settings]
            write_batch(episodes, args.out)
            result = verify_batch(args.out, runner)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
