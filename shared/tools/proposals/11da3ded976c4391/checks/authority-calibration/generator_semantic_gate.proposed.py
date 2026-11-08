#!/usr/bin/env python3
"""Task-linked semantic gate — the lesson-level companion the marginal gates lack.

22 independent generator workers (rounds v13-x / v13-y) reported the same
blindness in different words: `rule_smoke`, `generator_distribution_gate` and
`canonical_profile_gate` all stay green while the generated curriculum teaches
the WRONG thing (7d09ccad28c8 wrong key->direction mapping at 120/120 smoke;
1ce259f214c8 0/600 strict lessons; 3f2ed19e5882 ordinary draws that were
IDENTITY transformations; 612e018de4e1 a coarse profile matched by an 8x9
four-color impostor). Every generic gate measures MORPHOLOGY MARGINALS; none
can express "this lesson identifies the rule".

This gate runs the declared contract in `docs/SEMANTIC_GATE_CONTRACT.md` (v1,
frozen 2026-07-24; amended v1.1 2026-07-25 — see the "v1.1" section there).
A generator MAY declare any subset of:

  1. ``strict_canonical_like(grid) -> list[str] | bool`` — [] / True when the
     grid is a lawful instance of THIS task's canonical manifold, else short
     reasons / False. Both conventions are dispatched on TYPE, never on
     truthiness (spec amended 2026-07-24).
  2. ``SEMANTIC_WITNESSES: dict[str, Callable[[grid], bool]]`` — named branches
     the task must actually demonstrate.
  3. ``lesson_identifiable(demos, query) -> list[str]`` — [] when the demos
     uniquely determine the query answer, else reasons.

and, added 2026-07-25 (all OPT-IN, all default to zero blast radius because no
generator declares them yet):

  4. ``SEMANTIC_RIVALS: dict[str, Callable[[grid], grid]]`` +
     ``WITNESS_RIVALS: dict[str, list[str]]`` — a witness may CLAIM that when it
     fires, at least one NAMED rival rule differs from the authoritative
     (canonical Racket) output on that very grid. The gate verifies the claim.
     A witness firing 600/600 proves nothing if the rival it is supposed to
     refute also matches 600/600 — that measured case is why this exists.
     A witness with no rival claim is reported as WEAK — on the summary line,
     on its report line and in `weak_witnesses`; `--require-rival-witness`
     promotes that to a WARN.
  5. ``LESSON_COMPETITORS: dict[str, Callable[[grid], grid]]`` — named rival
     solvers scored against every materialized lesson, so an unidentifiable
     lesson can name WHICH competitor survived instead of only counting.
  6. ``CANONICAL_SHORTCUTS: dict[str, Callable[[grid], grid]]`` — task-local
     shortcuts asserted to fit ALL labeled canonical pairs. A false or
     unverifiable declaration fails. When a shortcut
     reproduces EVERY canonical pair, canonical cannot falsify it and only a
     GENERATED counterexample can; the gate says so and checks whether a
     rival-claiming witness supplies one.
  7. ``schedule_profile(seed, sample_index, difficulty=None) -> Hashable`` +
     ``SCHEDULE_PROFILES`` — a declared draw schedule whose residue/profile
     coverage the gate reports and (when the declared space is enumerated)
     checks.

Declaring NOTHING is lawful: the gate prints a LOUD advisory and exits 0, so
the legacy corpus is FLAGGED, never churned.

Usage:

    python3 scripts/generator_semantic_gate.py TASK_ID [TASK_ID ...] \
        [--per-band 50] [--lessons 20] [--min-strict-frac 0.05] [--strict] \
        [--require-rival-witness] [--require-shortcut-counterexample] \
        [--json-out PATH]

Exit codes: 0 = pass/advisory, 1 = warnings (or a bare advisory) under
``--strict``, 2 = failures.

Determinism: the census seeds come from `canonical_profile_gate._pinned_seed`
(imported, never re-derived) so this gate, the profile floor, every worker and
every intake measure the SAME census. No wall clock, no unseeded RNG.

Fail loud: a hook that raises, a hook that breaks its return contract, a
generation crash, an unmaterializable lesson — each is COUNTED and PRINTED.
There is no `except: pass` in this file.

Power-aware, so the loudness stays meaningful: the band-partial WARN only fires
when a band-zero is SURPRISING given the witness's own pooled rate (expected
firings >= MIN_EXPECTED_FIRINGS). A lawful rare branch is reported as a NOTE
with the census size that would actually test it, never as a warning. A witness
with ZERO POOLED firings is still a hard FAIL.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import importlib.util
import inspect
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ONE census definition, shared with the canonical-profile floor. A second copy
# of the seed derivation could drift, and then two gates would silently measure
# two different populations while quoting each other's numbers.
#
# `canonical_inputs` is the SAME shared reader the profile floor uses: it runs
# every canonical row through `_as_pairs` / `_norm_grid` (609/4341 canonical
# rows store grids as ROW-STRINGS, 1239/4350 store `test` as a bare dict, not a
# list). Re-implementing that read here would silently feed the hook garbage
# and blame the hook for it.
from scripts.canonical_profile_gate import (  # noqa: E402
    BANDS, _pinned_seed, canonical_inputs, canonical_pairs,
)
# ONE grid comparison, shared with the verifier: canonical stores some grids as
# row-strings, so `==` on the raw values is not answer-equivalence.
from scripts.coder_synth_verify import _grids_equal  # noqa: E402

HOOK_NAMES = ("strict_canonical_like", "SEMANTIC_WITNESSES", "lesson_identifiable")
MAX_EXAMPLES = 3          # per error class: loud but bounded
MAX_TOP_REASONS = 5
PREDICATE_FALSE_REASON = "predicate returned False"

# Minimum EXPECTED firings before a band-zero is treated as evidence of a gap.
#
# The band-partial WARN used to fire on any band with 0 hits, regardless of how
# rare the witness legitimately is — so a LAWFUL rare branch warned forever and
# no affordable census cured it. Measured (battery sweep over 13 hooked
# generators, 219 witness/band cells): the rarest lawful cell is
# 796907d6d950/template_size_6/hard at p ~= 0.033, which warns at --per-band
# 12/20/30 and only goes clean at 60+; P(spurious band-zero) = (1-p)^n is 0.67
# @12, 0.36 @30, 0.13 @60. A branch rarer than ~1/150 would warn spuriously at
# any census we can afford.
#
# The guard asks the only question that scales: given this witness's OWN pooled
# firing rate p_hat, is a zero in this band SURPRISING? Expected count is
# p_hat * n_band; requiring expected >= 3 bounds the false-alarm probability at
# (1 - p_hat)^n <= e^-3 ~= 4.98%, for every p_hat and every n. Below the floor
# the cell is under-powered: recorded as an informational NOTE, never a WARN.
#
# A witness with ZERO POOLED firings is untouched by this guard — that is the
# "declared but never generated" defect and stays a hard FAIL.
MIN_EXPECTED_FIRINGS = 3.0

# Default minimum strict-canonical-like rate below which the gate WARNs.
# Mirrors `canonical_profile_gate.--warn-frac` (same 0.05, same semantics: zero
# support is the hard FAIL, low-but-nonzero is a visible WARN).
#
# WHY 0.05 AND NOT 0.25 — measured, not guessed. Strict rates at --per-band 150
# for the 12 completed generators:
#
#   100.0  100.0  100.0  100.0  50.9  42.2  30.2  22.7  16.9  13.6  9.6  5.6
#
# and the two known-DEFECTIVE pre-repair sources measure 12.0% (0ae119475d57)
# and 44.0% (f67822970902, 33/75). Interleave them and the conclusion is
# forced: 44% defective sits ABOVE seven of the twelve verified-good rates, and
# 12% defective sits above two of them. **No global threshold separates the two
# classes** — a floor set to catch either one condemns generators we have just
# verified are correct (56f043832ecb at 9.6% and 1672855ac30c at 5.6% teach a
# deliberately broader-than-canonical distribution; that breadth is a defended
# design choice, not a defect).
#
# So the global floor is scoped to what it CAN honestly do: catch
# effectively-zero support that is not literally zero. The contract's own
# evidence table has exactly that class — 5ee8de1860a7 measured 1/600 (0.17%)
# while the coarse profile passed, and f67822970902's witness fired in 5/200
# easy draws (2.5%). 0.05 sits below every verified-good rate (min 5.6%) and
# above both documented defect rates. It is a floor against near-zero, not a
# quality bar.
#
# The rate-based discrimination the 0ae119475d57 class needs is TASK-LINKED,
# not global: a generator may declare `MIN_STRICT_FRAC = 0.9` and the gate
# holds it to its own promise. That is the same principle the whole contract
# rests on — task-linked semantics beat global marginals.
DEFAULT_MIN_STRICT_FRAC = 0.05

# Rival-disagreement verification calls the canonical RACKET rule once per
# checked grid, so it is the only part of the census that costs a subprocess
# round-trip. Cap it per witness: the claim "at least one named rival differs
# here" is a per-grid property, and 60 pinned firings settle it. The cap is
# COUNTED and reported (`rival_checked` vs `hits`), never silent.
MAX_RIVAL_CHECKS = 60

# Lesson sample_index stride. Every lesson used to start at sample_index 0,
# which is the aliasing defect this stride fixes: a generator scheduling its
# profiles on `sample_index % m` was shown ONLY residue 0 as a start offset, so
# whole branches of a declared schedule were never materialized. run_one
# consumes CONSECUTIVE sample indexes for the demos+query of one lesson, so
# lesson i starts at i*STRIDE. Longer lessons or rejected draws can overlap
# sample-index ranges. A stride of 11 visits residues for moduli coprime to 11;
# this sampled plan does not establish exhaustive cyclic-window coverage.
# The seed varies independently (it is a sha256 of task/band/index), so the
# pair (seed, sample_index) is not stepped in lockstep either.
LESSON_SAMPLE_STRIDE = 11

# Moduli whose residue coverage is reported for the census. A declared schedule
# keyed on `seed`, `sample_index` or their sum aliases exactly when the census
# fails to visit every residue of its modulus; 2..8 covers every schedule
# modulus seen in the corpus so far. Coverage is only JUDGED when the census is
# big enough for a miss to mean something (>= ALIAS_MIN_DRAWS_PER_RESIDUE draws
# per residue), for the same power reason as MIN_EXPECTED_FIRINGS.
SCHEDULE_MODULI = (2, 3, 4, 5, 6, 7, 8)
ALIAS_MIN_DRAWS_PER_RESIDUE = 4


# ---------------------------------------------------------------------------
# Simple shortcuts for the canonical-ambiguity detector (6).
#
# These are the shortcuts that need no task knowledge at all. When one of them
# reproduces EVERY canonical pair, the canonical set cannot falsify it — only a
# GENERATED counterexample can. Measured instance: 9df4a42fced1, where all 4/4
# canonical pairs were answer-equivalent under a keep-seed-position shortcut
# (`all_seeds_centered=true`) and the refuting witness fired 311/600 on
# generated draws only.
#
# NOTE the false-positive class this cannot rule out on its own: if the task's
# TRUE rule *is* `flip_lr`, then "flip_lr reproduces every canonical pair" is
# correct and uninteresting. That is why the generic detector is a NOTE by
# default and only a WARN under --require-shortcut-counterexample, while a
# TASK-DECLARED shortcut (which asserts "this is a WRONG rule I want refuted")
# warns on its own.
# ---------------------------------------------------------------------------

def _rot90(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


SIMPLE_SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": lambda g: [list(r) for r in g],
    "flip_lr": lambda g: [list(reversed(r)) for r in g],
    "flip_ud": lambda g: [list(r) for r in reversed(g)],
    "rot90": _rot90,
    "rot180": lambda g: [list(reversed(r)) for r in reversed(g)],
    "rot270": lambda g: _rot90(_rot90(_rot90(g))),
    "transpose": lambda g: [list(r) for r in zip(*g)],
}


# The prelude spelling of each SIMPLE_SHORTCUTS entry. `rotate-cw` is
# `(flip-lr (transpose g))`, which is exactly `_rot90`; `rotate-ccw` is its
# inverse, i.e. `rot270`.
_AUTHORITY_SHORTCUT_HEADS: dict[str, str] = {
    "transpose": "transpose",
    "flip-lr": "flip_lr",
    "flip-ud": "flip_ud",
    "rotate-cw": "rot90",
    "rotate-ccw": "rot270",
    "rotate-180": "rot180",
}

# `(rule! (transpose g))` or `(rule! (lambda (g) (transpose g)))`, whitespace
# collapsed. Anything more complex is NOT a bare dihedral authority.
_BARE_AUTHORITY_RE = re.compile(
    r"^\(rule!\s*(?:\(lambda\s*\(g\)\s*)?\("
    r"(transpose|flip-lr|flip-ud|rotate-cw|rotate-ccw|rotate-180)\s+g\)+$"
)

# Finite, exact syntax aliases; this is not a symbolic equivalence checker.
_EXACT_AUTHORITY_ALIASES = {
    "(rule! (flip-ud (flip-lr g)))": "rot180",
    "(rule! (flip-lr (flip-ud g)))": "rot180",
    "(rule! (lambda (g) (flip-ud (flip-lr g))))": "rot180",
    "(rule! (lambda (g) (flip-lr (flip-ud g))))": "rot180",
}


def authoritative_simple_shortcut(task_id: str) -> str | None:
    """The SIMPLE_SHORTCUTS name that IS this task's selected rule, if any.

    WFB-2001 (3f4b5ff68c93, 2026-07-27): the canonical rule is literally
    `(rule! (transpose g))`, so all 5 canonical pairs are answer-equivalent
    under the generic `transpose` shortcut. Under
    `--require-shortcut-counterexample` the gate demanded a GENERATED
    counterexample to `transpose` — i.e. a training row on which the task's own
    authority is wrong. There is no such row; producing one would poison the
    corpus, so the worker correctly left the stage red and escalated.

    This is a CLASS, not one task: 6 canonical rows are bare dihedral
    one-liners (4 transpose, 1 rotate-cw, 1 rotate-180) and every one of them
    hits the same false positive.

    The exclusion is deliberately narrow — only a rule whose whole normalized
    body is one prelude dihedral call applied to `g` qualifies. A shortcut that
    merely *happens* to agree on canonical still carries its obligation, and a
    DECLARED rival is never excluded: the author asserting "this is a plausible
    WRONG rule" outranks this heuristic.

    Returns None on any read failure — never raises, never silently passes.
    """
    try:
        program = _canonical_program_cached(task_id)
    except Exception:
        return None
    if not program:
        return None
    normalized = " ".join(program.split())
    # A first-class prelude callable is also an exact authority. Match the
    # whole normalized program; compound and unknown forms stay ineligible.
    for head, shortcut in _AUTHORITY_SHORTCUT_HEADS.items():
        if normalized == f"(rule! {head})":
            return shortcut
    match = _BARE_AUTHORITY_RE.match(normalized)
    if match:
        return _AUTHORITY_SHORTCUT_HEADS.get(match.group(1))
    return _EXACT_AUTHORITY_ALIASES.get(normalized)


# ---------------------------------------------------------------------------
# The canonical rule as an oracle — opened ONCE per task, and only when a hook
# actually needs the authoritative output.
# ---------------------------------------------------------------------------

class _RuleOracle:
    """The task's canonical Racket rule. `apply(grid) -> (output, error)`.

    Two callers need the AUTHORITATIVE output: rival-disagreement verification
    (which compares a named rival against it on a census grid) and lesson
    materialization (which needs it for every demo and query pair). Opening the
    bundle + bridge twice would pay the Racket startup cost twice and — worse —
    let two halves of one gate report outputs from two different processes.

    `error` is non-None when the oracle could not be opened. It is a COUNTED,
    reported failure that the caller surfaces; there is no silent skip.
    """

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        self.bundle: Any = None
        self.bridge: Any = None
        self.fn_name: str | None = None
        self.error: str | None = None
        self._runner: Any = None
        if not shutil.which("racket"):
            self.error = (
                "RACKET_MISSING: racket not on PATH — the canonical rule "
                "cannot be applied, so nothing authoritative can be compared"
            )
            return
        from puzzle_generators import runner  # late import: keeps --help offline

        self._runner = runner
        try:
            self.bundle = runner._load_bundle(task_id)
        except Exception as exc:
            self.error = f"LOAD_BUNDLE_FAIL: {type(exc).__name__}: {str(exc)[:200]}"
            return
        try:
            self.bridge, self.fn_name = runner._open_bridge_with_rule(
                self.bundle.rule_callable_text)
        except Exception as exc:
            self.error = f"BRIDGE_OPEN_FAIL: {type(exc).__name__}: {str(exc)[:200]}"

    @property
    def ready(self) -> bool:
        return self.bridge is not None

    def apply(self, grid: Any) -> tuple[Any, str | None]:
        """Authoritative output for `grid`. Exactly one of the two is non-None."""
        if not self.ready:
            return None, self.error
        try:
            return self._runner._apply_rule(
                self.bridge, self.fn_name, copy.deepcopy(grid)), None
        except Exception as exc:
            return None, (
                f"canonical rule raised {type(exc).__name__}: {str(exc)[:200]}"
            )

    def close(self) -> None:
        if self.bridge is None:
            return
        bridge, self.bridge = self.bridge, None
        try:
            bridge.shutdown()
        except Exception as exc:  # never mask the gate's own result
            print(
                f"LOUD: racket bridge shutdown failed for {self.task_id}: "
                f"{type(exc).__name__}: {exc}",
                file=sys.stderr,
            )


# ---------------------------------------------------------------------------
# Hook invocation — every call is normalized and every failure is returned,
# never swallowed.
# ---------------------------------------------------------------------------

def _call_reasons_hook(
    fn: Callable, *args: Any, allow_bool: bool = False,
) -> tuple[list[str] | None, str | None]:
    """Call a reasons hook on deep copies. Returns (reasons, error).

    Exactly one of the two is non-None. A raise is an error.

    Return values are dispatched on TYPE, NEVER on truthiness (contract v1
    amended 2026-07-24). `bool` is tested FIRST — before the list branch and
    before anything that could treat it as an int, since `isinstance(True, int)`
    is True. `[]` and `False` both mean "lawful"/"not lawful" respectively and
    must never collapse into each other:

        []               -> lawful                (allow_bool irrelevant)
        ["reason", ...]  -> not lawful, w/ reasons
        True             -> lawful                (allow_bool only)
        False            -> not lawful, reason = PREDICATE_FALSE_REASON
        anything else    -> contract violation, reported as an error

    `allow_bool` is True for `strict_canonical_like` (which reads as a
    predicate and shipped in bool form in 616a5c01a7ea) and False for
    `lesson_identifiable`, whose spec section was NOT amended and remains
    list[str]-only.
    """
    try:
        result = fn(*[copy.deepcopy(a) for a in args])
    except Exception as exc:
        return None, f"raised {type(exc).__name__}: {exc}"
    if isinstance(result, bool):
        if not allow_bool:
            return None, (
                f"returned bool {result!r} — contract is list[str] "
                "([] means lawful, otherwise short human-readable reasons)"
            )
        return ([] if result else [PREDICATE_FALSE_REASON]), None
    if isinstance(result, (list, tuple)):
        return [str(r) for r in result], None
    return None, (
        f"returned {type(result).__name__} {result!r} — contract is "
        + ("list[str] | bool" if allow_bool else "list[str]")
        + " ([] / True means lawful, otherwise short human-readable reasons"
        + (" or False)" if allow_bool else ")")
    )


def _call_witness(fn: Callable, grid: Any) -> tuple[bool | None, str | None]:
    """Call a witness predicate on a deep copy. Returns (fired, error)."""
    try:
        return bool(fn(copy.deepcopy(grid))), None
    except Exception as exc:
        return None, f"raised {type(exc).__name__}: {exc}"


def _compact_grid_preview(
    grid: Any, *, max_rows: int = 12, max_cols: int = 20,
) -> dict[str, Any]:
    """Return a bounded ARC-grid rendering for a failed rival claim."""
    if not isinstance(grid, (list, tuple)):
        return {"shape": None, "rows": [repr(grid)[:max_cols]], "truncated": True}
    height = len(grid)
    width = max(
        (len(row) for row in grid if isinstance(row, (list, tuple))),
        default=0,
    )
    rows: list[str] = []
    for row in grid[:max_rows]:
        if not isinstance(row, (list, tuple)):
            rows.append(repr(row)[:max_cols])
            continue
        rendered = "".join(
            str(value) if isinstance(value, int) and 0 <= value <= 9 else "?"
            for value in row[:max_cols]
        )
        rows.append(rendered + ("…" if len(row) > max_cols else ""))
    if height > max_rows:
        rows.append("…")
    return {
        "shape": [height, width],
        "rows": rows,
        "truncated": height > max_rows or width > max_cols,
    }


def _census_for_power(rate: float) -> int:
    """Smallest --per-band that would make a band-zero judgeable at `rate`.

    Solves expected = rate * n >= MIN_EXPECTED_FIRINGS. Reported so a rare-branch
    NOTE tells the operator the actual price of testing it instead of leaving
    them to guess.
    """
    if rate <= 0:
        return 0
    return int(-(-MIN_EXPECTED_FIRINGS // rate))  # ceil without importing math


def _effective_min_strict_frac(
    gen: Any, cli_value: float,
) -> tuple[float, str, list[str]]:
    """Resolve the strict-rate floor for one task: declared beats CLI.

    A generator MAY declare `MIN_STRICT_FRAC` (0..1). A task-linked floor is
    the only kind that can discriminate — see DEFAULT_MIN_STRICT_FRAC for the
    measurement showing no global value separates good from defective. Returns
    (floor, source, warnings).
    """
    declared = getattr(gen, "MIN_STRICT_FRAC", None)
    if declared is None:
        return cli_value, "cli", []
    if isinstance(declared, bool) or not isinstance(declared, (int, float)):
        return cli_value, "cli", [
            f"MIN_STRICT_FRAC={declared!r} is {type(declared).__name__}, "
            f"expected a number in 0..1 — falling back to --min-strict-frac "
            f"{cli_value}"
        ]
    if not 0.0 <= float(declared) <= 1.0:
        return cli_value, "cli", [
            f"MIN_STRICT_FRAC={declared!r} is outside 0..1 — falling back to "
            f"--min-strict-frac {cli_value}"
        ]
    return float(declared), "declared", []


def _declared_witnesses(gen: Any) -> tuple[dict[str, Callable], list[str]]:
    """Read SEMANTIC_WITNESSES. Returns (witnesses, errors)."""
    raw = getattr(gen, "SEMANTIC_WITNESSES", None)
    if raw is None:
        return {}, []
    if not isinstance(raw, dict):
        return {}, [
            f"SEMANTIC_WITNESSES is {type(raw).__name__}, expected "
            "dict[str, Callable[[grid], bool]]"
        ]
    witnesses: dict[str, Callable] = {}
    errors: list[str] = []
    for name, pred in raw.items():
        if not callable(pred):
            errors.append(
                f"SEMANTIC_WITNESSES[{name!r}] is {type(pred).__name__}, "
                "expected a callable predicate"
            )
            continue
        witnesses[str(name)] = pred
    return witnesses, errors


def _declared_branch_witnesses(
    gen: Any, witnesses: dict[str, Callable]
) -> tuple[set[str], list[str]]:
    """Read BRANCH_WITNESSES (adopted 2026-07-29, EWF-002038).

    A collection of SEMANTIC_WITNESSES names the author declares as POSITIVE
    branch coverage — they prove a scheduled branch is present, and never
    claimed to refute a rival. They are reported as branch coverage instead of
    being flagged weak, so positive branch counts stay first-class without a
    synthetic WITNESS_RIVALS mapping."""
    raw = getattr(gen, "BRANCH_WITNESSES", None)
    if raw is None:
        return set(), []
    if not isinstance(raw, (list, tuple, set, frozenset)):
        return set(), [
            f"BRANCH_WITNESSES is {type(raw).__name__}, expected a "
            "list/set of SEMANTIC_WITNESSES names"
        ]
    names = {str(name) for name in raw}
    unknown = sorted(names - set(witnesses))
    errors = []
    if unknown:
        errors.append(
            f"BRANCH_WITNESSES names {unknown} which are not in "
            "SEMANTIC_WITNESSES"
        )
    return names & set(witnesses), errors


def _declared_grid_rules(gen: Any, attr: str) -> tuple[dict[str, Callable], list[str]]:
    """Read a `dict[str, Callable[[grid], grid]]` declaration. (rules, errors).

    Shared by SEMANTIC_RIVALS, LESSON_COMPETITORS and CANONICAL_SHORTCUTS —
    three declarations with one shape. A non-dict, or a non-callable value, is
    a contract violation and is returned as an error, never dropped.
    """
    raw = getattr(gen, attr, None)
    if raw is None:
        return {}, []
    if not isinstance(raw, dict):
        return {}, [
            f"{attr} is {type(raw).__name__}, expected "
            "dict[str, Callable[[grid], grid]]"
        ]
    rules: dict[str, Callable] = {}
    errors: list[str] = []
    for name, fn in raw.items():
        if not callable(fn):
            errors.append(
                f"{attr}[{name!r}] is {type(fn).__name__}, expected a callable "
                "grid -> grid"
            )
            continue
        rules[str(name)] = fn
    return rules, errors


def _declared_witness_rivals(
    gen: Any, witnesses: dict[str, Callable], rivals: dict[str, Callable],
) -> tuple[dict[str, list[str]], list[str]]:
    """Read WITNESS_RIVALS. (witness -> named rivals it claims to refute, errors).

    THE CONVENTION (contract v1.1): declaring
    ``WITNESS_RIVALS = {"w": ["rival_a", "rival_b"]}`` is the witness CLAIMING
    that on every grid where `w` fires, at least ONE of the named rivals
    produces a DIFFERENT answer than the canonical rule does. That is the claim
    the gate verifies; a witness without it can only prove that some feature is
    PRESENT, which is what let a structural witness fire 600/600 while the
    rival it was supposed to refute also matched 600/600.

    A single string is accepted as shorthand for a one-element list.
    """
    raw = getattr(gen, "WITNESS_RIVALS", None)
    if raw is None:
        return {}, []
    if not isinstance(raw, dict):
        return {}, [
            f"WITNESS_RIVALS is {type(raw).__name__}, expected "
            "dict[str, list[str]] mapping a witness name to the rival names it "
            "claims to refute"
        ]
    claims: dict[str, list[str]] = {}
    errors: list[str] = []
    for witness, named in raw.items():
        witness = str(witness)
        if isinstance(named, str):
            named = [named]
        if not isinstance(named, (list, tuple)) or not named:
            errors.append(
                f"WITNESS_RIVALS[{witness!r}] is {named!r}, expected a "
                "non-empty list of SEMANTIC_RIVALS names"
            )
            continue
        if witness not in witnesses:
            errors.append(
                f"WITNESS_RIVALS names witness {witness!r}, which is not in "
                f"SEMANTIC_WITNESSES (declared: {sorted(witnesses)})"
            )
            continue
        unknown = [str(n) for n in named if str(n) not in rivals]
        if unknown:
            errors.append(
                f"WITNESS_RIVALS[{witness!r}] names {unknown} which are not in "
                f"SEMANTIC_RIVALS (declared: {sorted(rivals)})"
            )
            continue
        claims[witness] = [str(n) for n in named]
    return claims, errors


def _declared_schedule(gen: Any) -> tuple[Callable | None, list | None, list[str]]:
    """Read `schedule_profile` + optional `SCHEDULE_PROFILES`. (fn, space, errors).

    `schedule_profile(seed, sample_index, difficulty=None) -> Hashable` names
    which branch of a declared draw schedule a (seed, sample_index) pair lands
    on. The gate reports the observed profile histogram per band; when
    `SCHEDULE_PROFILES` enumerates the full declared space, a profile the
    census NEVER visits is a warning — that is modular aliasing, and it reads
    as a missing generator branch if nobody reports it.
    """
    fn = getattr(gen, "schedule_profile", None)
    errors: list[str] = []
    if fn is not None and not callable(fn):
        return None, None, [
            f"schedule_profile is {type(fn).__name__}, expected a callable "
            "(seed, sample_index, difficulty=None) -> Hashable"
        ]
    space = getattr(gen, "SCHEDULE_PROFILES", None)
    if space is not None:
        if not isinstance(space, (list, tuple, set, frozenset)):
            errors.append(
                f"SCHEDULE_PROFILES is {type(space).__name__}, expected a "
                "sequence enumerating every declared profile"
            )
            space = None
        else:
            space = list(space)
    if space is not None and fn is None:
        errors.append(
            "SCHEDULE_PROFILES is declared without a schedule_profile("
            "seed, sample_index, difficulty=None) function — the gate cannot "
            "tell which profile a draw landed on"
        )
    return fn, space, errors


def _accepts_difficulty(gen: Any) -> bool:
    """Does this module's `generate` accept a `difficulty` keyword?

    The spec signature is `generate(seed, sample_index, *, difficulty=None,
    **overrides)`, but the corpus predates the spec. Passing `difficulty` to a
    generator that cannot take it turns lesson materialization into a crash and
    blames the generator for the gate's assumption, so the gate ASKS first and
    REPORTS the answer (`lessons.difficulty_passed`) rather than assuming it.
    """
    fn = getattr(gen, "generate", None)
    if not callable(fn):
        return False
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False
    if "difficulty" in params:
        return True
    return any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())


# ---------------------------------------------------------------------------
# The pinned census (hooks 1 + 2 share it — same seeds, same grids)
# ---------------------------------------------------------------------------

def _census_sample_index(seed: int, index: int) -> int:
    """The pinned off-diagonal sample index. NEVER change this derivation.

    `seed` is a sha256 of (task_id, band, index) — it is pseudo-random per
    index, not a counter — so `seed` and `sample_index` do NOT step in
    lockstep, and a schedule keyed on `seed + sample_index` cannot alias the
    way one keyed on two counters stepped together would. That is a claim the
    gate MEASURES rather than asserts: `census["schedule"]["residues"]` records
    the observed residue coverage for moduli 2..8 over `seed`, `sample_index`
    and `seed + sample_index`, and `census["schedule"]["aliased"]` lists any
    cell that failed to cover its modulus.
    """
    return seed % 7919 + index


def schedule_coverage(
    draws: list[tuple[str, int, int]],
    *,
    profile_fn: Callable | None = None,
    profile_space: list | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Residue / profile coverage of the census draw log. (stats, errors).

    `draws` is the pinned [(band, seed, sample_index)] log. Reported, not
    inferred: every number here is a count over the draws that actually
    happened.
    """
    stats: dict[str, Any] = {
        "draws": len(draws),
        "sample_index_rule": "seed % 7919 + index (pinned)",
        "moduli": list(SCHEDULE_MODULI),
        "residues": {},
        "aliased": [],
        "profiles": None,
        "profiles_per_band": None,
        "profiles_missing": None,
        "profile_errors": 0,
        "profile_error_examples": [],
    }
    errors: list[str] = []
    expressions = {
        "seed": lambda seed, si: seed,
        "sample_index": lambda seed, si: si,
        "seed+sample_index": lambda seed, si: seed + si,
    }
    for label, expr in expressions.items():
        per_modulus: dict[str, Any] = {}
        for modulus in SCHEDULE_MODULI:
            seen = sorted({expr(seed, si) % modulus for _, seed, si in draws})
            judged = len(draws) >= ALIAS_MIN_DRAWS_PER_RESIDUE * modulus
            per_modulus[str(modulus)] = {
                "covered": len(seen), "of": modulus,
                "residues": seen, "judged": judged,
            }
            if judged and len(seen) < modulus:
                stats["aliased"].append({
                    "expression": label, "modulus": modulus,
                    "covered": len(seen), "residues": seen,
                })
        stats["residues"][label] = per_modulus

    if profile_fn is not None:
        pooled: Counter[str] = Counter()
        per_band: dict[str, Counter] = {}
        for band, seed, sample_index in draws:
            try:
                profile = profile_fn(seed, sample_index, difficulty=band)
            except TypeError:
                try:
                    profile = profile_fn(seed, sample_index)
                except Exception as exc:
                    stats["profile_errors"] += 1
                    if len(stats["profile_error_examples"]) < MAX_EXAMPLES:
                        stats["profile_error_examples"].append(
                            f"schedule_profile(seed={seed}, sample_index="
                            f"{sample_index}) raised {type(exc).__name__}: {exc}"
                        )
                    continue
            except Exception as exc:
                stats["profile_errors"] += 1
                if len(stats["profile_error_examples"]) < MAX_EXAMPLES:
                    stats["profile_error_examples"].append(
                        f"schedule_profile(seed={seed}, sample_index="
                        f"{sample_index}, difficulty={band!r}) raised "
                        f"{type(exc).__name__}: {exc}"
                    )
                continue
            # Plain string profiles are already human-readable identifiers.
            # repr() is reserved for non-string hashable profile objects.
            key = profile if isinstance(profile, str) else repr(profile)
            pooled[key] += 1
            per_band.setdefault(band, Counter())[key] += 1
        stats["profiles"] = dict(pooled)
        stats["profiles_per_band"] = {b: dict(c) for b, c in per_band.items()}
        if profile_space is not None:
            missing = [
                p if isinstance(p, str) else repr(p)
                for p in profile_space
                if (p if isinstance(p, str) else repr(p)) not in pooled
            ]
            stats["profiles_missing"] = missing
        if stats["profile_errors"]:
            errors.append(
                f"schedule_profile raised on {stats['profile_errors']}/"
                f"{len(draws)} draws: "
                + "; ".join(stats["profile_error_examples"])
            )
    return stats, errors

