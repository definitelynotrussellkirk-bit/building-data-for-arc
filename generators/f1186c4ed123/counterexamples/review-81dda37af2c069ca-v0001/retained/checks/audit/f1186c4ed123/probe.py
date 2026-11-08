"""Findings-only public authoring probe for f1186c4ed123."""
import json
from pathlib import Path
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
TASK = "f1186c4ed123"
mod, source, digest = load_selected_generator(TASK, root=ROOT)
meta = Catalog(ROOT).describe(TASK)
base = dict(grid_h=11, grid_w=11, n_dots=3, template_variant=0,
            orientation="horizontal", palette_kind="broad")
draws = []
for size in (1, 6):
    ov = {**base, "palette_size": size}
    grid = mod.generate(0, 0, **ov)
    draws.append(dict(seed=0, sample_index=0, difficulty=None, overrides=ov,
                      input=grid, self_check=mod.self_check(grid),
                      actual_singleton_colors=sorted({v for row in grid for v in row if v not in (0, 1)})))

attempts = []
for difficulty, overrides in ((None, {"n_dots": 1}),
                              ("hard", {"n_dots": 7}),
                              (None, {"grid_h": 6})):
    try:
        grid = mod.generate(0, 0, difficulty=difficulty, **overrides)
        result = {"input": grid, "self_check": mod.self_check(grid)}
    except Exception as exc:
        result = {"exception_type": type(exc).__name__, "exception": str(exc)}
    attempts.append(dict(seed=0, sample_index=0, difficulty=difficulty,
                         overrides=overrides, **result))

pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
canonical = [dict(variant=p["variant"], split=p["split"], pair_index=p["pair_index"],
                  self_check=mod.self_check(p["input"])) for p in pairs]
report = dict(task_id=TASK, generator_sha256=digest, rule_hash=meta["rule_hash"],
              selected_source=str(source.relative_to(ROOT)),
              review_index_exists=(ROOT / "generators" / TASK / "evidence/review_index.json").exists(),
              axes=mod.AXES, draws=draws, identical_palette_size_inputs=draws[0]["input"] == draws[1]["input"],
              advertised_range_attempts=attempts, canonical_validator_checks=canonical,
              limits="Two seeds/indices are identical by construction: both probes use seed0/sample0. This is a focused override audit, not generation coverage or lesson identifiability certification.")
(HERE / "input.json").write_text(json.dumps(draws[0]["input"]) + "\n")
(HERE / "report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"generator_sha256": digest, "rule_hash": meta["rule_hash"],
                  "palette_size_inputs_identical": report["identical_palette_size_inputs"],
                  "actual_dot_colors": draws[0]["actual_singleton_colors"],
                  "attempts": attempts, "canonical_pairs": len(pairs)}, indent=2))
