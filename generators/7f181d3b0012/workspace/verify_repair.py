"""Focused Racket labels and bounded adversarial checks for this repair."""
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from arcpuzzles import Catalog
from arcpuzzles.worker import lesson_check

HOME = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("repaired_generator", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
parser = argparse.ArgumentParser()
parser.add_argument("--out", required=True)
args = parser.parse_args()
report = {"task_id": gen.TASK_ID, "generator_sha256": hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest(), "canonical_counts": {}, "adversarial": {"unknown_key_cases": 0, "null_axes_preserve_default": 0, "family_cases": 0, "default_cases": 0}, "failures": []}
strict = lambda g: len(g) == 3 and len(g[0]) == 3 and {v for row in g for v in row} == {0, 1} and sum(map(sum, g)) in {2,4,5} and not gen._is_ud_sym(g) and not gen._is_lr_sym(g)
for band in ("easy", "medium", "hard"):
    report["canonical_counts"][band] = sum(strict(gen.generate(seed, seed, difficulty=band)) for seed in range(600))
    for seed in range(600, 900):
        g = gen.generate(seed, seed, difficulty=band)
        report["adversarial"]["default_cases"] += 1
        assert not gen._is_ud_sym(g), (band, seed, g)
        assert gen.self_check(g) == [], (band, seed, g)
for name in gen.AXES:
    assert gen.generate(23, 9, **{name: None}) == gen.generate(23, 9)
    report["adversarial"]["null_axes_preserve_default"] += 1
    for suffix in ("_typo", " "):
        for value in (None, 123):
            try:
                gen.generate(23, 9, **{name + suffix: value})
            except ValueError as exc:
                assert "unknown override" in str(exc)
            else:
                raise AssertionError((name, suffix, value))
            report["adversarial"]["unknown_key_cases"] += 1
from puzzle_generators.base import stable_rng
for seed in range(900, 1200):
    assert strict(gen._canonical_family(stable_rng(seed, "adversarial-family")))
    report["adversarial"]["family_cases"] += 1
# Exercise the bounded 200-attempt fallback rather than assuming random retries succeed.
class RejectedFamilyRng:
    def choice(self, options): return options[0]
    def sample(self, points, count): return [(1, 0), (1, 1)]
assert strict(gen._canonical_family(RejectedFamilyRng()))
report["adversarial"]["family_fallback"] = "strict"
catalog = Catalog()
puzzle = catalog.get(gen.TASK_ID)
canonical = puzzle["variants"][0]
pairs = [*canonical["train"]]
queries = canonical["test"]
if isinstance(queries, dict): queries = [queries]
pairs += queries
for band in ("easy", "medium", "hard"):
    for seed in range(8):
        g = gen.generate(seed, seed, difficulty=band)
        pairs.append({"input":g, "output":[*g, *reversed(g)]})
for kw in ({"texture":"single_row", "grid_w":2}, {"texture":"single_row", "grid_w":30, "palette_size":6}, {"texture":"ud_symmetric", "grid_h":3, "grid_w":2, "palette_size":4}, {"grid_h":15,"grid_w":30,"palette_size":6}, {"grid_h":1,"grid_w":6,"palette_size":6}):
    g = gen.generate(17, 3, **kw)
    pairs.append({"input":g, "output":[*g, *reversed(g)]})
labels = catalog.apply(gen.TASK_ID, [p["input"] for p in pairs], allow_unapproved=True, check_generator_domain=True)
for pair, label in zip(pairs, labels["results"], strict=True):
    assert label["valid_output"] and label["output"] == pair["output"], label
    assert label["generator_domain"]["status"] == "valid", label
report["racket"] = labels
report["racket_label_count"] = len(pairs)
# Symmetric queries are lawful when both rivals agree: do not reject on input
# symmetry alone. Isolate the rotation rival with a UD-asymmetric, LR-symmetric demo.
mkpair = lambda g: {"input":g, "output":[*g, *reversed(g)]}
symmetric = [[0,1,0],[1,0,1],[0,1,0]]
lr_symmetric = [[0,0,0],[0,1,0],[1,0,1]]
asymmetric = [[0,0,0],[1,0,1],[1,1,0]]
fixed = {"demonstration_policy":{"automatic":False,"declared_minimum":None}}
verdicts = {}
for name, episode in {"symmetric_all":{"train":[mkpair(symmetric)],"test":[mkpair(symmetric)]}, "rotation_only_ambiguity":{"train":[mkpair(lr_symmetric)],"test":[mkpair(asymmetric)]}}.items():
    saved = deepcopy(episode)
    verdicts[name] = lesson_check(gen, episode, fixed)
    assert episode == saved
assert verdicts["symmetric_all"]["status"] == "passed_declared_rivals"
assert verdicts["rotation_only_ambiguity"]["rivals"]["LESSON_COMPETITORS:duplicate_vertical"] == "refuted"
assert verdicts["rotation_only_ambiguity"]["rivals"]["LESSON_COMPETITORS:rotate180_bottom"] == "ambiguous"
report["lesson_adversarial"] = verdicts
Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k:v for k,v in report.items() if k not in {"racket","lesson_adversarial"}}, indent=2))