def run_census(
    task_id: str,
    gen: Any,
    *,
    per_band: int,
    strict_hook: Callable | None,
    witnesses: dict[str, Callable],
    rivals: dict[str, Callable] | None = None,
    witness_rivals: dict[str, list[str]] | None = None,
    oracle_factory: Callable[[], _RuleOracle] | None = None,
    profile_fn: Callable | None = None,
    profile_space: list | None = None,
) -> dict[str, Any]:
    """Draw `per_band` pinned instances per band and score the declared hooks.

    Returns a fully count-backed dict; hook failures are recorded, not raised.

    `rivals` / `witness_rivals` / `oracle_factory` are the OPT-IN
    rival-disagreement path (contract v1.1): when a witness claims that its
    firing implies a named rival differs from the authoritative output, the
    claim is verified on the grids where it fired. Omitting them leaves the
    census byte-identical to v1 — the pinned seeds are unchanged.
    """
    rivals = rivals or {}
    witness_rivals = witness_rivals or {}
    census: dict[str, Any] = {
        "per_band": {}, "draws": 0, "crashes": 0,
        "planned": per_band * len(BANDS),
    }
    draw_log: list[tuple[str, int, int]] = []
    # Grids a rival-claiming witness fired on, in pinned census order. Capped at
    # MAX_RIVAL_CHECKS per witness; the cap is reported, never silent.
    rival_queue: dict[str, list[tuple[str, int, int, Any]]] = {
        name: [] for name in witness_rivals
    }
    strict_stats: dict[str, Any] = {
        "per_band": {}, "draws": 0, "hits": 0, "hook_errors": 0,
        "rate": 0.0, "top_reasons": [],
    }
    wit_stats: dict[str, Any] = {
        name: {"per_band": {}, "draws": 0, "hits": 0, "hook_errors": 0}
        for name in witnesses
    }
    crash_messages: list[str] = []
    hook_error_messages: list[str] = []
    reason_counter: Counter[str] = Counter()

    for band in BANDS:
        band_draws = band_crashes = band_strict = band_hook_errors = 0
        band_wit = {name: 0 for name in witnesses}
        for index in range(per_band):
            seed = _pinned_seed(task_id, band, index)
            sample_index = _census_sample_index(seed, index)
            try:
                grid = gen.generate(seed, sample_index, difficulty=band)
            except Exception as exc:
                band_crashes += 1
                if len(crash_messages) < MAX_EXAMPLES:
                    crash_messages.append(
                        f"generate({band}, seed={seed}, sample_index="
                        f"{sample_index}) raised {type(exc).__name__}: {exc}"
                    )
                continue
            band_draws += 1
            draw_log.append((band, seed, sample_index))

            if strict_hook is not None:
                reasons, error = _call_reasons_hook(
                    strict_hook, grid, allow_bool=True)
                if error is not None:
                    band_hook_errors += 1
                    if len(hook_error_messages) < MAX_EXAMPLES:
                        hook_error_messages.append(
                            f"strict_canonical_like({band}, seed={seed}) {error}"
                        )
                elif not reasons:
                    band_strict += 1
                else:
                    for reason in reasons[:MAX_TOP_REASONS]:
                        reason_counter[reason[:120]] += 1

            for name, pred in witnesses.items():
                fired, error = _call_witness(pred, grid)
                if error is not None:
                    wit_stats[name]["hook_errors"] += 1
                    if len(hook_error_messages) < MAX_EXAMPLES:
                        hook_error_messages.append(
                            f"SEMANTIC_WITNESSES[{name!r}]({band}, seed={seed}) "
                            f"{error}"
                        )
                elif fired:
                    band_wit[name] += 1
                    queue = rival_queue.get(name)
                    if queue is not None and len(queue) < MAX_RIVAL_CHECKS:
                        queue.append((band, seed, sample_index, grid))

        census["per_band"][band] = {
            "planned": per_band, "draws": band_draws, "crashes": band_crashes,
        }
        census["draws"] += band_draws
        census["crashes"] += band_crashes

        if strict_hook is not None:
            strict_stats["per_band"][band] = {
                "draws": band_draws, "hits": band_strict,
                "hook_errors": band_hook_errors,
                "rate": (band_strict / band_draws) if band_draws else 0.0,
            }
            strict_stats["draws"] += band_draws
            strict_stats["hits"] += band_strict
            strict_stats["hook_errors"] += band_hook_errors

        for name in witnesses:
            wit_stats[name]["per_band"][band] = {
                "draws": band_draws, "hits": band_wit[name],
            }
            wit_stats[name]["draws"] += band_draws
            wit_stats[name]["hits"] += band_wit[name]

    if strict_hook is not None and strict_stats["draws"]:
        strict_stats["rate"] = strict_stats["hits"] / strict_stats["draws"]
    strict_stats["top_reasons"] = [
        [reason, count] for reason, count in reason_counter.most_common(MAX_TOP_REASONS)
    ]
    for name, stats in wit_stats.items():
        stats["bands_fired"] = sorted(
            b for b, row in stats["per_band"].items() if row["hits"] > 0
        )
        stats["bands_missing"] = sorted(
            b for b, row in stats["per_band"].items() if row["hits"] == 0
        )
        # Power accounting: a band-zero is only evidence of a gap when this
        # witness's own pooled rate says firings were EXPECTED there.
        rate = (stats["hits"] / stats["draws"]) if stats["draws"] else 0.0
        stats["rate"] = rate
        for row in stats["per_band"].values():
            n = row["draws"]
            row["expected"] = rate * n
            row["p_zero"] = (1.0 - rate) ** n if n else 1.0
        stats["bands_missing_judged"] = [
            b for b in stats["bands_missing"]
            if stats["per_band"][b]["expected"] >= MIN_EXPECTED_FIRINGS
        ]
        stats["bands_missing_underpowered"] = [
            b for b in stats["bands_missing"]
            if stats["per_band"][b]["expected"] < MIN_EXPECTED_FIRINGS
        ]

    schedule_stats, schedule_errors = schedule_coverage(
        draw_log, profile_fn=profile_fn, profile_space=profile_space)
    census["schedule"] = schedule_stats

    rival_stats = _verify_rival_claims(
        rival_queue, rivals=rivals, witness_rivals=witness_rivals,
        oracle_factory=oracle_factory, task_id=task_id, generator=gen,
    )
    for name, stats in rival_stats.items():
        wit_stats[name]["rival_claim"] = stats

    census["crash_examples"] = crash_messages
    census["hook_error_examples"] = hook_error_messages
    return {
        "census": census,
        "strict_canonical": strict_stats if strict_hook is not None else None,
        "witnesses": wit_stats,
        "crash_messages": crash_messages,
        "hook_error_messages": hook_error_messages,
        "schedule_errors": schedule_errors,
    }


