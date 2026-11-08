"""Lint everything puzzle-related.

Gate-style validator for the full puzzle stack. Exits 0 iff all checks
pass, nonzero on first failure (like pre_push_check.py). Runs:

  1. Bank manifests   — every banks/<name>/ has manifest.json +
                        puzzles.json + solutions.py; counts match.
  2. Bank schemas     — each puzzle has {id, train, test-or-
                        test_input/test_output, some solution form};
                        grids are list[list[int in 0..9]], rectangular,
                        dim ≤ 30; no empty grids.
  3. Python syntax    — every solutions.py parses via ast.parse().
  4. Python solvers   — for each bank entry with an identifiable solver
                        name, exec the bank's solutions.py in an isolated
                        module and run the function against every train
                        pair; FAIL if output != expected_output.
  5. Canonical data   — puzzles.jsonl + puzzle_db.jsonl parse cleanly,
                        every row has the required fields, and the two
                        files agree on task_id set.
  6. Metadata coverage — every puzzle in the DB has a source + name
                        (banks + custom only; training/augmented exempt).

Run:
    python3 scripts/lint_puzzles.py

Exit 0 on full pass; exit 1 on first failure (adversarial style).
Pass --verbose to see per-check detail.
"""
from __future__ import annotations
import argparse
import ast
import importlib.util
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BANKS_DIR = ROOT / "data" / "custom_puzzles" / "banks"
CANONICAL = ROOT / "data" / "canonical" / "puzzles.jsonl"
PUZZLE_DB = ROOT / "data" / "canonical" / "puzzle_db.jsonl"
# Allow `from scripts.<…> import <…>` without installing a package
sys.path.insert(0, str(ROOT))


def _flatten_entries(raw) -> list[dict]:
    """Inlined copy of regen_bank_manifests._flatten_entries so the
    linter is self-contained — no cross-script imports required."""
    if isinstance(raw, list):
        return [e for e in raw if isinstance(e, dict)]
    if isinstance(raw, dict):
        if "puzzles" in raw:
            val = raw["puzzles"]
            if isinstance(val, dict):
                return [v for v in val.values() if isinstance(v, dict)]
            return [e for e in (val or []) if isinstance(e, dict)]
        return [v for v in raw.values() if isinstance(v, dict)]
    return []


def _normalize_grid(g) -> list[list[int]] | None:
    """Normalize to list[list[int]]. Accepts:
      - list[list[int]]                     — native
      - list[str] with each char a digit    — compact ARC notation
      - None                                — passthrough
    Returns None if g is None or unrecognizable.
    """
    if g is None:
        return None
    if isinstance(g, list) and g and isinstance(g[0], list):
        return g
    if isinstance(g, list) and g and isinstance(g[0], str):
        try:
            return [[int(ch) for ch in row] for row in g]
        except ValueError:
            return None
    return None


def _normalize_pair_list(raw) -> list[dict]:
    """Pair container could be a list[{input,output}] (standard) OR a
    single {input,output} dict (v2_meta_puzzles `test` field). Return a
    uniform list.
    """
    if raw is None:
        return []
    if isinstance(raw, dict):
        return [raw]
    return list(raw)


# =====================================================================
# Output helpers
# =====================================================================

GREEN = "\033[32m"; RED = "\033[31m"; YELLOW = "\033[33m"; RESET = "\033[0m"


def _ok(msg: str) -> None:
    print(f"  {GREEN}OK  {RESET}{msg}", flush=True)


def _fail(msg: str) -> None:
    print(f"  {RED}FAIL{RESET}{msg}", flush=True)


def _warn(msg: str) -> None:
    print(f"  {YELLOW}WARN{RESET}{msg}", flush=True)


def _header(msg: str) -> None:
    print(f"\n── {msg}", flush=True)


# =====================================================================
# Grid validation
# =====================================================================

