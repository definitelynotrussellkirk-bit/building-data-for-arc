# Vertical Mirror Add implementation plan

This document retains the initial plan and records the current execution status separately. The unchecked task lists below preserve the original plan; they are not a live completion checklist. See **Current execution status** for completed work. Replay and package status remain authoritative in `WORK/RESULTS.json` and `WORK/REVIEW.md`.

> Original execution instruction: execute the bounded repair directly with the test-first workflow; retain independent diagnostic and final code review.

**Goal:** repair ignored controls and teach every occurrence of a mirrored seed, including right-side, repeated-color and centerline cases.

**Architecture:** one self-contained input generator with pixel-derived validation/observations and deterministic finite-rival lesson hooks; a separate portable diagnostic emits evidence. Racket remains the label authority.

**Tech stack:** Python 3.12+, existing `GenCtx` / grid / `reviewer_support` APIs, bundled Racket and pytest.

**Spec:** `WORK/DUTIES.md`, `WORK/RETURN-GUIDE.md`, `repo/docs/SEMANTIC_GATE_CONTRACT.md` and the selected canonical E31 rule.

## Global constraints

- Assignment `review-2b87cd571a9526b8` remains unchanged; edit only its selected task home and, only if required, selected active authority text.
- Keep the canonical Racket program unchanged. Collision-free completion is the ordinary domain; conflicting reflected colors have swap semantics in the authority and are rejected by this generator domain.
- Portable tests use `reviewer_support.find_root` and `canonical_pairs`. No frozen fixture, shared tool, catalog or audit source edits.
- Exact integer controls reject booleans/coercions. `None` means absent; unknown keys fail.
- Preserve real failed checks and source-bound counterexamples. The final patch must replay on a fresh original extraction.

## Review focus

1. Single-axis extremes must adapt unpinned defaults; explicit impossible tuples reject with named axes.
2. Aliases must be equal and observable; edge textures must honor dimensions/counts or explicitly reject incompatible controls.
3. Rich layouts need multiple cells in a row, repeated off-axis colors, right sources and varying coordinates without reflected conflicts.
4. Both centerline-bearing profiles must preserve center cells, retaining evidence in every 3-of-4 query rotation.
5. Canonical support must survive hard difficulty and portable staging; blank/center-only endpoints are opt-in.

## Initial plan: Task 1 — generator and regression contract

**Files:** `generator.py`, `tests/test_generator_contract.py`, `notes.md`.

**Interfaces:** `generate(seed, sample_index, difficulty=None, **overrides)`; `self_check(grid, difficulty=None, meta=None)`; `observe_overrides(grid)`; `strict_canonical_like(grid)`; `lesson_identifiable(demos, query)`.

- [ ] Write tests for declared boundaries, aliases, invalid controls, lawful edges, collision validation, canonical support, and all four cyclic lesson starts.
- [ ] Run the tests against v2.1.0; retain actual failures.
- [ ] Implement v3.0.0: canonical index 0; broad index 1; mixed, odd-width, center-bearing indices 2 and 3; rich draws have at least 4 off-axis seeds and a repeated off-axis color. Use exact pixel observations and Racket-bound semantic witnesses.
- [ ] Run focused tests, then twelve-stage battery with required rotations and explicit portable task tests.

## Initial plan: Task 2 — evidence and handoff

**Files:** `workspace/probe_mirror_curriculum.py`, `counterexamples/`, current notes and permitted `WORK` reports/checks.

- [ ] Retain source-bound baseline first-color, isolated-only and first-row wrong-query lessons, labeled by public Racket apply.
- [ ] Run 100 production lessons per band with rotations and enumerate all four fixed-seed schedule starts.
- [ ] Complete the exposed visible-only solve and both randomly assigned findings-only audits.
- [ ] Have an independent reviewer inspect the whole repair; fix material issues with tests.
- [ ] Build the delta, replay it in a fresh extraction, run focused tests there, bind hashes, and return the builder-produced ZIP.

## Execution decisions

The archive contract supplies a fresh isolated checkout and restricts paths, so this plan stays in the task workspace instead of creating a separate Git worktree or repository-wide plan tree. The user authorized implementation; no additional approval pause is needed. Real source/evidence is retained in the return rather than deleted as generic temporary plan output.

## Current execution status

**Task 1:** implementation and independent review are complete. Actual red/green evidence: 41 baseline failures / 16 passes, 57 initial passes, 2 center-capacity failures, and 59 fixed-source and portable passes. The canonical rule is unchanged.

**Task 2:** source diagnostics, both audits, both solves and all requested censuses are complete. Final replay and package status are recorded in `WORK/RESULTS.json` and `WORK/REVIEW.md`; this source document does not declare those steps complete.

**Acceptance:** the aggregate remains blocked by generic mutation heuristics despite rule-bound lawful/invalid fixture evidence. No unsupported waiver, fake restriction, shared edit or training approval is introduced.
