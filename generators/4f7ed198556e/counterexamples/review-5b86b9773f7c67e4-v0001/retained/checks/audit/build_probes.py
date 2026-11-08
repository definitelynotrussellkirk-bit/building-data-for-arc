from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path


def stamp_color5_only(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = [[0] * (2 * w) for _ in range(2 * h)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 5:
                out[2*r][2*c] = 1
                out[2*r][2*c+1] = 2
                out[2*r+1][2*c] = 2
                out[2*r+1][2*c+1] = 1
    return out


def fill_every_nonzero_bbox(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    colors: list[int] = []
    for row in grid:
        for value in row:
            if value and value not in colors:
                colors.append(value)
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                out[r][c] = color
    return out


def audit_4f() -> None:
    task = "4f7ed198556e"
    gen, path = load(task)
    outdir = PACKET / "checks" / "audit" / task
    witness = gen.generate(17, 0, difficulty="medium", texture="no_triggers")
    if not any(value not in {0, 5} for row in witness for value in row):
        raise AssertionError("expected advertised no_triggers texture to emit non-5 foreground")
    (outdir / "input.json").write_text(json.dumps(witness) + "\n")
    rival = stamp_color5_only(witness)
    (outdir / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")

    support = {}
    for band in ("easy", "medium", "hard"):
        sizes = {}
        palettes = set()
        for index in range(300):
            grid = gen.generate(1001, index, difficulty=band)
            sizes[f"{len(grid)}x{len(grid[0])}"] = sizes.get(f"{len(grid)}x{len(grid[0])}", 0) + 1
            palettes.update(value for row in grid for value in row)
        support[band] = {"draws": 300, "sizes": sizes, "observed_values": sorted(palettes)}

    base = gen.generate(777, 11, difficulty="medium")
    override_results = {}
    probes = {
        "grid_size": 3,
        "trigger_count": 1,
        "trigger_layout": "diagonal",
        "filler_pattern": "mixed_decoy",
        "filler_palette_size": 6,
        "unknown_axis": "accepted?",
    }
    for key, value in probes.items():
        try:
            candidate = gen.generate(777, 11, difficulty="medium", **{key: value})
            override_results[key] = {"accepted": True, "identical_to_base": candidate == base}
        except Exception as exc:
            override_results[key] = {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}

    payload = {
        "task_id": task,
        "generator_sha256": sha256(path),
        "version": getattr(gen, "VERSION", None),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "witness": {
            "seed": 17,
            "sample_index": 0,
            "difficulty": "medium",
            "overrides": {"texture": "no_triggers"},
            "input": witness,
            "self_check": gen.self_check(copy.deepcopy(witness)),
            "rival": "stamp only color 5; ignore every other nonzero color",
            "rival_output": rival,
            "generated_by_advertised_texture": True,
        },
        "ordinary_support": support,
        "override_probe": {
            "seed": 777,
            "sample_index": 11,
            "difficulty": "medium",
            "base": base,
            "results": override_results,
        },
    }
    (outdir / "probe.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def audit_e3() -> None:
    task = "e3a2ff6ea587"
    gen, path = load(task)
    outdir = PACKET / "checks" / "audit" / task
    witness = [[0] * 10 for _ in range(7)]
    for r, c in ((0, 0), (0, 3), (2, 0), (2, 3)):
        witness[r][c] = 2
    for r, c in ((4, 5), (4, 8), (6, 5)):
        witness[r][c] = 4
    (outdir / "input.json").write_text(json.dumps(witness) + "\n")
    rival = fill_every_nonzero_bbox(witness)
    (outdir / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")

    support = {}
    for band in ("easy", "medium", "hard"):
        qualifying = 0
        nonqualifying = 0
        draws = 300
        for index in range(draws):
            grid = gen.generate(2002, index, difficulty=band)
            colors = sorted({value for row in grid for value in row if value})
            for color in colors:
                cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
                rs = [r for r, _ in cells]; cs = [c for _, c in cells]
                corners = {(min(rs), min(cs)), (min(rs), max(cs)), (max(rs), min(cs)), (max(rs), max(cs))}
                if len(cells) == 4 and set(cells) == corners:
                    qualifying += 1
                else:
                    nonqualifying += 1
        support[band] = {
            "draws": draws,
            "qualifying_nonzero_colors": qualifying,
            "nonqualifying_nonzero_colors": nonqualifying,
        }

    base = gen.generate(888, 9, difficulty="medium")
    probes = {
        "palette_kind": "warm",
        "texture": "cool",
        "palette_size": 1,
        "position_bias": "spread",
        "n_distinct_colors": 1,
        "rect_area": "mixed",
        "unknown_axis": "accepted?",
    }
    override_results = {}
    for key, value in probes.items():
        try:
            candidate = gen.generate(888, 9, difficulty="medium", **{key: value})
            override_results[key] = {"accepted": True, "identical_to_base": candidate == base}
        except Exception as exc:
            override_results[key] = {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}

    payload = {
        "task_id": task,
        "generator_sha256": sha256(path),
        "version": getattr(gen, "VERSION", None),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "witness": {
            "input": witness,
            "self_check": gen.self_check(copy.deepcopy(witness)),
            "rival": "fill the bounding box of every nonzero color, regardless of exact-four-corner qualification",
            "rival_output": rival,
            "inside_validator_domain": gen.self_check(copy.deepcopy(witness)) == [],
            "inside_ordinary_generator_domain": False,
        },
        "ordinary_support": support,
        "override_probe": {
            "seed": 888,
            "sample_index": 9,
            "difficulty": "medium",
            "base": base,
            "results": override_results,
        },
    }
    (outdir / "probe.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    audit_4f()
    audit_e3()
