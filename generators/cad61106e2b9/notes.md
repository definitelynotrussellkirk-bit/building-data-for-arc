# Working notes: cad61106e2b9

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `21ab0a96d74b9b687bd37dd286a336ef7a6064b4310041fca095f9d7c6fc84d1`.

# Decisions for `cad61106e2b9`

Final generator version: `3.0.0`
Final SHA-256: `21ab0a96d74b9b687bd37dd286a336ef7a6064b4310041fca095f9d7c6fc84d1`

No prior return was used as a lead. “Original rationale” below refers to what could be recovered from the pinned baseline source and comments; where intent was not documented, it is marked unknown rather than reconstructed.

## D1 / R1 — keep the canonical Racket authority unchanged

**Original rationale:** the baseline was already linked to canonical rule hash `a3ad6fb565b1`, but did not pin it in the generator.
**Choice:** add `RULE_HASH = "a3ad6fb565b1"`; do not edit canonical data.
**Alternatives considered:** modify the rule to match the broader 2–5-frame generator; or create a new task family. Both were rejected because all five canonical pairs and the written rule agree, while the drift was generator-side.
**Probe:** canonical authority sync, Racket execution parity, five-pair independent oracle (`checks/after_final/...authority_sync.json`, `checks/cad61106e2b9_review_probe_final.json`).
**Failure mode / limitation:** the Python mirror could still share a conceptual mistake, so the retained probe independently reconstructs components and is checked against all canonical pairs.

## D2 / R1 — exactly three frames

**Original rationale:** baseline comments claimed frame count was a free combinatorial axis (`2..5`), but no reason tied that variation to the canonical task.
**Choice:** generate exactly three frames, matching every canonical pair and the control values 1–3.
**Alternatives considered:** keep 2–5 and clamp controls; permit more frames but select only the first three; or make frame count an exact axis. These teach frame-count/clamping artifacts and produce boards outside the demonstrated grammar.
**Probe:** structural tests, strict profile gate, 40-rule smoke, and production census.
**Failure mode / limitation:** the resulting generator does not teach a generalized “arbitrary number of nested frames” task. That restriction is intentional and documented.

## D3 / R1 — restore the irrelevant singleton distractor

**Original rationale:** unknown; the baseline omitted it even though each canonical input has one.
**Choice:** add exactly one singleton in canonical colors `{5,6,7,9}`, outside the outer frame.
**Alternatives considered:** arbitrary distractor colors, multiple distractors, or no distractor. Arbitrary/multiple distractors expand the latent rule without evidence; omission creates a palette/role mismatch and location shortcut.
**Probe:** `self_check`, override observation, canonical-profile floor, and tests that remove/duplicate singletons.
**Failure mode / limitation:** only the four canonical distractor colors are represented.

## D4 / R1 — expose only exact, observable axes

**Original rationale:** baseline advertised dimensions, frame count, gap, fixed palette size, position bias, and texture aliases, although most bypassed `GenCtx` or were inert.
**Choice:** retain only `grid_h`, `grid_w`, `ctrl_value`, and `distractor_color`; validate unknown keys and types before generation.
**Alternatives considered:** implement every old axis, or keep metadata for compatibility. Both would preserve a misleading API and force unsupported task variants.
**Probe:** the shared 30-seed strict override matrix and task tests for every boundary/value.
**Failure mode / limitation:** callers relying on undocumented acceptance of unknown keys now receive a deliberate error.

## D5 / R1 — canonical anchors plus live difficulty bands

**Original rationale:** baseline accepted `difficulty` but used it mainly to alter frame count/gap; dimensions were emergent and advertised overrides were ignored.
**Choice:** every fourth sample uses one of five canonical dimension profiles; other samples use observable easy/medium/hard size envelopes. Exact overrides always retain the full declared ranges.
**Alternatives considered:** all-canonical sizes (too little diversity); disjoint bands without anchors (fails canonical support in some bands); or keep difficulty behaviorally dead.
**Probe:** the red difficulty test, defect lint, canonical-profile floor, and exact override stage.
**Failure mode / limitation:** difficulty measures visual/layout scale, not deeper reasoning complexity.