# ---------------------------------------------------------------------------
# 1. Rival-disagreement verification — "the witness fired" is not evidence
# ---------------------------------------------------------------------------

def _witness_grid(grid: Any) -> list[list[int]] | None:
    """A complete, bounded ARC grid for JSON evidence; never a clipped preview."""
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return None
    rows = []
    for row in grid:
        if isinstance(row, str) and 1 <= len(row) <= 30 and all(c in "0123456789" for c in row):
            row = [int(c) for c in row]
        if not isinstance(row, (list, tuple)) or not 1 <= len(row) <= 30:
            return None
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            return None
        rows.append(list(row))
    if any(len(row) != len(rows[0]) for row in rows):
        return None
    return rows


def _witness_source_binding(generator: Any, oracle: Any) -> dict[str, Any]:
    """Observed generator bytes and the exact source/callable used by the oracle."""
    binding: dict[str, Any] = {
        "generator_sha256": None, "rule_source_sha256": None,
        "rule_callable_sha256": None, "rule_task_id": None, "errors": [],
    }
    path = getattr(generator, "__file__", None)
    if path is not None:
        try:
            binding["generator_sha256"] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        except (OSError, TypeError, ValueError) as exc:
            binding["errors"].append(f"generator source unavailable: {type(exc).__name__}")
    bundle = getattr(oracle, "bundle", None)
    for field, name in [("rule_source", "rule_source_sha256"),
                        ("rule_callable_text", "rule_callable_sha256")]:
        text = getattr(bundle, field, None)
        if isinstance(text, str):
            binding[name] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    rule_id = getattr(bundle, "rule_task_id", None)
    binding["rule_task_id"] = rule_id if isinstance(rule_id, str) else None
    binding["status"] = (
        "bound" if all(binding[name] is not None for name in
                       ("generator_sha256", "rule_source_sha256", "rule_callable_sha256"))
        else "incomplete"
    )
    return binding


def _semantic_witness_example(
    *, task_id: str | None, generator: Any, oracle: Any, witness: str, rival: str,
    band: str, seed: int, sample_index: int, grid: Any, authoritative: Any,
    rival_output: Any,
) -> dict[str, Any] | None:
    grids = [_witness_grid(value) for value in (grid, authoritative, rival_output)]
    if any(value is None for value in grids):
        return None
    validator = getattr(generator, "self_check", None)
    validation: dict[str, Any] = {"status": "not_declared"}
    if callable(validator):
        reasons, error = _call_reasons_hook(validator, grid, allow_bool=True)
        validation = {"status": "error" if error else "failed" if reasons else "passed",
                      "reasons": reasons, "error": error}
    return {
        "schema": "arcpuzzles-semantic-witness-v1",
        "task_id": task_id, "witness": witness, "rival": rival,
        "recipe": {"seed": seed, "sample_index": sample_index,
                   "difficulty": band, "overrides": {}},
        "input": grids[0], "authoritative_output": grids[1], "rival_output": grids[2],
        "source_binding": _witness_source_binding(generator, oracle),
        "validation": {"arc_grids": "passed", "rule_applied": True,
                       "rival_disagrees": True, "self_check": validation},
        "scope": "First checked census disagreement; not minimized or a universal identifiability proof.",
    }


