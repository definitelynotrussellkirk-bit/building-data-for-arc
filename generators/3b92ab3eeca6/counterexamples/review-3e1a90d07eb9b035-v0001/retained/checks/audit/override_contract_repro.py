from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arcpuzzles.catalog import Catalog

ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit"
COMMAND = ["python3", "run_with_racket.py", "python3", "../checks/audit/override_contract_repro.py"]


def load(task_id: str):
    path = ROOT / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def colors(grid: list[list[int]]) -> list[int]:
    return sorted({v for row in grid for v in row if v})


def write(task_id: str, payload: dict[str, Any]) -> None:
    path = OUT / task_id / "override_contract_repro.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT.parent))


catalog = Catalog(ROOT)

# 3b92ab3eeca6: palette_size is advertised as an exact integer control but
# is never consumed. Two distinct legal values therefore produce identical
# bytes and neither constrains the observed number of colors.
task_id = "3b92ab3eeca6"
module, source = load(task_id)
base_args = {"seed": 101, "sample_index": 7, "difficulty": None}
grid_2 = module.generate(**base_args, palette_size=2)
grid_5 = module.generate(**base_args, palette_size=5)
row = catalog.describe(task_id)
write(task_id, {
    "schema": "arc-audit-override-reproducer-v1",
    "finding_kind": "reproduced_override_contract_defect",
    "task_id": task_id,
    "generator_path": str(source.relative_to(ROOT)),
    "generator_sha256": sha(source),
    "expected_generator_sha256": "d3f210b0c154ddf273dc74fd18bbc44be79e0b882e1982077fcd99ae330963a8",
    "rule_hash": row["rule_hash"],
    "cwd": "packet_root",
    "command": COMMAND,
    "seed": base_args["seed"],
    "sample_index": base_args["sample_index"],
    "difficulty": base_args["difficulty"],
    "advertised_axis": module.AXES["palette_size"],
    "overrides_compared": [{"palette_size": 2}, {"palette_size": 5}],
    "outputs_identical": grid_2 == grid_5,
    "observed_nonzero_colors": {"palette_size=2": colors(grid_2), "palette_size=5": colors(grid_5)},
    "self_check": {
        "palette_size=2": module.self_check(grid_2, meta={"palette_size": 2}),
        "palette_size=5": module.self_check(grid_5, meta={"palette_size": 5}),
    },
    "generated_grid_palette_size_2": grid_2,
    "generated_grid_palette_size_5": grid_5,
    "validator_domain": "Both outputs are accepted by the target self_check; the defect is that a documented exact override is ignored.",
    "target_modified": False,
})

# 2a5919c40197: palette_size has a documented global valid range 2..10,
# but an eagerly evaluated band-local draw validates even explicit overrides.
# Legal endpoint values therefore raise before generation in easy/hard bands.
task_id = "2a5919c40197"
module, source = load(task_id)
row = catalog.describe(task_id)
cases = []
for difficulty, value in [("easy", 10), ("hard", 2)]:
    item: dict[str, Any] = {
        "seed": 101,
        "sample_index": 7,
        "difficulty": difficulty,
        "overrides": {"palette_size": value},
    }
    try:
        item["grid"] = module.generate(101, 7, difficulty=difficulty, palette_size=value)
        item["raised"] = False
    except Exception as exc:  # exact public-call behavior is the evidence
        item["raised"] = True
        item["exception_type"] = type(exc).__name__
        item["exception"] = str(exc)
    cases.append(item)
write(task_id, {
    "schema": "arc-audit-override-reproducer-v1",
    "finding_kind": "reproduced_override_contract_defect",
    "task_id": task_id,
    "generator_path": str(source.relative_to(ROOT)),
    "generator_sha256": sha(source),
    "expected_generator_sha256": "51388816c44bdee20ae0191aa7ae70ede07e49a08c4ae853c313cdb62671dac3",
    "rule_hash": row["rule_hash"],
    "cwd": "packet_root",
    "command": COMMAND,
    "advertised_axis": module.AXES["palette_size"],
    "cases": cases,
    "validator_domain": "Both values are inside the documented global valid range 2..10; generation aborts before a grid exists because the implementation revalidates the explicit override against a narrower difficulty band.",
    "target_modified": False,
})
