"""Check two values explicitly advertised by the selected AXES contract."""
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
gen, _, sha = load_selected_generator("80abb2f28d76", root=find_root(__file__))
cases = []
for overrides in ({"rect_w": 7}, {"rect_h": 6}):
    try:
        grid = gen.generate(0, 0, difficulty="hard", **overrides)
        result = {"generated": True, "input": grid}
    except Exception as exc:
        result = {"generated": False, "error": f"{type(exc).__name__}: {exc}"}
    result.update(seed=0, sample_index=0, difficulty="hard", overrides=overrides,
                  axis_contract={name: gen.AXES[name] for name in overrides})
    cases.append(result)
report = {"generator_sha256": sha, "cases": cases}
(HERE / "axis-result.json").write_text(json.dumps(report, indent=2)+"\n")
print(json.dumps(report, sort_keys=True))