def _verify_rival_claims(
    rival_queue: dict[str, list[tuple[str, int, int, Any]]],
    *,
    rivals: dict[str, Callable],
    witness_rivals: dict[str, list[str]],
    oracle_factory: Callable[[], _RuleOracle] | None,
    task_id: str | None = None,
    generator: Any = None,
) -> dict[str, dict[str, Any]]:
    """Check each witness's declared claim on the grids where it fired.

    THE CLAIM (contract v1.1): "on every grid where this witness fires, at
    least one of the NAMED rivals answers differently from the canonical rule."
    A witness that fires everywhere while every named rival still agrees with
    the rule proves only that a FEATURE is present — the measured 600/600 vs
    600/600 case this check exists for.

    Returns one stats dict per claiming witness. Every failure — no oracle, a
    rival that raises, a rule that raises — is COUNTED and carried out, never
    swallowed.
    """
    out: dict[str, dict[str, Any]] = {}
    if not witness_rivals:
        return out

    oracle: _RuleOracle | None = None
    for witness, named in witness_rivals.items():
        queue = rival_queue.get(witness, [])
        stats: dict[str, Any] = {
            "rivals": list(named),
            "fired_available": len(queue),
            "checked": 0,
            "claim_holds": 0,
            "claim_violated": 0,
            "oracle_errors": 0,
            "rival_errors": 0,
            "per_rival_disagreements": {name: 0 for name in named},
            "violation_examples": [],
            "error_examples": [],
            "oracle_error": None,
            "witness_examples": {},
            "witness_selection": "first_checked_disagreement_per_pair",
            "witness_retention_errors": [],
        }
        out[witness] = stats
        if not queue:
            continue
        if oracle_factory is None:
            stats["oracle_error"] = (
                "no rule oracle was supplied to run_census — the authoritative "
                "output could not be computed"
            )
            continue
        if oracle is None:
            oracle = oracle_factory()
        if not oracle.ready:
            stats["oracle_error"] = oracle.error
            continue

        for band, seed, sample_index, grid in queue:
            authoritative, error = oracle.apply(grid)
            if error is not None:
                stats["oracle_errors"] += 1
                if len(stats["error_examples"]) < MAX_EXAMPLES:
                    stats["error_examples"].append(
                        f"band={band} seed={seed} sample_index={sample_index}: "
                        f"{error}"
                    )
                continue
            stats["checked"] += 1
            disagreed = False
            for name in named:
                try:
                    rival_out = rivals[name](copy.deepcopy(grid))
                except Exception as exc:
                    stats["rival_errors"] += 1
                    if len(stats["error_examples"]) < MAX_EXAMPLES:
                        stats["error_examples"].append(
                            f"SEMANTIC_RIVALS[{name!r}](band={band} seed={seed} "
                            f"sample_index={sample_index}) raised "
                            f"{type(exc).__name__}: {exc}"
                        )
                    continue
                if not _grids_equal(rival_out, authoritative):
                    stats["per_rival_disagreements"][name] += 1
                    disagreed = True
                    if name not in stats["witness_examples"]:
                        example = _semantic_witness_example(
                            task_id=task_id, generator=generator, oracle=oracle,
                            witness=witness, rival=name, band=band, seed=seed,
                            sample_index=sample_index, grid=grid,
                            authoritative=authoritative, rival_output=rival_out,
                        )
                        if example is not None:
                            stats["witness_examples"][name] = example
                        elif len(stats["witness_retention_errors"]) < MAX_EXAMPLES:
                            stats["witness_retention_errors"].append(
                                f"{name}: band={band} seed={seed} sample_index={sample_index}: "
                                "a complete 1..30 rectangular ARC grid could not be retained"
                            )
            if disagreed:
                stats["claim_holds"] += 1
            else:
                stats["claim_violated"] += 1
                if len(stats["violation_examples"]) < MAX_EXAMPLES:
                    preview = _compact_grid_preview(grid)
                    stats["violation_examples"].append({
                        "band": band, "seed": seed,
                        "sample_index": sample_index,
                        "replay": (f"band={band} seed={seed} "
                                   f"sample_index={sample_index}"),
                        "grid_preview": preview,
                    })
    return out


# ---------------------------------------------------------------------------
# 3b. Canonical acceptance — the hook must own the inputs it characterises
# ---------------------------------------------------------------------------

def check_canonical_acceptance(
    task_id: str, hook: Callable,
) -> tuple[dict[str, Any], list[str]]:
    """Feed the task's REAL canonical train/test inputs to the hook.

    A `strict_canonical_like` that rejects the very inputs it claims to
    characterise is broken — an over-tight predicate makes the census rate
    meaningless (it can read 100% while describing a manifold the task never
    occupies). This is the exact parallel of `canonical_profile_gate` check 1,
    and it is the cheapest possible catch.

    Returns (stats, problems); never raises.
    """
    stats: dict[str, Any] = {
        "canonical_inputs": 0, "canonical_rejected": 0,
        "canonical_hook_errors": 0, "canonical_rejection_examples": [],
        "canonical_hook_error_examples": [],
    }
    try:
        grids = canonical_inputs(task_id)
    except Exception as exc:
        return stats, [
            f"{task_id}: canonical acceptance — reading canonical inputs "
            f"failed: {type(exc).__name__}: {exc}"
        ]
    stats["canonical_inputs"] = len(grids)
    if not grids:
        return stats, [
            f"{task_id}: strict_canonical_like is declared but NO canonical "
            "inputs were found — canonical acceptance (3b) could not be "
            "measured, so the census rate is unanchored"
        ]

    for index, grid in enumerate(grids):
        reasons, error = _call_reasons_hook(hook, grid, allow_bool=True)
        if error is not None:
            stats["canonical_hook_errors"] += 1
            if len(stats["canonical_hook_error_examples"]) < MAX_EXAMPLES:
                stats["canonical_hook_error_examples"].append(
                    f"canonical input #{index}: {error}"
                )
            continue
        if reasons:
            stats["canonical_rejected"] += 1
            if len(stats["canonical_rejection_examples"]) < MAX_EXAMPLES:
                stats["canonical_rejection_examples"].append({
                    "index": index,
                    "dims": [len(grid), len(grid[0]) if grid else 0],
                    "reasons": reasons[:MAX_TOP_REASONS],
                })

    problems: list[str] = []
    if stats["canonical_hook_errors"]:
        problems.append(
            f"{task_id}: strict_canonical_like raised/misreturned on "
            f"{stats['canonical_hook_errors']}/{len(grids)} CANONICAL inputs: "
            + "; ".join(stats["canonical_hook_error_examples"])
        )
    if stats["canonical_rejected"]:
        detail = "; ".join(
            f"#{e['index']} ({e['dims'][0]}x{e['dims'][1]}): "
            f"{', '.join(e['reasons'])[:160]}"
            for e in stats["canonical_rejection_examples"]
        )
        problems.append(
            f"{task_id}: strict_canonical_like REJECTS "
            f"{stats['canonical_rejected']}/{len(grids)} canonical inputs — "
            f"the predicate disowns the manifold it claims to describe: {detail}"
        )
    return stats, problems


# ---------------------------------------------------------------------------
# 6. Canonical ambiguity — when the canonical set CANNOT falsify a shortcut
# ---------------------------------------------------------------------------

# One scan of `puzzles.jsonl` costs ~0.17s, and a corpus sweep audits hundreds
# of tasks. Memoized on (path, mtime_ns, size, task_id) — NOT on task_id alone:
# a bare task_id key would silently serve stale pairs to a caller that
# repointed `CANONICAL`, which is exactly the kind of quiet wrong answer this
# gate exists to prevent. A deep copy is returned so no caller can mutate the
# cached rows.
_CANONICAL_PAIRS_CACHE: dict[tuple, list[dict]] = {}


def _canonical_pairs_cached(task_id: str) -> list[dict]:
    import scripts.canonical_profile_gate as cpg  # late: honours a patched path

    stat = cpg.CANONICAL.stat()
    key = (str(cpg.CANONICAL), stat.st_mtime_ns, stat.st_size, task_id)
    if key not in _CANONICAL_PAIRS_CACHE:
        _CANONICAL_PAIRS_CACHE[key] = canonical_pairs(task_id)
    return copy.deepcopy(_CANONICAL_PAIRS_CACHE[key])


_CANONICAL_PROGRAM_CACHE: dict[tuple, str | None] = {}


def _canonical_program_cached(task_id: str) -> str | None:
    """The task's canonical `program_solution` text, or None if absent.

    Keyed exactly like `_CANONICAL_PAIRS_CACHE` — on (path, mtime, size,
    task_id) — so a caller that repoints `CANONICAL` cannot be served a stale
    rule. Used only by `authoritative_simple_shortcut`.
    """
    import scripts.canonical_profile_gate as cpg  # late: honours a patched path

    stat = cpg.CANONICAL.stat()
    key = (str(cpg.CANONICAL), stat.st_mtime_ns, stat.st_size, task_id)
    if key not in _CANONICAL_PROGRAM_CACHE:
        found = None
        with cpg.CANONICAL.open(encoding="utf-8") as handle:
            for line in handle:
                if task_id not in line:
                    continue
                row = json.loads(line)
                if row.get("content_hash") == task_id or row.get("task_id") == task_id:
                    found = row.get("program_solution")
                    break
        _CANONICAL_PROGRAM_CACHE[key] = found
    return _CANONICAL_PROGRAM_CACHE[key]

def check_canonical_ambiguity(
    task_id: str,
    *,
    declared_shortcuts: dict[str, Callable],
    rival_claims: dict[str, dict[str, Any]],
    witness_rivals: dict[str, list[str]],
) -> dict[str, Any]:
    """Which shortcuts reproduce EVERY canonical pair — and is that refuted?

    Measured motivation (9df4a42fced1): ALL 4/4 canonical pairs were
    answer-equivalent under a WRONG keep-seed-position shortcut
    (`all_seeds_centered=true`), so no canonical pair could falsify it; only a
    GENERATED off-center counterexample could, and the refuting witness fired
    311/600. Canonical alone is not always able to discriminate, and a gate
    that only ever reads canonical will never notice.

    Two shortcut sources:

    * `SIMPLE_SHORTCUTS` — identity + the 7 dihedral maps. No task knowledge,
      so it also cannot tell "wrong shortcut" from "this IS the task's rule";
      its finding is a NOTE unless --require-shortcut-counterexample.
    * `CANONICAL_SHORTCUTS` declared by the generator — the author asserting
      "this is a plausible WRONG rule fitting all canonical labels".
      A false/unverifiable declaration fails; unrefuted ambiguity warns.

    A finding is SATISFIED when a `SEMANTIC_RIVALS` entry of the SAME NAME is
    claimed by a witness whose claim was verified to HOLD at least once on the
    generated census: that is exactly "a generated counterexample witness".

    Never raises; every failure is counted and returned.
    """
    stats: dict[str, Any] = {
        "canonical_pairs": 0, "usable_pairs": 0,
        "shortcuts_tested": [], "shortcut_errors": 0,
        "shortcut_error_examples": [],
        "ambiguous_simple": [], "ambiguous_declared": [],
        "satisfied_by_witness": {}, "unsatisfied": [],
        "authority_equal": [],
        "declared_validation": {}, "invalid_declared": [],
        "read_error": None,
    }
    # Which generic shortcut, if any, IS this task's selected rule.
    authority_shortcut = authoritative_simple_shortcut(task_id)
    stats["authority_shortcut"] = authority_shortcut
    try:
        pairs = _canonical_pairs_cached(task_id)
    except Exception as exc:
        stats["read_error"] = (
            f"reading canonical pairs failed: {type(exc).__name__}: {exc}"
        )
        for name in declared_shortcuts:
            stats["declared_validation"][name] = {
                "status": "read_error", "checked": 0, "mismatches": 0,
                "errors": 0, "examples": [],
            }
        stats["invalid_declared"] = list(declared_shortcuts)
        return stats
    stats["canonical_pairs"] = len(pairs)
    usable = [
        p for p in pairs
        if isinstance(p.get("input"), list) and isinstance(p.get("output"), list)
    ]
    stats["usable_pairs"] = len(usable)
    if not usable:
        for name in declared_shortcuts:
            stats["declared_validation"][name] = {
                "status": "no_labeled_pairs", "checked": 0, "mismatches": 0,
                "errors": 0, "examples": [],
            }
        stats["invalid_declared"] = list(declared_shortcuts)
        return stats

    # Which witnesses supply a verified generated counterexample, per rival name.
    verified_rivals: dict[str, list[str]] = {}
    for witness, claim in rival_claims.items():
        if claim.get("claim_holds", 0) <= 0:
            continue
        for rival_name in witness_rivals.get(witness, []):
            if claim["per_rival_disagreements"].get(rival_name, 0) > 0:
                verified_rivals.setdefault(rival_name, []).append(witness)

    candidates: list[tuple[str, str, Callable]] = (
        [("declared", name, fn) for name, fn in declared_shortcuts.items()]
        + [("simple", name, fn) for name, fn in SIMPLE_SHORTCUTS.items()]
    )
    for source, name, fn in candidates:
        reproduces = True
        validation = {"status": "fits_all_labeled_pairs", "checked": 0,
                      "mismatches": 0, "errors": 0, "examples": []}
        for index, pair in enumerate(usable):
            validation["checked"] += 1
            identity = copy.deepcopy(pair.get("pair_identity",
                                             {"usable_pair_index": index}))
            try:
                predicted = fn(copy.deepcopy(pair["input"]))
                matches = _grids_equal(predicted, pair["output"])
            except Exception as exc:
                stats["shortcut_errors"] += 1
                if len(stats["shortcut_error_examples"]) < MAX_EXAMPLES:
                    stats["shortcut_error_examples"].append(
                        f"{source} shortcut {name!r} on canonical pair #{index} "
                        f"raised {type(exc).__name__}: {exc}"
                    )
                reproduces = False
                if source == "simple":
                    break
                validation["errors"] += 1
                if len(validation["examples"]) < MAX_EXAMPLES:
                    validation["examples"].append({"pair_identity": identity,
                        "error": f"{type(exc).__name__}: {exc}"})
                continue
            if not matches:
                reproduces = False
                if source == "simple":
                    break
                validation["mismatches"] += 1
                if len(validation["examples"]) < MAX_EXAMPLES:
                    # Invalid outputs can be arbitrary Python objects; do not
                    # put those objects into a JSON report.
                    validation["examples"].append({"pair_identity": identity,
                        "expected_output": copy.deepcopy(pair["output"]),
                        "predicted_output": _witness_grid(predicted),
                        "predicted_type": type(predicted).__name__})
        if source == "declared":
            if not reproduces:
                validation["status"] = "invalid_declaration"
                stats["invalid_declared"].append(name)
            stats["declared_validation"][name] = validation
        stats["shortcuts_tested"].append(name)
        if not reproduces:
            continue
        (stats["ambiguous_declared"] if source == "declared"
         else stats["ambiguous_simple"]).append(name)
        if name in verified_rivals:
            stats["satisfied_by_witness"][name] = sorted(verified_rivals[name])
        elif source == "simple" and name == authority_shortcut:
            # The "shortcut" IS the selected rule (WFB-2001). Demanding a
            # generated counterexample here asks for a row on which the task's
            # own authority is wrong — a poisoned row. Record it as satisfied
            # BY AUTHORITY so the finding stays visible and auditable, and
            # never place it in `unsatisfied`.
            stats["authority_equal"].append(name)
        else:
            stats["unsatisfied"].append({"source": source, "shortcut": name})
    return stats


# ---------------------------------------------------------------------------
# Lesson materialization (hook 3) — real outputs from the canonical Racket rule
# ---------------------------------------------------------------------------

def _band_quotas(count: int, bands: tuple[str, ...]) -> dict[str, int]:
    """Split `count` lessons across the difficulty bands, remainder first.

    `--lessons N` keeps its v1 meaning (the TOTAL number of lessons), so the
    battery's `--lessons 12` still costs 12 Racket-backed lessons; what changes
    is that they are now 4 per band instead of 12 at whatever difficulty the
    generator defaults to.
    """
    base, extra = divmod(count, len(bands))
    return {band: base + (1 if i < extra else 0) for i, band in enumerate(bands)}


LEGACY_BAND = "legacy"


