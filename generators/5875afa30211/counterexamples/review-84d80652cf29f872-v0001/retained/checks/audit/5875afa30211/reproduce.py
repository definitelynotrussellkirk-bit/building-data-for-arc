from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "repo"
TASK = "5875afa30211"
GEN_PATH = ROOT / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_gen", GEN_PATH)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)

seed, sample_index = 123, 4
base = gen.generate(seed, sample_index, size=6)
ignored_palette = gen.generate(seed, sample_index, size=6, palette_size=1)
ignored_distinct = gen.generate(seed, sample_index, size=6, n_distinct_colors=1)
ignored_typo = gen.generate(seed, sample_index, size=6, typo_axis="silently accepted")

raised = []
for kwargs in (
    {"size": 4, "cell_count": 1},
    {"size": 12, "cell_count": 30},
):
    try:
        gen.generate(seed, sample_index, **kwargs)
        result = {"kwargs": kwargs, "status": "returned"}
    except Exception as exc:
        result = {
            "kwargs": kwargs,
            "status": "raised",
            "error": f"{type(exc).__name__}: {exc}",
        }
    raised.append(result)

nonzero_colors = lambda grid: sorted({value for row in grid for value in row if value != 0})
payload = {
    "schema": "arc-review-audit-override-probe-v1",
    "task_id": TASK,
    "generator_version": gen.VERSION,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "seed": seed,
    "sample_index": sample_index,
    "declared_axes": gen.AXES,
    "range_failures": raised,
    "ignored_override_cases": [
        {
            "kwargs": {"size": 6, "palette_size": 1},
            "same_as_baseline": ignored_palette == base,
            "observed_nonzero_colors": nonzero_colors(ignored_palette),
        },
        {
            "kwargs": {"size": 6, "n_distinct_colors": 1},
            "same_as_baseline": ignored_distinct == base,
            "observed_nonzero_colors": nonzero_colors(ignored_distinct),
        },
        {
            "kwargs": {"size": 6, "typo_axis": "silently accepted"},
            "same_as_baseline": ignored_typo == base,
        },
    ],
    "baseline_grid": base,
    "finding": (
        "Advertised exact controls are not a truthful callable contract: legal endpoint overrides can raise, "
        "palette_size/n_distinct_colors are ignored while five colors are emitted, and an unknown key is silently accepted."
    ),
    "command": "PYTHONPATH=repo/shared/runtime:repo python3 checks/audit/5875afa30211/reproduce.py",
    "cwd": "packet root",
}
(HERE / "finding.json").write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps({"range_failures": raised, "ignored": payload["ignored_override_cases"]}, indent=2))
