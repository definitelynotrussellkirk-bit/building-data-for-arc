"""Focused executable proposal tests; copies tools to a disposable runtime."""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import inspect
import json
import sys
from types import SimpleNamespace
import unittest

sys.dont_write_bytecode = True  # Candidate imports must not add caches to evidence.

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
WORK = REPO.parent
sys.path.insert(0, str(REPO / "src"))
from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import prepare_runtime

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=("stock", "patched"), required=True)
parser.add_argument("--tag", default="", help="new alphanumeric evidence snapshot suffix")
parser.add_argument("--runtime-cache", type=Path,
                    default=WORK.parents[1] / "lint-proposal-runtime-cache",
                    help="scratch cache outside the return/evidence tree")
args = parser.parse_args()
if args.tag and not args.tag.isalnum():
    parser.error("--tag must be alphanumeric")
snapshot = args.mode + ("-" + args.tag if args.tag else "")
evidence = WORK / "checks/lint-proposal"
runtime_cache = args.runtime_cache.resolve()
if runtime_cache == WORK or WORK in runtime_cache.parents:
    parser.error("--runtime-cache must be outside WORK so disposable trees cannot enter returns")
runtime_cache.mkdir(parents=True, exist_ok=True)
runtime = runtime_cache / ("runtime-" + snapshot)
if not runtime.exists():
    prepare_runtime(Catalog(REPO), runtime, "12ace26107fd")
if args.mode == "patched":
    import subprocess
    patch = (HERE / "generator_defect_lint.patch").read_text()
    # The repository stores tools under shared/tools; prepare_runtime maps
    # exactly those bytes to scripts. Translate only the two diff headers.
    patch = patch.replace("a/shared/tools/", "a/scripts/").replace(
        "b/shared/tools/", "b/scripts/")
    expected = json.loads((HERE / "source-hashes.json").read_text())
    actual = hashlib.sha256((runtime / "scripts/generator_defect_lint.py").read_bytes()).hexdigest()
    if actual != expected["patched_sha256"]:
        if actual != expected["stock_sha256"]:
            raise ValueError("Disposable linter is neither the bound stock nor patched source")
        subprocess.run(["patch", "--batch", "--forward", "-p1"], input=patch,
                       text=True, cwd=runtime, check=True)
sys.path.insert(0, str(runtime))
from scripts import generator_defect_lint as lint
from scripts.canonical_profile_gate import normalized_rule_hash
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, load_selected_generator

module, source, generator_hash = load_selected_generator("12ace26107fd", root=runtime)
canonical = canonical_pairs("12ace26107fd", root=runtime)
with (runtime / "data/canonical/puzzles.jsonl").open() as handle:
    row = next(json.loads(line) for line in handle
               if json.loads(line).get("task_id") == "12ace26107fd")
rule_hash = normalized_rule_hash(row["program_solution"])
body = lint._rule_body(row["program_solution"])
bridge = RacketBridge(max_calls_before_restart=48)
def label(grid):
    bridge.define_grid("g", copy.deepcopy(grid))
    return lint._norm(bridge.eval_text(body))

grid = [[0] * 7 for _ in range(7)]
for r, c in ((2,3),(3,2),(3,3),(3,4),(4,3)):
    grid[r][c] = 2

def check(g, **kwargs):
    # Isolate the minimal-kind detector: model the intended min-three/area
    # boundary, rather than depending on a concurrently edited generator.
    n = sum(v != 0 for row in g for v in row)
    return [] if 3 <= n <= 14 else ["outside this focused fixture domain"]

decl = {name: {"justification":
    "The selected onion rule accepts connected solid shapes; four cells "
    "form one nonempty shell and produce a single count of four.",
    "rule_hash": rule_hash, "expected_output": [[4]]}
    for name in ("solid_2x2", "short_line")}

def run(declarations=decl, *, reference=label, current_hash=rule_hash,
        checker=check, input_grid=grid):
    m = SimpleNamespace(self_check=checker, LAWFUL_MINIMAL_PROBES=declarations)
    kwargs = dict(canonical_train=[(p["input"], p["output"])
                                  for p in canonical if p["split"] == "train"],
                  reference_label=reference, rule_hash=current_hash,
                  validation_notes=[])
    # Stock lacks the feature: still exercise its real behavior and fail the
    # expected exemption assertion, instead of failing on a missing keyword.
    parameters = inspect.signature(lint.probe_selfcheck_minimal_impostors).parameters
    result = lint.probe_selfcheck_minimal_impostors(
        m, [copy.deepcopy(input_grid)], ["medium"],
        **{k:v for k,v in kwargs.items() if k in parameters})
    return result, kwargs["validation_notes"]

