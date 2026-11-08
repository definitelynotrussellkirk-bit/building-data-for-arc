# Current parametric decision: review-c1f55e4b54bf0ee3

Built the native `ring_motion` family under `workspace/parametric/`: exact
canonical program, inverse, odd-distinct-count canonical and even-distinct-count
canonical. The original corner and midpoint cycles move in opposite directions;
the executable authority takes precedence over the old clockwise summary.

Each conditional rule detects a ring, counts its distinct border colors including
zero, and chooses a permutation from that input-dependent count. Different rings
in one scene can require different directions. This is contextual gating, not
iterative state simulation. The canonical generator and reference ledger are
unchanged; the native sampler independently enforces complete, separated rings.

Independent counts support 2–6 demonstrations and 1–4 novel queries. All settings
share inputs, and both demo/query prefixes are stable. Two demonstrations suffice
to eliminate the other three settings and the 40 explicit extra rivals on the
checked seeds; this finite statement is not universal identifiability. Fixed core
profiles and separated-slot later layouts remain deliberate support limits.

The authoring probe in `checks/630d6cc550e4/probe.py` and task evidence under
`workspace/parametric/evidence/final/` retain 972 protected evaluations, eight
standard lessons, 32 count-boundary requests, four official pairs and two 3×3
anchors. Final task tests pass 56 tests plus four canonical subtests. Native
qualification, witness and current reviewer status are recorded in the return's
`RESULTS.json` and `checks/630d6cc550e4/`; owner exact-source acceptance remains
pending. The prior resolved canonical placement audit is not reopened by this
separate extension.

The first-query projector is tested against the native canonical serializer.
Shared export still contains all controller-side queries; sequential visibility
requires the existing consumer to use the task-local first-turn projection.

---

# Working notes: 630d6cc550e4

## 2026-10-24 repair

The prior sampler encoded a narrow fixed-lattice lesson: advertised corner/height controls were inert, canonical-size edge placements were absent, and ring palettes excluded legal zero/repeated colors. The selected `2.1.1` repair samples separated rings across the full 7..16 canvas domain, preserves exact canonical detection, guarantees observable `block_count`/`palette_size`, and uses a bounded constructive fallback when randomized placement strands a realizable count.

Regression coverage retains the original fixed-lattice rival, canonical structural/rule parity, 7×7 corner layouts, the one-corner-block early-return bug, exact six-block and nine-color endpoints, repeated/zero ring values, and strict unknown-control rejection. The canonical Racket rule was not changed.

Evidence: `checks/630d6cc550e4-task-tests-final/`, `checks/630d6cc550e4-lint-final/`, `checks/630d6cc550e4-selfcheck-final/`, `checks/630d6cc550e4-rule_smoke-final/`, `checks/bounded-override-final/`, `checks/final-adversarial/`, and `checks/racket-parity-final/`.

Limit: the official 30-seed override controller previously stalled during post-matrix finalization after 79,000 of 80,100 draws with no findings. The retained bounded full Cartesian run completed 8,010 draws with zero findings or warnings; the sole mathematical incompatibility (`block_count=1`, `palette_size=9`) is declared explicitly. A separate retained probe checked 1,260 exact single-axis observations.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-5ecad9cd111a9c71:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `e63387493be05e381d2a5792039e4db500cd713133ce9175b4d98e3c086016e3`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted sourcebc09219197b55adc2e6a1680b5da303f3bff235d7d3524ad03331e22de50404c replaces fixed placement with separated canonical-size ring scenes through16x16and observable exact controls. Reviewer reports10tests/four canonical subtests,120reference-smoke cases and bounded override/stress evidence; no owner rerun.

### Assessment or prior finding

## 630d6cc550e4

**Issue found — A630-1: fixed placement permits a spatial-template shortcut and excludes canonical support.** Findings-only audit; target generator and shared/reference code remain unchanged.

At `generators/630d6cc550e4/generator.py:85–104`, normal draws fix height to `4*block_count+3`, top rows to `1+4*i`, and left columns to `1` or `width-4`. The advertised `anchor_corner` override is never consumed. `rng.sample(pool,8)` also forces eight distinct nonzero border colors, whereas canonical training examples include repeated colors and 0. Canonical inputs are 7×7 with edge/off-lattice blocks; the declared `grid_w` axis only admits 9..16 and the default is 11. Randomizing the palette does not vary this block-location support.

A concrete rival in `checks/audit/630d6cc550e4/probe.py` applies the reference cell permutation only at rows `1,5,9,...` and columns `{1,width-4}`, using just the candidate top-left color to skip empty slots. It never searches for orange centers or discovers arbitrary block locations. This rival agrees with **12/12 generated draws (9 distinct input grids)** across all three difficulty bands, seeds 0 and 1, sample indices 0 and 1. Sample 0 uses defaults; sample 1 uses declared-valid `grid_w=9, position_bias=right, anchor_corner=True`. All 12 generated inputs pass the generator's `self_check`, and public Racket execution produces valid outputs. Source inspection establishes the fixed-lattice restriction for all normal draws with declared-valid widths and position biases; finite sampling alone is not a universal empirical census.

The same rival agrees with **0/3 canonical training inputs**. All three pass the current `self_check` and receive valid canonical Racket outputs. Thus these are reference-supported cases on which the generator-trained positional rival fails; they are not out-of-domain hand constructions. The weak validator accepts canonical input but cannot reveal the generator's coverage gap. All 15 Racket labels were obtained through the supported public `arcpuzzles apply` command, not a Python rule reimplementation. The rival is intentionally a shortcut, not an alternative reference label.

**Suggested maintainer action:** vary rows/columns independently of block index, include edge anchoring and canonical-size draws, and allow repeated/0 border colors while preserving lawful block separation. Add a regression requiring generated lessons to distinguish this fixed-lattice rival using an off-lattice or edge block. This audit proposes no code changes.

**Evidence and identity:** selected generator SHA-256 `e63387493be05e381d2a5792039e4db500cd713133ce9175b4d98e3c086016e3`; canonical executed/catalog rule hash `6dfce0f7503c`, rule-text SHA-256 `8fa2066b3ea67431fdb9a8229b5bf3e9d9cc4bb9796f75332789c3461b1331d4`. Evidence: `checks/audit/630d6cc550e4/{probe.py,input.json,probe_records.json,racket.json,analysis.json,audit_receipt.json}`. Current `notes.md` is a placeholder; no `evidence/review_index.json` or task-local `tests/` exists to resolve this issue or supply focused regressions. Associated notes contain no entries. The audit checked 15 inputs only; it did not run full batteries, enumerate lessons, inspect solve/private-label material, or claim training approval.

Reproducer (outer packet root; the Racket output path must be new when rerunning):

```bash
PYTHONDONTWRITEBYTECODE=1 /workspace/scratch/a95c88c2e105/review-runtime/bin/python3 WORK/checks/audit/630d6cc550e4/probe.py prepare
PATH=/workspace/scratch/a95c88c2e105/review-runtime/bin:$PATH python3 review.py run python3 -m arcpuzzles apply 630d6cc550e4 --input ../checks/audit/630d6cc550e4/input.json --out ../checks/audit/630d6cc550e4/racket.json
PYTHONDONTWRITEBYTECODE=1 /workspace/scratch/a95c88c2e105/review-runtime/bin/python3 WORK/checks/audit/630d6cc550e4/probe.py analyze
```

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-5ecad9cd111a9c71-v0001/audit_assets.json), manifest SHA-256 `b04095b069401a6fea0380e90d76a1ea34459ae84a4826aaf6aba65de6f7ce9f`.
<!-- arcpuzzles-current-audit-assessment:end -->
