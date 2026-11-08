"""Proposed task-local rule family, outside the production generator contract."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import re
import sys

from arcpuzzles.catalog import Catalog
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "b3d7f3a15b3d"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[2]
SETTINGS = tuple((direction, threshold) for direction in
                 ("both", "horizontal", "vertical") for threshold in (2, 3))


def validate_settings(direction, min_anchors):
    if type(direction) is not str or direction not in {"both", "horizontal", "vertical"}:
        raise ValueError("direction must be both, horizontal, or vertical")
    if type(min_anchors) is not int or min_anchors not in (2, 3):
        raise ValueError("min_anchors must be integer 2 or 3")


@lru_cache(maxsize=1)
def canonical_rule():
    """Read authoring authority through the supported catalog, never solve data."""
    variants = Catalog(ROOT).get(TASK_ID)["variants"]
    rules = {row["program_solution"] for row in variants if row.get("program_solution")}
    if len(rules) != 1:
        raise RuntimeError("expected one unambiguous canonical reference program")
    return rules.pop()


def emit_rule(direction="both", min_anchors=2):
    """Emit exact executable text, preserving canonical bytes at default."""
    validate_settings(direction, min_anchors)
    source = canonical_rule()
    if (direction, min_anchors) == ("both", 2):
        return source
    for indices, disabled in (("js", direction == "vertical"),
                              ("is", direction == "horizontal")):
        pattern = rf"\(<\s+\(length\s+{indices}\)\s+2\)"
        replacement = f"(or {'#t' if disabled else '#f'} (< (length {indices}) {min_anchors}))"
        source, count = re.subn(pattern, replacement, source)
        if count != 1:
            raise RuntimeError(f"canonical program structure changed: expected one {indices} threshold")
    return source


class _Verifier:
    def __init__(self):
        self.bridge = RacketBridge()

    def apply(self, program, grid):
        # This family emits a complete lambda with its own geometry bindings;
        # no free g/h/w, dict literals, or for/X shorthand needs conversion.
        body = strip_rule_wrapper(program)
        if not body.startswith("(lambda (g)"):
            raise ValueError("prototype accepts only the emitted self-contained lambda")
        self.bridge.define_grid("g", grid)
        return self.bridge.eval_text(f"({body} g)")

    def close(self):
        self.bridge.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def open_verifier():
    return _Verifier()


def grid_key(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def apply_python(grid, direction="both", min_anchors=2):
    """Auditing mirror for lawful framed inputs; Racket remains label authority."""
    validate_settings(direction, min_anchors)
    h, w = len(grid), len(grid[0])
    if h < 6 or w < 6 or (h-1) % 5 or (w-1) % 5 or any(len(row) != w for row in grid):
        raise ValueError("expected rectangular stride-five framed input")
    nr, nc = (h-1)//5, (w-1)//5
    vals = [grid[1+5*i+dr][1+5*j+dc] for i in range(nr) for j in range(nc)
            for dr in (1,2) for dc in (1,2)]
    common = Counter(vals).most_common(1)[0][0]
    colors = sorted({v for row in grid for v in row} - {0, common})
    result = deepcopy(grid)
    for color in colors:
        for dr in (1,2):
            for dc in (1,2):
                if direction != "vertical":
                    for i in range(nr):
                        anchors = [j for j in range(nc) if grid[1+5*i+dr][1+5*j+dc] == color]
                        if len(anchors) >= min_anchors:
                            for j in range(min(anchors), max(anchors)+1):
                                result[1+5*i+dr][1+5*j+dc] = color
                if direction != "horizontal":
                    for j in range(nc):
                        anchors = [i for i in range(nr) if grid[1+5*i+dr][1+5*j+dc] == color]
                        if len(anchors) >= min_anchors:
                            for i in range(min(anchors), max(anchors)+1):
                                result[1+5*i+dr][1+5*j+dc] = color
    return result


def _draw_input(rng):
    """Four independent channels witness H2, H3, V2, V3 in every scene."""
    nr, nc = rng.choice(((4,4), (4,5), (5,4), (5,5)))
    border, common, color_h, color_v = rng.sample(range(1,10), 4)
    grid = [[0] * (5*nc+1) for _ in range(5*nr+1)]
    for i in range(nr):
        for j in range(nc):
            for dr in range(4):
                for dc in range(4):
                    grid[1+5*i+dr][1+5*j+dc] = border if dr in (0,3) or dc in (0,3) else common
    offsets = [(1,1), (1,2), (2,1), (2,2)]
    rng.shuffle(offsets)
    for (direction, count), (dr,dc) in zip((("h",2),("h",3),("v",2),("v",3)), offsets):
        extent = nc if direction == "h" else nr
        start = rng.randrange(extent-3)
        stop = rng.randrange(start+3, extent)
        anchors = [start, stop]
        if count == 3:
            anchors.append(rng.randrange(start+1, stop))
        line = rng.randrange(nr if direction == "h" else nc)
        for anchor in anchors:
            i, j = (line, anchor) if direction == "h" else (anchor, line)
            grid[1+5*i+dr][1+5*j+dc] = color_h if direction == "h" else color_v
    return grid


def identify_from_demos(demos, verifier):
    """Exhaust all six settings using ONLY labeled demonstrations."""
    if not demos or any(set(pair) != {"input", "output"} for pair in demos):
        raise ValueError("identification requires nonempty input/output demonstrations only")
    survivors = []
    for direction, threshold in SETTINGS:
        rule = emit_rule(direction, threshold)
        if all(verifier.apply(rule, pair["input"]) == pair["output"] for pair in demos):
            survivors.append({"direction": direction, "min_anchors": threshold})
    return survivors


def generate_episode(seed, *, direction=None, min_anchors=None, n_train=3, n_test=4, verifier=None):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(n_train) is not int or not 3 <= n_train <= 128:
        raise ValueError("n_train must be an integer in 3..128")
    if type(n_test) is not int or not 1 <= n_test <= 128:
        raise ValueError("n_test must be an integer in 1..128")
    rng = random.Random(seed)
    # Draw once, before any input draws; explicit values override only that field.
    sampled_direction, sampled_threshold = rng.choice(SETTINGS)
    direction = sampled_direction if direction is None else direction
    min_anchors = sampled_threshold if min_anchors is None else min_anchors
    validate_settings(direction, min_anchors)
    params = {"direction": direction, "min_anchors": min_anchors}
    rule = emit_rule(direction, min_anchors)
    owned = verifier is None
    runner = open_verifier() if owned else verifier
    try:
        pairs, seen = [], set()
        attempts = 0
        while len(pairs) < n_train+n_test:
            attempts += 1
            if attempts > 100*(n_train+n_test):
                raise RuntimeError("distinct-input sampling budget exhausted")
            grid = _draw_input(rng)
            key = grid_key(grid)
            if key in seen:
                continue
            seen.add(key)
            output = runner.apply(rule, grid)
            if output != apply_python(grid, direction, min_anchors):
                raise RuntimeError("Python/Racket mismatch")
            pairs.append({"input": grid, "output": output})
        train = pairs[:n_train]
        survivors = identify_from_demos(train, runner)
        if survivors != [params]:
            raise RuntimeError(f"demonstrations fail parameter identification: {survivors}")
        return {"public": {"train": train, "test": [{"input": p["input"]} for p in pairs[n_train:]]},
                "private": {"seed": seed, "parameters": params, "rule": rule,
                            "rule_sha256": hashlib.sha256(rule.encode()).hexdigest(),
                            "query_outputs": [p["output"] for p in pairs[n_train:]],
                            "demo_only_survivors": survivors,
                            "input_sha256": [grid_key(p["input"]) for p in pairs],
                            "n_train": n_train, "n_test": n_test, "sampling_attempts": attempts}}
    finally:
        if owned:
            runner.close()


def _json_bytes(value):
    return (json.dumps(value, separators=(",", ":")) + "\n").encode("utf-8")


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def _public_export_plan(episodes):
    """Validate and sort a batch before any public/private files are written."""
    planned = []
    seen = {}
    for episode in episodes:
        if not isinstance(episode, dict) or set(episode) != {"public", "private"}:
            raise ValueError("episode must contain exactly public and private records")
        public, private = episode["public"], episode["private"]
        if not isinstance(private, dict) or type(private.get("rule")) is not str:
            raise ValueError("private episode record must contain an exact rule string")
        visible = public_challenge_bytes(public)
        public_id = public_challenge_id(public)
        if hashlib.sha256(visible).hexdigest() != public_id:
            raise RuntimeError("public challenge ID does not hash the written bytes")
        if public_id in seen:
            if seen[public_id] == visible:
                raise ValueError(f"duplicate public payload: {public_id}")
            raise RuntimeError(f"public challenge ID collision: {public_id}")
        seen[public_id] = visible

        public_rel = Path("public") / f"{public_id}.json"
        private_rel = Path("private") / public_id / "private.json"
        rule_rel = Path("private") / public_id / "rule.rkt"
        private_record = dict(private)
        rule = private_record.pop("rule")
        private_record.update(public_id=public_id, public_path=public_rel.as_posix())
        planned.append({
            "public_id": public_id,
            "public_rel": public_rel,
            "public_bytes": visible,
            "private_rel": private_rel,
            "private_record": private_record,
            "private_bytes": _json_bytes(private_record),
            "rule_rel": rule_rel,
            "rule_bytes": rule.encode("utf-8"),
        })
    return sorted(planned, key=lambda row: row["public_id"])


def write_episode_batch(out, episodes):
    """Write visible challenges by content ID and controller data separately."""
    out = Path(out)
    plan = _public_export_plan(episodes)
    rows = []
    for item in plan:
        public_id = item["public_id"]
        public_rel = item["public_rel"]
        private_rel = item["private_rel"]
        rule_rel = item["rule_rel"]
        private_record = item["private_record"]

        public_path = out / public_rel
        public_path.parent.mkdir(parents=True, exist_ok=True)
        public_path.write_bytes(item["public_bytes"])

        private_path = out / private_rel
        private_path.parent.mkdir(parents=True, exist_ok=True)
        private_path.write_bytes(item["private_bytes"])
        rule_path = out / rule_rel
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_bytes(item["rule_bytes"])

        rows.append({
            "public_id": public_id,
            "public_path": public_rel.as_posix(),
            "private_path": private_rel.as_posix(),
            "rule_path": rule_rel.as_posix(),
            **{key: value for key, value in private_record.items()
               if key not in {"query_outputs", "public_id", "public_path"}},
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7321)
    parser.add_argument("--n-train", type=int, default=3)
    parser.add_argument("--n-test", type=int, default=4)
    parser.add_argument("--direction", choices=("both", "horizontal", "vertical"))
    parser.add_argument("--min-anchors", type=int, choices=(2,3))
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.all_settings and (args.direction is not None or args.min_anchors is not None):
        parser.error("--all-settings cannot be combined with a setting override")
    settings = SETTINGS if args.all_settings else ((args.direction, args.min_anchors),)
    report = {"status": "proposed prototype; no production approval", "seed": args.seed,
              "payload_command": " ".join(sys.argv), "episodes": [],
              "limits": ["Bounded task-local evidence; no production parametric API or admission.",
                         "Samplers use collision-free four-channel witnesses on 4..5 by 4..5 cells.",
                         "Demonstration identifiability is against these six settings only."]}
    with open_verifier() as verifier:
        pairs = canonical_pairs(TASK_ID, root=ROOT)
        for pair in pairs:
            actual = verifier.apply(emit_rule(), pair["input"])
            if actual != pair["output"] or apply_python(pair["input"]) != actual:
                raise RuntimeError("default canonical parity failed")
        report["canonical_parity"] = {"passed": len(pairs), "total": len(pairs),
                                       "unique_inputs": len({grid_key(p["input"]) for p in pairs})}
        contrast_input = _draw_input(random.Random(args.seed))
        contrast = {"input": contrast_input, "executed_settings": []}
        for direction, threshold in SETTINGS:
            output = verifier.apply(emit_rule(direction, threshold), contrast_input)
            contrast["executed_settings"].append({"direction": direction, "min_anchors": threshold,
                                                  "output": output, "output_sha256": grid_key(output)})
        if len({row["output_sha256"] for row in contrast["executed_settings"]}) != 6:
            raise RuntimeError("contrast scene does not distinguish all six executed rules")
        _write_json(args.out / "contrast-private.json", contrast)
        episodes = [
            generate_episode(args.seed+index, direction=direction, min_anchors=threshold,
                             n_train=args.n_train, n_test=args.n_test, verifier=verifier)
            for index, (direction, threshold) in enumerate(settings)
        ]
        report["episodes"] = write_episode_batch(args.out, episodes)
    sources = [Path(__file__), Path(__file__).with_name("README.md"), HOME/"tests/test_parametric.py",
               HOME/"generator.py", ROOT/"shared/runtime/arc_repl/racket_bridge.py",
               ROOT/"shared/runtime/puzzle_generators/rule_wrap.py"]
    report["source_sha256"] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sources}
    report["canonical_rule_sha256"] = hashlib.sha256(canonical_rule().encode()).hexdigest()
    evidence_files = [args.out / "contrast-private.json"]
    evidence_files.extend(args.out / row[key] for row in report["episodes"]
                          for key in ("public_path", "private_path", "rule_path"))
    report["files_sha256"] = {str(p.relative_to(args.out)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in evidence_files}
    _write_json(args.out / "report.json", report)
    print(json.dumps({"canonical_parity": report["canonical_parity"], "episodes": len(report["episodes"]),
                      "n_train": args.n_train, "n_test": args.n_test, "out": str(args.out)}))


if __name__ == "__main__":
    main()
