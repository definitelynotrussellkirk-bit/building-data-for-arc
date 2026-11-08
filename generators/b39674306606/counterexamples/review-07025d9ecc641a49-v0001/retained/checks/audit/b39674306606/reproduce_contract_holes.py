from pathlib import Path
import json
from reviewer_support import load_selected_generator

root = Path.cwd()
gen, _, _ = load_selected_generator("b39674306606", root=root)

accepted = []
for kwargs in (
    {"grid_h": 10.9},
    {"grid_h": "10"},
    {"pair_count": True},
    {"singleton_size": "4"},
):
    try:
        grid = gen.generate(271828, 0, **kwargs)
        accepted.append({"overrides": kwargs, "observed": gen.observe_overrides(grid)})
    except Exception as exc:
        accepted.append({"overrides": kwargs, "error": f"{type(exc).__name__}: {exc}"})

base = gen.generate(271828, 0)
padded = [row + [0] * 5 for row in base] + [[0] * (len(base[0]) + 5) for _ in range(5)]
result = {
    "generator": "b39674306606",
    "accepted_non_strict_overrides": accepted,
    "padded_dimensions": [len(padded), len(padded[0])],
    "declared_grid_h": gen.AXES["grid_h"]["valid"],
    "declared_grid_w": gen.AXES["grid_w"]["valid"],
    "padded_self_check": gen.self_check(padded),
    "padded_strict_canonical_like": gen.strict_canonical_like(padded),
    "padded_observed": gen.observe_overrides(padded),
}
print(json.dumps(result, indent=2, sort_keys=True))