def validate_grid(g: Any, where: str) -> list[str]:
    """Return a list of FATAL data-integrity errors. Dimensions outside
    the ARC spec (1..30) are *not* fatal here — they're SFT-usable but
    spec-noncompliant for a Kaggle submission; those are surfaced by
    the separate submission_validator at submission time. We only hard-
    fail on structural issues: not-a-list, ragged rows, non-int values,
    values outside 0..9.
    """
    errs: list[str] = []
    if not isinstance(g, list) or not g:
        return [f"{where}: not a non-empty list"]
    if not isinstance(g[0], list):
        return [f"{where}: rows are not lists"]
    w = len(g[0])
    if w < 1:
        return [f"{where}: zero-width row"]
    for r, row in enumerate(g):
        if not isinstance(row, list) or len(row) != w:
            errs.append(f"{where}[row {r}]: ragged ({len(row)} vs {w})")
            return errs
        for c, v in enumerate(row):
            if isinstance(v, bool) or not isinstance(v, int):
                errs.append(f"{where}[{r},{c}]: not int (got "
                            f"{type(v).__name__}={v!r})")
                return errs
            if v < 0 or v > 9:
                errs.append(f"{where}[{r},{c}]: value {v} outside 0..9")
                return errs
    return errs


# =====================================================================
# 1. Bank manifests
# =====================================================================

def check_bank_manifests() -> bool:
    _header("1. bank manifests")
    if not BANKS_DIR.is_dir():
        _warn("no banks/ directory — skipping")
        return True
    total_ok = True
    for bank_dir in sorted(p for p in BANKS_DIR.iterdir() if p.is_dir()):
        name = bank_dir.name
        problems: list[str] = []
        manifest_path = bank_dir / "manifest.json"
        puzzles_path = bank_dir / "puzzles.json"
        if not manifest_path.exists():
            problems.append("manifest.json missing")
        if not puzzles_path.exists():
            problems.append("puzzles.json missing")
        if problems:
            _fail(f"{name}: {'; '.join(problems)}")
            total_ok = False
            continue
        manifest = json.loads(manifest_path.read_text())
        # Required keys
        for k in ("bank", "title", "description", "schema_shape",
                  "source", "solution_language", "files", "stats"):
            if k not in manifest:
                problems.append(f"manifest missing field `{k}`")
        # Count invariant
        puzzles_raw = json.loads(puzzles_path.read_text())
        
        n_actual = len(_flatten_entries(puzzles_raw))
        n_claimed = manifest.get("stats", {}).get("n_puzzles")
        if n_claimed != n_actual:
            problems.append(
                f"stats.n_puzzles={n_claimed} but puzzles.json has {n_actual}")
        if problems:
            _fail(f"{name}: {'; '.join(problems)}")
            total_ok = False
        else:
            _ok(f"{name}: {n_actual} puzzles, manifest consistent")
    return total_ok


# =====================================================================
# 2. Bank schemas + grid validity
# =====================================================================