def _lesson_plan(
    task_id: str, count: int, *, bands: tuple[str, ...],
    pass_difficulty: bool, legacy: bool,
) -> list[tuple[str, int, int, dict]]:
    """The pinned lesson draw plan: [(band, seed, sample_index, axes)].

    `legacy=True` reproduces the v1 population EXACTLY — every lesson at
    `sample_index = 0`, seeds `_pinned_seed(task_id, "lesson", i)`, no
    `difficulty` — and exists only so a v1.1 finding can be compared against
    pre-2026-07-25 evidence. It is NOT a fallback: that fixed start offset is
    the aliasing the per-band plan replaced.
    """
    if legacy:
        return [(LEGACY_BAND, _pinned_seed(task_id, "lesson", i), 0, {})
                for i in range(count)]
    plan: list[tuple[str, int, int, dict]] = []
    quotas = _band_quotas(count, bands)
    for band in bands:
        for k in range(quotas[band]):
            plan.append((
                band,
                _pinned_seed(task_id, f"lesson:{band}", k),
                k * LESSON_SAMPLE_STRIDE,
                {"difficulty": band} if pass_difficulty else {},
            ))
    return plan


def materialize_lessons(
    task_id: str,
    count: int,
    *,
    n_demos: int,
    n_queries: int = 1,
    bands: tuple[str, ...] = BANDS,
    pass_difficulty: bool = True,
    legacy: bool = False,
    oracle_factory: Callable[[], _RuleOracle] | None = None,
) -> tuple[list[dict], list[str]]:
    """Build `count` pinned lessons (n_demos demos + n_queries query) PER BAND.

    Outputs come from the task's canonical Racket rule via the existing
    `puzzle_generators.runner` path (`_load_bundle` / `_open_bridge_with_rule` /
    `run_one`) — the same path `materialize_pool_sample.py` uses, so a lesson
    the gate judges is byte-identical to a lesson the trainer would see.

    Three v1.1 changes, all about measuring the population the shard actually
    ships:

    * **Per band.** `count` is split across `bands` and `difficulty=band` is
      passed through `run_one`, which forwards it to EVERY demo and query
      `generate()` call. v1 materialized every lesson at the generator's
      default difficulty, so a band-specific branch was never lesson-tested.
      A generator whose `generate` cannot accept `difficulty` is handled by
      `pass_difficulty=False` — a COUNTED, reported degradation, not a silent
      one.
    * **Stride.** Lesson i starts at `sample_index = i * LESSON_SAMPLE_STRIDE`
      instead of 0, so a schedule keyed on `sample_index % m` is not pinned to
      residue 0 forever.
    * **Replay tuple.** Every lesson carries (band, seed, sample_index) so an
      unidentifiable one can be reproduced exactly.

    Returns (lessons, errors); never raises. The bridge is ALWAYS shut down in
    a `finally` — a leaked Racket subprocess made batteries look hung for ~8
    workers before `gen_diversity_probe.py` was fixed the same way.
    """
    from puzzle_generators import runner  # late import: keeps --help offline

    lessons: list[dict] = []
    errors: list[str] = []

    oracle = oracle_factory() if oracle_factory is not None else _RuleOracle(task_id)
    owns_oracle = oracle_factory is None
    if not oracle.ready:
        if owns_oracle:
            oracle.close()
        return [], [str(oracle.error)]

    plan = _lesson_plan(task_id, count, bands=bands,
                        pass_difficulty=pass_difficulty, legacy=legacy)
    try:
        for index, (band, seed, sample_index, axes) in enumerate(plan):
            try:
                inst = runner.run_one(
                    task_id, seed=seed, sample_index=sample_index,
                    n_train=n_demos, n_test=n_queries,
                    bundle=oracle.bundle, bridge=oracle.bridge,
                    fn_name=oracle.fn_name, **axes,
                )
            except Exception as exc:
                errors.append(
                    f"RUN_ONE_FAIL lesson={index} band={band} seed={seed} "
                    f"sample_index={sample_index}: "
                    f"{type(exc).__name__}: {str(exc)[:200]}"
                )
                continue
            lessons.append({
                "index": index,
                "band": band,
                "seed": seed,
                "sample_index": sample_index,
                "difficulty_passed": bool(axes),
                "replay": (f"band={band} seed={seed} "
                           f"sample_index={sample_index}"),
                "demos": inst["train"],
                "query": inst["test"][0],
            })
    finally:
        if owns_oracle:
            oracle.close()
    return lessons, errors


def evaluate_competitors(
    competitors: dict[str, Callable], lesson: dict,
) -> dict[str, Any]:
    """Score named rival solvers against ONE lesson. Never raises.

    Three outcomes per competitor, kept SEPARATE because they mean different
    things and conflating them is how a witness ends up proving nothing:

      refuted            — some demo's output disagrees with the competitor, so
                           the lesson does eliminate it.
      survived_all       — fits every demo AND matches the query answer: the
                           lesson never distinguishes the true rule from this
                           competitor anywhere. This is the raw-shape rival that
                           selected the official odd panel 600/600.
      query_discriminates— fits every demo but answers the query differently:
                           the demos alone do not determine the query answer.

    "Which competitor survived" (the thing an unidentifiable lesson must name)
    is `survived_demos` = survived_all + query_discriminates.
    """
    out: dict[str, Any] = {
        "refuted": [], "survived_all": [], "query_discriminates": [],
        "survived_demos": [], "errors": [], "error_names": [],
    }
    for name, fn in sorted(competitors.items()):
        try:
            fits = all(
                _grids_equal(fn(copy.deepcopy(demo["input"])), demo["output"])
                for demo in lesson["demos"]
            )
            agrees = _grids_equal(
                fn(copy.deepcopy(lesson["query"]["input"])),
                lesson["query"]["output"],
            )
        except Exception as exc:
            out["error_names"].append(name)
            if len(out["errors"]) < MAX_EXAMPLES:
                out["errors"].append(
                    f"LESSON_COMPETITORS[{name!r}] raised on lesson "
                    f"{lesson.get('replay', lesson['index'])}: "
                    f"{type(exc).__name__}: {exc}"
                )
            continue
        if not fits:
            out["refuted"].append(name)
            continue
        out["survived_demos"].append(name)
        (out["survived_all"] if agrees else out["query_discriminates"]).append(name)
    return out


def score_lessons(
    task_id: str,
    hook: Callable | None,
    *,
    count: int,
    n_demos: int,
    bands: tuple[str, ...] = BANDS,
    pass_difficulty: bool = True,
    legacy: bool = False,
    competitors: dict[str, Callable] | None = None,
    oracle_factory: Callable[[], _RuleOracle] | None = None,
    searched_generator=None,
    rotate_query: bool = False,
    require_rotations: bool = False,
) -> tuple[dict[str, Any], list[str], list[str]]:
    """Materialize lessons per band and run `lesson_identifiable` over each. LOUD.

    Returns (stats, problems, warnings). v1 returned an aggregate count and a
    bare `#index(seed=…)` — not enough to reproduce a failure and not enough to
    say WHICH competitor survived. Every unidentifiable lesson now carries its
    full replay tuple (band, seed, sample_index) and, when the generator
    declares `LESSON_COMPETITORS`, the names that survived the demos.
    """
    competitors = competitors or {}
    rotate_query = rotate_query or require_rotations
    rotation_worker = None
    if rotate_query:
        spec = importlib.util.spec_from_file_location(
            '_semantic_rotation_worker', Path(__file__).with_name('lesson_census.py'))
        rotation_worker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rotation_worker)
    lessons, errors = materialize_lessons(
        task_id, count, n_demos=n_demos, bands=bands,
        pass_difficulty=pass_difficulty, legacy=legacy,
        oracle_factory=oracle_factory,
    )
    band_keys = (LEGACY_BAND,) if legacy else bands
    plan = _lesson_plan(task_id, count, bands=bands,
                        pass_difficulty=pass_difficulty, legacy=legacy)
    stats: dict[str, Any] = {
        "requested": count, "n_demos": n_demos, "n_queries": 1,
        "hook_declared": hook is not None,
        "assessment_basis": (
            "declared_rivals" if hook is None else
            "lesson_identifiable_and_declared_rivals" if competitors else
            "lesson_identifiable"),
        "bands": list(band_keys),
        "legacy_sample": legacy,
        "requested_per_band": dict(Counter(band for band, *_ in plan)),
        "difficulty_passed": pass_difficulty and not legacy,
        "materialized": len(lessons), "identifiable": 0,
        "unidentifiable": 0, "hook_errors": 0,
        "per_band": {
            band: {"materialized": 0, "identifiable": 0,
                   "unidentifiable": 0, "hook_errors": 0}
            for band in band_keys
        },
        "materialize_errors": list(errors),
        "unidentifiable_examples": [], "hook_error_examples": [],
        "competitors_declared": sorted(competitors),
        "competitor_survivor_counts": {},
        "competitor_survived_all_counts": {},
        "competitor_errors": 0,
        "competitor_error_examples": [],
        "survivors_on_identifiable_lessons": [],
        "rotations": {
            "requested": rotate_query, "required": require_rotations,
            "checked": 0, "ambiguous": 0, "hook_warnings": 0, "errors": 0,
            "status": "incomplete" if rotate_query else "not_requested",
            "examples": [],
        },
    }
    problems: list[str] = [f"{task_id}: lesson materialization — {e}" for e in errors]
    warnings: list[str] = []
    survivor_counter: Counter[str] = Counter()
    survived_all_counter: Counter[str] = Counter()

    stats["searched_rivals"] = []
    for lesson in lessons:
        if searched_generator is not None:
            from review_diagnostics import search_lesson
            instance = {"train":lesson["demos"], "test":[lesson["query"]]}
            searched = {"replay":lesson["replay"], "production":search_lesson(searched_generator,instance),
                        "rotation_policy":"require" if require_rotations else "diagnostic" if rotate_query else "not_requested",
                        "rotations":[]}
            if rotate_query:
                pairs=instance["train"]+instance["test"]
                for qi,pair in enumerate(pairs):
                    searched["rotations"].append({"query_index":qi, **search_lesson(searched_generator,{"train":pairs[:qi]+pairs[qi+1:],"test":[pair]})})
            stats["searched_rivals"].append(searched)
            if searched["production"]["ambiguous"] or (require_rotations and any(r["ambiguous"] for r in searched["rotations"])):
                warnings.append(f"{task_id}: searched rival ambiguity on {lesson['replay']} (advisory; inspect retained witness)")
        band = lesson.get("band", "?")
        band_row = stats["per_band"].setdefault(
            band, {"materialized": 0, "identifiable": 0,
                   "unidentifiable": 0, "hook_errors": 0})
        band_row["materialized"] += 1

        if rotation_worker is not None:
            instance = {"train": lesson["demos"], "test": [lesson["query"]]}
            cache = {}
            rotations = rotation_worker.score_rotations(
                SimpleNamespace(lesson_identifiable=hook), competitors, instance,
                prediction_cache=cache)
            summary = stats["rotations"]
            pairs = instance["train"] + instance["test"]
            refuting = {
                name: [i for i, pair in enumerate(pairs)
                       if (name, rotation_worker.digest(pair["input"])) in cache
                       and cache[(name, rotation_worker.digest(pair["input"]))][0]
                       and cache[(name, rotation_worker.digest(pair["input"]))][1]
                       != pair["output"]]
                for name in competitors
            }
            for row in rotations:
                summary["checked"] += 1
                summary["ambiguous"] += int(row["ambiguous"])
                summary["hook_warnings"] += int(bool(row["warnings"]))
                summary["errors"] += int(bool(row["errors"]))
                if ((row["ambiguous"] or row["warnings"] or row["errors"])
                        and len(summary["examples"]) < MAX_EXAMPLES):
                    query_hash = rotation_worker.digest(pairs[row["query_index"]]["input"])
                    summary["examples"].append({
                        **row, "index": lesson["index"], "band": band,
                        "seed": lesson["seed"],
                        "sample_index": lesson.get("sample_index"),
                        "replay": lesson.get("replay"), "instance": instance,
                        "instance_hash": rotation_worker.digest(instance),
                        "refuting_pair_indices": refuting,
                        "query_predictions": {
                            name: cache[(name, query_hash)][1] for name in competitors
                            if (name, query_hash) in cache and cache[(name, query_hash)][0]
                        },
                    })

        scored: dict[str, Any] = {}
        if competitors:
            scored = evaluate_competitors(competitors, lesson)
            for name in scored["survived_demos"]:
                survivor_counter[name] += 1
            for name in scored["survived_all"]:
                survived_all_counter[name] += 1
            if scored["errors"]:
                stats["competitor_errors"] += len(scored["error_names"])
                for message in scored["errors"]:
                    if len(stats["competitor_error_examples"]) < MAX_EXAMPLES:
                        stats["competitor_error_examples"].append(message)

        if hook is None:
            reasons = [f"declared rival {name!r} fits every demo but changes the query"
                       for name in scored.get("query_discriminates", [])]
            error = None
        else:
            reasons, error = _call_reasons_hook(hook, lesson["demos"], lesson["query"])
        if error is not None:
            stats["hook_errors"] += 1
            band_row["hook_errors"] += 1
            replay = lesson.get("replay") or "seed=%s" % lesson["seed"]
            message = (
                f"lesson_identifiable(lesson={lesson['index']}, {replay}) "
                f"{error}"
            )
            if len(stats["hook_error_examples"]) < MAX_EXAMPLES:
                stats["hook_error_examples"].append(message)
            continue
        if reasons:
            stats["unidentifiable"] += 1
            band_row["unidentifiable"] += 1
            if len(stats["unidentifiable_examples"]) < MAX_EXAMPLES:
                stats["unidentifiable_examples"].append({
                    "index": lesson["index"],
                    "band": band,
                    "seed": lesson["seed"],
                    "sample_index": lesson.get("sample_index"),
                    "replay": lesson.get("replay"),
                    "n_demos": len(lesson["demos"]),
                    "reasons": reasons[:MAX_TOP_REASONS],
                    "survivors": scored.get("survived_demos") if competitors else None,
                    "survived_all": scored.get("survived_all") if competitors else None,
                    "survivor_source": (
                        "LESSON_COMPETITORS" if competitors
                        else "none declared — reasons only"
                    ),
                })
        else:
            stats["identifiable"] += 1
            band_row["identifiable"] += 1
            # A competitor that also matches the official query is answer-
            # equivalent for this lesson. It remains reported in the census,
            # but it does not contradict an identifiable query answer.
            if competitors and scored["query_discriminates"]:
                stats["survivors_on_identifiable_lessons"].append({
                    "index": lesson["index"], "band": band,
                    "replay": lesson.get("replay"),
                    "survivors": scored["query_discriminates"],
                    "survived_all": scored["survived_all"],
                })

    stats["competitor_survivor_counts"] = dict(survivor_counter)
    stats["competitor_survived_all_counts"] = dict(survived_all_counter)

    rotations = stats["rotations"]
    if rotate_query:
        rotations["status"] = (
            "error" if errors or not lessons or rotations["errors"] else
            "ambiguous" if rotations["ambiguous"] else
            "warning" if rotations["hook_warnings"] else
            "no_ambiguity_found" if competitors else "hook_only")
        if require_rotations and rotations["status"] in ("error", "ambiguous", "warning"):
            problems.append(
                f"{task_id}: required query rotations: {rotations['ambiguous']}/"
                f"{rotations['checked']} ambiguous, {rotations['errors']} errors, "
                f"{rotations['hook_warnings']} hook warnings; see rotations.examples")

    if not lessons:
        problems.append(
            f"{task_id}: lesson scoring requested but ZERO of {count} "
            "lessons materialized — nothing was measured"
        )
    if stats["hook_errors"]:
        problems.append(
            f"{task_id}: lesson_identifiable raised/misreturned on "
            f"{stats['hook_errors']}/{len(lessons)} lessons: "
            + "; ".join(stats["hook_error_examples"])
        )
    if stats["unidentifiable"]:
        detail = "; ".join(
            f"#{e['index']}[{e['replay']}]: {', '.join(e['reasons'])[:160]}"
            + (f" | survivors: {e['survivors'] or 'none'}"
               if e["survivors"] is not None else
               " | survivor unnamed (declare LESSON_COMPETITORS)")
            for e in stats["unidentifiable_examples"]
        )
        problems.append(
            f"{task_id}: {stats['unidentifiable']}/{len(lessons)} lessons are "
            f"UNIDENTIFIABLE (per band "
            f"{ {b: r['unidentifiable'] for b, r in stats['per_band'].items()} }"
            f") — {detail}"
        )
    if stats["competitor_errors"]:
        warnings.append(
            f"{task_id}: LESSON_COMPETITORS raised on "
            f"{stats['competitor_errors']} lesson/competitor pairs: "
            + "; ".join(stats["competitor_error_examples"])
        )
    if stats["survivors_on_identifiable_lessons"]:
        first = stats["survivors_on_identifiable_lessons"][0]
        warnings.append(
            f"{task_id}: {len(stats['survivors_on_identifiable_lessons'])}/"
            f"{len(lessons)} lessons were reported IDENTIFIABLE while a declared "
            f"query-changing competitor still fit every demo — e.g. #{first['index']}"
            f"[{first['replay']}] survivors {first['survivors']} "
            f"(answer-equivalent survivors: {first['survived_all']}). The hook and "
            "LESSON_COMPETITORS disagree; one of them is wrong"
        )
    return stats, problems, warnings


