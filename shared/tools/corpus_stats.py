#!/usr/bin/env python3
"""Single source of truth for every headline corpus number.

WHY THIS EXISTS
---------------
"How many generators are safe?" was answered "4". The real answer was 382.
The wrong number came from grepping review PROSE with a regex; the right one
lives in a structured field (`train_safety` in the assignment ledger). Nothing
in the repo said where the number was supposed to come from, so an ad-hoc
measurement looked as authoritative as the real one.

Every stat here therefore carries its PROVENANCE — the file it is read from
and the field/method used. If you want a corpus number, run this. Do not
grep for it, and do not quote a number out of a markdown file unless that
number is inside a `stat:` marker maintained by `--sync-markers`.

USAGE
-----
    python3 scripts/corpus_stats.py                 # table, with provenance
    python3 scripts/corpus_stats.py --json-out P    # machine-readable
    python3 scripts/corpus_stats.py --write-doc     # regenerate docs/CORPUS_STATS.md
    python3 scripts/corpus_stats.py --sync-markers  # rewrite <!--stat:KEY--> spans in docs
    python3 scripts/corpus_stats.py --check         # exit 1 if any marker is stale (CI gate)

ADDING A STAT
-------------
Append to STATS below. A stat MUST declare `source` and `method` — a value
without provenance is exactly the failure this file exists to prevent.
"""
from __future__ import annotations

import argparse
import ast
import collections
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENT = ROOT / "data/derived/kimi_generator_assignment.jsonl"
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
PUZZLE_DB = ROOT / "data/canonical/puzzle_db.jsonl"
GROUNDED = ROOT / "solvers/grounded_rules.py"
PER_PUZZLE = ROOT / "puzzle_generators/per_puzzle"
TESTS = ROOT / "tests"
PROCESSED = ROOT / "reviews/landing/processed"
STATS_DOC = ROOT / "docs/CORPUS_STATS.md"
LINT_PUZZLES = ROOT / "scripts/lint_puzzles.py"
CANONICAL_BUILDER = ROOT / "scripts/build_canonical_puzzles.py"
BASE_SOLUTIONS = ROOT / "data/base/solutions"
BASE_IMAGES = ROOT / "data/base/images"
SAFE_POOL_MANIFEST = ROOT / "qwen9b/colab/assets/safe_pool_manifest.json"

# Docs whose `<!--stat:KEY-->value<!--/stat-->` spans are kept in sync.
MARKER_DOCS = [
    ROOT / "CLAUDE.md",
    ROOT / "LIVE_PATH.md",
    ROOT / "README.md",
    ROOT / "docs/PROJECT_OVERVIEW.md",
    ROOT / "docs/COLAB_G4_TRAINING_PLAN.md",
    STATS_DOC,
]
MARKER_RE = re.compile(
    r"(<!--stat:(?P<key>[a-z0-9_.]+)-->)(?P<value>.*?)(<!--/stat-->)",
    re.DOTALL,
)


# --------------------------------------------------------------------------
# loaders (cached; every stat states which of these it reads)
# --------------------------------------------------------------------------
_cache: dict[str, Any] = {}


def _jsonl(path: Path) -> list[dict]:
    key = str(path)
    if key not in _cache:
        if not path.is_file():
            raise SystemExit(f"LOUD: authoritative source missing: {path}")
        rows = []
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
        _cache[key] = rows
    return _cache[key]


def _assignment() -> list[dict]:
    return _jsonl(ASSIGNMENT)


def _canonical() -> list[dict]:
    return _jsonl(CANONICAL)


def _counts(rows: list[dict], field: str) -> collections.Counter:
    return collections.Counter(str(r.get(field)) for r in rows)


# --------------------------------------------------------------------------
# stat definitions
# --------------------------------------------------------------------------
class Stat:
    def __init__(self, key: str, desc: str, source: str, method: str,
                 fn: Callable[[], Any]):
        self.key, self.desc, self.source, self.method, self.fn = (
            key, desc, source, method, fn)


def _safety_dist() -> dict:
    return dict(sorted(_counts(_assignment(), "train_safety").items()))