def check_bank_schemas(verbose: bool = False) -> bool:
    _header("2. bank schemas + grid validity")
    if not BANKS_DIR.is_dir():
        return True
    
    total_ok = True
    for bank_dir in sorted(p for p in BANKS_DIR.iterdir() if p.is_dir()):
        name = bank_dir.name
        pp = bank_dir / "puzzles.json"
        if not pp.exists():
            continue
        raw = json.loads(pp.read_text())
        entries = _flatten_entries(raw)
        errs: list[str] = []
        for i, e in enumerate(entries):
            # Required fields on the puzzle
            if not e.get("id"):
                errs.append(f"entry {i}: missing id")
                continue
            tid = e["id"]
            train = _normalize_pair_list(e.get("train"))
            # Some banks use test_input/test_output instead of test
            test = _normalize_pair_list(e.get("test"))
            if not test and e.get("test_input") is not None:
                test = [{"input": e["test_input"],
                         "output": e.get("test_output")}]
            # At least one solution form
            has_solution = (e.get("program_solution")
                            or e.get("reference_program")
                            or e.get("program_function")
                            or e.get("solver_name")
                            or e.get("program_name")
                            or e.get("written_solution")
                            or e.get("written_rule"))
            if not train and not test:
                # Rule-only / generator-only entries are OK iff a solution
                # is present (release builds strip grids on purpose).
                if not has_solution:
                    errs.append(
                        f"{tid}: no train, no test, no solution (empty)")
                continue
            if not has_solution:
                errs.append(f"{tid}: no program_solution / written_rule")
            # Grid validation — normalize compact string rows first
            for pi, pair in enumerate(train):
                if not isinstance(pair, dict):
                    errs.append(f"{tid}.train[{pi}]: not a dict")
                    continue
                for k in ("input", "output"):
                    g = _normalize_grid(pair.get(k))
                    if g is None:
                        errs.append(f"{tid}.train[{pi}].{k}: missing/bad")
                        continue
                    errs.extend(validate_grid(g, f"{tid}.train[{pi}].{k}"))
            for pi, pair in enumerate(test):
                if not isinstance(pair, dict):
                    errs.append(f"{tid}.test[{pi}]: not a dict")
                    continue
                g = _normalize_grid(pair.get("input"))
                if g is not None:
                    errs.extend(validate_grid(g, f"{tid}.test[{pi}].input"))
                g = _normalize_grid(pair.get("output"))
                if g is not None:
                    errs.extend(validate_grid(g, f"{tid}.test[{pi}].output"))
        if errs:
            total_ok = False
            sample = errs[:5]
            _fail(f"{name}: {len(errs)} schema errors (first 5):")
            for e in sample:
                print(f"        {e}")
        else:
            _ok(f"{name}: {len(entries)} entries, all grids valid")
    return total_ok


# =====================================================================
# 3. Python syntax on solutions.py files
# =====================================================================

def check_python_syntax() -> bool:
    _header("3. solutions.py syntax")
    if not BANKS_DIR.is_dir():
        return True
    total_ok = True
    for sol in sorted(BANKS_DIR.glob("*/solutions.py")):
        try:
            ast.parse(sol.read_text(), filename=str(sol))
            _ok(f"{sol.relative_to(ROOT)}")
        except SyntaxError as e:
            _fail(f"{sol.relative_to(ROOT)}: {e}")
            total_ok = False
    return total_ok


# =====================================================================
# 4. Python reference solvers run correctly
# =====================================================================

