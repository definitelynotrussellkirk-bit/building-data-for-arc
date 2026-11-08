#!/usr/bin/env python3
"""Replay small, exact override-contract probes for audit target f1668de79fa1."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PACKET = Path(__file__).resolve().parents[3]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load_generator():
    path = REPO / "generators" / "f1668de79fa1" / "generator.py"
    spec = importlib.util.spec_from_file_location("audit_generator_f1668de79fa1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def grid_sha(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def summarized(grid, generator):
    return {
        "shape": [len(grid), len(grid[0])],
        "grid_sha256": grid_sha(grid),
        "self_check_errors": generator.self_check(grid),
    }


def attempt(generator, kwargs):
    try:
        grid = generator.generate(**kwargs)
    except Exception as exc:  # evidence records the exact acceptance/rejection behavior
        return {"accepted": False, "error_type": type(exc).__name__, "error": str(exc)}
    return {"accepted": True, **summarized(grid, generator)}


def main() -> None:
    generator, source = load_generator()
    common = {"seed": 19, "sample_index": 4, "difficulty": "hard"}
    requested_dimensions = attempt(generator, common | {"grid_h": 6, "grid_w": 8})
    unknown_key = attempt(generator, common | {"grid_height_typo": 6})
    no_template = attempt(generator, common | {"texture": "no_template"})
    default_palette = attempt(generator, common | {"palette_kind": "default"})
    warm_palette = attempt(generator, common | {"palette_kind": "warm"})

    evidence = {
        "schema": "arcpuzzles-audit-override-probe-v1",
        "finding_id": "A2",
        "task_id": "f1668de79fa1",
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "generator_version": generator.VERSION,
        "declared_axes": generator.AXES,
        "declared_helpful_textures": list(generator.HELPFUL_TEXTURES),
        "declared_degenerate_textures": list(generator.DEGENERATE_TEXTURES),
        "probe_command": {
            "cwd": "packet_root",
            "argv": ["python3", "checks/audit/f1668de79fa1/probe.py"],
            "exit_code": 0,
        },
        "probes": {
            "declared_dimensions": {
                "call": common | {"grid_h": 6, "grid_w": 8},
                "result": requested_dimensions,
                "defect_reproduced": requested_dimensions.get("accepted") is True
                    and requested_dimensions.get("shape") != [6, 8],
                "explanation": "AXES advertises grid_h/grid_w, but generate draws internal names height/width and does not consume the requested values.",
            },
            "unknown_key": {
                "call": common | {"grid_height_typo": 6},
                "result": unknown_key,
                "defect_reproduced": unknown_key.get("accepted") is True,
                "explanation": "An unrecognized override key is silently accepted instead of raising ValueError.",
            },
            "invalid_degenerate_texture": {
                "call": common | {"texture": "no_template"},
                "result": no_template,
                "defect_reproduced": no_template.get("accepted") is True
                    and bool(no_template.get("self_check_errors")),
                "explanation": "A declared texture returns a grid that violates the generator's own required template invariant.",
            },
            "palette_kind_pair": {
                "default_call": common | {"palette_kind": "default"},
                "default_result": default_palette,
                "warm_call": common | {"palette_kind": "warm"},
                "warm_result": warm_palette,
                "same_grid": default_palette.get("grid_sha256") == warm_palette.get("grid_sha256"),
                "explanation": "The implementation never reads palette_kind; the exhaustive override report is the authoritative dead-axis measurement.",
            },
        },
        "override_stage": {
            "cwd": "packet_root",
            "argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "check", "f1668de79fa1", "--stage", "override", "--timeout", "600", "--phase", "before", "--out", "../checks/audit/f1668de79fa1/override-check"],
            "exit_code": int((Path(__file__).resolve().parent / "override-check.rc").read_text().strip()),
            "result_path": "checks/audit/f1668de79fa1/override-check/result.json",
            "report_path": "checks/audit/f1668de79fa1/override-check/checks/f1668de79fa1_before_override_results.json",
        },
    }
    out = Path(__file__).resolve().parent / "override_probe.json"
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        name: probe.get("defect_reproduced", probe.get("same_grid"))
        for name, probe in evidence["probes"].items()
    }, indent=2))


if __name__ == "__main__":
    main()