def _rule_hash_count() -> int:
    n = 0
    for path in PER_PUZZLE.glob("*/generator.py"):
        head = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"^RULE_HASH\s*=", head, re.M):
            n += 1
    return n


def _canonical_with_program() -> int:
    return sum(1 for r in _canonical() if (r.get("program_solution") or "").strip())


def _grounded_rule_count() -> int:
    text = GROUNDED.read_text(encoding="utf-8", errors="replace")
    # Rules are registered one per task_id key in the RULES mapping.
    return len(re.findall(r'^\s{4}["\']([0-9a-f]{8,12})["\']\s*:', text, re.M))


def _cell_at_canonical() -> dict:
    """`cell-at` usage in the live rule corpus.

    Replaces the unsourced "977 times across 785 rules" claim that sat in
    CLAUDE.md. Bare-token match, so it agrees with the one-liner a human would
    run: `jq -r '.program_solution // ""' … | grep -o 'cell-at' | wc -l`.
    """
    if "cell_at" not in _cache:
        occ = rows = 0
        for row in _canonical():
            hits = len(re.findall(r"cell-at", row.get("program_solution") or ""))
            if hits:
                occ += hits
                rows += 1
        _cache["cell_at"] = {"occurrences": occ, "rows": rows}
    return _cache["cell_at"]