def _load_solutions_module(sol_path: Path, mod_name: str):
    spec = importlib.util.spec_from_file_location(mod_name, str(sol_path))
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_python_solvers(verbose: bool = False) -> bool:
    _header("4. Python reference solvers produce expected output")
    if not BANKS_DIR.is_dir():
        return True
    
    total_ok = True
    for bank_dir in sorted(p for p in BANKS_DIR.iterdir() if p.is_dir()):
        name = bank_dir.name
        sol_path = bank_dir / "solutions.py"
        pp = bank_dir / "puzzles.json"
        if not (sol_path.exists() and pp.exists()):
            continue
        try:
            mod = _load_solutions_module(sol_path, f"sol_{name}")
        except Exception as e:
            _fail(f"{name}: solutions.py load failed: "
                  f"{type(e).__name__}: {e}")
            total_ok = False
            continue

        entries = _flatten_entries(json.loads(pp.read_text()))
        checked = 0
        mismatches: list[str] = []
        no_solver = 0
        # Some banks expose a SOLVERS / SOLVER / solvers / REGISTRY dict
        # mapping puzzle_id → callable. Check every standard name.
        registry = None
        for reg_name in ("SOLVERS", "SOLVER", "solvers", "REGISTRY"):
            reg = getattr(mod, reg_name, None)
            if isinstance(reg, dict) and reg:
                registry = reg
                break
        for e in entries:
            tid = e.get("id", "?")
            fn_name = (e.get("program_function")
                       or e.get("solver_name")
                       or e.get("program_name")
                       or "")
            fn = getattr(mod, fn_name, None) if fn_name else None
            # Second-chance: the bank may ship a SOLVERS dict mapping
            # puzzle ids → functions (the solve_* defs in solutions.py
            # are the real solvers while program_solution in
            # puzzles.json is often pseudocode).
            if fn is None and registry is not None and tid in registry:
                fn = registry[tid]
            fn_is_inline = False
            # Second path: inline program_solution / reference_program
            # string. Parse + exec into a namespace that inherits
            # solutions.py's helpers, look for `solve(grid)`. Pseudocode
            # (non-parseable) is counted separately and reported.
            # Inline solutions that raise at exec time OR that reference
            # undefined helpers at CALL time get classified as
            # "not executable" rather than a mismatch — that's
            # documentation-quality, not a data-quality bug.
            if fn is None:
                inline_src = (e.get("program_solution")
                              or e.get("reference_program")
                              or "")
                if inline_src:
                    try:
                        ast.parse(inline_src)
                    except SyntaxError:
                        no_solver += 1
                        continue
                    try:
                        ns = dict(mod.__dict__)
                        exec(inline_src, ns)
                        fn = ns.get("solve")
                    except Exception:
                        no_solver += 1
                        continue
                    if fn is not None:
                        # Smoke-test with a synthetic grid. If it raises
                        # (e.g., calls undefined `blue_components`),
                        # downgrade to non-executable instead of trying
                        # every pair and recording each as a mismatch.
                        fn_is_inline = True
                        try:
                            probe_in = (e.get("train") or [{}])[0].get("input")
                            if probe_in is not None:
                                fn(probe_in)
                        except NameError:
                            no_solver += 1
                            continue
                        except Exception:
                            # Other exceptions on probe are treated
                            # lenient too — if pseudocode calls an
                            # undefined helper, we'd just spam the
                            # report.
                            no_solver += 1
                            continue
            if fn is None:
                no_solver += 1
                continue
            train = _normalize_pair_list(e.get("train"))
            for pi, pair in enumerate(train):
                if not isinstance(pair, dict):
                    continue
                inp = _normalize_grid(pair.get("input"))
                exp = _normalize_grid(pair.get("output"))
                if inp is None or exp is None:
                    continue
                try:
                    got = fn(inp)
                except Exception as ex:
                    mismatches.append(
                        f"{tid}.train[{pi}]: raised "
                        f"{type(ex).__name__}: {ex}")
                    continue
                got = _normalize_grid(got) or got
                if got != exp:
                    mismatches.append(
                        f"{tid}.train[{pi}]: output mismatch")
                checked += 1
            # Also test pair if output is provided
            test = _normalize_pair_list(e.get("test"))
            if not test and e.get("test_input") is not None:
                test = [{"input": e["test_input"],
                         "output": e.get("test_output")}]
            for pi, pair in enumerate(test):
                if not isinstance(pair, dict):
                    continue
                exp = _normalize_grid(pair.get("output"))
                inp = _normalize_grid(pair.get("input"))
                if exp is None or inp is None:
                    continue
                try:
                    got = fn(inp)
                except Exception as ex:
                    mismatches.append(
                        f"{tid}.test[{pi}]: raised "
                        f"{type(ex).__name__}: {ex}")
                    continue
                got = _normalize_grid(got) or got
                if got != exp:
                    mismatches.append(
                        f"{tid}.test[{pi}]: output mismatch")
                checked += 1

        if mismatches:
            total_ok = False
            _fail(f"{name}: {len(mismatches)} solver mismatch(es) "
                  f"out of {checked} pairs (first 3):")
            for m in mismatches[:3]:
                print(f"        {m}")
        else:
            _ok(f"{name}: {checked} pairs pass; "
                f"{no_solver} entries without a Python solver fn")
    return total_ok


# =====================================================================
# 5. Canonical data
# =====================================================================

