"""Findings-only diagonal-connectivity audit; labels come from public apply CLI."""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root


TASK = "364829da8490"
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
EIGHT = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def eight_connected_background(grid):
    """Change only zero-region connectivity to 8; retain cardinal color boundary."""
    height, width = len(grid), len(grid[0])
    out, seen = deepcopy(grid), set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0 or (row, col) in seen:
                continue
            region, queue, colors = [], deque([(row, col)]), set()
            seen.add((row, col))
            while queue:
                r, c = queue.popleft()
                region.append((r, c))
                for dr, dc in EIGHT:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == 0 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
                for dr, dc in CARDINAL:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < height and 0 <= nc < width and grid[nr][nc]:
                        colors.add(grid[nr][nc])
            touches_border = any(r in (0, height - 1) or c in (0, width - 1) for r, c in region)
            if not touches_border and len(colors) == 1:
                color = next(iter(colors))
                for r, c in region:
                    out[r][c] = color
    return out


def load_generator(root):
    path = root / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("audit_target_364829da8490", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path


def prepare(root, destination):
    gen, source = load_generator(root)
    metadata = Catalog(root).describe(TASK)
    rows = []

    def add(grid, kind, replay):
        declared = {}
        for attribute in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
            for name, rival in getattr(gen, attribute, {}).items():
                declared[f"{attribute}:{name}"] = digest(rival(deepcopy(grid)))
        rows.append({"kind": kind, "replay": replay, "input": grid,
                     "input_sha256": digest(grid), "self_check": gen.self_check(grid),
                     "strict_canonical_like": gen.strict_canonical_like(grid),
                     "observed": gen.observe_overrides(grid),
                     "rival_8_connected_output": eight_connected_background(grid),
                     "declared_rival_output_sha256": declared})
        if "overrides" in replay:
            rows[-1]["self_check_original_override"] = gen.self_check(grid, meta={"overrides": replay["overrides"]})

    for pair in canonical_pairs(TASK, root=root):
        add(pair["input"], "canonical", {key: pair[key] for key in ("variant", "split", "pair_index")})
    for band in ("easy", "medium", "hard"):
        for seed in (17, 29):
            for index in range(4):
                add(gen.generate(seed, index, difficulty=band), "generated_default",
                    {"seed": seed, "sample_index": index, "difficulty": band, "overrides": {}})
    for index, profile in enumerate(gen.SCENE_PROFILES):
        for height, width in ((9, 11), (16, 18)):
            overrides = {"grid_h": height, "grid_w": width, "scene_profile": profile}
            add(gen.generate(17, index, difficulty="medium", **overrides), "generated_boundary",
                {"seed": 17, "sample_index": index, "difficulty": "medium", "overrides": overrides})

    add(gen.generate(0, 0, grid_h=16.9), "invalid_fractional_override_accepted",
        {"seed": 0, "sample_index": 0, "difficulty": None, "overrides": {"grid_h": 16.9}})

    base_parameters = {"seed": 17, "sample_index": 0, "difficulty": "medium",
                       "overrides": {"grid_h": 9, "grid_w": 11, "scene_profile": "rect_pair"}}
    base = gen.generate(17, 0, difficulty="medium", **base_parameters["overrides"])
    mutation = None
    for row in range(len(base)):
        for col in range(len(base[0])):
            color = base[row][col]
            if not color:
                continue
            for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                nr, nc = row + dr, col + dc
                if not (0 <= nr < len(base) and 0 <= nc < len(base[0])):
                    continue
                if base[nr][col] == color and base[row][nc] == color and base[nr][nc] == 0:
                    candidate = deepcopy(base)
                    candidate[row][col] = 0
                    if gen.self_check(candidate) == []:
                        mutation = {"input": candidate, "row": row, "col": col, "old": color, "new": 0}
                        break
            if mutation:
                break
        if mutation:
            break
    if mutation is None:
        raise RuntimeError("no accepted diagonal-corner mutation found")
    add(mutation["input"], "validator_accepted_corner_mutation",
        {**base_parameters, "mutation": {k: v for k, v in mutation.items() if k != "input"},
         "base_input": base, "base_input_sha256": digest(base)})
    unknown = {"__audit_unknown_axis__": 123}
    try:
        gen.generate(17, 0, difficulty="medium", **unknown)
    except (ValueError, TypeError, KeyError) as exc:
        unknown_result = {"rejected": True, "type": type(exc).__name__, "message": str(exc)}
    else:
        unknown_result = {"rejected": False}
    report = {"task_id": TASK, "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "generator_version": gen.VERSION, "catalog_rule_hash": metadata["rule_hash"],
              "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "unknown_override": unknown_result, "rows": rows}
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in (("prepared.json", report), ("inputs.json", [row["input"] for row in rows])):
        path = destination / name
        if path.exists():
            raise FileExistsError(path)
        path.write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    print(json.dumps({"rows": len(rows), "generator_sha256": report["generator_sha256"],
                      "unknown_override": unknown_result,
                      "mutation": rows[-1]["replay"]["mutation"],
                      "mutation_validation": rows[-1]["self_check"]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    prepare(find_root(__file__), args.out_dir)


if __name__ == "__main__":
    main()