class ProposalTests(unittest.TestCase):
    def test_live_reference_validates_only_named_lawful_shapes(self):
        warnings, notes = run()
        self.assertEqual(warnings, [])
        self.assertTrue(any("solid_2x2" in n and "short_line" in n for n in notes))
    def test_absent_declaration_preserves_stock_warning(self):
        warnings, _ = run({})
        self.assertIn("solid_2x2", " ".join(warnings))
        self.assertIn("short_line", " ".join(warnings))
    def test_missing_reference_fails_closed(self):
        self.assertIn("short_line", " ".join(run(reference=None)[0]))
    def test_stale_rule_hash_fails_closed(self):
        self.assertIn("short_line", " ".join(run(current_hash="stale")[0]))
    def test_wrong_expected_label_fails_closed(self):
        changed = copy.deepcopy(decl)
        changed["short_line"]["expected_output"] = [[3]]
        self.assertIn("short_line", " ".join(run(changed)[0]))
    def test_unknown_kind_and_blank_justification_are_not_waivers(self):
        changed = copy.deepcopy(decl)
        changed["all"] = changed.pop("short_line")
        changed["solid_2x2"]["justification"] = ""
        text = " ".join(run(changed)[0])
        self.assertIn("short_line", text)
        self.assertIn("solid_2x2", text)
    def test_undeclared_acceptances_remain_visible(self):
        warnings, _ = run(checker=lambda g, **kwargs: [])
        text = " ".join(warnings)
        self.assertIn("singleton", text)
        self.assertIn("all_background", text)
    def test_invalid_generated_label_fails_closed(self):
        def invalid_on_source(g):
            return [] if g == grid else label(g)
        self.assertIn("short_line", " ".join(run(reference=invalid_on_source)[0]))
    def test_probe_reference_error_fails_closed(self):
        def source_only(g):
            if g != grid:
                raise RuntimeError("deliberate probe labeling failure")
            return label(g)
        self.assertIn("short_line", " ".join(run(reference=source_only)[0]))
    def test_invalid_expected_grid_and_wrong_container_fail_closed(self):
        changed = copy.deepcopy(decl)
        changed["short_line"]["expected_output"] = [[12]]
        self.assertIn("short_line", " ".join(run(changed)[0]))
        self.assertIn("solid_2x2", " ".join(run(["solid_2x2"])[0]))
    def test_selected_generated_input_has_real_reference_output(self):
        g = module.generate(71, 0, difficulty="medium")
        self.assertTrue(lint._valid_arc_grid(label(g)))

try:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProposalTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    identity = {"mode": args.mode, "generator_sha256": generator_hash,
                "rule_hash": rule_hash,
                "rule_sha256": hashlib.sha256(row["program_solution"].encode()).hexdigest(),
                "linter_sha256": hashlib.sha256(Path(lint.__file__).read_bytes()).hexdigest(),
                "tests": result.testsRun, "failures": len(result.failures),
                "errors": len(result.errors), "success": result.wasSuccessful()}
    (evidence / (snapshot + "-tests.json")).write_text(json.dumps(identity, indent=2)+"\n")
    if args.mode == "patched" and result.wasSuccessful():
        candidate = evidence / (snapshot + "-declared-candidate.py")
        candidate.write_text(source.read_text() + "\nLAWFUL_MINIMAL_PROBES = " + repr(decl) + "\n")
        report = lint.lint_one("12ace26107fd", rules={"12ace26107fd":row["program_solution"]},
            canon={"12ace26107fd":[(p["input"],p["output"]) for p in canonical if p["split"]=="train"]},
            bridge=bridge, seeds=2, bands=["medium"], gen_file=candidate, fast=True)
        (evidence / (snapshot + "-integration.json")).write_text(json.dumps(report, indent=2)+"\n")
        remaining = [w["issue"] for w in report["warnings"]
                     if w["issue"].startswith("selfcheck-minimal-impostor:")]
        assert not any("solid_2x2" in w or "short_line" in w for w in remaining), remaining
        assert any("lawful-minimal-probes: current canonical rule" in n for n in report["notes"])
        print("PASS: lint_one live bridge adapter exempts only declared kinds; unrelated findings retained")
finally:
    bridge.shutdown()
sys.exit(0 if result.wasSuccessful() else 1)