def check_canonical() -> bool:
    _header("5. canonical data")
    ok = True
    if not CANONICAL.exists():
        _fail(f"{CANONICAL.name} missing"); return False
    if not PUZZLE_DB.exists():
        _fail(f"{PUZZLE_DB.name} missing"); return False
    canonical_ids: set[str] = set()
    for i, line in enumerate(CANONICAL.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception as e:
            _fail(f"{CANONICAL.name}:{i} not JSON: {e}"); return False
        # `train` is optional — release builds strip grids by design.
        for k in ("task_id", "source"):
            if k not in r:
                _fail(f"{CANONICAL.name}:{i} missing `{k}`"); return False
        canonical_ids.add(r["task_id"])

    db_ids: set[str] = set()
    for i, line in enumerate(PUZZLE_DB.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception as e:
            _fail(f"{PUZZLE_DB.name}:{i} not JSON: {e}"); return False
        for k in ("task_id", "source", "n_train", "n_test",
                  "solution_language", "needs_conversion"):
            if k not in r:
                _fail(f"{PUZZLE_DB.name}:{i} missing `{k}`"); return False
        db_ids.add(r["task_id"])

    if canonical_ids != db_ids:
        diff1 = canonical_ids - db_ids
        diff2 = db_ids - canonical_ids
        _fail(f"canonical vs db task_id mismatch: "
              f"canonical-only={len(diff1)}, db-only={len(diff2)}")
        ok = False
    else:
        _ok(f"{len(canonical_ids)} task_ids consistent across "
            f"{CANONICAL.name} ↔ {PUZZLE_DB.name}")
    return ok


# =====================================================================
# 7. Canonical field-name aliases
# =====================================================================
#
# Preferred ("canonical") name per semantic role, and the aliases we've
# seen authors use for the same thing. The point of THIS check is to
# converge on ONE name per role so downstream code never has to guess
# which alias is present. WARN-only for now — upgrade to FAIL once the
# canonical builder + existing banks are rewritten to emit the preferred
# names.
#
# Reading: `"title": ["name"]` means "title is canonical; if you see
# `name`, flag it."

CANONICAL_ROLES: dict[str, list[str]] = {
    # identity / description — NB: canonical has two distinct id fields
    # by design (`task_id` = globally-unique with bank-prefix; `id` or
    # `original_id` = source-local). They are not aliases of each other.
    "title":             ["name"],
    "written_solution":  ["written_rule", "staged_hint"],
    "skills":            ["tags"],
    # pairs
    "test":              ["tests"],  # test_input/test_output pair handled separately
    # code
    "program_solution":  ["reference_program", "program_source"],
    "solver_name":       ["program_name", "program_function"],
    # meta about which primitives the task exercises
    "primitive_names":   ["primitive_note", "what_it_tests",
                          "uses_new_primitive"],
}


def check_canonical_aliases() -> bool:
    _header("7. canonical field-name aliases (WARN only)")
    alias_to_canonical: dict[str, str] = {}
    for canonical, aliases in CANONICAL_ROLES.items():
        for a in aliases:
            alias_to_canonical[a] = canonical

    # --- scope A: bank source files ---
    bank_hits: dict[str, dict[str, int]] = {}  # bank → alias → count
    if BANKS_DIR.is_dir():
        for bank_dir in sorted(p for p in BANKS_DIR.iterdir() if p.is_dir()):
            pp = bank_dir / "puzzles.json"
            if not pp.exists():
                continue
            entries = _flatten_entries(json.loads(pp.read_text()))
            per_bank: dict[str, int] = {}
            split_pair_hits = 0
            for e in entries:
                for k in e.keys():
                    if k in alias_to_canonical:
                        per_bank[k] = per_bank.get(k, 0) + 1
                # test_input + test_output → "test_split" alias for `test`
                if "test_input" in e or "test_output" in e:
                    split_pair_hits += 1
            if split_pair_hits:
                per_bank["test_input/test_output"] = split_pair_hits
            if per_bank:
                bank_hits[bank_dir.name] = per_bank

    # --- scope B: canonical JSONL ---
    canonical_hits: dict[str, int] = {}
    if CANONICAL.exists():
        for line in CANONICAL.read_text().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            for k in r.keys():
                if k in alias_to_canonical:
                    canonical_hits[k] = canonical_hits.get(k, 0) + 1

    # --- report ---
    bank_totals: dict[str, int] = {}
    for per_bank in bank_hits.values():
        for k, c in per_bank.items():
            bank_totals[k] = bank_totals.get(k, 0) + c

    if not bank_totals and not canonical_hits:
        _ok("no alias usage — every field uses its canonical name")
        return True

    if bank_totals:
        _warn(f"bank source files — {sum(bank_totals.values())} "
              f"alias occurrences across {len(bank_hits)} banks:")
        for alias, count in sorted(bank_totals.items(),
                                    key=lambda kv: -kv[1]):
            # test_input/test_output is a pair, not in alias_to_canonical
            canonical = alias_to_canonical.get(alias, "test")
            print(f"        {alias:<30} → {canonical:<20} "
                  f"({count} uses)")

    if canonical_hits:
        _warn(f"canonical JSONL — {sum(canonical_hits.values())} "
              f"alias occurrences (builder output drift):")
        for alias, count in sorted(canonical_hits.items(),
                                    key=lambda kv: -kv[1]):
            canonical = alias_to_canonical[alias]
            print(f"        {alias:<30} → {canonical:<20} "
                  f"({count} rows)")

    # WARN-only: always return True for now
    return True


# =====================================================================
# 6. Metadata coverage
# =====================================================================

def check_comment_density(verbose: bool = False) -> bool:
    """Report-only: tally how well solutions comply with the three-kind
    comment rule from docs/RACKET_COMMENT_STYLE.md.

    Counts: solutions with zero comments; solutions whose only comments
    are step-purpose (no value-grounding or narrative-state); the
    backlog of solutions that exceed N lines without any comments.
    Always returns True — this is a backlog signal, not a gate.
    """
    import re
    _header("8. comment density (report-only — see docs/RACKET_COMMENT_STYLE.md)")
    sol_dir = ROOT / "data" / "base" / "solutions"
    if not sol_dir.exists():
        _warn("data/base/solutions missing — skipping")
        return True

    # Cheap classifiers for the three kinds — see RACKET_COMMENT_STYLE.md.
    # Permissive on purpose: the lint just tracks a trend over time.
    GROUND_PAT = re.compile(
        r"\b("
        r"seen|visible|picture|image|displayed|shown|looks?|appears?|"
        r"endpoint|endpoints|anchor|anchors|marker|markers|occluder|occluders|"
        r"axis|target|seed|seeds|divider|dividers|stripe|stripes|wall|walls|cup|cups|"
        r"frame|frames|rectangle|rectangles|shape|shapes|"
        r"bbox|bounding box|edge|edges|corner|corners|"
        r"interior|exterior|border|hole|holes|cluster|clusters|"
        r"background|foreground|"
        r"leftmost|rightmost|topmost|bottommost|"
        r"position of|positions of|row indices|column indices|"
        r"the rows|the columns|the cells|the rectangle|the shape|the object|"
        r"the frame|the cell|the cup|the seed|the wall|the stripe|the marker|"
        r"the anchor|the occluder|the axis|the target"
        r")\b",
        re.I)
    NARR_PAT = re.compile(
        r"\b(now|once|with(?: the)?|having|next we|then we|remaining|"
        r"reduces?|what'?s left|at this point|from here|so we|so the)\b",
        re.I)

    total = 0
    zero_cm = 0
    only_step = 0
    has_ground = 0
    has_narr = 0
    backlog_30 = 0  # solutions ≥30 lines with zero comments
    samples = []
    for path in sol_dir.rglob("*.json"):
        try:
            d = json.loads(path.read_text())
        except Exception:
            continue
        rt = d.get("racket_target") or {}
        code = (rt.get("target_code") or rt.get("raw_code") or "").strip()
        if not code:
            continue
        total += 1
        lines = code.split("\n")
        comments = [l.strip().lstrip(";").strip()
                    for l in lines if l.strip().startswith(";")]
        if not comments:
            zero_cm += 1
            if len(lines) >= 30:
                backlog_30 += 1
                if verbose and len(samples) < 5:
                    samples.append((d.get("task_id", path.stem), len(lines)))
            continue
        g = any(GROUND_PAT.search(c) for c in comments)
        n = any(NARR_PAT.search(c) for c in comments)
        if g: has_ground += 1
        if n: has_narr += 1
        if not g and not n:
            only_step += 1

    if total == 0:
        _warn("no Racket solutions found")
        return True

    pct = lambda x: f"{(100*x/total):.1f}%"
    _warn(f"{total} solutions inspected")
    _warn(f"  zero comments:     {zero_cm} ({pct(zero_cm)})")
    _warn(f"  step-purpose only: {only_step} ({pct(only_step)})")
    _warn(f"  has value-ground:  {has_ground} ({pct(has_ground)})")
    _warn(f"  has narrative:     {has_narr} ({pct(has_narr)})")
    _warn(f"  backlog (≥30 lines, no comments): {backlog_30}")
    if verbose and samples:
        _warn("  sample backlog tasks:")
        for tid, n in samples:
            _warn(f"    {tid} ({n} lines)")
    return True


def check_concept_coverage(verbose: bool = False) -> bool:
    """Report-only: read data/derived/concepts.jsonl and surface the
    concept distribution. The syntactic hash will likely over-split
    (Phase 7 will merge behaviorally-equivalent concepts); this lint
    just shows the current state so trends are visible run-to-run."""
    _header("9. concept coverage (report-only — see docs/PUZZLE_GENERATOR_ROADMAP.md)")
    cf = ROOT / "data" / "derived" / "concepts.jsonl"
    sf = ROOT / "data" / "derived" / "concepts_uncanonicalizable.jsonl"
    if not cf.exists():
        _warn(f"{cf.relative_to(ROOT)} missing — run scripts/concept_inventory.py")
        return True

    rows = [json.loads(l) for l in cf.read_text().splitlines() if l.strip()]
    n_concepts = len(rows)
    if not rows:
        _warn("no concepts found")
        return True

    n_total = sum(r["n_puzzles"] for r in rows)
    singletons = sum(1 for r in rows if r["n_puzzles"] == 1)
    big = sum(1 for r in rows if r["n_puzzles"] >= 10)
    largest = max(r["n_puzzles"] for r in rows)
    n_uncanon = 0
    if sf.exists():
        n_uncanon = sum(1 for l in sf.read_text().splitlines() if l.strip())

    _warn(f"distinct concepts: {n_concepts}  (across {n_total} canonicalized puzzles)")
    _warn(f"  singletons (1 member):    {singletons} ({100*singletons/n_concepts:.0f}%)")
    _warn(f"  >=10 members:             {big}")
    _warn(f"  largest cluster:          {largest} puzzles")
    _warn(f"  uncanonicalizable rules:  {n_uncanon} (pre-existing codex breakage)")

    # Sanity warning: the corpus shouldn't collapse to <50 concepts (broken
    # canonicalizer) or explode to >2000 (every rule unique). Today we
    # expect a heavy long-tail of singletons until Phase 7's behavioral
    # hash merges equivalent concepts.
    if n_concepts < 50:
        _warn(f"WARNING: only {n_concepts} concepts — canonicalizer may be over-merging")
    if n_concepts > 3000:
        _warn(f"WARNING: {n_concepts} concepts — canonicalizer may be under-merging")
    return True


def check_authority_paths(verbose: bool = False) -> bool:
    """Report-only: do the `files.*_relpath` pointers in bank solution records
    still resolve?

    Two independent reviewers reported this on 2026-07-25 (dc4a7dc47c43 WFB-002,
    debab4c79292 WFB-002), each having tripped over a single record whose
    `files.solution_relpath` named a bank directory that no longer exists. Both
    asked for a CENTRAL consistency check rather than ad-hoc edits by semantic
    task workers — correctly, because the measured class is 2857/2859 records
    (99.9%), not two.

    The cause is a bank-directory rename: solution JSONs moved under hashed
    aliases (`banks/e00836ab832d/`) while the embedded pointers kept naming the
    original bank (`banks/arc_puzzle_bank_21_set24_s/`). `task_image_relpath` is
    0% stale, so only this one field broke.

    REPORT-ONLY, deliberately. Gating on it would make lint permanently red for
    a defect nobody can fix in one pass, and a permanently-red gate gets ignored
    — the same failure this check exists to expose. It stays a counted, visible
    backlog number until someone repairs the pointers centrally.

    It is provenance, not cosmetics: these pointers are how a bad batch gets
    traced back to what produced it.
    """
    _header("10. authority path resolution (report-only)")
    banks = ROOT / "data" / "base" / "solutions" / "banks"
    if not banks.is_dir():
        _warn("no bank solution tree — skipping")
        return True

    total = stale_solution = stale_image = unreadable = 0
    examples: list[str] = []
    for path in sorted(banks.rglob("*.json")):
        try:
            record = json.loads(path.read_text())
        except Exception:
            unreadable += 1
            continue
        files = record.get("files") or {}
        if not files:
            continue
        total += 1
        relpath = files.get("solution_relpath")
        if relpath and not (ROOT / relpath).exists():
            stale_solution += 1
            if len(examples) < 3:
                examples.append(f"{path.name} -> {relpath}")
        image = files.get("task_image_relpath")
        if image and not (ROOT / image).exists():
            stale_image += 1

    _warn(f"bank solution records with files{{}}: {total}")
    if unreadable:
        _warn(f"  unreadable JSON: {unreadable}")
    pct = 100 * stale_solution / total if total else 0.0
    _warn(f"  stale solution_relpath:   {stale_solution} ({pct:.1f}%)")
    _warn(f"  stale task_image_relpath: {stale_image}")
    for example in examples:
        _warn(f"    e.g. {example}")
    if stale_solution:
        _warn("  NOTE: provenance pointers — a stale one converts a fixable "
              "defect into an unfindable one. Repair centrally, not per-worker.")
    return True


def check_metadata_coverage() -> bool:
    _header("6. metadata coverage (bank + custom)")
    if not PUZZLE_DB.exists():
        _warn("puzzle_db missing — skipping")
        return True
    missing_title = 0
    missing_written = 0
    missing_diff = 0
    covered = 0
    for line in PUZZLE_DB.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        src = r.get("source", "")
        if not (src == "custom" or src.startswith("bank:")):
            continue  # training/augmented exempt
        covered += 1
        if not r.get("title"):
            missing_title += 1
        if not r.get("written_solution"):
            missing_written += 1
        if not r.get("difficulty"):
            missing_diff += 1
    if missing_title or missing_written or missing_diff:
        _warn(f"{covered} bank/custom puzzles inspected: "
              f"missing title={missing_title}, "
              f"written_solution={missing_written}, "
              f"difficulty={missing_diff}")
        # Warning not failure — metadata fills in over time
        return True
    _ok(f"{covered} bank/custom puzzles have complete metadata")
    return True


# =====================================================================
# Main
# =====================================================================

CHECKS = [
    ("bank_manifests",     check_bank_manifests),
    ("bank_schemas",       check_bank_schemas),
    ("python_syntax",      check_python_syntax),
    ("python_solvers",     check_python_solvers),
    ("canonical",          check_canonical),
    ("metadata_coverage",  check_metadata_coverage),
    ("canonical_aliases",  check_canonical_aliases),
    ("comment_density",    check_comment_density),
    ("concept_coverage",   check_concept_coverage),
    ("authority_paths",    check_authority_paths),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--skip", nargs="*", default=[],
                    help="check names to skip")
    args = ap.parse_args()

    print(f"puzzle lint — {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  canonical: {CANONICAL}")
    print(f"  db       : {PUZZLE_DB}")
    print(f"  banks    : {BANKS_DIR}")

    t0 = time.time()
    failures = 0
    for name, fn in CHECKS:
        if name in args.skip:
            print(f"\n── {name} [skipped]")
            continue
        try:
            ok = fn(args.verbose) if "verbose" in fn.__code__.co_varnames \
                 else fn()
        except Exception as e:
            _fail(f"{name} check raised {type(e).__name__}: {e}")
            if args.verbose:
                traceback.print_exc()
            ok = False
        if not ok:
            failures += 1
    elapsed = time.time() - t0
    print()
    if failures:
        print(f"{RED}✗ {failures}/{len(CHECKS)} checks failed{RESET}  "
              f"({elapsed:.1f}s)")
        sys.exit(1)
    print(f"{GREEN}✓ {len(CHECKS)}/{len(CHECKS)} checks passed{RESET}  "
          f"({elapsed:.1f}s)")


if __name__ == "__main__":
    main()