# ---------------------------------------------------------------------------
# Per-task audit
# ---------------------------------------------------------------------------

def _load_census_worker():
    spec = importlib.util.spec_from_file_location(
        '_semantic_schedule_worker', Path(__file__).with_name('lesson_census.py'))
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)
    return worker


def _enumerate_schedule_coverage(task_id, gen, path, seed):
    """Use the existing native census; checkpoint labelled evidence in this stage."""
    period = getattr(gen, 'LESSON_SCHEDULE_PERIOD', None)
    if type(period) is not int or period < 1:
        raise ValueError('Enumeration requires positive integer LESSON_SCHEDULE_PERIOD (not bool)')
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError('schedule_seed must be a uint32 integer (not bool)')
    manifest = json.loads(Path('RUNTIME_MANIFEST.json').read_text())
    source_hash = hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest()
    entries = [r for r in manifest['files']
               if r.get('library_path') == f'generators/{task_id}/generator.py']
    if manifest.get('task_id') != task_id or len(entries) != 1 or entries[0].get('sha256') != source_hash:
        raise ValueError('Enumeration requires the matching staged runtime manifest; use arcpuzzles check')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    def save(report):
        # A killed stage leaves status=incomplete; no controller completion is invented.
        report['runtime_manifest'] = manifest
        report['runtime_manifest_sha256'] = hashlib.sha256(
            (json.dumps(manifest, indent=2) + '\n').encode()).hexdigest()
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_text(json.dumps(report, indent=2) + '\n')
        temporary.replace(path)
    worker = _load_census_worker()
    request = {'task_id': task_id, 'per_band': period, 'n_demos': None,
               'n_queries': 1, 'period': period, 'bands': list(BANDS),
               'rotate_query': True, 'rotation_policy': 'require',
               'enumerate_schedule_period': True, 'schedule_seed': seed}
    report = worker.census(request, checkpoint=save)
    report['execution'] = {'kind': 'in_process_native_census', 'timed_out': False,
                          'exit_code': 0 if report['status'] in (
                              'no_ambiguity_found', 'no_declared_ambiguity', 'hook_only', 'warning', 'no_contract')
                          else (1 if report['status'] == 'ambiguous' else 2)}
    save(report)
    coverage = _schedule_receipt_coverage(task_id, gen, path, seed)
    coverage.update(status='complete_fixed_seed_executed',
                    evidence_basis='source_bound_native_label_execution',
                    scope='Executed every declared start and query position at this fixed seed and these bands only; '
                          'does not prove the period, all-seed identifiability, audit closure or training admission.')
    return coverage


def _schedule_receipt_coverage(task_id, gen, path, seed):
    """Consume source-bound reported coverage without opening a Racket bridge."""
    # The same stdlib reader is copied by prepare_runtime; the second path is
    # this repository's source layout for direct developer/fixture inspection.
    reader_path = Path(__file__).with_name('receipt_input.py')
    if not reader_path.is_file():
        reader_path = Path(__file__).parents[2] / 'src/arcpuzzles/receipt_input.py'
    reader_spec = importlib.util.spec_from_file_location('_schedule_receipt_input', reader_path)
    reader = importlib.util.module_from_spec(reader_spec)
    reader_spec.loader.exec_module(reader)
    source = reader.read_receipt(path)
    raw = source['raw']
    receipt = json.loads(raw)
    from puzzle_generators import runner
    bundle = runner._load_bundle(task_id)
    binding = _witness_source_binding(gen, type('ReceiptSource', (), {'bundle': bundle})())
    if binding['status'] != 'bound' or binding['errors']:
        raise ValueError('Incomplete current source binding for schedule receipt')
    binding.update(rule_file=str(bundle.rule_file), declared_rule_hash=getattr(gen, 'RULE_HASH', None))
    worker = _load_census_worker()
    rivals, declaration_errors = worker.declared_rivals(gen)
    if declaration_errors:
        raise ValueError('Invalid current rival declarations: ' + '; '.join(declaration_errors))
    binding['rivals'] = sorted(rivals)
    worker.validate_schedule_receipt(receipt, task_id=task_id, binding=binding,
        period=getattr(gen, 'LESSON_SCHEDULE_PERIOD', None), seed=seed,
        bands=BANDS, n_demos=getattr(gen, 'EXAMPLES_NEEDED', 3))
    return {'status': 'complete_fixed_seed_reported', 'enumerated': True,
            'evidence_basis': 'source_bound_reported_receipt_not_reexecuted',
            'receipt_sha256': hashlib.sha256(raw).hexdigest(),
            'receipt_transport': source['transport'],
            'receipt_path': str(path), 'seed': seed, 'bands': list(BANDS),
            'semantic_contract': receipt['contract'], 'rivals': receipt['rivals'],
            'lessons': receipt['summary']['materialized'],
            'rotations': receipt['summary']['rotations'], 'followup_argv': None,
            'scope': 'Reported declared-period enumeration at this seed and these bands only; '
                     'does not prove the period, all-seed identifiability, audit closure or training admission.'}