## D6 / R2 — deterministic 1/2/3 coverage in each three-example lesson

**Original rationale:** baseline drew the control randomly, so a lesson could omit one or two control meanings.
**Choice:** schedule `ctrl_value = sample_index % 3 + 1`, making every consecutive three-example window cover all three profiles. Exact overrides still take precedence.
**Alternatives considered:** random resampling until coverage, lesson-aware external assembly, or four demonstrations. Deterministic local coverage is cheap, reproducible, and works with the existing three-demo sampler.
**Probe:** exhaustive starts `0..5`, five seeds, and all four difficulty settings in task tests; 300 production lessons plus rotations in the census.
**Failure mode / limitation:** sample order itself may leak the control phase if a downstream system exposes global indices. Randomizing the phase per lesson would be a future improvement if the sampler gains lesson context.

## D7 / R2 — alternate singleton order and move the control

**Original rationale:** all canonical examples permit two accidental rules: top-left is control, and first row-major singleton is control.
**Choice:** on even indices place the distractor at `(0,0)` and the control elsewhere; on odd indices put the control before the distractor.
**Alternatives considered:** random placement only, or keep canonical top-row placement. Random placement gives no per-lesson guarantee; canonical placement never refutes the shortcuts.
**Probe:** both shortcuts are first verified to fit all five canonical pairs, then required to fail generated witnesses and every assembled lesson.
**Failure mode / limitation:** `(0,0)` is intentionally overrepresented for the distractor on half the schedule. It is a teaching witness, not a claim that canonical distractors are usually at that cell.

## D8 / R2 — executable competitors and lesson rejection

**Original rationale:** baseline had no semantic contract.
**Choice:** declare eight pure competitors, canonical-fitting shortcuts, witnesses, and `lesson_identifiable`.
**Alternatives considered:** prose-only documentation or a model-based quality check. Pure deterministic rivals are replayable, inexpensive, and identify exact teaching failures.
**Probe:** strict semantic gate, 75-lesson independent probe, and 300-lesson rotated production census.
**Failure mode / limitation:** passing a finite list cannot prove unique induction. New plausible shortcuts should be added when discovered.

## D9 / R3 — strong fail-closed validation

**Original rationale:** baseline validated one marker and nested-looking color-4 components but did not enforce the canonical distractor, exact frame count, moat separation, public palette, or axis observations.
**Choice:** validate the complete grammar and expose `strict_canonical_like`/`observe_overrides`.
**Alternatives considered:** repair malformed draws after generation or rely only on the Racket output. Repairing can hide generator defects; Racket legality does not establish intended training distribution.
**Probe:** nearest-impostor mutations in task tests and shared mutation-sensitive self-check stage.
**Failure mode / limitation:** validation is intentionally strict and rejects lawful hypothetical extensions outside this generator's declared domain.

## D10 / R3 — retain independent tools for future agents

**Original rationale:** none existed in the task workspace.
**Choice:** add `tests/test_review_contract.py` and `workspace/review_probe.py`. The probe loads the final source by path, independently extracts rectangular components, verifies all canonical pairs, and audits assembled lessons against the generator's actual competitor declarations.
**Alternatives considered:** ad-hoc shell snippets only, or tests that call only `rule_mirror`. Those are harder to replay and more vulnerable to shared implementation errors.
**Probe:** red-first logs, portable task-test result, and final-source probe report.
**Failure mode / limitation:** the independent oracle shares the high-level written interpretation; Racket execution remains the authority.

## Audit-only decisions

Targets `c8132e595372` and `0b8631a5fc70` were inspected and evidenced but not modified, as required. Their findings are isolated in `AUDIT.md` and `checks/audit/`; no audit source appears in the returned patch.
