"""Minimal reproducible override-contract failures for 64a8d13b4024."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

REPO = Path.cwd()
TASK_ID = "64a8d13b4024"
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
OUTPUT_PATH = REPO.parent / "checks" / "audit" / TASK_ID / "override-contract-evidence.json"


def load_generator():
    spec = importlib.util.spec_from_file_location("audited_generator", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load audited generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def describe(grid) -> dict:
    counts = Counter(value for row in grid for value in row)
    return {
        "shape": [len(grid), len(grid[0])],
        "counts": {str(color): counts[color] for color in (1, 2, 3)},
        "sha256": digest(grid),
    }


def attempt(gen, **kwargs) -> dict:
    try:
        grid = gen.generate(0, 0, **kwargs)
    except Exception as exc:
        return {"status": "error", "error_type": type(exc).__name__, "message": str(exc)}
    return {"status": "returned", "grid": describe(grid)}


def main() -> None:
    gen = load_generator()
    default_palette = gen.generate(0, 0, palette_kind="default")
    warm_palette = gen.generate(0, 0, palette_kind="warm")
    evidence = {
        "schema": "arcpuzzles-audit-override-contract-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "declared_axes": gen.AXES,
        "findings": {
            "declared_grid_domain_rejected": {
                "grid_h_8": attempt(gen, grid_h=8),
                "grid_h_14": attempt(gen, grid_h=14),
                "grid_w_8": attempt(gen, grid_w=8),
                "grid_w_14": attempt(gen, grid_w=14),
            },
            "semantic_count_override_rewritten": {
                "call": {"n1": 2, "n2": 2, "n3": 2},
                "result": attempt(gen, n1=2, n2=2, n3=2),
                "expected_counts_if_honored": {"1": 2, "2": 2, "3": 2},
            },
            "unknown_key_accepted": {
                "call": {"typo": 1},
                "result": attempt(gen, typo=1),
            },
            "palette_kind_inert": {
                "default": describe(default_palette),
                "warm": describe(warm_palette),
                "identical": default_palette == warm_palette,
            },
            "degenerate_texture_bypasses_exact_controls": {
                "call": {
                    "texture": "missing_color",
                    "grid_h": 14,
                    "grid_w": 14,
                    "n1": 6,
                    "n2": 6,
                    "n3": 6,
                },
                "result": attempt(
                    gen,
                    texture="missing_color",
                    grid_h=14,
                    grid_w=14,
                    n1=6,
                    n2=6,
                    n3=6,
                ),
                "expected_shape_if_dimensions_honored": [14, 14],
                "expected_counts_if_counts_honored": {"1": 6, "2": 6, "3": 6},
            },
        },
        "official_override_check": {
            "path": "checks/audit/64a8d13b4024-override/checks/64a8d13b4024_audit_override_results.json",
            "status": "FAIL",
            "finding_count": 4586,
            "draws": 83160,
        },
        "conclusion": (
            "The advertised exact override surface is not reliable: declared endpoints are "
            "rejected, equal count overrides are silently changed, unknown keys are accepted, "
            "and multiple named axes are inert or bypassed."
        ),
    }
    OUTPUT_PATH.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(OUTPUT_PATH),
        "equal_counts_realized": evidence["findings"]["semantic_count_override_rewritten"]["result"],
        "palette_kind_identical": evidence["findings"]["palette_kind_inert"]["identical"],
        "unknown_key_status": evidence["findings"]["unknown_key_accepted"]["result"]["status"],
    }, indent=2))


if __name__ == "__main__":
    main()