def audit_task(
    task_id: str, *, per_band: int = 50, lessons: int = 20, strict: bool = False,
    min_strict_frac: float = DEFAULT_MIN_STRICT_FRAC,
    require_rival_witness: bool = False,
    require_shortcut_counterexample: bool = False,
    legacy_lesson_sample: bool = False,
    require_contract: bool = False,
    rotate_query: bool = False,
    require_rotations: bool = False,
    schedule_census: Path | None = None,
    schedule_seed: int = 0,
    enumerate_schedule_period: bool = False,
    schedule_census_out: Path | None = None,
) -> dict[str, Any]:
    """Run the declared semantic contract for one task. Never raises."""
    result: dict[str, Any] = {
        "task_id": task_id,
        "per_band": per_band,
        "lessons_requested": lessons,
        "strict_mode": strict,
        "require_rival_witness": require_rival_witness,
        "require_shortcut_counterexample": require_shortcut_counterexample,
        "rotate_query": rotate_query or require_rotations,
        "require_rotations": require_rotations,
        # Flat, per-task, machine-readable summary of the headline number. The
        # battery consumes `.audits[].strict_rate` without walking into the
        # nested census. None when the hook is not declared — never 0.0, which
        # would be indistinguishable from a real zero rate.
        "strict_rate": None,
        "strict_hits": None,
        "strict_draws": None,
        "min_strict_frac": None,
        "min_strict_frac_source": None,
        "strict_rate_below_floor": None,
        "hooks_declared": {name: False for name in HOOK_NAMES},
        "census": None,
        "strict_canonical": None,
        "witnesses": {},
        "lessons": None,
        "schedule_coverage": {"status": "not_checked", "declared_period": None,
                              "enumerated": False, "followup_argv": None},
        "rival_claims": {},
        "weak_witnesses": [],
        "canonical_ambiguity": None,
        "advisories": [],
        "errors": [],
        "warnings": [],
        "notes": [],
    }

    try:
        gen = importlib.import_module(
            f"puzzle_generators.per_puzzle.{task_id}.generator"
        )
    except Exception as exc:  # LOUD: an unimportable generator is a failure
        result["status"] = "IMPORT_FAIL"
        result["errors"] = [f"{task_id}: generator import failed: {exc!r}"]
        return result

    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []          # informational ONLY: never moves the status

    period = getattr(gen, "LESSON_SCHEDULE_PERIOD", None)
    coverage = result["schedule_coverage"]
    coverage["declared_period"] = period if isinstance(period, (int, float, str, bool, type(None))) else repr(period)
    coverage["scope"] = "Semantic gate samples pinned seeds and strides; it does not enumerate a fixed-seed declared period."
    if period is None:
        coverage["status"] = "not_declared"
    elif type(period) is not int or period < 1:
        coverage["status"] = "invalid_declaration"
        warnings.append(f"{task_id}: LESSON_SCHEDULE_PERIOD must be a positive integer (not bool).")
    else:
        coverage["status"] = "declared_period_not_enumerated"
        coverage["followup_argv"] = [
            "python3", "-m", "arcpuzzles", "lesson-census", task_id,
            "--enumerate-schedule-period", "--schedule-seed", str(schedule_seed),
            *[arg for band in BANDS for arg in ("--band", band)],
            "--out", f"var/checks/{task_id}/schedule-period-s{schedule_seed}.json",
        ]
    if enumerate_schedule_period:
        path = schedule_census_out or Path('checks') / f'{task_id}_schedule-census.json'
        coverage['receipt_path'] = str(path)
        try:
            if schedule_census is not None:
                raise ValueError('Enumeration and --schedule-census are mutually exclusive')
            coverage.update(_enumerate_schedule_coverage(task_id, gen, path, schedule_seed))
        except Exception as exc:
            coverage['receipt_status'] = 'rejected'
            coverage['rejection'] = f'{type(exc).__name__}: {exc}'
            if Path(path).is_file():
                coverage['receipt_sha256'] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            errors.append(f'{task_id}: schedule enumeration rejected: {coverage["rejection"]}')
    elif schedule_census is not None:
        coverage['receipt_path'] = str(schedule_census)
        try:
            coverage['receipt_sha256'] = hashlib.sha256(Path(schedule_census).read_bytes()).hexdigest()
            coverage.update(_schedule_receipt_coverage(task_id, gen, schedule_census, schedule_seed))
        except Exception as exc:
            coverage['receipt_status'] = 'rejected'
            coverage['rejection'] = f'{type(exc).__name__}: {exc}'
            errors.append(f'{task_id}: schedule receipt rejected: {coverage["rejection"]}')
    if coverage['status'] == 'declared_period_not_enumerated':
        warnings.append(f"{task_id}: declared_period_not_enumerated (period={period}); "
                        "smoke and query-rotation results do not establish fixed-seed schedule coverage.")

    strict_hook = getattr(gen, "strict_canonical_like", None)
    if strict_hook is not None and not callable(strict_hook):
        errors.append(
            f"{task_id}: strict_canonical_like is "
            f"{type(strict_hook).__name__}, expected a callable"
        )
        strict_hook = None
    lesson_hook = getattr(gen, "lesson_identifiable", None)
    if lesson_hook is not None and not callable(lesson_hook):
        errors.append(
            f"{task_id}: lesson_identifiable is "
            f"{type(lesson_hook).__name__}, expected a callable"
        )
        lesson_hook = None
    witnesses, witness_decl_errors = _declared_witnesses(gen)
    errors.extend(f"{task_id}: {msg}" for msg in witness_decl_errors)

    # --- v1.1 opt-in declarations. Every one of these is absent from the whole
    # --- legacy corpus, so nothing below can change an existing verdict.
    rivals, rival_decl_errors = _declared_grid_rules(gen, "SEMANTIC_RIVALS")
    errors.extend(f"{task_id}: {msg}" for msg in rival_decl_errors)
    witness_rivals, claim_decl_errors = _declared_witness_rivals(
        gen, witnesses, rivals)
    errors.extend(f"{task_id}: {msg}" for msg in claim_decl_errors)
    branch_witnesses, branch_decl_errors = _declared_branch_witnesses(
        gen, witnesses)
    errors.extend(f"{task_id}: {msg}" for msg in branch_decl_errors)
    result["branch_witnesses"] = sorted(branch_witnesses)
    competitors, competitor_decl_errors = _declared_grid_rules(
        gen, "LESSON_COMPETITORS")
    errors.extend(f"{task_id}: {msg}" for msg in competitor_decl_errors)
    shortcuts, shortcut_decl_errors = _declared_grid_rules(
        gen, "CANONICAL_SHORTCUTS")
    errors.extend(f"{task_id}: {msg}" for msg in shortcut_decl_errors)
    profile_fn, profile_space, schedule_decl_errors = _declared_schedule(gen)
    errors.extend(f"{task_id}: {msg}" for msg in schedule_decl_errors)

    result["hooks_declared"] = {
        "strict_canonical_like": strict_hook is not None,
        "SEMANTIC_WITNESSES": bool(witnesses),
        "lesson_identifiable": lesson_hook is not None,
    }
    result["optional_declarations"] = {
        "SEMANTIC_RIVALS": sorted(rivals),
        "WITNESS_RIVALS": {k: list(v) for k, v in sorted(witness_rivals.items())},
        "LESSON_COMPETITORS": sorted(competitors),
        "CANONICAL_SHORTCUTS": sorted(shortcuts),
        "schedule_profile": profile_fn is not None,
        # repr()'d, like the observed histogram keys: a declared profile may be
        # any hashable, and the JSON report must not depend on it happening to
        # be JSON-serializable.
        "SCHEDULE_PROFILES": (
            None if profile_space is None else [repr(p) for p in profile_space]
        ),
    }
    result["witness_names"] = sorted(witnesses)

    # The oracle (canonical Racket rule) is opened LAZILY and at most once per
    # task: only the rival-disagreement path and lesson materialization need it,
    # and a gate run over a corpus that declares neither must not pay for a
    # Racket subprocess it never uses.
    oracle_slot: list[_RuleOracle | None] = [None]

    def _oracle() -> _RuleOracle:
        if oracle_slot[0] is None:
            oracle_slot[0] = _RuleOracle(task_id)
        return oracle_slot[0]

    if require_rotations and lesson_hook is None and not (competitors or shortcuts):
        errors.append(
            f"{task_id}: required query rotations cannot be assessed without "
            "lesson_identifiable, LESSON_COMPETITORS or CANONICAL_SHORTCUTS")

    if not any(result["hooks_declared"].values()) and not (competitors or shortcuts) and not callable(getattr(gen,"SEARCHED_RIVAL_PROVIDER",None)):
        # Lawful: the legacy corpus is FLAGGED, never churned. A bulk sweep over
        # 3,937 generators must not turn red for a contract most of them predate.
        #
        # BUT advisory-by-default is exactly the hole eight independent reviewers
        # reported on 2026-07-25 (WFB-701/WFB-001 x3/WFB-003): a generator with no
        # semantic contract returns NO_CONTRACT *with no errors*, the battery
        # prints green, and nothing states that the central question — does this
        # teach the rule or a shortcut? — was never asked. Two shortcut-teaching
        # generators passed through that hole in one batch: 6c0ee2a97246, where
        # bbox-outline equalled solid-fill in 600/600 draws, and 7aee010af40d,
        # where a color-blind "smallest object" rival matched the orange-only rule
        # on every generated scene. Both were green here.
        #
        # So the severity is now the CALLER's to choose, and the two callers
        # differ: a legacy sweep keeps the advisory, while an assigned repair
        # passes --require-contract and gets a hard FAIL. Returning a candidate
        # with no contract is not a legacy condition — it is unfinished work.
        result["status"] = "NO_CONTRACT"
        message = (
            f"{task_id}: no semantic contract declared "
            "(strict_canonical_like / SEMANTIC_WITNESSES / lesson_identifiable)"
        )
        result["advisories"] = [f"LOUD: {message}"]
        if require_contract:
            errors = list(errors) + [
                f"{message} — required under --require-contract: an assigned "
                "repair must prove it teaches the rule, not merely that it runs"
            ]
        result["errors"] = errors
        result["warnings"] = warnings
        if errors:
            result["status"] = "FAIL"
        return result

    # --- hook 1 / step 3b: canonical acceptance ----------------------------
    # Runs BEFORE the census is judged: an over-tight predicate makes every
    # census number downstream meaningless, so it is reported first.
    canonical_stats: dict[str, Any] = {}
    if strict_hook is not None:
        canonical_stats, canonical_problems = check_canonical_acceptance(
            task_id, strict_hook)
        errors.extend(canonical_problems)

    # --- hooks 1 + 2: one shared pinned census -----------------------------
    rival_claims: dict[str, dict[str, Any]] = {}
    if strict_hook is not None or witnesses:
        scored = run_census(
            task_id, gen, per_band=per_band,
            strict_hook=strict_hook, witnesses=witnesses,
            rivals=rivals, witness_rivals=witness_rivals,
            oracle_factory=_oracle if witness_rivals else None,
            profile_fn=profile_fn, profile_space=profile_space,
        )
        result["census"] = scored["census"]
        result["strict_canonical"] = scored["strict_canonical"]
        result["witnesses"] = scored["witnesses"]
        errors.extend(f"{task_id}: {msg}" for msg in scored["schedule_errors"])

        crashes = scored["census"]["crashes"]
        planned = scored["census"]["planned"]
        if crashes:
            message = (
                f"{task_id}: {crashes}/{planned} census draws CRASHED in "
                f"generate(): " + "; ".join(scored["crash_messages"])
            )
            # Mirrors canonical_profile_gate: a majority of crashed draws means
            # there is no census left to judge.
            (errors if crashes > planned // 2 else warnings).append(message)

        strict_stats = scored["strict_canonical"]
        if strict_stats is not None:
            strict_stats.update(canonical_stats)   # 3b counts ride along
            result["strict_rate"] = strict_stats["rate"]
            result["strict_hits"] = strict_stats["hits"]
            result["strict_draws"] = strict_stats["draws"]
            if strict_stats["hook_errors"]:
                errors.append(
                    f"{task_id}: strict_canonical_like raised/misreturned on "
                    f"{strict_stats['hook_errors']}/{strict_stats['draws']} "
                    "draws: " + "; ".join(scored["hook_error_messages"])
                )
            # Only judge the rate over draws the hook actually SCORED. When
            # every call errored there is no census to call zero — the
            # raised/misreturned error above is the honest finding, and
            # claiming "0% canonical-like" on top of it would invent a
            # measurement that never happened.
            measured = strict_stats["draws"] - strict_stats["hook_errors"]
            strict_stats["measured"] = measured
            if measured > 0 and strict_stats["hits"] == 0:
                reasons = ", ".join(
                    f"{reason} x{count}"
                    for reason, count in strict_stats["top_reasons"]
                ) or "no reasons recorded"
                errors.append(
                    f"{task_id}: ZERO of {measured} census draws "
                    f"are strict_canonical_like (per-band "
                    f"{ {b: r['hits'] for b, r in strict_stats['per_band'].items()} }"
                    f") — top reasons: {reasons}"
                )
            elif measured > 0:
                # Low-but-nonzero support: a visible WARN, exactly like the
                # canonical-profile floor's --warn-frac. Zero already FAILed
                # above; this catches "effectively zero but not literally zero"
                # (the 1/600 class), NOT low-quality-per-se — see
                # DEFAULT_MIN_STRICT_FRAC for why no global floor can do more.
                floor, floor_source, floor_warnings = _effective_min_strict_frac(
                    gen, min_strict_frac)
                warnings.extend(f"{task_id}: {w}" for w in floor_warnings)
                rate = strict_stats["rate"]
                strict_stats["min_strict_frac"] = floor
                strict_stats["min_strict_frac_source"] = floor_source
                strict_stats["below_floor"] = bool(floor > 0 and rate < floor)
                result["min_strict_frac"] = floor
                result["min_strict_frac_source"] = floor_source
                result["strict_rate_below_floor"] = strict_stats["below_floor"]
                if strict_stats["below_floor"]:
                    remedy = (
                        "the generator declares this floor itself "
                        "(MIN_STRICT_FRAC)"
                        if floor_source == "declared"
                        else "raise the generator's canonical support, or "
                             "declare MIN_STRICT_FRAC if a broader-than-"
                             "canonical distribution is the intent"
                    )
                    warnings.append(
                        f"{task_id}: strict_canonical_like rate {rate:.1%} "
                        f"({strict_stats['hits']}/{strict_stats['draws']}) "
                        f"is below the "
                        f"{floor:.1%} floor [{floor_source}] — {remedy}"
                    )

        for name, stats in scored["witnesses"].items():
            if stats["hook_errors"]:
                errors.append(
                    f"{task_id}: witness {name!r} raised/misreturned on "
                    f"{stats['hook_errors']}/{stats['draws']} draws"
                )
            measured = stats["draws"] - stats["hook_errors"]
            stats["measured"] = measured
            if measured > 0 and stats["hits"] == 0:
                errors.append(
                    f"{task_id}: declared witness {name!r} NEVER fires "
                    f"(0/{measured} draws) — documented but never "
                    "generated is precisely the defect this gate exists for"
                )
            elif stats["hits"] and stats["bands_missing"]:
                per_band_hits = {b: r["hits"] for b, r in stats["per_band"].items()}
                if stats["bands_missing_judged"]:
                    expected = {
                        b: round(stats["per_band"][b]["expected"], 1)
                        for b in stats["bands_missing_judged"]
                    }
                    warnings.append(
                        f"{task_id}: witness {name!r} fires in "
                        f"{stats['bands_fired']} but never in "
                        f"{stats['bands_missing_judged']} where its pooled rate "
                        f"{stats['rate']:.1%} predicted {expected} firings "
                        f"(per-band hits {per_band_hits})"
                    )
                if stats["bands_missing_underpowered"]:
                    # Under-powered, NOT a defect: at this census a lawful rare
                    # branch is expected to miss a band. Informational only —
                    # it must never move the status or the exit code.
                    detail = {
                        b: (round(stats["per_band"][b]["expected"], 2),
                            round(stats["per_band"][b]["p_zero"], 2))
                        for b in stats["bands_missing_underpowered"]
                    }
                    notes.append(
                        f"{task_id}: witness {name!r} is too rare to judge "
                        f"per-band at this census — pooled rate "
                        f"{stats['rate']:.1%}, missing bands "
                        f"{stats['bands_missing_underpowered']} "
                        f"(expected, P(zero)) = {detail}; raise --per-band to "
                        f"~{_census_for_power(stats['rate'])} per band to test them"
                    )

            # --- 1. rival-disagreement verification (opt-in) ----------------
            claim = stats.get("rival_claim")
            if claim is None and name in branch_witnesses:
                # Declared positive branch coverage (BRANCH_WITNESSES): proves
                # a scheduled branch fires; never claimed refutation, so it is
                # not WEAK (EWF-002038).
                continue
            elif claim is None:
                # A witness with NO rival claim can only prove that a feature is
                # PRESENT. That is exactly how a structural witness fired
                # 600/600 while the top-aligned rival it was meant to refute
                # also matched 600/600.
                #
                # Reported as WEAK on the summary line ("weak=N/M"), on the
                # per-witness report line ("| no rival claim (WEAK)") and in the
                # machine-readable `weak_witnesses` — but NOT as a note or a
                # warning by default. Every witness in the hooked corpus is in
                # this state (108 generators, 0 rival claims), so a per-witness
                # note would bury the rare-branch notes that DO need reading,
                # and a warning would flip the whole hooked corpus to WARN,
                # which is the "gate everyone ignores" failure mode.
                # --require-rival-witness promotes it to a real warning.
                result["weak_witnesses"].append(name)
                if require_rival_witness:
                    warnings.append(
                        f"{task_id}: witness {name!r} is WEAK — it declares no "
                        "rival disagreement (WITNESS_RIVALS), so its firings "
                        "prove a feature is PRESENT, not that any named rival "
                        "answers differently there"
                    )
                continue

            rival_claims[name] = claim
            if claim["oracle_error"]:
                errors.append(
                    f"{task_id}: witness {name!r} claims rivals "
                    f"{claim['rivals']} disagree, but the claim could NOT be "
                    f"verified: {claim['oracle_error']}"
                )
            if claim["rival_errors"] or claim["oracle_errors"]:
                errors.append(
                    f"{task_id}: witness {name!r} rival check errored on "
                    f"{claim['rival_errors']} rival calls and "
                    f"{claim['oracle_errors']} rule applications: "
                    + "; ".join(claim["error_examples"])
                )
            if claim["checked"] and claim["claim_holds"] == 0:
                errors.append(
                    f"{task_id}: witness {name!r} PROVES NOTHING — it fired "
                    f"{stats['hits']}/{stats['measured']} draws, but on all "
                    f"{claim['checked']} checked firings every named rival "
                    f"{claim['rivals']} still matched the canonical answer "
                    f"(per-rival disagreements "
                    f"{claim['per_rival_disagreements']})"
                )
            elif claim["claim_violated"]:
                first_example = claim["violation_examples"][0]
                first = first_example["replay"]
                preview = "/".join(first_example["grid_preview"]["rows"])
                warnings.append(
                    f"{task_id}: witness {name!r} rival claim holds on only "
                    f"{claim['claim_holds']}/{claim['checked']} checked "
                    f"firings — e.g. {first} fires while every named rival "
                    f"{claim['rivals']} agrees with the canonical answer; "
                    f"counterexample grid={preview}"
                )

        # --- 4. schedule-residue / profile coverage -------------------------
        schedule = scored["census"].get("schedule") or {}
        for cell in schedule.get("aliased") or []:
            warnings.append(
                f"{task_id}: census ALIASES on {cell['expression']} % "
                f"{cell['modulus']} — only residues {cell['residues']} of "
                f"{cell['modulus']} are visited, so a schedule keyed on it is "
                "only partly exercised and a missing branch would read as a "
                "generator defect"
            )
        missing_profiles = schedule.get("profiles_missing")
        if missing_profiles:
            warnings.append(
                f"{task_id}: declared SCHEDULE_PROFILES never visited by the "
                f"census: {missing_profiles} (observed "
                f"{schedule.get('profiles')}) — raise --per-band or fix the "
                "schedule; an unvisited profile is untested, not absent"
            )
        elif schedule.get("profiles"):
            notes.append(
                f"{task_id}: schedule profile coverage (pooled) "
                f"{schedule['profiles']}, per band "
                f"{schedule['profiles_per_band']}"
            )

    # --- 6. canonical ambiguity ---------------------------------------------
    # Runs whether or not a census happened: it reads canonical, and only the
    # SATISFACTION check needs the generated evidence.
    ambiguity = check_canonical_ambiguity(
        task_id, declared_shortcuts=shortcuts,
        rival_claims=rival_claims, witness_rivals=witness_rivals,
    )
    result["canonical_ambiguity"] = ambiguity
    for name in ambiguity["invalid_declared"]:
        validation = ambiguity["declared_validation"][name]
        errors.append(
            f"{task_id}: CANONICAL_SHORTCUTS[{name!r}] is not verified to fit "
            f"all labeled canonical pairs: {validation['status']}; "
            f"checked={validation['checked']}, mismatches={validation['mismatches']}, "
            f"errors={validation['errors']}; examples={validation['examples']!r}. "
            "Partial/noncanonical heuristics belong in LESSON_COMPETITORS."
        )
    if ambiguity["read_error"]:
        warnings.append(f"{task_id}: canonical ambiguity — {ambiguity['read_error']}")
    if ambiguity["shortcut_errors"]:
        warnings.append(
            f"{task_id}: canonical-shortcut evaluation errored "
            f"{ambiguity['shortcut_errors']} times: "
            + "; ".join(ambiguity["shortcut_error_examples"])
        )
    for finding in ambiguity["unsatisfied"]:
        shortcut = finding["shortcut"]
        message = (
            f"{task_id}: ALL {ambiguity['usable_pairs']} canonical pairs are "
            f"answer-equivalent under the {finding['source']} shortcut "
            f"{shortcut!r} — canonical CANNOT falsify it, so only a GENERATED "
            f"counterexample can. Declare SEMANTIC_RIVALS[{shortcut!r}] and a "
            "witness claiming it (WITNESS_RIVALS) so the gate can verify the "
            "counterexample is actually generated"
        )
        if finding["source"] == "declared":
            # The author asserted this is a plausible WRONG rule, so an
            # unrefuted match is a real finding about the curriculum.
            warnings.append(message)
        elif require_shortcut_counterexample:
            warnings.append(message)
        else:
            # A generic dihedral/identity match can also mean "this IS the
            # task's rule", which is not a defect. NOTE by default.
            notes.append(message + " (or confirm this shortcut IS the rule)")
    if ambiguity["satisfied_by_witness"]:
        notes.append(
            f"{task_id}: canonical-ambiguous shortcuts refuted by generated "
            f"counterexample witnesses: {ambiguity['satisfied_by_witness']}"
        )
    if ambiguity.get("authority_equal"):
        # Visible, not silent: the obligation was discharged by an argument
        # (the shortcut is the rule), not by evidence, so a reader must be able
        # to see it and disagree.
        notes.append(
            f"{task_id}: shortcut(s) {ambiguity['authority_equal']} are the "
            f"SELECTED RULE itself (canonical is a bare "
            f"{ambiguity['authority_shortcut']!r} call), so no counterexample "
            "can exist and none is required — WFB-2001 exclusion"
        )

    # --- hook 3: lesson identifiability ------------------------------------
    if lesson_hook is not None or competitors or shortcuts or callable(getattr(gen,"SEARCHED_RIVAL_PROVIDER",None)):
        # 5. EXAMPLES_NEEDED is the module's own statement of how many demos a
        # lesson needs; auditing 3 demos while the shard ships EXAMPLES_NEEDED
        # would judge a lesson shape the trainer never sees.
        declared_demos = getattr(gen, "EXAMPLES_NEEDED", None)
        n_demos = declared_demos
        n_demos_source = "EXAMPLES_NEEDED"
        # Match the materializer's bounded positive count contract. One rich
        # demonstration can refute several rivals; score its actual evidence.
        if type(n_demos) is not int or not 1 <= n_demos <= 32:
            if declared_demos is not None:
                warnings.append(
                    f"{task_id}: EXAMPLES_NEEDED={declared_demos!r} is not an "
                    "integer in 1..32; falling back to 3 demos"
                )
            n_demos = 3
            n_demos_source = "default"
        pass_difficulty = _accepts_difficulty(gen)
        # CANONICAL_SHORTCUTS are ALWAYS scored as lesson competitors
        # (adopted 2026-07-29, EWF-002034): a shortcut the author declared as
        # fitting the canonical demos is exactly the rival a sliding lesson
        # window must refute — omitting it from LESSON_COMPETITORS let an
        # all-canonical window pass while the shortcut survived
        # (a9f315ca9cc7's memorize_public_masks case).
        merged_competitors = dict(competitors)
        auto_scored_shortcuts = sorted(
            name for name in shortcuts if name not in merged_competitors)
        for name in auto_scored_shortcuts:
            merged_competitors[name] = shortcuts[name]
        if auto_scored_shortcuts:
            notes.append(
                f"{task_id}: CANONICAL_SHORTCUTS auto-included in lesson "
                f"competitor scoring: {auto_scored_shortcuts} (not listed in "
                "LESSON_COMPETITORS — list them there explicitly, or record "
                "an answer-equivalence justification in the return, if they "
                "should not be window-scored)"
            )
        stats, problems, lesson_warnings = score_lessons(
            task_id, lesson_hook, count=lessons, n_demos=n_demos,
            pass_difficulty=pass_difficulty, legacy=legacy_lesson_sample,
            competitors=merged_competitors, oracle_factory=_oracle, searched_generator=gen,
            rotate_query=rotate_query, require_rotations=require_rotations,
        )
        stats["auto_scored_canonical_shortcuts"] = auto_scored_shortcuts
        stats["n_demos_source"] = n_demos_source
        if lesson_hook is None:
            notes.append(f"{task_id}: lesson_identifiable absent; lessons checked "
                         "against declared rivals only, without a universal identifiability claim")
        result["lessons"] = stats
        errors.extend(problems)
        warnings.extend(lesson_warnings)
        if legacy_lesson_sample:
            notes.append(
                f"{task_id}: --legacy-lesson-sample is ON — these "
                f"{stats['materialized']} lessons reproduce the v1 population "
                "(every lesson at sample_index 0, generator-default "
                "difficulty). Per-band identifiability was NOT measured; use "
                "this only to compare against pre-2026-07-25 evidence"
            )
        elif not pass_difficulty:
            # COUNTED degradation, never silent: the lessons were materialized,
            # but not per band, so a band-specific branch is untested.
            notes.append(
                f"{task_id}: generate() does not accept a `difficulty` keyword, "
                f"so the {stats['materialized']} lessons were materialized at "
                "the generator's default difficulty — per-band lesson "
                "identifiability was NOT measured"
            )
        if stats["unidentifiable"] and not merged_competitors:
            notes.append(
                f"{task_id}: {stats['unidentifiable']} unidentifiable lessons "
                "could not NAME a surviving competitor — declare "
                "LESSON_COMPETITORS so the gate reports which rival fit every "
                "demo instead of only counting failures"
            )

    # Normal-path reap. If a gate bug ever raises before this line, the oracle
    # is only reachable from `oracle_slot`, so CPython's refcount drop runs
    # `RacketBridge.__del__` -> `shutdown()` (the bridge's own documented
    # non-finalizing fallback) and the child is still reaped.
    if oracle_slot[0] is not None:
        oracle_slot[0].close()

    result["rival_claims"] = rival_claims
    result["errors"] = errors
    result["warnings"] = warnings
    result["notes"] = notes
    result["status"] = "FAIL" if errors else ("WARN" if warnings else "PASS")
    return result


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _summary_line(audit: dict[str, Any]) -> str:
    task_id = audit["task_id"]
    parts = [f"{task_id}: {audit['status']}"]
    declared = [k for k, v in audit.get("hooks_declared", {}).items() if v]
    parts.append("hooks=" + (",".join(declared) if declared else "none"))
    coverage = audit.get("schedule_coverage") or {}
    if coverage.get("status") in {"declared_period_not_enumerated", "invalid_declaration", "complete_fixed_seed_reported", "complete_fixed_seed_executed"}:
        parts.append(f"schedule={coverage['status']} (declared {coverage['declared_period']!r})")
    strict_stats = audit.get("strict_canonical")
    if strict_stats:
        parts.append(
            f"strict={strict_stats['hits']}/{strict_stats['draws']} "
            f"({strict_stats['rate']:.1%})"
        )
        if "canonical_inputs" in strict_stats:
            accepted = (strict_stats["canonical_inputs"]
                        - strict_stats["canonical_rejected"]
                        - strict_stats["canonical_hook_errors"])
            parts.append(
                f"canonical-accepted={accepted}/"
                f"{strict_stats['canonical_inputs']}"
            )
    witnesses = audit.get("witnesses") or {}
    if witnesses:
        fired = sum(1 for s in witnesses.values() if s["hits"] > 0)
        parts.append(f"witnesses={fired}/{len(witnesses)} firing")
        claims = audit.get("rival_claims") or {}
        if claims:
            holding = sum(1 for c in claims.values() if c["claim_holds"] > 0)
            parts.append(f"rival-claims={holding}/{len(claims)} verified")
        weak = audit.get("weak_witnesses") or []
        if weak:
            parts.append(f"weak={len(weak)}/{len(witnesses)} (no rival claim)")
    lessons = audit.get("lessons")
    if lessons:
        per_band = {
            band: f"{row['identifiable']}/{row['materialized']}"
            for band, row in (lessons.get("per_band") or {}).items()
        }
        verdict = ("identifiable" if lessons.get("hook_declared", True) else
                   "without detected declared-rival ambiguity")
        parts.append(
            f"lessons={lessons['identifiable']}/{lessons['materialized']} "
            f"{verdict} (requested {lessons['requested']}, per band "
            f"{per_band})"
        )
        rotations = lessons.get("rotations", {})
        if rotations.get("requested"):
            policy = "required" if rotations["required"] else "diagnostic"
            parts.append(
                f"rotations={rotations['ambiguous']}/{rotations['checked']} "
                f"ambiguous ({rotations['status']}, {policy})")
    census = audit.get("census")
    if census and census.get("crashes"):
        parts.append(f"crashes={census['crashes']}/{census['planned']}")
    return " — ".join(parts[:1]) + " — " + ", ".join(parts[1:])


def report(audit: dict[str, Any]) -> None:
    print(_summary_line(audit))
    followup = (audit.get("schedule_coverage") or {}).get("followup_argv")
    if followup:
        import shlex
        print("  FOLLOW-UP (new output path required): " + shlex.join(followup))
    for message in audit.get("advisories") or []:
        print(f"  {message}")
    for message in audit.get("errors") or []:
        print(f"  ERROR: {message}")
    for message in audit.get("warnings") or []:
        print(f"  WARN:  {message}")
    for message in audit.get("notes") or []:
        print(f"  NOTE:  {message}")
    witnesses = audit.get("witnesses") or {}
    for name in sorted(witnesses):
        stats = witnesses[name]
        per_band = {b: r["hits"] for b, r in stats["per_band"].items()}
        line = f"  witness {name}: {stats['hits']}/{stats['draws']} {per_band}"
        claim = stats.get("rival_claim")
        if claim is not None:
            line += (
                f" | rival claim {claim['claim_holds']}/{claim['checked']} "
                f"checked, per-rival {claim['per_rival_disagreements']}"
            )
        elif name in (audit.get("branch_witnesses") or []):
            line += " | branch coverage (declared BRANCH_WITNESSES)"
        else:
            line += " | no rival claim (WEAK)"
        print(line)
    lessons = audit.get("lessons") or {}
    for example in lessons.get("unidentifiable_examples") or []:
        print(
            f"  UNIDENTIFIABLE lesson #{example['index']} [{example['replay']}]"
            f" survivors={example['survivors']} "
            f"[{example['survivor_source']}] reasons={example['reasons']}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("task_ids", nargs="+")
    parser.add_argument(
        "--per-band", type=int, default=50,
        help="pinned census draws per difficulty band (default: 50)",
    )
    parser.add_argument(
        "--lessons", type=int, default=20,
        help="lessons materialized for lesson_identifiable (default: 20)",
    )
    parser.add_argument(
        "--min-strict-frac", type=float, default=DEFAULT_MIN_STRICT_FRAC,
        help="WARN when the pooled strict_canonical_like rate is below this "
             "fraction (default: %(default)s; 0 disables). Mirrors "
             "canonical_profile_gate --warn-frac: ZERO support is always the "
             "hard FAIL, low-but-nonzero is a visible warning. A generator may "
             "override it per task with MIN_STRICT_FRAC.",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="warnings — and a bare 'no semantic contract declared' advisory — "
             "exit 1 instead of 0",
    )
    parser.add_argument(
        "--require-rival-witness", action="store_true",
        help="promote the WEAK-witness report (a witness that declares no "
             "WITNESS_RIVALS disagreement claim; reported on the summary line, "
             "on its witness line and in weak_witnesses) to a WARNING. OFF by "
             "default: every hooked generator in the corpus is currently in "
             "that state, and a gate that warns on all of them gets ignored.",
    )
    parser.add_argument(
        "--require-shortcut-counterexample", action="store_true",
        help="promote the generic canonical-ambiguity NOTE to a WARNING. OFF "
             "by default because a simple shortcut reproducing every canonical "
             "pair can also mean the shortcut IS the task's rule. A shortcut "
             "the generator DECLARES (CANONICAL_SHORTCUTS) always warns.",
    )
    parser.add_argument(
        "--legacy-lesson-sample", action="store_true",
        help="reproduce the v1 lesson population (every lesson at "
             "sample_index 0, generator-default difficulty, no per-band "
             "split). For comparing a v1.1 finding against pre-2026-07-25 "
             "evidence ONLY — that fixed start offset is the aliasing the "
             "per-band plan replaced.",
    )
    parser.add_argument(
        "--require-contract", action="store_true",
        help="turn NO_CONTRACT into a hard FAIL instead of an advisory. Use "
             "this for ASSIGNED REPAIRS and candidate acceptance, never for a "
             "legacy sweep: most of the corpus predates the contract and a gate "
             "that is red for all of it gets ignored. Requested by eight "
             "independent reviewers on 2026-07-25 after two shortcut-teaching "
             "generators passed a green baseline whose semantic gate had simply "
             "never asked the question.",
    )
    parser.add_argument("--json-out", type=Path)
    parser.add_argument('--schedule-census', type=Path,
                        help='consume a complete source-bound fixed-seed census JSON or native hash-bound gzip/manifest (one task only)')
    parser.add_argument('--schedule-seed', type=int, default=0,
                        help='required census seed; coverage stays limited to this seed')
    parser.add_argument('--enumerate-schedule-period', action='store_true',
                        help='generate every declared start and query rotation at one fixed seed; requires staged runtime and --json-out')
    parser.add_argument(
        "--rotate-query", action="store_true",
        help="diagnose every held-out pair using already labelled lessons; "
             "reported separately from the production lesson verdict")
    parser.add_argument(
        "--require-rotations-identifiable", action="store_true",
        help="run query rotations and fail on ambiguity, hook warnings or scoring errors")
    args = parser.parse_args(argv)
    if args.schedule_census is not None and len(args.task_ids) != 1:
        parser.error('--schedule-census requires exactly one task')
    if args.enumerate_schedule_period and (len(args.task_ids) != 1 or args.json_out is None or args.schedule_census is not None):
        parser.error('--enumerate-schedule-period requires one task and --json-out, without --schedule-census')
    if not 0 <= args.schedule_seed < 2**32:
        parser.error('--schedule-seed must be a uint32')

    audits: list[dict[str, Any]] = []
    failed = 0
    warned = 0
    advisory = 0
    for task_id in args.task_ids:
        audit = audit_task(
            task_id, per_band=args.per_band, lessons=args.lessons,
            strict=args.strict, min_strict_frac=args.min_strict_frac,
            require_rival_witness=args.require_rival_witness,
            require_shortcut_counterexample=args.require_shortcut_counterexample,
            legacy_lesson_sample=args.legacy_lesson_sample,
            require_contract=args.require_contract,
            rotate_query=args.rotate_query,
            require_rotations=args.require_rotations_identifiable,
            schedule_census=args.schedule_census, schedule_seed=args.schedule_seed,
            enumerate_schedule_period=args.enumerate_schedule_period,
            schedule_census_out=args.json_out.with_name(args.json_out.stem + '.schedule-census.json') if args.enumerate_schedule_period else None,
        )
        audits.append(audit)
        report(audit)
        if audit["status"] in ("FAIL", "IMPORT_FAIL"):
            failed += 1
        elif audit["status"] == "WARN":
            warned += 1
        elif audit["status"] == "NO_CONTRACT":
            advisory += 1

    if args.json_out:
        path = (args.json_out if args.json_out.is_absolute()
                else ROOT / args.json_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            # 2 adds (all additive; every v1 key is still present and unchanged):
            #   audits[].rival_claims / weak_witnesses / canonical_ambiguity
            #   audits[].optional_declarations
            #   audits[].census.schedule (residue + profile coverage)
            #   audits[].lessons.per_band / .difficulty_passed and the
            #     (band, seed, sample_index) replay tuple + named survivors on
            #     every unidentifiable_examples row
            "schema_version": 2,
            "gate": "generator_semantic_gate",
            "audits": audits,
        }, indent=2) + "\n")

    passed = len(audits) - failed - warned - advisory
    print(
        f"semantic-gate: {passed} pass, {warned} warn, {advisory} "
        f"no-contract, {failed} fail (of {len(audits)})"
    )
    if failed:
        return 2
    if args.strict and (warned or advisory):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
