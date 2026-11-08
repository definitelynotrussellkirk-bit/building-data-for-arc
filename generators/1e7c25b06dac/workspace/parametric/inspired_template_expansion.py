"""Proposed, opt-in extension inspired by public evaluation task 65b59efc.

This does not parameterize or replace canonical task 1e7c25b06dac. Every
retained label is obtained through RacketBridge; Python supplies finite rivals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ID = "1e7c25b06dac"
PARENT_ID = "65b59efc"
PARENT_CHALLENGE_SHA256 = "ee576437bcd000a274eb9a3ab26c827d293736f23a2940e227f575b1423ee067"
SETTINGS = ("identity", "transpose")
RIVALS = ("identity", "transpose", "column_match", "wrong_swatch", "solid_tiles",
          "ignore_swatches", "transpose_template")
REPO = Path(__file__).resolve().parents[4]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def exact_int(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def check_setting(setting):
    if type(setting) is not str or setting not in SETTINGS:
        raise ValueError("coarse placement must be identity or transpose")


def validate_grid(grid, name="grid"):
    """Require bounded rectangular grids with exact integer colors at API edges."""
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError(f"{name} must be a 1..30 by 1..30 integer grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError(f"{name} must be rectangular with exact integer colors 0..9")


def parse_input(grid):
    """Validate the bounded role grammar, including the two public query layouts."""
    validate_grid(grid, "input")
    width = len(grid[0])
    if 5 not in grid[0]:
        raise ValueError("first template must be followed by a gray separator")
    size = grid[0].index(5)
    if size not in (3, 4, 5) or len(grid) < 2 * size + 4:
        raise ValueError("supported template sizes are 3, 4, 5 with a two-row swatch band")
    panels, role_cells, occupied = [], set(), set()
    saw_empty = False
    for left in range(0, width - size + 1, size + 1):
        template = [row[left:left + size] for row in grid[:size]]
        colors = set(sum(template, [])) - {0}
        if not colors:
            saw_empty = True
            continue
        if saw_empty or len(colors) != 1 or 5 in colors:
            raise ValueError("templates must be consecutive, monochrome, and non-gray")
        source = next(iter(colors))
        mask = [row[left:left + size] for row in grid[size + 1:2 * size + 1]]
        mask_colors = set(sum(mask, [])) - {0}
        if len(mask_colors) != 1 or 5 in mask_colors:
            raise ValueError("every middle panel needs one non-gray mask color")
        swatches = {grid[r][c] for r in range(2 * size + 2, 2 * size + 4)
                    for c in range(left, left + size)} - {0}
        if len(swatches) != 1 or 5 in swatches:
            raise ValueError("each aligned swatch band needs one non-gray color")
        for r in range(size):
            for c in range(size):
                if mask[r][c]:
                    if (r, c) in occupied:
                        raise ValueError("middle masks must have disjoint coarse locations")
                    occupied.add((r, c))
        for r in list(range(size)) + list(range(size + 1, 2 * size + 1)) + [2 * size + 2, 2 * size + 3]:
            role_cells.update((r, c) for c in range(left, left + size))
        panels.append(dict(source=source, template=template, mask=mask,
                           mask_color=next(iter(mask_colors)), swatch=next(iter(swatches))))
    if len(panels) not in (3, 4):
        raise ValueError("supported inputs have three or four template panels")
    sources = [p["source"] for p in panels]
    if len(set(sources)) != len(sources):
        raise ValueError("template source colors must be distinct")
    if sorted(sources) != sorted(p["mask_color"] for p in panels):
        raise ValueError("middle mask colors must match the template keys exactly once each")
    if len({p["swatch"] for p in panels}) != len(panels):
        raise ValueError("this prototype requires distinct target swatches")
    if any(grid[r][c] not in (0, 5) for r in range(len(grid)) for c in range(width)
           if (r, c) not in role_cells):
        raise ValueError("outside the role panels, only background and gray separators are supported")
    return size, panels


def predict(grid, setting, rival=None):
    """Finite interpretation used for certification, never as the label source."""
    check_setting(setting)
    if rival is not None and rival not in RIVALS:
        raise ValueError("unknown finite rival")
    if rival in SETTINGS:
        setting = rival
    size, panels = parse_input(grid)
    keyed = {p["source"]: p for p in panels}
    output = [[0] * (size * size) for _ in range(size * size)]
    for panel in panels:
        for r in range(size):
            for c in range(size):
                source = panel["mask"][r][c]
                if not source:
                    continue
                template = panel if rival == "column_match" else keyed[source]
                target = panel["swatch"] if rival == "wrong_swatch" else template["swatch"]
                if rival == "ignore_swatches":
                    target = source
                rr, cc = (c, r) if setting == "transpose" else (r, c)
                for a in range(size):
                    for b in range(size):
                        pixel = template["template"][b][a] if rival == "transpose_template" else template["template"][a][b]
                        output[rr * size + a][cc * size + b] = target if pixel or rival == "solid_tiles" else 0
    return output


def make_program(setting):
    """Return the complete, pure Racket function for exactly one fixed setting."""
    check_setting(setting)
    coarse_r, coarse_c = ("mc", "mr") if setting == "transpose" else ("mr", "mc")
    return f"""(lambda (g)
  (define n (for/first ([c (in-range (cols g))] #:when (= (at g 0 c) 5)) c))
  (define starts
    (for/list ([left (in-range 0 (+ 1 (- (cols g) n)) (+ n 1))]
               #:when (for*/or ([r (in-range n)] [c (in-range n)])
                        (> (at g r (+ left c)) 0))) left))
  (define slots
    (for/list ([left starts])
      (list (for*/first ([r (in-range n)] [c (in-range n)]
                         #:when (> (at g r (+ left c)) 0)) (at g r (+ left c)))
            left
            (for*/first ([r (in-range (+ (* 2 n) 2) (+ (* 2 n) 4))] [c (in-range n)]
                         #:when (> (at g r (+ left c)) 0)) (at g r (+ left c))))))
  (grid-from-fn (* n n) (* n n)
    (lambda (r c)
      (define mr (quotient r n))
      (define mc (quotient c n))
      (define key
        (or (for/or ([left starts])
              (define v (at g (+ n 1 {coarse_r}) (+ left {coarse_c})))
              (and (> v 0) v)) 0))
      (if (= key 0) 0
          (let ([slot (for/first ([s slots] #:when (= (first s) key)) s)])
            (if (> (at g (remainder r n) (+ (second slot) (remainder c n))) 0)
                (third slot) 0))))))
"""


def execute(bridge, grid, setting):
    """Execute the materialized Racket program and independently check mirror parity."""
    check_setting(setting)
    parse_input(grid)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    result = bridge.eval_text(f"({make_program(setting)} {literal})")
    if result != predict(grid, setting):
        raise RuntimeError("Racket and the finite-rival Python interpretation disagree")
    return result


def sample_input(input_seed, sample_index, *, size=None, templates=None):
    """Draw from a setting-independent stream with bounded, constructive constraints."""
    exact_int(input_seed, "input_seed", 0, 2**63 - 1)
    exact_int(sample_index, "sample_index", 0, 2**31 - 1)
    if size is not None:
        exact_int(size, "size", 3, 5)
    if templates is not None:
        exact_int(templates, "templates", 3, 4)
    rng = random.Random(int(digest(json_bytes(["input-v1", input_seed, sample_index])), 16))
    size = rng.choice((3, 4, 5)) if size is None else size
    count = rng.choice((3, 4)) if templates is None else templates
    palette = [1, 2, 3, 4, 6, 7, 8, 9]
    sources, swatches = rng.sample(palette, count), rng.sample(palette, count)
    if sources == swatches:
        swatches = swatches[1:] + swatches[:1]
    shapes = []
    for source in sources:
        for _ in range(64):
            shape = [[source if rng.random() < 0.65 else 0 for _ in range(size)] for _ in range(size)]
            bits = tuple(v != 0 for row in shape for v in row)
            if (any(bits) and not all(bits)
                    and any(shape[r][c] != shape[c][r] for r in range(size) for c in range(size))
                    and bits not in [tuple(v != 0 for row in old for v in row) for old in shapes]):
                shapes.append(shape)
                break
        else:
            raise RuntimeError("shape sampling exhausted its 64 attempts")
    order = rng.sample(range(count), count)
    if order == list(range(count)):
        order = order[1:] + order[:1]
    for _ in range(64):
        positions = [(r, c) for r in range(size) for c in range(size)]
        rng.shuffle(positions)
        occupied_count = rng.randint(2 * count, size * size)
        owners = list(range(count)) * 2 + [rng.randrange(count) for _ in range(occupied_count - 2 * count)]
        coarse = [[0] * size for _ in range(size)]
        for (r, c), owner in zip(positions, owners):
            coarse[r][c] = sources[owner]
        if coarse != list(map(list, zip(*coarse))):
            break
    else:
        raise RuntimeError("asymmetric layout sampling exhausted its 64 attempts")
    height, width = 2 * size + 4, count * (size + 1) - 1
    grid = [[0] * width for _ in range(height)]
    for divider in (size, 2 * size + 1):
        for c in range(width):
            if c % (size + 1) in (0, size - 1, size) or c % 2 == 0:
                grid[divider][c] = 5
    for divider in range(size, width, size + 1):
        for r in range(height):
            if r % (size + 1) in (0, size - 1, size) or r % 2 == 0:
                grid[r][divider] = 5
    for i in range(count):
        left, mask_source = i * (size + 1), sources[order[i]]
        for r in range(size):
            grid[r][left:left + size] = shapes[i][r]
            for c in range(size):
                if coarse[r][c] == mask_source:
                    grid[size + 1 + r][left + c] = mask_source
        for c in range((size - 1) // 2, size // 2 + 1):
            grid[2 * size + 3][left + c] = swatches[i]
    parse_input(grid)
    return grid


def certify(demonstrations, query_inputs, setting):
    """Filter rivals using demonstrations only, then compare surviving predictions."""
    check_setting(setting)
    if type(demonstrations) is not list or not demonstrations or type(query_inputs) is not list or not query_inputs:
        raise ValueError("certificate requires nonempty demonstration and query-input lists")
    for pair in demonstrations:
        if type(pair) is not dict or "input" not in pair or "output" not in pair:
            raise ValueError("every demonstration requires input and output grids")
        validate_grid(pair["output"], "demonstration output")
    eliminated = {}
    for rival in RIVALS:
        witnesses = [i for i, pair in enumerate(demonstrations)
                     if predict(pair["input"], setting, rival) != pair["output"]]
        if witnesses:
            eliminated[rival] = witnesses
    survivors = [rival for rival in RIVALS if rival not in eliminated]
    if setting not in survivors:
        raise ValueError("demonstrations contradict the declared setting")
    queries = []
    for grid in query_inputs:
        selected = predict(grid, setting)
        conflicts = [rival for rival in survivors if predict(grid, setting, rival) != selected]
        queries.append(dict(input_sha256=digest(json_bytes(grid)), supported=not conflicts,
                            conflicting_survivors=conflicts))
    return dict(scope="finite declared rivals only; demonstrations select survivors",
                tested_rivals=list(RIVALS), eliminated_by_demo=eliminated,
                surviving_rivals=survivors, queries=queries)


def make_episode(bridge, *, input_seed, setting, n_demos=3, n_queries=4):
    check_setting(setting)
    exact_int(input_seed, "input_seed", 0, 2**63 - 1)
    exact_int(n_demos, "n_demos", 1, 12)
    exact_int(n_queries, "n_queries", 1, 8)
    inputs, seen = [], set()
    for index in range(256):
        grid = sample_input(input_seed, index)
        key = json_bytes(grid)
        if key not in seen:
            seen.add(key)
            inputs.append(grid)
        if len(inputs) == n_demos + n_queries:
            break
    else:
        raise RuntimeError("could not obtain the requested distinct inputs within 256 draws")
    pairs = [dict(input=grid, output=execute(bridge, grid, setting)) for grid in inputs]
    train, test = pairs[:n_demos], pairs[n_demos:]
    certificate = certify(train, [pair["input"] for pair in test], setting)
    if not all(query["supported"] for query in certificate["queries"]):
        raise RuntimeError("demonstrations do not identify all requested queries against declared rivals")
    program = make_program(setting)
    return dict(train=train, test=test, certificate=certificate, metadata=dict(
        status="proposed_inspired_prototype", canonical_task_id=TASK_ID,
        inspiration_parent_id=PARENT_ID, public_challenge_sha256=PARENT_CHALLENGE_SHA256,
        verified_lineage=False, training_admitted=False,
        parameters={"coarse_placement": setting}, input_seed=input_seed,
        n_demos=n_demos, n_queries=n_queries, input_draws=index + 1,
        label_backend="RacketBridge", program=program, program_sha256=digest(program.encode()),
        prototype_source_sha256=digest(Path(__file__).read_bytes())))


def write_bundle(destination, episodes):
    """Write sorted opaque public filenames and separate private answer/metadata files."""
    if type(episodes) is not list or not episodes:
        raise ValueError("provide at least one episode")
    projected = []
    for episode in episodes:
        public = public_challenge_bytes(episode)
        for pair in episode["test"]:
            if "output" in pair:
                validate_grid(pair["output"], "private query output")
        projected.append((public_challenge_id(episode), public, json_bytes(episode)))
    projected.sort()
    if len({key for key, _, _ in projected}) != len(projected):
        raise ValueError("duplicate public challenges are not separate episodes")
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "public").mkdir()
    (destination / "private").mkdir()
    for key, public, private in projected:
        (destination / "public" / f"{key}.json").write_bytes(public)
        (destination / "private" / f"{key}.json").write_bytes(private)
    return [f"public/{key}.json" for key, _, _ in projected]


def check_parent(bridge):
    path = REPO / "shared/data/raw/arc-agi_evaluation_challenges.json"
    raw = path.read_bytes()
    task = json.loads(raw)[PARENT_ID]
    # The assignment pins this selected task's compact object, without a newline.
    challenge_hash = digest(json.dumps(task, sort_keys=True, separators=(",", ":")).encode())
    if challenge_hash != PARENT_CHALLENGE_SHA256:
        raise ValueError("selected public challenge differs from the pinned inspiration source")
    rows = []
    for i, pair in enumerate(task["train"]):
        output = execute(bridge, pair["input"], "identity")
        if output != pair["output"]:
            raise RuntimeError(f"identity rule disagrees with public demonstration {i}")
        rows.append(dict(split="train", index=i, exact_match=True,
                         input_sha256=digest(json_bytes(pair["input"])),
                         output_sha256=digest(json_bytes(output))))
    for i, pair in enumerate(task["test"]):
        output = execute(bridge, pair["input"], "identity")
        rows.append(dict(split="test", index=i, executed=True, official_label_available=False,
                         inferred_shape=[len(output), len(output[0])],
                         input_sha256=digest(json_bytes(pair["input"])),
                         inferred_output_sha256=digest(json_bytes(output))))
    return dict(parent_id=PARENT_ID, challenge_sha256=challenge_hash,
                source_file_sha256=digest(raw), pairs=rows,
                limit="Training examples reproduced; public query answers are unavailable.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-seed", type=int, default=137)
    parser.add_argument("--n-demos", type=int, default=3)
    parser.add_argument("--n-queries", type=int, default=4)
    parser.add_argument("--settings", nargs="+", choices=SETTINGS, default=list(SETTINGS))
    parser.add_argument("--out", type=Path, required=True, help="new output directory")
    args = parser.parse_args(argv)
    if len(set(args.settings)) != len(args.settings):
        parser.error("settings must not repeat")
    with RacketBridge(timeout=15) as bridge:
        parent = check_parent(bridge)
        episodes = [make_episode(bridge, input_seed=args.input_seed, setting=setting,
                                 n_demos=args.n_demos, n_queries=args.n_queries)
                    for setting in args.settings]
        boundaries = []
        for size, count in ((3, 3), (3, 4), (5, 3), (5, 4)):
            grid = sample_input(410, 0, size=size, templates=count)
            boundaries.append(dict(size=size, templates=count, input=grid,
                                   outputs={s: execute(bridge, grid, s) for s in SETTINGS}))
        runtime = bridge.runtime_identity
    public_files = write_bundle(args.out, episodes)
    private = args.out / "private"
    (private / "programs").mkdir()
    for setting in SETTINGS:
        program = make_program(setting)
        (private / "programs" / f"{digest(program.encode())}.rkt").write_text(program)
    (private / "boundaries.json").write_bytes(json_bytes(boundaries))
    sources = [Path(__file__), Path(__file__).with_name("README.md"),
               REPO / f"generators/{TASK_ID}/tests/test_inspired_template_expansion.py"]
    report = dict(status="pass", scope="separate proposed inspired prototype; canonical rule unchanged",
                  argv=sys.argv if argv is None else argv, input_seed=args.input_seed,
                  settings=args.settings, n_demos=args.n_demos, n_queries=args.n_queries,
                  parent=parent, public_files=public_files,
                  program_sha256={s: digest(make_program(s).encode()) for s in SETTINGS},
                  source_sha256={str(p.relative_to(REPO)): digest(p.read_bytes()) for p in sources},
                  runtime=runtime, distinct_queries_per_episode=args.n_queries,
                  boundary_cases=len(boundaries), boundary_labels=2 * len(boundaries),
                  executed_labels=5 + len(episodes) * (args.n_demos + args.n_queries) + 2 * len(boundaries),
                  limits=["Finite rivals and bounded seeds do not prove unique semantics or measured difficulty.",
                          "Not a canonical E38 variant, accepted family, or training admission.",
                          "Reference function is specified only on the Python-validated input grammar."])
    (private / "report.json").write_bytes(json_bytes(report))
    print(json.dumps({k: report[k] for k in ("status", "settings", "n_demos", "n_queries",
                                            "executed_labels", "boundary_cases", "public_files")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
