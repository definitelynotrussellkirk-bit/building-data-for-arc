#!/usr/bin/env python3
"""Canonical-profile floor — the semantic companion the coarse gate lacks.

20+ independent worker reports (EWF-000329/337/354/367/380/417/423/442/448/
451/461/462/471/474/478/482/491/494/504…) documented the same blindness: the
morphology-marginals distribution gate stays green while a generator has ZERO
support for the canonical task manifold. Measured baseline failures of that
class: 4bf462ff34fb 0.0% canonical-profile support, 3f533a120cf5 0.0%,
61b78c2a0489 self_check rejecting ALL canonical inputs.

This gate enforces the floor those reports asked for, per task:

  1. HARD FAIL — the generator's self_check rejects any canonical
     train/test input (the generator disowns the very distribution it is
     supposed to teach).
  2. HARD FAIL — across a pinned-seed census (all bands), NOT ONE returned
     grid matches ANY canonical exact profile (h, w, palette-size). A
     difficulty curriculum only anchors canonical scale somewhere (usually
     the easy band), so the requirement is support > 0 anywhere, not a rate.
     A generator may opt out of this check ONLY by declaring
     ``CANONICAL_PROFILE_OPT_OUT = "reason"`` — reported LOUD, never silent.
  3. WARN — exact support exists but is under --warn-frac (default 5%), or
     the in-envelope rate (dims/palette within canonical min..max) is under
     --warn-envelope-frac (default 25%). Warnings are visible and exit 0 by
     default; pass --require-pass when the caller needs WARN to block.

Draws are pinned (sha256-derived seeds, off-diagonal sample indexes) so every
worker and intake measures the same census. Usage:

    python3 scripts/canonical_profile_gate.py TASK_ID [TASK_ID ...] \
        [--per-band 20] [--json-out out.json]
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
BANDS = ("easy", "medium", "hard")

# ONE canonical-encoding normalizer, shared with the verifier: canonical rows
# store some grids as row-strings and singleton splits as bare dicts. Feeding
# either representation raw into self_check rejects lawful canonical inputs
# (v13-x WFB: 3c66fa1a10c7 baseline rejected 4/4 as "bad string code").
from scripts.coder_synth_verify import _as_pairs, _norm_grid


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return (len(grid), len(grid[0]), len({c for row in grid for c in row}))


def _pinned_seed(task_id: str, band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{task_id}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def canonical_pairs(task_id: str) -> list[dict[str, Any]]:
    """Every canonical train/test (input, output) PAIR for task_id.

    One reader, two views: `canonical_inputs` is this function's input column.
    A second walk of `puzzles.jsonl` with its own normalization could drift, and
    then the profile floor and the semantic gate would characterise two
    different populations while quoting each other's numbers.

    Invalid inputs are dropped. An unlabeled/invalid output remains None, so
    the input view does not lose query inputs; label consumers exclude it.
    Pair identities use zero-based JSONL line, task-variant and split indexes.
    """
    pairs: list[dict[str, Any]] = []
    variant = -1
    with CANONICAL.open(encoding="utf-8") as handle:
        for row_index, line in enumerate(handle):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != task_id:
                continue
            variant += 1
            for split in ("train", "test"):
                for pair_index, pair in enumerate(_as_pairs(row.get(split))):
                    if not isinstance(pair, dict):
                        continue  # rule-only/template rows carry non-pair entries
                    grid = _norm_grid(pair.get("input"))
                    if not grid:
                        continue
                    pairs.append({"input": grid,
                                  "output": _norm_grid(pair.get("output")),
                                  "pair_identity": {"canonical_row": row_index,
                                      "variant": variant, "split": split,
                                      "pair_index": pair_index}})
    return pairs


def canonical_inputs(task_id: str) -> list[list[list[int]]]:
    """Every canonical train/test input across ALL source rows for task_id."""
    return [pair["input"] for pair in canonical_pairs(task_id)]


def canonical_rule_source(task_id: str) -> str:
    """The SELECTED canonical Racket source (`program_solution`) for task_id.

    This is the one authoritative selected-rule reader, beside canonical_pairs:
    focused tests and tools must not re-scan puzzles.jsonl with their own
    normalization, and must NOT hash the runner's wrapped callable text
    (`_load_bundle().rule_callable_text`) — that wrapper hashes differently
    from the source and produced the 1569ecfa4ff1 hash confusion.

    Raises FileNotFoundError if no canonical row carries a program_solution.
    """
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == task_id and row.get("program_solution"):
                return str(row["program_solution"])
    raise FileNotFoundError(
        f"{task_id}: no canonical row with a program_solution"
    )


def normalized_rule_hash(source: str) -> str:
    """THE rule-hash convention, defined once.

    sha256 of the WHITESPACE-normalized source, first 12 hex chars. It is
    comment-SENSITIVE by design: a comment edit to the selected source is a
    source change and must re-pin RULE_HASH atomically (comment-stripped
    "behavior hashes" exist only as diagnostics in authority-sync tooling and
    are never what RULE_HASH pins). Shared by set_rule_text,
    generator_defect_lint's staleness probe, and focused generator tests.
    """
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def canonical_rule_hash(task_id: str) -> str:
    """normalized_rule_hash of the selected canonical source for task_id."""
    return normalized_rule_hash(canonical_rule_source(task_id))


def audit_task(
    task_id: str, *, per_band: int = 20, strict: bool = False,
    min_band_support: int = 0,   # 0 = report zero-support bands, do not gate
) -> dict[str, Any]:
    result: dict[str, Any] = {"task_id": task_id}
    canon = canonical_inputs(task_id)
    if not canon:
        result["status"] = "NO_CANONICAL"
        result["errors"] = [f"{task_id}: no canonical inputs found"]
        return result
    profiles = {_profile(g) for g in canon}
    hs = [p[0] for p in profiles]
    ws = [p[1] for p in profiles]
    ps = [p[2] for p in profiles]
    envelope = ((min(hs), max(hs)), (min(ws), max(ws)), (min(ps), max(ps)))
    result["canonical_profiles"] = sorted(profiles)
    result["envelope"] = envelope

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

    # 1. Canonical acceptance: the generator must own its own task's inputs.
    self_check = getattr(gen, "self_check", None)
    rejected = 0
    if callable(self_check):
        for index, grid in enumerate(canon):
            try:
                findings = self_check(copy.deepcopy(grid))
            except Exception as exc:
                findings = [f"self_check crashed: {exc!r}"]
            if findings:
                rejected += 1
                if rejected <= 3:
                    errors.append(
                        f"{task_id}: self_check REJECTS canonical input "
                        f"#{index}: {str(findings)[:140]}"
                    )
        if rejected > 3:
            errors.append(
                f"{task_id}: …and {rejected - 3} more canonical rejections"
            )
    else:
        errors.append(f"{task_id}: generator has no callable self_check")
    result.setdefault("strict_would_fail", False)
    result["canonical_inputs"] = len(canon)
    result["canonical_rejected"] = rejected

    # 2. Pinned census: exact-profile and envelope support.
    per_band_stats: dict[str, dict[str, Any]] = {}
    exact_hits = 0
    envelope_hits = 0
    crashes = 0
    total = 0
    exception_examples: list[dict[str, Any]] = []
    exception_keys: set[tuple[str, str]] = set()
    for band in BANDS:
        band_exact = band_env = band_crash = 0
        for index in range(per_band):
            seed = _pinned_seed(task_id, band, index)
            sample_index = seed % 7919 + index
            try:
                grid = gen.generate(seed, sample_index, difficulty=band)
            except Exception as exc:
                band_crash += 1
                # Preserve replay coordinates and a few representative causes.
                # Bound both retained text and deduplication state; counts and
                # verdict policy below remain independent of these examples.
                if len(exception_examples) < 3:
                    message = str(exc)
                    message_hash = hashlib.sha256(message.encode("utf-8", errors="replace")).hexdigest()
                    key = (type(exc).__name__, message_hash)
                    if key not in exception_keys:
                        exception_keys.add(key)
                        exception_examples.append({
                            "exception_type": key[0], "message": message[:500],
                            "message_truncated": len(message) > 500,
                            "message_sha256": message_hash,
                            "band": band, "seed": seed,
                            "sample_index": sample_index,
                        })
                continue
            prof = _profile(grid)
            total += 1
            if prof in profiles:
                band_exact += 1
            (h_lo, h_hi), (w_lo, w_hi), (p_lo, p_hi) = envelope
            if (h_lo <= prof[0] <= h_hi and w_lo <= prof[1] <= w_hi
                    and p_lo <= prof[2] <= p_hi):
                band_env += 1
        exact_hits += band_exact
        envelope_hits += band_env
        crashes += band_crash
        per_band_stats[band] = {
            "draws": per_band, "crashes": band_crash,
            "exact": band_exact, "envelope": band_env,
            # Envelope is inclusive: every exact hit is also an envelope hit.
            "envelope_only": band_env - band_exact,
        }
    result["per_band"] = per_band_stats
    result["draws_total"] = total
    result["crashes"] = crashes
    result["generation_exception_examples"] = exception_examples
    result["exact_hits"] = exact_hits
    result["envelope_hits"] = envelope_hits
    result["envelope_only_hits"] = envelope_hits - exact_hits
    result["band_support_basis"] = "exact"

    if crashes and crashes > (per_band * len(BANDS)) // 2:
        errors.append(
            f"{task_id}: {crashes} generation crashes during the census"
        )
    elif crashes:
        # A MINORITY of crashes used to be completely silent: a run with 4
        # crashes and 56 successful draws passed --strict with nothing said
        # (v13-z 80b1344c17c8 WFB-001). Those seeds produce NO training data,
        # and an unreported generator crash is a defect that never gets fixed.
        # Measured blast radius before making this blocking: 0 of 80 sampled
        # generators crash at all, so this is a safety net, not churn.
        message = (
            f"{task_id}: {crashes} generation crash(es) in {total + crashes} "
            f"census draws — those seeds yield no data and the failure is "
            f"otherwise unreported"
        )
        if strict:
            errors.append(message)
        else:
            warnings.append(message + " [FAIL under --strict]")
            result["strict_would_fail"] = True

    opt_out = getattr(gen, "CANONICAL_PROFILE_OPT_OUT", None)
    if total and exact_hits == 0:
        envelope_frac = envelope_hits / total
        zero_message = (
            f"{task_id}: ZERO of {total} draws match any canonical "
            f"profile {sorted(profiles)} (envelope rate "
            f"{envelope_frac:.1%})"
        )
        if opt_out:
            warnings.append(
                zero_message + f" — CANONICAL_PROFILE_OPT_OUT="
                f"{str(opt_out)[:100]!r} declared; allowed LOUDLY"
            )
        elif envelope_frac < 0.10:
            # No exact anchor AND essentially nothing inside the canonical
            # dims/palette envelope: the generator teaches a different task
            # scale than it claims (the 4bf462/3f533a baseline class).
            # Strict mode (required for NEW repairs) fails; default mode
            # reports LOUDLY so the legacy corpus is flagged, not churned.
            target = errors if strict else warnings
            # Machine-readable twin of the "[FAIL under --strict]" prose. A
            # non-strict stage exited 0 while its own text said it would fail,
            # and battery summaries recorded that as a clean pass — reported
            # by 3 workers (v13-y c8d8b907048d WFB-003, 8af64ebfaf77 WFB-002,
            # 061fc3ec486a WFB-002). Consumers can now branch on the flag.
            result["strict_would_fail"] = True
            target.append(
                zero_message + " — declare CANONICAL_PROFILE_OPT_OUT with "
                "a reason ONLY if this is intentional and reviewed"
                + ("" if strict else " [FAIL under --strict]")
            )
        else:
            warnings.append(
                zero_message + " — draws stay inside the canonical envelope "
                "but never anchor an exact canonical profile; add an "
                "exact-profile branch or declare CANONICAL_PROFILE_OPT_OUT"
            )
    # PER-BAND FLOOR. Everything above is POOLED, so a generator that anchors
    # canonical scale only in `easy` passed cleanly with medium 0/200 and hard
    # 0/200 and strict_would_fail=False — the per-band counts were collected
    # and then never consulted (v13-z a5df658a2503 WFB-002). Pooled acceptance
    # is not cross-band coverage, and a reviewer reading "strict PASS" cannot
    # tell the difference.
    #
    # Only meaningful when the task anchors SOMEWHERE: if nothing matched at
    # all, the zero-support check above already fired and this would just
    # restate it.
    if total and (exact_hits or envelope_hits):
        zero_bands = sorted(
            band for band, stats in per_band_stats.items()
            if stats["exact"] == 0
        )
        # ALWAYS machine-readable, so "strict PASS" can never be mistaken for
        # cross-band coverage even when we do not gate on it.
        result["bands_with_zero_support"] = zero_bands
        starved = sorted(
            band for band, stats in per_band_stats.items()
            if stats["exact"] < min_band_support
        ) if min_band_support > 0 else []
        if starved:
            message = (
                f"{task_id}: band(s) {starved} have fewer than "
                f"{min_band_support} exact canonical-profile hit(s) in "
                f"{per_band} draws each "
                f"({exact_hits} exact / {envelope_hits} inclusive envelope of {total}). "
                f"Exact support is required independently in each band"
            )
            if opt_out:
                warnings.append(
                    message + f" — CANONICAL_PROFILE_OPT_OUT="
                    f"{str(opt_out)[:100]!r} declared; allowed LOUDLY"
                )
            else:
                result["strict_would_fail"] = True
                result["bands_below_floor"] = starved
                (errors if strict else warnings).append(
                    message + ("" if strict else " [FAIL under --strict]")
                )
        elif zero_bands:
            # Not gated, but never silent: measured at 35/60 generators in a
            # corpus sample, and several repairs document band-scale
            # divergence as deliberate ("hard explores larger lattices while
            # preserving the same rule"). So this is reported, not enforced —
            # enforcement is opt-in via --min-band-support.
            warnings.append(
                f"{task_id}: band(s) {zero_bands} have ZERO canonical-profile "
                f"support in {per_band} draws each; the pooled census passes "
                f"on the other band(s). This is reported, not gated — pass "
                f"--min-band-support N to make it blocking"
            )
    result["min_band_support"] = min_band_support
    result["opt_out"] = str(opt_out) if opt_out else None
    return _finish(result, errors, warnings)


def _finish(result, errors, warnings):
    result["errors"] = errors
    result["warnings"] = warnings
    result["status"] = "FAIL" if errors else ("WARN" if warnings else "PASS")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_ids", nargs="+")
    parser.add_argument("--per-band", type=int, default=20)
    parser.add_argument("--warn-frac", type=float, default=0.05)
    parser.add_argument("--warn-envelope-frac", type=float, default=0.25)
    parser.add_argument(
        "--strict", action="store_true",
        help="zero canonical support (exact AND envelope) is a FAIL, not a "
             "loud WARN — required for newly repaired generators",
    )
    parser.add_argument(
        "--min-band-support", type=int, default=0,
        help="minimum exact canonical-profile hits required in "
             "EVERY difficulty band once the task anchors anywhere. The "
             "verdict is otherwise pooled-only, so a generator anchoring "
             "solely in `easy` passes with medium 0/N and hard 0/N. Default "
             "0 = report zero-support bands as a WARNING but do not gate "
             "(35/60 sampled generators vary band scale deliberately); "
             "set >=1 to make it blocking.",
    )
    parser.add_argument(
        "--require-pass", action="store_true",
        help="return nonzero for WARN as well as FAIL. This is an opt-in "
             "clean-verdict policy; the calibrated default keeps advisory "
             "warnings non-blocking.",
    )
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    audits = []
    for task_id in args.task_ids:
        audit = audit_task(
            task_id, per_band=args.per_band, strict=args.strict,
            min_band_support=args.min_band_support,
        )
        # Rate-based warnings depend on CLI thresholds, applied here.
        total = audit.get("draws_total") or 0
        if audit.get("status") in ("PASS", "WARN") and total:
            exact_frac = audit.get("exact_hits", 0) / total
            env_frac = audit.get("envelope_hits", 0) / total
            if 0 < exact_frac < args.warn_frac:
                audit["warnings"].append(
                    f"{task_id}: exact canonical-profile support "
                    f"{exact_frac:.1%} < {args.warn_frac:.0%}"
                )
            if env_frac < args.warn_envelope_frac:
                audit["warnings"].append(
                    f"{task_id}: canonical-envelope rate {env_frac:.1%} < "
                    f"{args.warn_envelope_frac:.0%}"
                )
            if audit["warnings"] and audit["status"] == "PASS":
                audit["status"] = "WARN"
        audits.append(audit)
        total = audit.get("draws_total") or 0
        exact = audit.get("exact_hits", 0)
        print(
            f"{task_id}: {audit['status']} — canonical inputs "
            f"{audit.get('canonical_inputs', 0)} (rejected "
            f"{audit.get('canonical_rejected', '?')}), exact-profile "
            f"{exact}/{total}, envelope "
            f"{audit.get('envelope_hits', 0)}/{total}"
            # Crashes belong in the ONE line a reviewer reads, not only in the
            # JSON — they were invisible there (v13-z 80b1344c17c8 WFB-001).
            + (f", crashes {audit['crashes']}" if audit.get("crashes") else "")
        )
        for message in audit.get("errors") or []:
            print(f"  ERROR: {message}")
        for message in audit.get("warnings") or []:
            print(f"  WARN:  {message}")
        for example in audit.get("generation_exception_examples") or []:
            # One bounded line even when an exception contains newlines.
            message = example["message"].replace("\n", "\\n").replace("\r", "\\r")
            print(
                f"  EXCEPTION: {example['exception_type']}: {message}"
                + (" [message truncated]" if example["message_truncated"] else "")
                + f" (band={example['band']} seed={example['seed']}"
                + f" sample_index={example['sample_index']})"
            )
    if args.json_out:
        path = (args.json_out if args.json_out.is_absolute()
                else ROOT / args.json_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(
            {"schema_version": 1, "audits": audits}, indent=2) + "\n")

    # A WARN row used to be counted into "N/N pass", so an aggregate log could
    # read `canonical-profile-floor: 1/1 pass` directly beneath its own
    # `exact-profile 0/60 ... [FAIL under --strict]` text (v13-z 1d26c382ab68
    # WFB-003). Reserve "pass" for rows with nothing to say and surface the
    # warned count separately.
    failed = sum(
        1 for a in audits
        if a.get("status") in ("FAIL", "IMPORT_FAIL", "NO_CANONICAL")
    )
    warned = sum(1 for a in audits if a.get("status") == "WARN")
    clean = len(audits) - failed - warned
    summary = f"canonical-profile-floor: {clean}/{len(audits)} pass"
    if warned:
        summary += f", {warned} WARN"
        if args.require_pass:
            summary += " (blocking under --require-pass)"
    if failed:
        summary += f", {failed} FAIL"
    print(summary)
    return 1 if failed or (args.require_pass and warned) else 0


if __name__ == "__main__":
    raise SystemExit(main())
