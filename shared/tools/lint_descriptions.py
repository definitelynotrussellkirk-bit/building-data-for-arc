#!/usr/bin/env python3
"""Lint rule descriptions against docs/CANONICAL_DESCRIPTIONS.md.

Two passes, both regex/table-driven (no semantic parsing):

  1. VOCAB     color-name forms, transform names, lookup-arrow form,
               distance-metric names, direction names, banned vague
               nouns. Each finding has an auto-fix suggestion when
               possible.

  2. STRUCTURE detect SCENE / KEY / SELECT / ACTION / OUTPUT slot
               keywords; verify they appear in canonical order; flag
               descriptions with no detectable ACTION slot.

Read-only; outputs:
  - /tmp/description_lint.jsonl   per-description findings
  - /tmp/description_lint.md      summary report (counts, top offenders)

Usage:
    python3 scripts/lint_descriptions.py                     # all sources
    python3 scripts/lint_descriptions.py --task-id <tid>     # single rule
    python3 scripts/lint_descriptions.py --bank <bank>       # one bank only
    python3 scripts/lint_descriptions.py --auto-fix-preview  # show
        # what auto-fix would change (does NOT write back).
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DB = ROOT / "docs" / "arc_reference.jsonl"


def load_reference_aliases() -> list[dict]:
    """Pull alias-with-regex rules out of the reference DB so the lint
    table and the human-readable doc share one source of truth.

    Returns a list of {kind, severity, regex, fix, label, entry_id}.
    Aliases without a regex are skipped (display-only)."""
    rules = []
    if not REFERENCE_DB.exists():
        return rules
    for line in REFERENCE_DB.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue
        for a in entry.get("often_used_as") or []:
            rx = a.get("regex")
            if not rx:
                continue
            try:
                compiled = re.compile(rx, re.IGNORECASE)
            except re.error:
                continue
            rules.append({
                "kind": f"{entry.get('category', 'misc').lower().replace(' ', '-').replace('/', '-')}-alias",
                "severity": a.get("severity", "warn"),
                "regex": compiled,
                "fix": a.get("fix"),
                "fix_template": a.get("fix_template"),  # for capture-group fixes
                "label": a.get("label"),
                "entry_id": entry["id"],
            })
    return rules


# ---------------------------------------------------------------------------
# Canonical vocab tables — kept here only for things not yet in the DB
# (slot-detection regexes, lookup-arrow forms, banned phrases, color-form
# patterns). Color-name and transform/distance/direction alias tables are
# loaded from the reference DB.
# ---------------------------------------------------------------------------

COLOR_NAMES = {
    0: "black", 1: "blue", 2: "red", 3: "green", 4: "yellow",
    5: "gray", 6: "magenta", 7: "orange", 8: "cyan", 9: "maroon",
}
COLOR_NAME_TO_NUM = {v: k for k, v in COLOR_NAMES.items()}

# Transform / distance / direction / lookup-arrow / banned-phrase tables
# all live in docs/arc_reference.jsonl now. Loaded via load_reference_aliases().
# Only color-form regex stays here — the {sanitize-good-form, then scan
# bare-name} idiom can't be cleanly expressed as a single DB-side regex.

# Banned phrasings — moved to DB Phrases category. Local kept empty for now.
BANNED_PHRASES: dict[str, str] = {}

# Color-form regex — match `name` (no parens) and `name(N)` separately.
COLOR_NAME_PATTERN = "|".join(COLOR_NAMES.values())  # black|blue|red|...
COLOR_GOOD_RE = re.compile(rf"\b({COLOR_NAME_PATTERN})\((\d)\)", re.IGNORECASE)
COLOR_BARE_NAME_RE = re.compile(rf"\b({COLOR_NAME_PATTERN})\b(?!\s*\()", re.IGNORECASE)
# `color N` / `color-N` — old form
COLOR_NUMBER_PHRASE_RE = re.compile(r"\bcolor[-\s](\d)\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Slot detection
# ---------------------------------------------------------------------------

# Keyword markers per slot. First-match-wins, applied to each sentence in order.
SLOT_MARKERS = {
    "SCENE": [
        r"^\s*(?:the|a|an)\s+(?:top|bottom|left|right|first|last)\s+(?:row|column|band)\b",
        r"^\s*there\s+(?:is|are)\b",
        r"^\s*the\s+grid\b",
        r"^\s*most\s+of\b",
        r"^\s*the\s+wall\s+cells\b",
        r"^\s*split\b",                # "split the grid into N panels"
        r"^\s*the\s+(?:top|bottom)\s+two?\s+rows?\s+form\b",
    ],
    "KEY": [
        r"\b\d\s*(?:→|=>|=|means)\s*\w",                # explicit lookup
        r"\bdefault\s+(?:to\s+)?\w",                    # default-value clause
        r"\b(?:cell|marker)\[\s*\d+\s*\]\b",            # cell[0]= form
        r"\bthe\s+(?:operation|rotation|transform)\s+control\b",
        r"\bthe\s+number\s+of\s+\w+\s+markers?\s+(?:chooses|picks)\b",
        r"^\s*(?:read|interpret|count(?:\s+the)?)\b",   # Read X → KEY intro
        r"^\s*use\s+the\s+(?:top-?\w+|legend|key|control)\b",
    ],
    "SELECT": [
        # All anchored to sentence start. The previous unanchored
        # `\bthe\s+(unique|smallest|...)\b` matched object-references
        # inside ACTION sentences ("Recolor the smallest object…") and
        # produced ~150 false slot-out-of-order findings.
        r"^\s*(?:find|extract|take|locate)\s+(?:every|the)\b",
        r"^\s*(?:among|of)\s+the\s+\w+\b",
        r"^\s*the\s+(?:unique|only|single|largest|smallest|tallest|widest|first)\b",
        r"^\s*every\s+(?:non-?(?:zero|background)\s+)?(?:cell|component|object|row|column)\b",
    ],
    "ACTION": [
        # Leading imperative verb. Note: `read`, `split`, `interpret`,
        # `count`, `compute`, `take` are intentionally NOT in this list —
        # they are KEY/SCENE introducers ("Read the legend …", "Split the
        # input into three panels …") and putting them in ACTION causes
        # systemic slot-out-of-order false positives.
        r"^\s*(?:recolor|rotate|fill|slide|stamp|delete|copy|crop|paste|swap|paint|draw|extend|connect|reflect|mirror|overlay|flood-?fill|trace|complete|extract|move|push|pull|sort|place|output|return|replace|change|update|remove|keep|merge|build|render|apply|transform|scale|upscale|downscale|tile|stack|align|identify|locate|traverse|discard|ignore|propagate|attach|detach|select|pick|pack|whenever|for\s+each|if|when|in\s+every|every)\b",
        r"\b(?:recolor|rotate|fill|slide|stamp|deletes?|replaces?|sets?|changes?|updates?|removes?|keeps?|builds?|outputs?|returns?|paints?|draws?|extends?|connects?|reflects?|mirrors?|overlays?|crops?|pastes?|swaps?|extracts?|moves?|stamps?|ignores?|discards?)\b",
    ],
    "OUTPUT": [
        r"\bleave\s+(?:the\s+)?(?:rest|other|all\s+other)\b",
        r"\boutput\s+(?:on|the\s+result|only)\b",
        r"\b(?:keep|preserve)\s+(?:the\s+)?(?:rest|legend|separator)\b",
        r"\bdiscard\b",
    ],
}
SLOT_ORDER = ["SCENE", "KEY", "SELECT", "ACTION", "OUTPUT"]


# ---------------------------------------------------------------------------
# Linting
# ---------------------------------------------------------------------------

_DB_RULES_CACHE: list[dict] | None = None


def _db_rules() -> list[dict]:
    global _DB_RULES_CACHE
    if _DB_RULES_CACHE is None:
        _DB_RULES_CACHE = load_reference_aliases()
    return _DB_RULES_CACHE


def lint_vocab(text: str) -> list[dict]:
    findings = []

    # 0. Color-name/number consistency. `blue(6)` is wrong — blue is
    # always 1; magenta is 6. The previous COLOR_GOOD_RE silently
    # accepted any `name(\d)` without checking the pair.
    for m in COLOR_GOOD_RE.finditer(text):
        name, num_str = m.group(1).lower(), m.group(2)
        try:
            num = int(num_str)
        except Exception:
            continue
        if COLOR_NAME_TO_NUM.get(name) != num:
            # Mismatch — both candidates are valid canonical forms; the
            # author meant one of them and we can't tell which without
            # cross-checking the rule.
            correct_name_for_num = COLOR_NAMES.get(num, "?")
            correct_num_for_name = COLOR_NAME_TO_NUM.get(name, "?")
            findings.append({
                "kind": "color-mismatch",
                "severity": "error",
                "match": m.group(0),
                "suggest": f"either `{correct_name_for_num}({num})` or "
                           f"`{name}({correct_num_for_name})` — cross-check rule",
                "offset": m.start(),
            })

    # 1. DB-driven aliases (colors, transforms, distances, directions, …)
    sanitized_for_color = COLOR_GOOD_RE.sub(lambda m: "___COLORTOKEN___", text)
    for rule in _db_rules():
        # For color "bare name" rules, run on the color-sanitized text so we
        # don't false-flag good `blue(1)` forms; but use original offsets.
        target = sanitized_for_color if rule["kind"].startswith("colors-") else text
        for m in rule["regex"].finditer(target):
            findings.append({
                "kind": rule["kind"],
                "severity": rule["severity"],
                "match": m.group(0) if target is text else text[m.start():m.start() + len(m.group(0))],
                "suggest": rule["fix"] or rule["label"],
                "offset": m.start(),
                "entry": rule["entry_id"],
            })

    return findings


_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def detect_slots(text: str) -> list[tuple[str, str]]:
    """Heuristically classify each sentence by its first-matching slot.
    Returns list of (slot, sentence) in document order."""
    out = []
    for sentence in _SENT_SPLIT_RE.split(text.strip()):
        if not sentence.strip():
            continue
        slot = "?"
        for s, pats in SLOT_MARKERS.items():
            if any(re.search(p, sentence, re.IGNORECASE) for p in pats):
                slot = s
                break
        out.append((slot, sentence.strip()))
    return out


# Token-length lint — uses tiktoken.cl100k_base as a stable, model-independent
# proxy. The exact tokenizer doesn't matter as long as it's consistent across
# authoring + CI; cl100k_base is widely available and decoupled from model
# weights. Per docs/CANONICAL_DESCRIPTIONS.md:
#   target ≤ 280 tokens (warn above)
#   hard cap 600 tokens (error above)
LENGTH_TARGET_TOKENS = 280
LENGTH_HARD_CAP_TOKENS = 600

_ENC = None


def _tokenize_count(text: str) -> int:
    global _ENC
    if _ENC is None:
        try:
            import tiktoken
            _ENC = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _ENC = False
    if _ENC is False:
        return len(text) // 4  # rough fallback
    return len(_ENC.encode(text))


def lint_length(text: str) -> list[dict]:
    n = _tokenize_count(text)
    findings: list[dict] = []
    if n > LENGTH_HARD_CAP_TOKENS:
        findings.append({
            "kind": "length-over-cap",
            "severity": "error",
            "match": f"{n} tokens",
            "suggest": f"description is {n} tokens (hard cap {LENGTH_HARD_CAP_TOKENS}); "
                       "flatten nested structure or share repeated phrasing via vocab",
            "offset": 0,
        })
    elif n > LENGTH_TARGET_TOKENS:
        findings.append({
            "kind": "length-over-target",
            "severity": "warn",
            "match": f"{n} tokens",
            "suggest": f"description is {n} tokens (target ≤ {LENGTH_TARGET_TOKENS}); "
                       "consider flattening or re-vocabbing",
            "offset": 0,
        })
    return findings


# Description quality lint — placeholder markers and missing-rule heuristics.
# Distinct from vocab/structure: this rejects descriptions that aren't actually
# rules. The previous corpus had ~30 entries like "needs Python" or "complex,
# unclear" that survived as written_solution; those are TODO markers, not
# learnable targets.
_PLACEHOLDER_MARKERS = re.compile(
    r"\b(?:"
    r"tbd|TBD|"
    r"needs?\s+(?:python|to\s+be|further|more|clarification|review|attention|"
    r"a\s+\w+\s+(?:approach|primitive|rule|algorithm|solver))|"
    r"unclear|not\s+clear|not\s+yet|"
    r"todo|TODO|fixme|FIXME|"
    r"can'?t\s+yet\s+be\s+expressed|"
    r"probably\s+\w+|likely\s+\w+\s+\w+|maybe\s+\w+\s+\w+|"
    r"semantic\s+rule\s+(?:needs|unclear|complex)"
    r")\b",
    re.IGNORECASE,
)
_HEDGE_MARKERS = re.compile(
    r"\b(?:complex|"
    r"some\s+(?:cases?|examples?|pairs?)\s+(?:fail|miss|need)|"
    r"miss(?:es)?\s+official\s+placements?|"
    r"this\s+is\s+not\s+a\s+simple|"
    r"not\s+(?:obvious|simple|trivial)"
    r")\b",
    re.IGNORECASE,
)


def lint_quality(text: str) -> list[dict]:
    """Detect non-rule descriptions (placeholders, hedges, too-short).

    Severity:
      error — text contains a TODO/placeholder marker. These are not rules.
      warn  — text is hedge-y ("complex", "not obvious") or under length floor.
    """
    findings: list[dict] = []
    stripped = text.strip()

    for m in _PLACEHOLDER_MARKERS.finditer(text):
        findings.append({
            "kind": "vague-placeholder",
            "severity": "error",
            "match": m.group(0),
            "suggest": "this looks like a TODO marker, not a rule description — "
                       "rewrite from scratch by reading the rule + image",
            "offset": m.start(),
        })

    for m in _HEDGE_MARKERS.finditer(text):
        findings.append({
            "kind": "vague-hedge",
            "severity": "warn",
            "match": m.group(0),
            "suggest": "hedge phrasing — rule descriptions should be definite",
            "offset": m.start(),
        })

    # Too-short heuristic: a description is fine if it carries either a
    # canonical color reference OR an action/transform marker. Many valid
    # rules are pure-geometric ("Rotate the entire square grid 90° clockwise.")
    # so requiring both was over-eager. Now warn only when both are missing
    # AND the text is also under 50 chars — i.e., short prose with no anchor.
    if len(stripped) < 50:
        has_color = bool(COLOR_GOOD_RE.search(stripped))
        has_action = bool(re.search(
            r"\b(?:recolor|rotate|fill|slide|stamp|delete|copy|crop|paste|swap|"
            r"paint|draw|mirror|flip|move|remove|keep|extract|output|return|"
            r"replace|build|complete|extend|reflect|connect|select|find|"
            r"tile|translate|stack|interleave|sort|upscale|downscale|"
            r"alternate|alternating|checkerboard|self-tile|"
            r"fall|falling|cycle|adopt|assign|"
            r"identity|transpose|90°|180°)\b|→",
            stripped, re.IGNORECASE))
        if not (has_color or has_action):
            findings.append({
                "kind": "vague-too-short",
                "severity": "warn",
                "match": stripped[:80],
                "suggest": f"description is {len(stripped)} chars and lacks "
                           "both a canonical color reference and any action/transform anchor — "
                           "probably a stub",
                "offset": 0,
            })

    return findings


def lint_structure(text: str) -> list[dict]:
    slots = detect_slots(text)
    findings = []
    # Note: the previous "missing-action" check was a noisy heuristic
    # (~495 false positives in the corpus — KEY-introducing prose with
    # no obvious imperative verb still describes the rule fine). Removed
    # in favor of treating slot-detection as guidance, not a gate.
    # Order check — relaxed:
    #   - SCENE must not appear after KEY/SELECT/ACTION/OUTPUT
    #   - OUTPUT must not appear before any other classified slot
    # KEY/SELECT/ACTION can interleave freely. The strict
    # SCENE → KEY → SELECT → ACTION → OUTPUT order is an ideal but real
    # prose often has prep-actions before keys (e.g. "Crop the object,
    # then interpret the header as a transform command, then apply.")
    classified = [(s, sentence) for s, sentence in slots if s != "?"]
    seen_after_scene = False
    seen_non_output = False
    for slot, sentence in classified:
        if slot != "SCENE" and not seen_after_scene:
            seen_after_scene = True
        elif slot == "SCENE" and seen_after_scene:
            findings.append({
                "kind": "slot-out-of-order",
                "severity": "warn",
                "match": sentence[:80],
                "suggest": "SCENE should be the first classified slot",
                "offset": 0,
            })
        if slot != "OUTPUT":
            seen_non_output = True
        elif slot == "OUTPUT" and not seen_non_output:
            # OUTPUT is fine first if it's the only slot
            pass
    # OUTPUT-not-last: scan in reverse
    for i, (slot, sentence) in enumerate(classified):
        if slot == "OUTPUT" and i < len(classified) - 1:
            # OK if all subsequent are also OUTPUT
            if any(s != "OUTPUT" for s, _ in classified[i+1:]):
                findings.append({
                    "kind": "slot-out-of-order",
                    "severity": "warn",
                    "match": sentence[:80],
                    "suggest": "OUTPUT should be the last classified slot",
                    "offset": 0,
                })
                break
    return findings


# ---------------------------------------------------------------------------
# Auto-fix preview
# ---------------------------------------------------------------------------

def auto_fix(text: str) -> str:
    """Apply every DB-driven alias rule.

    Two-phase to protect already-canonical color forms from over-matching:
      1. Replace each `name(N)` with a unique placeholder token so the
         bare-name color regex can't match inside an already-good form.
      2. Apply every DB rule (with or without fix_template).
      3. Restore placeholders to original good forms."""
    out = text

    # Phase 1: stash existing good color forms
    placeholders: dict[str, str] = {}

    def _stash(m):
        token = f"\x00CTOK{len(placeholders)}\x00"
        placeholders[token] = m.group(0)
        return token

    out = COLOR_GOOD_RE.sub(_stash, out)

    # Phase 2: apply DB rules (the placeholder bytes won't match \b ... \b)
    for rule in _db_rules():
        if rule.get("fix_template"):
            out = rule["regex"].sub(rule["fix_template"], out)
        elif rule.get("fix"):
            out = rule["regex"].sub(rule["fix"], out)

    # Phase 3: restore good forms
    for token, original in placeholders.items():
        out = out.replace(token, original)

    return out


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

def collect_descriptions(*, bank_filter=None, tid_filter=None):
    rows = []
    # bank source files
    pattern = "data/base/solutions/banks/*/*.json"
    if bank_filter:
        pattern = f"data/base/solutions/banks/{bank_filter}/*.json"
    for f in glob.glob(str(ROOT / pattern)):
        try:
            d = json.loads(Path(f).read_text())
        except Exception:
            continue
        tid = d.get("task_id", "")
        if tid_filter and tid != tid_filter:
            continue
        text = (d.get("description_target") or {}).get("target_text", "").strip()
        if text:
            rows.append({"tid": tid, "source": "bank", "text": text})
    # canonical for standalone tasks
    if not bank_filter:
        with (ROOT / "data/canonical/puzzles.jsonl").open() as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                tid = r.get("task_id", "")
                if tid_filter and tid != tid_filter:
                    continue
                if ":" in tid:
                    continue  # already covered above
                text = (r.get("written_solution") or "").strip()
                if text:
                    rows.append({"tid": tid, "source": "training", "text": text})
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", help="restrict to a single bank")
    ap.add_argument("--task-id", help="single task only")
    ap.add_argument("--auto-fix-preview", action="store_true",
                    help="show before/after for each row that would change")
    ap.add_argument("--top", type=int, default=20,
                    help="show top N offenders by finding count")
    args = ap.parse_args()

    rows = collect_descriptions(bank_filter=args.bank, tid_filter=args.task_id)
    print(f"linting {len(rows)} descriptions", file=sys.stderr)

    by_kind = Counter()
    by_severity = Counter()
    n_clean = 0
    per_row = []
    out_jsonl = Path("/tmp/description_lint.jsonl").open("w")
    for r in rows:
        v = lint_vocab(r["text"])
        s = lint_structure(r["text"])
        l = lint_length(r["text"])
        q = lint_quality(r["text"])
        f = v + s + l + q
        per_row.append({"tid": r["tid"], "source": r["source"],
                        "n_findings": len(f), "findings": f,
                        "text": r["text"]})
        if not f:
            n_clean += 1
        for finding in f:
            by_kind[finding["kind"]] += 1
            by_severity[finding["severity"]] += 1
        out_jsonl.write(json.dumps({
            "tid": r["tid"], "source": r["source"],
            "n_findings": len(f), "findings": f,
        }) + "\n")
    out_jsonl.close()

    if args.auto_fix_preview:
        n_changed = 0
        for r in rows:
            fixed = auto_fix(r["text"])
            if fixed != r["text"]:
                n_changed += 1
                if n_changed <= 8:
                    print(f"\n=== {r['tid']} ===")
                    print("BEFORE:", r["text"])
                    print("AFTER: ", fixed)
        print(f"\nauto-fix would change {n_changed}/{len(rows)} descriptions")

    # Summary
    print()
    print(f"=== summary ===")
    print(f"  rows scanned:       {len(rows)}")
    print(f"  clean (0 findings): {n_clean} ({n_clean / max(len(rows), 1):.1%})")
    print(f"  findings by severity: {dict(by_severity)}")
    print(f"\nfindings by kind:")
    for k, n in by_kind.most_common():
        print(f"  {k:30s} {n}")

    print(f"\ntop {args.top} offenders (most findings):")
    per_row.sort(key=lambda r: -r["n_findings"])
    for r in per_row[:args.top]:
        print(f"  {r['n_findings']:3d}  {r['tid']:60s}  {r['text'][:80]}")

    # Markdown report
    md = [f"# Description Lint Report\n",
          f"Source: `data/base/solutions/banks/` + `data/canonical/puzzles.jsonl`",
          f"Rows scanned: **{len(rows)}**  Clean: **{n_clean}** "
          f"({n_clean / max(len(rows), 1):.1%})\n"]
    md.append("## Findings by kind\n")
    md.append("| kind | count |")
    md.append("|---|---:|")
    for k, n in by_kind.most_common():
        md.append(f"| `{k}` | {n} |")
    Path("/tmp/description_lint.md").write_text("\n".join(md) + "\n")
    print("\nwrote /tmp/description_lint.{jsonl,md}")


if __name__ == "__main__":
    main()