def _lint_check_count() -> int:
    """Length of the CHECKS list in lint_puzzles.py, read WITHOUT importing.

    Parsed from the AST so adding a check updates the number automatically and
    the gate never executes the linter as a side effect of a stat lookup.
    """
    tree = ast.parse(LINT_PUZZLES.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "CHECKS":
                    if not isinstance(node.value, (ast.List, ast.Tuple)):
                        raise SystemExit(
                            "LOUD: lint_puzzles.CHECKS is not a literal list — "
                            "corpus_stats can no longer count it")
                    return len(node.value.elts)
    raise SystemExit("LOUD: no CHECKS assignment found in scripts/lint_puzzles.py")


def _drift() -> dict:
    """Full canonical-vs-true-source drift report (dry run, writes nothing).

    Shells out to `build_canonical_puzzles.py --check-drift --json-out` because
    that script is the only thing that knows how to rebuild canonical. It
    rebuilds into a temp dir and cleans up; it EXITS 1 when drift exists, which
    is the normal state here, so the return code is informational only — the
    json file is the contract. ~1.6s.
    """
    if "drift" not in _cache:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "drift.json"
            proc = subprocess.run(
                [sys.executable, str(CANONICAL_BUILDER),
                 "--check-drift", "--json-out", str(out)],
                cwd=str(ROOT), capture_output=True, text=True, timeout=600,
            )
            if not out.is_file():
                raise SystemExit(
                    "LOUD: --check-drift produced no json "
                    f"(rc={proc.returncode})\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
            _cache["drift"] = json.loads(out.read_text(encoding="utf-8"))
    return _cache["drift"]


def _drift_total() -> int:
    d = _drift()
    return len(d["reformat_only"]) + len(d["token_level"])


def _canonical_source_split() -> dict:
    """training / augmented / custom / bank row counts (bank:<hash> collapsed).

    Canonical carries no `eval` source: the 120 official evaluation tasks are
    a held-out panel and are deliberately NOT ingested as rows.
    """
    out: collections.Counter = collections.Counter()
    for row in _canonical():
        src = str(row.get("source"))
        out["bank" if src.startswith("bank:") else src] += 1
    return dict(sorted(out.items()))


def _canonical_program_split() -> dict:
    """Same buckets as _canonical_source_split, but only rows WITH a program."""
    out: collections.Counter = collections.Counter()
    for row in _canonical():
        if not (row.get("program_solution") or "").strip():
            continue
        src = str(row.get("source"))
        out["bank" if src.startswith("bank:") else src] += 1
    return dict(sorted(out.items()))


def _canonical_bank_count() -> int:
    return len({str(r.get("source")) for r in _canonical()
                if str(r.get("source")).startswith("bank:")})


def _generator_dirs() -> set[str]:
    return {p.parent.name for p in PER_PUZZLE.glob("*/generator.py")}


def _canonical_task_ids() -> set[str]:
    return {r["task_id"] for r in _canonical()}


def _base_solution_scan() -> dict:
    """One pass over data/base/solutions/**.json (4.3k files, ~0.5s warm)."""
    if "base_solutions" not in _cache:
        if not BASE_SOLUTIONS.is_dir():
            raise SystemExit(f"LOUD: authoritative source missing: {BASE_SOLUTIONS}")
        files = verified = described = 0
        for path in BASE_SOLUTIONS.rglob("*.json"):
            files += 1
            row = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            if (row.get("verification") or {}).get("status"):
                verified += 1
            if row.get("description_target"):
                described += 1
        _cache["base_solutions"] = {
            "files": files, "verified": verified, "described": described,
        }
    return _cache["base_solutions"]


def _safe_pool() -> dict:
    if "safe_pool" not in _cache:
        if not SAFE_POOL_MANIFEST.is_file():
            raise SystemExit(f"LOUD: authoritative source missing: {SAFE_POOL_MANIFEST}")
        _cache["safe_pool"] = json.loads(
            SAFE_POOL_MANIFEST.read_text(encoding="utf-8"))
    return _cache["safe_pool"]


def _safe_pool_dropped_no_program() -> int:
    return sum(1 for d in _safe_pool().get("dropped", [])
               if d.get("reason") == "no canonical program_solution")


def _safe_pool_share() -> str:
    pool, queued = _safe_pool()["tasks"], len(_assignment())
    return f"{pool} of {queued} ({100.0 * pool / queued:.1f}%)"


def _safe_pool_pass_whitelist() -> int:
    """Pool tasks surviving the pre-existing whitelist/blacklist layer.

    Mirrors `qwen9b/build_dataset.py:allowed_task_ids` exactly: intersect with
    the whitelist if present, then subtract the blacklist.
    """
    pool_path = SAFE_POOL_MANIFEST.parent / "safe_pool.json"
    if not pool_path.is_file():
        raise SystemExit(f"LOUD: authoritative source missing: {pool_path}")
    allowed = set(json.loads(pool_path.read_text(encoding="utf-8")))
    whitelist = ROOT / "data/derived/generator_whitelist.txt"
    blacklist = ROOT / "data/derived/generator_blacklist.txt"
    if whitelist.is_file():
        allowed &= {ln.split()[0]
                    for ln in whitelist.read_text().splitlines() if ln.strip()}
    if blacklist.is_file():
        allowed -= {ln.split()[0]
                    for ln in blacklist.read_text().splitlines() if ln.strip()}
    return len(allowed)


STATS: list[Stat] = [
    # ---- the one that was answered wrong -----------------------------------
    Stat("safety.reviewed_safe",
         "generators with train_safety == reviewed_safe",
         "data/derived/kimi_generator_assignment.jsonl",
         "count of rows where field `train_safety` == 'reviewed_safe'",
         lambda: _counts(_assignment(), "train_safety")["reviewed_safe"]),
    Stat("safety.distribution",
         "full train_safety distribution",
         "data/derived/kimi_generator_assignment.jsonl",
         "Counter over field `train_safety`",
         _safety_dist),
    Stat("safety.provisionally_safe", "train_safety == provisionally_safe",
         "data/derived/kimi_generator_assignment.jsonl", "field `train_safety`",
         lambda: _counts(_assignment(), "train_safety")["provisionally_safe"]),
    Stat("safety.unsafe", "train_safety == unsafe",
         "data/derived/kimi_generator_assignment.jsonl", "field `train_safety`",
         lambda: _counts(_assignment(), "train_safety")["unsafe"]),
    Stat("safety.unverified", "train_safety == unverified (never assessed)",
         "data/derived/kimi_generator_assignment.jsonl", "field `train_safety`",
         lambda: _counts(_assignment(), "train_safety")["unverified"]),
    Stat("safety.caution", "train_safety == caution",
         "data/derived/kimi_generator_assignment.jsonl", "field `train_safety`",
         lambda: _counts(_assignment(), "train_safety")["caution"]),
    Stat("safety.reviewed_standard", "train_safety == reviewed_standard (tier-2)",
         "data/derived/kimi_generator_assignment.jsonl", "field `train_safety`",
         lambda: _counts(_assignment(), "train_safety")["reviewed_standard"]),

    # ---- review / assignment ----------------------------------------------
    Stat("generators.tracked", "generator modules in the assignment ledger",
         "data/derived/kimi_generator_assignment.jsonl", "row count",
         lambda: len(_assignment())),
    Stat("generators.on_disk", "per-puzzle generator.py files present",
         "puzzle_generators/per_puzzle/*/generator.py", "glob count",
         lambda: len(list(PER_PUZZLE.glob("*/generator.py")))),
    Stat("generators.with_rule_hash", "generators declaring RULE_HASH",
         "puzzle_generators/per_puzzle/*/generator.py",
         "regex ^RULE_HASH= per file", _rule_hash_count),
    # The 3889 / 3890 / 3892 confusion, pinned down. `ls per_puzzle | wc -l`
    # returns 3892 because it also counts __pycache__ and the spec README —
    # that number is NOT a generator count and must never be quoted as one.
    Stat("generators.canonical_covered",
         "canonical task_ids that have a per-puzzle generator.py",
         "data/canonical/puzzles.jsonl + puzzle_generators/per_puzzle/*/generator.py",
         "len(set(canonical task_id) & set(generator dir names))",
         lambda: len(_canonical_task_ids() & _generator_dirs())),
    Stat("generators.canonical_uncovered",
         "canonical task_ids with NO per-puzzle generator",
         "data/canonical/puzzles.jsonl + puzzle_generators/per_puzzle/*/generator.py",
         "len(set(canonical task_id) - set(generator dir names))",
         lambda: len(_canonical_task_ids() - _generator_dirs())),
    Stat("generators.orphan",
         "generator dirs whose task_id is not in canonical",
         "puzzle_generators/per_puzzle/*/generator.py + data/canonical/puzzles.jsonl",
         "len(set(generator dir names) - set(canonical task_id))",
         lambda: len(_generator_dirs() - _canonical_task_ids())),
    Stat("review.reviewed", "generators with latest_review_status set",
         "data/derived/kimi_generator_assignment.jsonl",
         "count of non-empty `latest_review_status`",
         lambda: sum(1 for r in _assignment() if r.get("latest_review_status"))),
    Stat("review.pending", "assignment status == pending",
         "data/derived/kimi_generator_assignment.jsonl", "field `status`",
         lambda: _counts(_assignment(), "status")["pending"]),
    Stat("review.complete", "assignment status == complete",
         "data/derived/kimi_generator_assignment.jsonl", "field `status`",
         lambda: _counts(_assignment(), "status")["complete"]),
    Stat("review.has_self_check", "generators with a self_check",
         "data/derived/kimi_generator_assignment.jsonl", "field `has_self_check`",
         lambda: _counts(_assignment(), "has_self_check")["True"]),
    Stat("review.divergence", "source divergence_class distribution",
         "data/derived/kimi_generator_assignment.jsonl", "field `divergence_class`",
         lambda: dict(sorted(_counts(_assignment(), "divergence_class").items()))),

    # ---- canonical corpus --------------------------------------------------
    Stat("canonical.rows", "rows in canonical puzzles.jsonl",
         "data/canonical/puzzles.jsonl", "line count",
         lambda: len(_canonical())),
    Stat("canonical.unique_task_ids", "distinct task_ids in canonical",
         "data/canonical/puzzles.jsonl", "len(set(task_id))",
         lambda: len({r["task_id"] for r in _canonical()})),
    Stat("canonical.with_program_solution",
         "canonical rows carrying a non-empty program_solution",
         "data/canonical/puzzles.jsonl", "count of non-empty `program_solution`",
         _canonical_with_program),
    Stat("canonical.needs_conversion", "rows still flagged needs_conversion",
         "data/canonical/puzzles.jsonl", "count where `needs_conversion` is true",
         lambda: sum(1 for r in _canonical() if r.get("needs_conversion"))),
    Stat("puzzle_db.rows", "rows in puzzle_db.jsonl (1 per CANONICAL ROW, "
         "not 1 per task_id — augmented variants reuse their parent's task_id)",
         "data/canonical/puzzle_db.jsonl", "line count",
         lambda: len(_jsonl(PUZZLE_DB))),
    Stat("puzzle_db.unique_task_ids", "distinct task_ids in puzzle_db.jsonl",
         "data/canonical/puzzle_db.jsonl", "len(set(task_id))",
         lambda: len({r["task_id"] for r in _jsonl(PUZZLE_DB)})),
    Stat("canonical.source_split",
         "canonical rows by source (bank:<hash> collapsed to `bank`; "
         "official eval tasks are a held-out panel and are never rows)",
         "data/canonical/puzzles.jsonl", "Counter over field `source`",
         _canonical_source_split),
    Stat("canonical.rows_training", "canonical rows with source == training",
         "data/canonical/puzzles.jsonl", "field `source`",
         lambda: _canonical_source_split().get("training", 0)),
    Stat("canonical.rows_augmented", "canonical rows with source == augmented",
         "data/canonical/puzzles.jsonl", "field `source`",
         lambda: _canonical_source_split().get("augmented", 0)),
    Stat("canonical.rows_custom", "canonical rows with source == custom",
         "data/canonical/puzzles.jsonl", "field `source`",
         lambda: _canonical_source_split().get("custom", 0)),
    Stat("canonical.rows_bank", "canonical rows from a bank",
         "data/canonical/puzzles.jsonl", "field `source` starting with `bank:`",
         lambda: _canonical_source_split().get("bank", 0)),
    Stat("canonical.program_training", "training rows with a program_solution",
         "data/canonical/puzzles.jsonl", "field `source` + non-empty `program_solution`",
         lambda: _canonical_program_split().get("training", 0)),
    Stat("canonical.program_augmented", "augmented rows with a program_solution",
         "data/canonical/puzzles.jsonl", "field `source` + non-empty `program_solution`",
         lambda: _canonical_program_split().get("augmented", 0)),
    Stat("canonical.program_custom", "custom rows with a program_solution",
         "data/canonical/puzzles.jsonl", "field `source` + non-empty `program_solution`",
         lambda: _canonical_program_split().get("custom", 0)),
    Stat("canonical.program_bank", "bank rows with a program_solution",
         "data/canonical/puzzles.jsonl", "field `source` + non-empty `program_solution`",
         lambda: _canonical_program_split().get("bank", 0)),
    Stat("canonical.banks", "distinct banks contributing canonical rows",
         "data/canonical/puzzles.jsonl", "len(set of `bank:<hash>` sources)",
         _canonical_bank_count),

    # ---- canonical drift (gates whether a rebuild DESTROYS beautifications) --
    Stat("canonical.drift.total",
         "task_ids whose program_solution a canonical rebuild would CHANGE",
         "scripts/build_canonical_puzzles.py --check-drift --json-out",
         "len(reformat_only) + len(token_level) from the drift json",
         _drift_total),
    Stat("canonical.drift.reformat_only",
         "drifting task_ids where only whitespace differs (compaction undone)",
         "scripts/build_canonical_puzzles.py --check-drift --json-out",
         "len(reformat_only) from the drift json",
         lambda: len(_drift()["reformat_only"])),
    Stat("canonical.drift.token_level",
         "drifting task_ids whose CODE differs (needs a human read, one at a time)",
         "scripts/build_canonical_puzzles.py --check-drift --json-out",
         "len(token_level) from the drift json",
         lambda: len(_drift()["token_level"])),

    # ---- base export (the training-facing solution/image targets) -----------
    Stat("base_solutions.files", "solution json files under data/base/solutions/",
         "data/base/solutions/**/*.json", "rglob count",
         lambda: _base_solution_scan()["files"]),
    Stat("base_solutions.verified",
         "base solutions carrying a non-empty verification.status",
         "data/base/solutions/**/*.json", "count of non-empty `verification.status`",
         lambda: _base_solution_scan()["verified"]),
    Stat("base_solutions.description_targets",
         "base solutions carrying a description_target",
         "data/base/solutions/**/*.json", "count of truthy `description_target`",
         lambda: _base_solution_scan()["described"]),
    Stat("base_images.png", "rendered task PNGs in the base export",
         "data/base/images/**/*.png", "rglob count",
         lambda: len(list(BASE_IMAGES.rglob("*.png")))),

    # ---- qwen9b safe pool ---------------------------------------------------
    Stat("safe_pool.tasks", "tasks admitted to the qwen9b safe pool",
         "qwen9b/colab/assets/safe_pool_manifest.json", "field `tasks`",
         lambda: _safe_pool()["tasks"]),
    Stat("safe_pool.tier1", "tier-1 (reviewed_safe) tasks in the pool",
         "qwen9b/colab/assets/safe_pool_manifest.json", "field `tier1`",
         lambda: _safe_pool()["tier1"]),
    Stat("safe_pool.total_weight", "summed recommended_mix_weight of the pool",
         "qwen9b/colab/assets/safe_pool_manifest.json", "field `total_weight`",
         lambda: _safe_pool()["total_weight"]),
    Stat("safe_pool.dropped_no_program",
         "safe-tagged tasks dropped for having no canonical program_solution",
         "qwen9b/colab/assets/safe_pool_manifest.json",
         "count of `dropped` entries with reason == 'no canonical program_solution'",
         _safe_pool_dropped_no_program),
    Stat("safe_pool.share_of_queue", "pool size as a share of the review queue",
         "qwen9b/colab/assets/safe_pool_manifest.json + "
         "data/derived/kimi_generator_assignment.jsonl",
         "`tasks` / assignment row count, formatted 'N of M (P%)'",
         _safe_pool_share),
    Stat("safe_pool.pass_whitelist",
         "pool tasks that also survive the whitelist/blacklist layer",
         "qwen9b/colab/assets/safe_pool.json + "
         "data/derived/generator_{whitelist,blacklist}.txt",
         "same set algebra as qwen9b/build_dataset.py:allowed_task_ids",
         _safe_pool_pass_whitelist),

    # ---- solvers / tests / intake -------------------------------------------
    Stat("grounded.rules", "Racket rules registered in grounded_rules.py",
         "solvers/grounded_rules.py", "regex over the RULES mapping keys",
         _grounded_rule_count),
    # ---- vocabulary usage (was quoted from unsourced prose; now measured) ---
    Stat("vocab.cell_at.canonical", "`cell-at` occurrences in canonical programs",
         "data/canonical/puzzles.jsonl",
         "bare-token regex `cell-at` over `program_solution`, summed",
         lambda: _cell_at_canonical()["occurrences"]),
    Stat("vocab.cell_at.canonical_rows", "canonical rows whose program uses `cell-at`",
         "data/canonical/puzzles.jsonl",
         "count of rows where `program_solution` matches `cell-at`",
         lambda: _cell_at_canonical()["rows"]),
    Stat("vocab.cell_at.grounded", "`cell-at` occurrences in grounded_rules.py",
         "solvers/grounded_rules.py", "bare-token regex `cell-at` over the file",
         lambda: len(re.findall(r"cell-at",
                                GROUNDED.read_text(encoding="utf-8", errors="replace")))),

    Stat("lint.checks", "checks the puzzle linter runs",
         "scripts/lint_puzzles.py", "len of the CHECKS list, read via ast (no import)",
         _lint_check_count),
    Stat("tests.generator_modules", "focused per-generator test modules",
         "tests/test_generator_*.py", "glob count",
         lambda: len(list(TESTS.glob("test_generator_*.py")))),
    Stat("intake.returns_processed", "review returns released to processed/",
         "reviews/landing/processed/", "file count",
         lambda: len(list(PROCESSED.iterdir())) if PROCESSED.is_dir() else 0),
]

BY_KEY = {s.key: s for s in STATS}


def compute() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for stat in STATS:
        try:
            value = stat.fn()
            error = None
        except Exception as exc:            # LOUD, never a silent zero
            value, error = None, f"{type(exc).__name__}: {exc}"
            print(f"LOUD: stat {stat.key} failed to compute: {error}",
                  file=sys.stderr)
        out[stat.key] = {
            "value": value, "description": stat.desc,
            "source": stat.source, "method": stat.method, "error": error,
        }
    return out


def _fmt(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(f"{k}={v}" for k, v in value.items())
    return str(value)


def render_table(data: dict[str, dict]) -> str:
    width = max(len(k) for k in data)
    lines = []
    for key, row in data.items():
        lines.append(f"{key:<{width}}  {_fmt(row['value'])}")
        lines.append(f"{'':<{width}}    source: {row['source']}")
        lines.append(f"{'':<{width}}    method: {row['method']}")
    return "\n".join(lines)


def render_doc(data: dict[str, dict]) -> str:
    out = [
        "# Corpus statistics (GENERATED — do not hand-edit)",
        "",
        "Regenerate with `python3 scripts/corpus_stats.py --write-doc`.",
        "",
        "Every number below is computed from the stated source at generation",
        "time. **Do not quote a corpus number from anywhere else.** If you need",
        "a figure, run the script — a number pasted into prose goes stale",
        "silently and will be quoted as fact months later.",
        "",
        "| stat | value | source | method |",
        "|---|---|---|---|",
    ]
    for key, row in data.items():
        out.append(
            f"| `{key}` | <!--stat:{key}-->{_fmt(row['value'])}<!--/stat--> "
            f"| `{row['source']}` | {row['method']} |"
        )
    out.append("")
    return "\n".join(out)


def sync_markers(data: dict[str, dict], *, check_only: bool) -> int:
    """Rewrite (or verify) every <!--stat:KEY-->…<!--/stat--> span."""
    stale, updated, unknown = [], [], []
    for doc in MARKER_DOCS:
        if not doc.is_file():
            continue
        text = doc.read_text(encoding="utf-8")

        def replace(match: re.Match) -> str:
            key = match.group("key")
            if key not in data:
                unknown.append(f"{doc.relative_to(ROOT)}: unknown stat '{key}'")
                return match.group(0)
            fresh = _fmt(data[key]["value"])
            if match.group("value") != fresh:
                stale.append(
                    f"{doc.relative_to(ROOT)}: {key} says "
                    f"{match.group('value')!r}, live value is {fresh!r}"
                )
            return f"{match.group(1)}{fresh}{match.group(4)}"

        new = MARKER_RE.sub(replace, text)
        if new != text and not check_only:
            doc.write_text(new, encoding="utf-8")
            updated.append(str(doc.relative_to(ROOT)))

    for message in unknown:
        print(f"LOUD: {message}", file=sys.stderr)
    if check_only:
        for message in stale:
            print(f"STALE: {message}", file=sys.stderr)
        if stale or unknown:
            print(f"corpus-stats: {len(stale)} stale marker(s), "
                  f"{len(unknown)} unknown — run --sync-markers", file=sys.stderr)
            return 1
        print("corpus-stats: all stat markers current")
        return 0
    if updated:
        print(f"updated markers in: {', '.join(updated)}")
    else:
        print("markers already current")
    return 1 if unknown else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--write-doc", action="store_true",
                    help="regenerate docs/CORPUS_STATS.md")
    ap.add_argument("--sync-markers", action="store_true",
                    help="rewrite <!--stat:KEY--> spans in tracked docs")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if any tracked marker is stale (CI gate)")
    ap.add_argument("--only", help="print one stat's value and exit")
    args = ap.parse_args()

    data = compute()

    if args.only:
        if args.only not in data:
            print(f"LOUD: unknown stat '{args.only}'. Known keys:", file=sys.stderr)
            for key in data:
                print(f"  {key}", file=sys.stderr)
            return 2
        row = data[args.only]
        print(_fmt(row["value"]))
        print(f"  source: {row['source']}", file=sys.stderr)
        print(f"  method: {row['method']}", file=sys.stderr)
        return 0

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.json_out}")

    if args.write_doc:
        STATS_DOC.parent.mkdir(parents=True, exist_ok=True)
        STATS_DOC.write_text(render_doc(data), encoding="utf-8")
        print(f"wrote {STATS_DOC.relative_to(ROOT)}")

    if args.check:
        return sync_markers(data, check_only=True)
    if args.sync_markers:
        return sync_markers(data, check_only=False)

    if not (args.json_out or args.write_doc):
        print(render_table(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
