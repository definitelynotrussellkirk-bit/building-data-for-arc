#!/usr/bin/env python3
"""Source-bound episodes varying whether frame growth is capped by grid edges."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import shutil
import sys
import tempfile

for _parent in Path(__file__).resolve().parents:
    for _runtime in (_parent / "shared/runtime", _parent):
        if (_runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_runtime))
            break
    else:
        continue
    break

from reviewer_support import (  # noqa: E402
    find_root,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)
from arc_repl.racket_bridge import RacketBridge, racket_runtime_status  # noqa: E402

ROOT = find_root(__file__)
TASK_ID = "5e619caf1f27"
DEFAULT_EDGE_CAP = "capped"
PROGRAMS = {
    "capped": """(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         ;; The non-zero bounding box is the original outer rectangle.
         (cells (positions-of g (lambda (v) (!= v 0))))
         (bb (bbox-of-cells cells))
         (r1 (first bb))
         (c1 (second bb))
         (r2 (third bb))
         (c2 (fourth bb))
         (outer (at g r1 c1))
         ;; The other non-zero color forms the solid inner rectangle.
         (inner-cells
           (filter (lambda (p)
             (!= (at g (first p) (second p)) outer))
             cells))
         (ibb (bbox-of-cells inner-cells))
         (ir1 (first ibb))
         (ic1 (second ibb))
         (ir2 (third ibb))
         (ic2 (fourth ibb))
         (inner (at g ir1 ic1))
         (inner-h (+ 1 (- ir2 ir1)))
         (inner-w (+ 1 (- ic2 ic1)))
         ;; Expand uniformly, capped by both inner size and every grid edge.
         (thick (min inner-h inner-w r1 c1
                     (- (- h 1) r2) (- (- w 1) c2)))
         (nr1 (- r1 thick))
         (nc1 (- c1 thick))
         (nr2 (+ r2 thick))
         (nc2 (+ c2 thick)))
    (cellmap g
      (r c v)
      (if (and (>= r nr1) (<= r nr2)
               (>= c nc1) (<= c nc2)
               (not (and (>= r r1) (<= r r2)
                         (>= c c1) (<= c c2))))
          inner
          v)))))""",
    "uncapped_inner": """(rule! (lambda (g)
  (let* ((cells (positions-of g (lambda (v) (!= v 0))))
         (bb (bbox-of-cells cells))
         (r1 (first bb))
         (c1 (second bb))
         (r2 (third bb))
         (c2 (fourth bb))
         (outer (at g r1 c1))
         (inner-cells
           (filter (lambda (p)
             (!= (at g (first p) (second p)) outer))
             cells))
         (ibb (bbox-of-cells inner-cells))
         (ir1 (first ibb))
         (ic1 (second ibb))
         (ir2 (third ibb))
         (ic2 (fourth ibb))
         (inner (at g ir1 ic1))
         (inner-h (+ 1 (- ir2 ir1)))
         (inner-w (+ 1 (- ic2 ic1)))
         (thick (min inner-h inner-w))
         (nr1 (- r1 thick))
         (nc1 (- c1 thick))
         (nr2 (+ r2 thick))
         (nc2 (+ c2 thick)))
    (cellmap g
      (r c v)
      (if (and (>= r nr1) (<= r nr2)
               (>= c nc1) (<= c nc2)
               (not (and (>= r r1) (<= r r2)
                         (>= c c1) (<= c c2))))
          inner
          v)))))""",
}
RULE_WRAPPER = "(define (rule! f) f)"
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1
DEMO_SHAPES = ((12, 13), (14, 15), (16, 17), (18, 18), (20, 21), (22, 22))
QUERY_SHAPES = ((23, 25), (26, 24), (28, 30), (30, 30))
DEMO_PROFILES = (
    "edge_top_one",
    "inner_width",
    "edge_bottom_two",
    "inner_height",
    "edge_left_one",
    "edge_right_two",
)
QUERY_PROFILES = (
    "inner_width",
    "edge_left_one",
    "inner_height",
    "edge_bottom_two",
)
LIMITATIONS = [
    "Proposed prototype only; canonical generator and approval are unchanged.",
    "Only the edge-cap term of frame thickness is varied.",
    "All inputs preserve the source grammar of one solid outer rectangle and one inset solid inner rectangle.",
    "Episodes contain 2..6 demonstrations and exactly four private queries.",
    "Identifiability is checked only against the two declared settings.",
    "Finite source-bound evidence is not proof over every seed.",
]


def open_bridge():
    bridge = RacketBridge()
    try:
        bridge.eval_text(RULE_WRAPPER)
    except BaseException:
        bridge.shutdown()
        raise
    return bridge


def execute(bridge, edge_cap, grids):
    if edge_cap not in PROGRAMS:
        raise ValueError(f"edge_cap must be one of {tuple(PROGRAMS)}")
    bridge.eval_text(f"(define prototype-rule {PROGRAMS[edge_cap]})")
    outputs = []
    for grid in grids:
        bridge.define_grid("prototype-input", normalize_grid(grid))
        outputs.append(normalize_grid(bridge.eval_text("(prototype-rule prototype-input)")))
    return outputs


def _validate_request(seed, n_train, n_test):
    if type(seed) is not int or not 0 <= seed <= MAX_SEED:
        raise ValueError(f"seed must be an exact integer in [0, {MAX_SEED}]")
    if type(n_train) is not int or not MIN_DEMOS <= n_train <= MAX_DEMOS:
        raise ValueError(f"n_train must be an exact integer in [{MIN_DEMOS}, {MAX_DEMOS}]")
    if type(n_test) is not int or n_test != QUERY_COUNT:
        raise ValueError(f"n_test must be the exact integer {QUERY_COUNT}")


def _bbox(points):
    rows = [row for row, _ in points]
    cols = [col for _, col in points]
    return min(rows), min(cols), max(rows), max(cols)


def analyze_scene(grid):
    """Recover the source geometry used by both declared frame rules."""
    try:
        grid = normalize_grid(grid)
    except ValueError as error:
        return {"errors": [str(error)]}
    height, width = len(grid), len(grid[0])
    points = [(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0]
    if not points:
        return {"errors": ["missing outer rectangle"]}
    r1, c1, r2, c2 = _bbox(points)
    corners = {grid[r1][c1], grid[r1][c2], grid[r2][c1], grid[r2][c2]}
    if len(corners) != 1 or 0 in corners:
        return {"errors": ["outer bounding-box corners must share one nonzero color"]}
    outer_color = next(iter(corners))
    inner_points = [(r, c) for r, c in points if grid[r][c] != outer_color]
    if not inner_points:
        return {"errors": ["missing distinct inner rectangle"]}
    inner_colors = {grid[r][c] for r, c in inner_points}
    if len(inner_colors) != 1:
        return {"errors": ["inner rectangle must have one color"]}
    inner_color = next(iter(inner_colors))
    ir1, ic1, ir2, ic2 = _bbox(inner_points)
    errors = []
    if not (r1 < ir1 <= ir2 < r2 and c1 < ic1 <= ic2 < c2):
        errors.append("inner rectangle must be strictly inset")
    for row in range(height):
        for col in range(width):
            if r1 <= row <= r2 and c1 <= col <= c2:
                expected = inner_color if ir1 <= row <= ir2 and ic1 <= col <= ic2 else outer_color
            else:
                expected = 0
            if grid[row][col] != expected:
                errors.append("scene must contain exactly two solid nested rectangles")
                break
        if errors:
            break
    inner_h, inner_w = ir2 - ir1 + 1, ic2 - ic1 + 1
    margins = (r1, c1, height - 1 - r2, width - 1 - c2)
    thickness = min(inner_h, inner_w, *margins)
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "outer_color": outer_color,
        "inner_color": inner_color,
        "outer_bbox": (r1, c1, r2, c2),
        "inner_bbox": (ir1, ic1, ir2, ic2),
        "inner_h": inner_h,
        "inner_w": inner_w,
        "margins": margins,
        "thickness": thickness,
        "edge_limited": min(margins) < min(inner_h, inner_w),
    }


def _profile_geometry(profile):
    if profile == "inner_width":
        return (5, 2, 1, 2, 2, 1, None, None)
    if profile == "inner_height":
        return (2, 5, 2, 1, 1, 2, None, None)
    if profile == "edge_top_one":
        return (4, 5, 1, 1, 2, 1, "top", 1)
    if profile == "edge_bottom_two":
        return (5, 4, 2, 1, 1, 2, "bottom", 2)
    if profile == "edge_left_one":
        return (4, 5, 1, 2, 2, 1, "left", 1)
    if profile == "edge_right_two":
        return (5, 4, 2, 1, 1, 2, "right", 2)
    raise ValueError(f"unknown profile {profile!r}")


def sample_grid(*, seed, role, index, height, width):
    """Construct a deterministic setting-neutral nested-rectangle scene."""
    if type(seed) is not int or type(index) is not int:
        raise ValueError("seed and index must be exact integers")
    if type(height) is not int or type(width) is not int or not (11 <= height <= 30 and 11 <= width <= 30):
        raise ValueError("height and width must be exact integers in [11, 30]")
    profiles = QUERY_PROFILES if role == "query" else DEMO_PROFILES
    profile = profiles[index % len(profiles)]
    ih, iw, gt, gl, gb, gr, side, cap = _profile_geometry(profile)
    outer_h, outer_w = ih + gt + gb, iw + gl + gr
    if outer_h + 2 > height or outer_w + 2 > width:
        raise ValueError("requested canvas is too small for the selected profile")
    rng = random.Random(f"{TASK_ID}|{seed}|{role}|{index}|{height}x{width}")
    if side == "top":
        outer_row = cap
        outer_col = rng.randint(1, width - outer_w - 1)
    elif side == "bottom":
        outer_row = height - outer_h - cap
        outer_col = rng.randint(1, width - outer_w - 1)
    elif side == "left":
        outer_row = rng.randint(1, height - outer_h - 1)
        outer_col = cap
    elif side == "right":
        outer_row = rng.randint(1, height - outer_h - 1)
        outer_col = width - outer_w - cap
    else:
        inner_min = min(ih, iw)
        row_lo, row_hi = inner_min, height - outer_h - inner_min
        col_lo, col_hi = inner_min, width - outer_w - inner_min
        if row_lo > row_hi or col_lo > col_hi:
            raise ValueError("canvas cannot keep the inner-limited scene away from every edge")
        outer_row = rng.randint(row_lo, row_hi)
        outer_col = rng.randint(col_lo, col_hi)
    palette = rng.sample(range(1, 10), 2)
    outer_color, inner_color = palette
    grid = [[0] * width for _ in range(height)]
    for row in range(outer_row, outer_row + outer_h):
        for col in range(outer_col, outer_col + outer_w):
            grid[row][col] = outer_color
    inner_row, inner_col = outer_row + gt, outer_col + gl
    for row in range(inner_row, inner_row + ih):
        for col in range(inner_col, inner_col + iw):
            grid[row][col] = inner_color
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise AssertionError(analysis["errors"])
    if side is not None and not analysis["edge_limited"]:
        raise AssertionError("edge profile failed to expose edge-limited thickness")
    if side is None and analysis["edge_limited"]:
        raise AssertionError("inner profile accidentally became edge-limited")
    return grid


def _sample_grids(seed, n_train, n_test):
    _validate_request(seed, n_train, n_test)
    grids = [
        sample_grid(seed=seed, role="demo", index=index, height=height, width=width)
        for index, (height, width) in enumerate(DEMO_SHAPES[:n_train])
    ]
    grids.extend(
        sample_grid(seed=seed, role="query", index=index, height=height, width=width)
        for index, (height, width) in enumerate(QUERY_SHAPES[:n_test])
    )
    fingerprints = {json.dumps(grid, separators=(",", ":")) for grid in grids}
    if len(fingerprints) != len(grids):
        raise ValueError("sampler produced duplicate visible inputs")
    return grids


def python_transform(grid, edge_cap):
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    if edge_cap not in PROGRAMS:
        raise ValueError(f"edge_cap must be one of {tuple(PROGRAMS)}")
    requested = min(analysis["inner_h"], analysis["inner_w"])
    thickness = analysis["thickness"] if edge_cap == "capped" else requested
    r1, c1, r2, c2 = analysis["outer_bbox"]
    height, width = analysis["height"], analysis["width"]
    output = [list(row) for row in grid]
    for row in range(max(0, r1 - thickness), min(height - 1, r2 + thickness) + 1):
        for col in range(max(0, c1 - thickness), min(width - 1, c2 + thickness) + 1):
            if not (r1 <= row <= r2 and c1 <= col <= c2):
                output[row][col] = analysis["inner_color"]
    return output


def build_claimed_episode(*, seed, edge_cap, n_train, n_test=QUERY_COUNT):
    _validate_request(seed, n_train, n_test)
    if edge_cap not in PROGRAMS:
        raise ValueError(f"edge_cap must be one of {tuple(PROGRAMS)}")
    grids = _sample_grids(seed, n_train, n_test)
    pairs = [{"input": grid, "output": python_transform(grid, edge_cap)} for grid in grids]
    return {"train": pairs[:n_train], "test": pairs[n_train:]}


def assess_episode(bridge, episode):
    pairs = episode["train"] + episode["test"]
    split = len(episode["train"])
    rivals = {}
    for edge_cap in PROGRAMS:
        outputs = execute(bridge, edge_cap, [pair["input"] for pair in pairs])
        matches = [actual == pair["output"] for actual, pair in zip(outputs, pairs)]
        rivals[edge_cap] = {
            "outputs": outputs,
            "demo_matches": matches[:split],
            "query_matches": matches[split:],
            "demo_consistent": all(matches[:split]),
            "full_episode_consistent": all(matches),
        }
    survivors = [key for key, value in rivals.items() if value["demo_consistent"]]
    return {
        "rivals": rivals,
        "demo_survivors": survivors,
        "identifiable_from_demos": len(survivors) == 1,
    }


def build_episode(bridge, *, seed, edge_cap=None, n_train=3, n_test=QUERY_COUNT):
    _validate_request(seed, n_train, n_test)
    selected = random.Random(f"{TASK_ID}|{seed}|edge-cap").choice(tuple(PROGRAMS))
    if edge_cap is not None:
        if edge_cap not in PROGRAMS:
            raise ValueError(f"edge_cap must be one of {tuple(PROGRAMS)}")
        selected = edge_cap
    grids = _sample_grids(seed, n_train, n_test)
    outputs = execute(bridge, selected, grids)
    pairs = [{"input": grid, "output": output} for grid, output in zip(grids, outputs)]
    program = PROGRAMS[selected]
    episode = {
        "seed": seed,
        "edge_cap": selected,
        "program": program,
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "train": pairs[:n_train],
        "test": pairs[n_train:],
    }
    episode["rival_check"] = assess_episode(bridge, episode)
    if episode["rival_check"]["demo_survivors"] != [selected]:
        raise ValueError("draw does not distinguish the selected setting from demonstrations")
    return episode


def public_challenge(episode, query_indices=None):
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train/test lists")
    if query_indices is None:
        indices = list(range(len(test)))
    else:
        if type(query_indices) not in (list, tuple) or not query_indices:
            raise ValueError("query_indices must be a nonempty list or tuple")
        indices = list(query_indices)
        if any(type(index) is not int or not 0 <= index < len(test) for index in indices):
            raise ValueError("query index outside the episode")
        if len(set(indices)) != len(indices):
            raise ValueError("query_indices must be distinct")
    challenge = {
        "train": [{"input": pair["input"], "output": pair["output"]} for pair in train],
        "test": [{"input": test[index]["input"]} for index in indices],
    }
    return json.loads(public_challenge_bytes(challenge))


def sequential_turn(episode, query_index):
    test = episode.get("test")
    if type(test) is not list or type(query_index) is not int or not 0 <= query_index < len(test):
        raise ValueError("query_index must name one stored query")
    if query_index == 0:
        return public_challenge(episode, query_indices=[0])
    return deepcopy({"test": [{"input": test[query_index]["input"]}]})


def verify_episode(episode, bridge):
    if not isinstance(episode, dict):
        raise ValueError("episode must be a dictionary")
    train, test = episode.get("train"), episode.get("test")
    _validate_request(
        episode.get("seed"),
        len(train) if type(train) is list else None,
        len(test) if type(test) is list else None,
    )
    edge_cap = episode.get("edge_cap")
    if edge_cap not in PROGRAMS:
        raise ValueError("stored edge_cap is outside the declared family")
    program = PROGRAMS[edge_cap]
    if episode.get("program") != program:
        raise ValueError("stored program differs from the selected setting")
    if episode.get("program_sha256") != hashlib.sha256(program.encode()).hexdigest():
        raise ValueError("stored program hash differs from the selected setting")
    public_challenge_bytes(public_challenge(episode))
    pairs = train + test
    seen = set()
    for pair in pairs:
        if type(pair) is not dict or "input" not in pair or "output" not in pair:
            raise ValueError("private episode must contain complete input/output pairs")
        key = json.dumps(pair["input"], separators=(",", ":"))
        if key in seen:
            raise ValueError("duplicate visible input within episode")
        seen.add(key)
        if analyze_scene(pair["input"])["errors"]:
            raise ValueError("stored input is outside the declared nested-rectangle grammar")
    outputs = execute(bridge, edge_cap, [pair["input"] for pair in pairs])
    if outputs != [pair["output"] for pair in pairs]:
        raise ValueError("stored labels differ from fresh Racket execution")
    fresh = assess_episode(bridge, episode)
    if fresh.get("demo_survivors") != [edge_cap]:
        raise ValueError("demonstrations do not uniquely identify the selected setting")
    if episode.get("rival_check") != fresh:
        raise ValueError("stored rival certificate differs from fresh demo-only replay")
    return True


def source_hashes():
    runtime = Path(sys.modules["arc_repl.racket_bridge"].__file__).resolve().parent
    paths = [
        Path(__file__).resolve(),
        runtime / "racket_bridge.py",
        runtime / "racket_prelude/arc-prelude.rkt",
        Path(sys.modules["reviewer_support"].__file__).resolve(),
    ]
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def write_batch(episodes, out, bridge):
    if type(episodes) is not list or not episodes:
        raise ValueError("batch must contain at least one episode")
    out = Path(out)
    if out.exists():
        raise ValueError("output path already exists")
    planned = []
    for episode in episodes:
        verify_episode(episode, bridge)
        public = public_challenge(episode)
        planned.append((public_challenge_id(public), public_challenge_bytes(public), episode))
    planned.sort(key=lambda row: row[0])
    if len({row[0] for row in planned}) != len(planned):
        raise ValueError("duplicate visible payload in batch")
    witness = sample_grid(seed=0, role="witness", index=0, height=15, width=17)
    witness_outputs = {key: execute(bridge, key, [witness])[0] for key in PROGRAMS}
    report = {
        "schema": f"{TASK_ID}-edge-cap-parametric-v1",
        "status": "proposed prototype; not production approval",
        "training_admitted": False,
        "episode_count": len(planned),
        "public_ids": [row[0] for row in planned],
        "demonstration_counts": [len(row[2]["train"]) for row in planned],
        "query_counts": [len(row[2]["test"]) for row in planned],
        "label_count": sum(len(row[2][split]) for row in planned for split in ("train", "test")),
        "settings_exercised": sorted({row[2]["edge_cap"] for row in planned}),
        "parameter": {
            "name": "edge_cap",
            "allowed": list(PROGRAMS),
            "original_default": DEFAULT_EDGE_CAP,
            "input_constraints_depend_on_setting": False,
        },
        "programs": {
            key: {"text": value, "sha256": hashlib.sha256(value.encode()).hexdigest()}
            for key, value in PROGRAMS.items()
        },
        "source_sha256": source_hashes(),
        "racket_runtime": racket_runtime_status(),
        "witness": {
            "input": witness,
            "outputs": witness_outputs,
            "distinct": witness_outputs["capped"] != witness_outputs["uncapped_inner"],
        },
        "limitations": LIMITATIONS,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".edge-cap-parametric-", dir=out.parent))
    try:
        (stage / "public").mkdir()
        (stage / "private").mkdir()
        private_rows = []
        for public_id, raw, episode in planned:
            (stage / "public" / f"{public_id}.json").write_bytes(raw)
            private_rows.append(dict(deepcopy(episode), public_id=public_id))
        (stage / "private/episodes.json").write_text(
            json.dumps(private_rows, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        (stage / "private/verification.json").write_text(
            json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        stage.rename(out)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return report


def verify_batch(path, bridge):
    path = Path(path)
    try:
        rows = json.loads((path / "private/episodes.json").read_text(encoding="utf-8"))
        report = json.loads((path / "private/verification.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError("missing or invalid private batch evidence") from error
    if type(rows) is not list or not rows:
        raise ValueError("private episode list must be nonempty")
    ids = []
    for row in rows:
        verify_episode(row, bridge)
        public = public_challenge(row)
        public_id = public_challenge_id(public)
        if row.get("public_id") != public_id:
            raise ValueError("private public-ID binding mismatch")
        if (path / "public" / f"{public_id}.json").read_bytes() != public_challenge_bytes(public):
            raise ValueError("public bytes differ from their exact visible projection")
        ids.append(public_id)
    if ids != sorted(set(ids)):
        raise ValueError("batch must be sorted and visibly distinct")
    if sorted(item.name for item in (path / "public").iterdir()) != [f"{value}.json" for value in ids]:
        raise ValueError("unexpected public files")
    expected = {
        "episode_count": len(rows),
        "public_ids": ids,
        "demonstration_counts": [len(row["train"]) for row in rows],
        "query_counts": [len(row["test"]) for row in rows],
        "label_count": sum(len(row[split]) for row in rows for split in ("train", "test")),
        "settings_exercised": sorted({row["edge_cap"] for row in rows}),
    }
    for key, value in expected.items():
        if report.get(key) != value:
            raise ValueError(f"verification report field {key} differs from replay")
    if report.get("schema") != f"{TASK_ID}-edge-cap-parametric-v1":
        raise ValueError("verification report schema mismatch")
    if report.get("training_admitted") is not False:
        raise ValueError("prototype report must not claim training admission")
    return {"verified_episodes": len(rows), "public_ids": ids}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--edge-cap", choices=tuple(PROGRAMS), default=None)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=QUERY_COUNT)
    args = parser.parse_args(argv)
    with open_bridge() as bridge:
        episodes = [
            build_episode(
                bridge,
                seed=seed,
                edge_cap=args.edge_cap,
                n_train=args.demos,
                n_test=args.queries,
            )
            for seed in args.seeds
        ]
        report = write_batch(episodes, args.out.resolve(), bridge)
        verified = verify_batch(args.out.resolve(), bridge)
    print(json.dumps({
        "out": str(args.out.resolve()),
        "episodes": report["episode_count"],
        "settings": report["settings_exercised"],
        "public_ids": verified["public_ids"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
