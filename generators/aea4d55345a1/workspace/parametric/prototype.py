"""Carry-policy parametric prototype for aea4d55345a1.

The canonical setting applies the latest horizontally shifted cell diff and
also carries a prior-row diff when the latest transition skipped that row.  The
alternate setting applies only the latest shifted diff.  Every generated input
contains both kinds of row, so matched demonstrations identify the active
policy from labels alone.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import tempfile
from typing import Any

from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ID = "aea4d55345a1"
SCHEMA = "arcpuzzles-parametric-prototype-v1"
CARRY_POLICIES = ("skipped_rows", "latest_only")
HERE = Path(__file__).resolve().parent
_SECTION_HEIGHTS = (3, 4, 5, 6)
_WIDTHS = (11, 16, 22, 30)
_ACTIVE_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)

CANONICAL_PROGRAM = """(rule! (lambda (g)
  (let* ((h (rows g)) (w (cols g))
         (seps (filter (lambda (r) (= (at g r 0) 5)) (range 0 h)))
         (sec-h (first seps))
         (starts (append (list 0) (map (lambda (s) (+ s 1)) seps)))
         (ns (length starts))
         (sec (lambda (si)
           (let* ((start (nth starts si)))
             (for/list ((r (range start (+ start sec-h))))
               (for/list ((c (range 0 w))) (at g r c))))))
         (s-last (sec (- ns 1)))
         (s-prev (sec (- ns 2)))
         (s-pprev (sec (- ns 3)))
         ;; Diff: changed cells between two sections
         (diff (lambda (sa sb)
           (filter (lambda (d) d)
             (for*/list ((r (range 0 sec-h)) (c (range 0 w)))
               (let* ((va (nth (nth sa r) c)) (vb (nth (nth sb r) c)))
                 (and (!= va vb) (list r c va vb)))))))
         (d-prev (diff s-pprev s-prev))
         (d-last (diff s-prev s-last))
         (d-last-rows (unique (map first d-last)))
         (carry-diffs (filter (lambda (d) (not (find (lambda (r) (= r (first d))) d-last-rows))) d-prev))
         ;; Column shift between consecutive diffs
         (col-shift (if (or (empty? d-prev) (empty? d-last)) 0
           (- (reduce (lambda (a b) (if (< a b) a b))
                (second (first d-last)) (map second (rest d-last)))
              (reduce (lambda (a b) (if (< a b) a b))
                (second (first d-prev)) (map second (rest d-prev)))))))
    ;; Apply shifted diff to last section
    (grid-from-fn sec-h w (lambda (r c)
      (let* ((m (find (lambda (d) (and (= (first d) r)
              (= (+ (second d) col-shift) c))) d-last))
             (m2 (find (lambda (d)
                  (and (= (first d) r)
                       (> c (second d))
                       (= (nth (nth s-last r) c) (third d))
                       (not (for/or ((cc (range (+ (second d) 1) c)))
                              (= (nth (nth s-last r) cc) (third d))))))
                carry-diffs)))
          (cond
            [(and m (= (nth (nth s-last r) c) (third m))) (fourth m)]
            [m2 (fourth m2)]
            [else (nth (nth s-last r) c)])))))))"""


def _latest_only_program() -> str:
    branch = "            [m2 (fourth m2)]\n"
    if CANONICAL_PROGRAM.count(branch) != 1:
        raise RuntimeError("canonical carry branch not found exactly once")
    return CANONICAL_PROGRAM.replace(branch, "")


LATEST_ONLY_PROGRAM = _latest_only_program()


def _integer(value: object, name: str, lo: int, hi: int) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in [{lo}, {hi}]")
    return value


def _policy(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"carry_policy"}:
        raise ValueError("settings must contain exactly carry_policy")
    policy = settings["carry_policy"]
    if type(policy) is not str or policy not in CARRY_POLICIES:
        raise ValueError(f"carry_policy must be one of {CARRY_POLICIES}")
    return policy


def program(settings: object) -> str:
    return CANONICAL_PROGRAM if _policy(settings) == "skipped_rows" else LATEST_ONLY_PROGRAM


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


def _split_sections(grid: list[list[int]]) -> tuple[int, list[list[list[int]]]]:
    _grid_check(grid)
    width = len(grid[0])
    separators = [
        row for row, values in enumerate(grid)
        if all(value == 5 for value in values)
    ]
    if len(separators) != 3:
        raise ValueError("expected exactly three full gray separator rows")
    section_height = separators[0]
    if section_height < 1:
        raise ValueError("section height must be positive")
    expected = [section_height, 2 * section_height + 1, 3 * section_height + 2]
    if separators != expected or len(grid) != 4 * section_height + 3:
        raise ValueError("sections must be four equal blocks separated by gray rows")
    starts = [0] + [row + 1 for row in separators]
    sections = [
        [values[:] for values in grid[start : start + section_height]]
        for start in starts
    ]
    if any(len(section) != section_height for section in sections):
        raise ValueError("truncated section")
    if any(5 in row for section in sections for row in section):
        raise ValueError("gray may appear only in separator rows")
    if any(len(row) != width for section in sections for row in section):
        raise ValueError("section width mismatch")
    return section_height, sections


def _diff(first: list[list[int]], second: list[list[int]]) -> list[tuple[int, int, int, int]]:
    return [
        (row, col, first[row][col], second[row][col])
        for row in range(len(first))
        for col in range(len(first[0]))
        if first[row][col] != second[row][col]
    ]


def transform(grid: list[list[int]], *, carry_policy: str = "skipped_rows") -> list[list[int]]:
    if type(carry_policy) is not str or carry_policy not in CARRY_POLICIES:
        raise ValueError(f"carry_policy must be one of {CARRY_POLICIES}")
    section_height, sections = _split_sections(grid)
    s_pprev, s_prev, s_last = sections[-3:]
    d_prev = _diff(s_pprev, s_prev)
    d_last = _diff(s_prev, s_last)
    d_last_rows = {row for row, _, _, _ in d_last}
    carry_diffs = [diff for diff in d_prev if diff[0] not in d_last_rows]
    col_shift = 0
    if d_prev and d_last:
        col_shift = min(diff[1] for diff in d_last) - min(diff[1] for diff in d_prev)
    width = len(s_last[0])
    output = [[0 for _ in range(width)] for _ in range(section_height)]
    for row in range(section_height):
        for col in range(width):
            moved = next(
                (
                    diff for diff in d_last
                    if diff[0] == row and diff[1] + col_shift == col
                ),
                None,
            )
            carried = None
            if carry_policy == "skipped_rows":
                carried = next(
                    (
                        diff for diff in carry_diffs
                        if (
                            diff[0] == row
                            and col > diff[1]
                            and s_last[row][col] == diff[2]
                            and not any(
                                s_last[row][between] == diff[2]
                                for between in range(diff[1] + 1, col)
                            )
                        )
                    ),
                    None,
                )
            if moved is not None and s_last[row][col] == moved[2]:
                output[row][col] = moved[3]
            elif carried is not None:
                output[row][col] = carried[3]
            else:
                output[row][col] = s_last[row][col]
    return output


def _rng(seed: int, index: int, stream: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{index}|{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _assemble(sections: list[list[list[int]]]) -> list[list[int]]:
    width = len(sections[0][0])
    grid: list[list[int]] = []
    for index, section in enumerate(sections):
        grid.extend([row[:] for row in section])
        if index < len(sections) - 1:
            grid.append([5] * width)
    return grid


def sample_input(seed: int, index: int) -> list[list[int]]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    index = _integer(index, "index", 0, 2**31 - 1)
    slot = index % 4
    section_height = _SECTION_HEIGHTS[slot]
    width = _WIDTHS[slot]
    rng = _rng(seed, index, "layout")
    base_color, accent_color = rng.sample(_ACTIVE_COLORS, 2)
    anchor = rng.randrange(2, width - 3)
    latest_row = rng.randrange(section_height - 1)
    signature_col = index % width
    signature_accent = (signature_col + 3 + (index // 4)) % width
    sections = [
        [[0 for _ in range(width)] for _ in range(section_height)]
        for _ in range(4)
    ]
    active_rows = range(section_height - 1)
    base_cells = range(anchor - 2, anchor + 4)
    for row in active_rows:
        for section in sections:
            for col in base_cells:
                section[row][col] = base_color
        prefix_lengths = (1, 2, 3, 4) if row == latest_row else (1, 2, 3, 3)
        for section, prefix_length in zip(sections, prefix_lengths):
            for col in range(anchor - 2, anchor - 2 + prefix_length):
                section[row][col] = accent_color
    static_row = section_height - 1
    for section in sections:
        section[static_row][signature_col] = base_color
        section[static_row][signature_accent] = accent_color
    grid = _assemble(sections)
    carried = transform(grid, carry_policy="skipped_rows")
    latest = transform(grid, carry_policy="latest_only")
    if carried == latest:
        raise RuntimeError("sample does not distinguish carry policies")
    return grid


def _pair(grid: list[list[int]], carry_policy: str) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": transform(grid, carry_policy=carry_policy)}


def sample_episode(
    seed: int,
    *,
    carry_policy: str = "skipped_rows",
    n_demo: int = 3,
    n_query: int = 4,
) -> dict[str, Any]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    if type(carry_policy) is not str or carry_policy not in CARRY_POLICIES:
        raise ValueError(f"carry_policy must be one of {CARRY_POLICIES}")
    n_demo = _integer(n_demo, "n_demo", 2, 6)
    n_query = _integer(n_query, "n_query", 1, 4)
    train = [_pair(sample_input(seed, index), carry_policy) for index in range(n_demo)]
    test = [
        _pair(sample_input(seed, 100 + index), carry_policy)
        for index in range(n_query)
    ]
    all_inputs = [pair["input"] for pair in train + test]
    keys = {json.dumps(grid, separators=(",", ":")) for grid in all_inputs}
    if len(keys) != len(all_inputs):
        raise RuntimeError("episode contains duplicate inputs")
    episode = {
        "train": train,
        "test": test,
        "program_solution": program({"carry_policy": carry_policy}),
        "parameters": {"carry_policy": carry_policy},
        "seed": seed,
    }
    certificate = lesson_certificate(episode)
    if certificate["survivors"] != [carry_policy]:
        raise RuntimeError(f"demonstrations do not identify carry policy: {certificate}")
    return episode


def lesson_certificate(episode: dict[str, Any]) -> dict[str, Any]:
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    survivors = []
    for policy in CARRY_POLICIES:
        try:
            fits = all(
                transform(pair["input"], carry_policy=policy) == pair["output"]
                for pair in train
            )
        except (KeyError, TypeError, ValueError):
            fits = False
        if fits:
            survivors.append(policy)
    query_agreement = []
    for pair in test:
        predictions = {
            json.dumps(transform(pair["input"], carry_policy=policy), separators=(",", ":"))
            for policy in survivors
        }
        query_agreement.append(len(predictions) <= 1)
    return {
        "family": "carry_policy",
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
    episode = sample_episode(seed, carry_policy=policy, n_demo=demos, n_query=queries)
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
    carry_policy: str = "skipped_rows",
    n_demo: int = 3,
    n_query: int = 4,
    bridge: Any | None = None,
) -> dict[str, Any]:
    if bridge is None:
        from arc_repl.racket_bridge import RacketBridge

        with RacketBridge(timeout=15) as owned:
            return generate_episode(
                seed,
                carry_policy=carry_policy,
                n_demo=n_demo,
                n_query=n_query,
                bridge=owned,
            )
    episode = sample_episode(
        seed, carry_policy=carry_policy, n_demo=n_demo, n_query=n_query
    )
    for pair in episode["train"] + episode["test"]:
        for candidate in CARRY_POLICIES:
            actual = racket_label(
                bridge, program({"carry_policy": candidate}), pair["input"]
            )
            expected = transform(pair["input"], carry_policy=candidate)
            if actual != expected:
                raise ValueError("Racket/Python carry prediction mismatch")
            if candidate == carry_policy:
                pair["output"] = actual
    racket_program = episode.pop("program_solution")
    episode.update(
        schema=SCHEMA,
        task_id=TASK_ID,
        status="proposed",
        training_admitted=False,
        parameters={"carry_policy": carry_policy},
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
    stage = Path(tempfile.mkdtemp(prefix=".aea-carry-stage-", dir=out.parent))
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
            for candidate in CARRY_POLICIES:
                actual = racket_label(
                    bridge, program({"carry_policy": candidate}), pair["input"]
                )
                if actual != transform(pair["input"], carry_policy=candidate):
                    raise ValueError("Racket/Python prediction mismatch")
                if candidate == policy and actual != pair["output"]:
                    raise ValueError("stored label disagrees with Racket")
        labeled_pairs += len(all_pairs)
        queries += n_query
        rows.append(
            {
                "public_id": public_id,
                "carry_policy": policy,
                "demos": n_demo,
                "queries": n_query,
                "query_input_shapes": [
                    [len(pair["input"]), len(pair["input"][0])]
                    for pair in episode["test"]
                ],
                "query_output_shapes": [
                    [len(pair["output"]), len(pair["output"][0])]
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
        "racket_parameter_replays": len(CARRY_POLICIES) * labeled_pairs,
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
    build.add_argument("--policy", choices=("all", *CARRY_POLICIES), default="all")
    build.add_argument("--out", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("out", type=Path)
    args = parser.parse_args(argv)
    if args.command == "verify":
        print(json.dumps(verify_batch(args.out), sort_keys=True))
        return 0
    from arc_repl.racket_bridge import RacketBridge

    policies = CARRY_POLICIES if args.policy == "all" else (args.policy,)
    with RacketBridge(timeout=15) as bridge:
        episodes = [
            generate_episode(
                args.seed,
                carry_policy=policy,
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
