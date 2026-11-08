# Working notes: af373b71d67d

## Review `review-45c7781a3c9cd255`

The selected 2.0.3 baseline described a narrower and partly incorrect family:
it fixed the frame color at 7, required motif sizes 3–5, stated that the frame
was preserved, narrowed advertised dimensions by difficulty, silently accepted
unknown overrides, and had no executable semantic contract. The canonical
authority instead accepts other frame colors and a two-cell motif, and its test
pair proves that stamping can overwrite the frame border.

Version 2.1.0 keeps the canonical Racket authority unchanged and pins
`RULE_HASH = "7364b3464a5f"`. It uses constructive placements, legal frame-color
coverage, exact dimension overrides, a validator aligned with the canonical
family, independent semantic rivals/witnesses, and a four-index teaching
schedule containing two `frame_overwrite` and two `roomy_anchor` examples in
every consecutive lesson-sized window.

A first implementation used a five-index schedule. The semantic gate reproduced
an ambiguity at sample index 22: three roomy demonstrations allowed the
`preserve_frame` rival while an overwrite query differed. The retained failing
log is `checks/focused-semantic_gate/..._semantic_gate.log`; the task-local red
regression is `checks/semantic-schedule-red.log`. The modulo-four schedule fixes
that root cause.

Independent reviewer tooling is in `workspace/reference_probe.py`. It provides
an oracle separate from production helpers, canonical loading through
`reviewer_support`, five declared rivals, witness counts, deterministic sampling
checks, and optional real-Racket parity. It is not label authority and never
silently substitutes Python for an unavailable Racket runtime.

The associated-notes file was empty, so no prior return or unintegrated patch
was used as a lead. Full rationale, commands, and limitations are recorded in
the packet-level `DECISIONS.md`, `REVIEW.md`, and `RESULTS.json`.
## Current reviewer considerations

Source SHA-256: `3742557cb43a7fda9e0eddc1dba87fbeaadc5be882ab537e2a8d9c7317ca7361`.

# Decisions for `af373b71d67d`

All final-source claims below refer to generator SHA-256
`3742557cb43a7fda9e0eddc1dba87fbeaadc5be882ab537e2a8d9c7317ca7361`.
The selected Racket authority was not changed.

## D1 — Treat the selected canonical program as authoritative

**Choice.** Preserve the Racket rule and pin `RULE_HASH = "7364b3464a5f"`.
Align Python validation, summary text, tests, and sampling with that authority.
The actual rule accepts non-7 frame colors and lets stamp cells overwrite a
frame edge.

**Why.** Rule smoke was green before repair, and the canonical test explicitly
overwrites the bottom frame border. The defect was in generator ownership and
documentation, not label authority.

**Rejected alternatives.** I rejected changing the Racket program to preserve
the border, fixing the frame color at 7, or excluding the canonical two-cell
motif. Each would alter or narrow selected authority to fit the broken sampler.

**Probe/failure mode.** All canonical pairs must pass `self_check` and the
independent Python oracle must match every output. A summary that says “frame
preserved” is falsified by the canonical test. Tests and evidence are in
`tests/test_generator.py` and `checks/independent-audit.json`.

**Limit.** Archival authority remains divergent, as reported by authority sync;
selected canonical execution parity is green.

## D2 — Use a small explicit motif library with full quarter-turn orbits

**Choice.** Sample eight connected 3–5-cell motifs whose four normalized
quarter-turn orientations are distinct. Keep validator support for canonical
2–5-cell motifs.

**Why.** Every generated board should distinguish clockwise rotation from both
unrotated and counterclockwise rivals. An explicit library is easy to review and
avoids rejection loops.

**Rejected alternatives.** Random polyomino growth was rejected because it can
produce symmetric shapes and require capped retries. Sampling a two-cell domino
was rejected for production because clockwise and counterclockwise normalized
outputs coincide, hiding direction on that board.

**Probe/failure mode.** `clockwise_direction` fired 750/750 times in the
independent 250-per-band probe. The remaining limitation is that production does
not teach two-cell motifs directly; canonical ownership and Racket parity cover
the known two-cell case but do not prove all unseen shapes.

## D3 — Generalize the frame palette without adding semantic noise

**Choice.** Cycle frame colors `(1, 2, 4, 5, 6, 7, 8, 9)` by sample index;
reserve 3 for the motif and 0 for background.

**Why.** Canonical examples use several frame colors, while the baseline used
only 7. A deterministic cycle guarantees coverage even in short runs and makes
palette independent of the transformation.

**Rejected alternatives.** A single color was too narrow. Fully random color
choice could miss rare colors in small gate samples. Allowing frame color 3
would merge frame and motif components and destroy task parsing.

**Probe/failure mode.** Every band used all eight colors in 250 draws. Validator
mutations reject an added third foreground color.

## D4 — Honor the complete declared dimension domain in every band

**Choice.** Advertise and construct grids of 8–16 rows and 10–18 columns in all
bands. Difficulty changes default weighting, not the validity of explicit
controls. Unknown keys and non-exact integer types are errors.

**Why.** The baseline advertised a common domain but passed overrides through
band-specific `draw_int` ranges, causing 840 generation errors and 5,460
undeclared multi-axis rejections. Exact controls must mean the same thing in
every band.

**Rejected alternatives.** Narrowing `AXES` by band would make portable callers
and the common contract harder to reason about. Declaring most combinations
incompatible was unnecessary because constructive placements exist for all of
them.

**Probe/failure mode.** Task tests cover boundary and canonical dimensions in
all bands. The final override gate accepted the complete matrix, rejected the
unknown-key probe, and reported no finding category.

## D5 — Construct layouts rather than retrying random scenes

**Choice.** Cache all source/frame placements that fit the requested grid and
leave at least one blank row or column between bounding boxes, then draw from
that finite set.

**Why.** This guarantees termination and exact overrides, including the smallest
8×10 boundary. It also makes failures explicit if future geometry changes make
a combination impossible.

**Rejected alternatives.** The baseline-style random draw plus capped retry can
bias distributions, hide unsupported axes, and fail nondeterministically near
boundaries. Hand-coded one-layout templates would reduce positional diversity.

**Probe/failure mode.** 750/750 independent samples were lawful and deterministic;
all were unique within band. A future impossible combination raises a precise
`no constructive layout` error instead of silently clipping or retrying forever.

## D6 — Separate two teaching profiles and schedule them two-by-two

**Choice.** `frame_overwrite` examples make the clockwise stamp touch exactly
one frame edge. `roomy_anchor` examples leave enough slack for centered and
true top-left placements to differ. The schedule is periodic with profiles
`overwrite, overwrite, roomy, roomy`.

**Why.** Canonical pairs leave the centered-placement shortcut unfalsified, and
some examples are needed to show that stamping wins over the frame. A four-pair
lesson has three demonstrations plus one query; every cyclic start must teach
both branches before any query rotation.

**Rejected alternatives.** Pure random profile selection could produce all-roomy
or all-overwrite lessons. The first deterministic period-five schedule was also
rejected: at sample index 22 it produced three roomy demonstrations and an
overwrite query, allowing `preserve_frame` to survive.

**Probe/failure mode.** The retained semantic failure is
`checks/focused-semantic_gate/checks/af373b71d67d_after_semantic_gate.log`; the
red cyclic-start regression is `checks/semantic-schedule-red.log`. Final tests
enumerate starts 0–24, and the 300-lesson rotated census found no declared-rival
ambiguity.

## D7 — Make plausible rivals executable and independently checked

**Choice.** Declare five pure rivals: unrotated, counterclockwise, keep-source,
centered-when-fits, and preserve-frame. Pair them with four witnesses and retain
`centered_when_fits` as a canonical shortcut.

**Why.** Correct labels are insufficient if demonstrations permit a simpler rule
that predicts a different query. Executable rivals make teaching claims
falsifiable and let the shared semantic gate and census identify an exact lesson.

**Rejected alternatives.** Prose-only comments were not machine-checkable. A
single “wrong rotation” rival would miss erasure, anchor, and overwrite defects.
Claiming universal identifiability was rejected because the rival set is finite.

**Probe/failure mode.** Production and all 1,200 query rotations refuted every
declared rival in the 300-lesson census. Undeclared rivals and semantically
equivalent formulations remain outside that guarantee.

## D8 — Keep the Python oracle independent from production helpers

**Choice.** Put scene parsing, geometry, rivals, canonical loading, and optional
Racket execution in `workspace/reference_probe.py`, loaded separately by tests.

**Why.** Tests that reuse production rotation or stamping helpers can agree on
the same bug. The probe also gives future agents a reproducible command and
never silently substitutes Python when Racket is unavailable.

**Rejected alternatives.** Importing private runner functions into tests was
avoided. Duplicating canonical paths with fixed `parents[...]` guesses was
avoided in favor of `reviewer_support.find_root` and `canonical_pairs`.

**Probe/failure mode.** Independent Python outputs match all three canonical
pairs; real Racket parity matched 39/39 inputs. The probe is reviewer tooling,
not a second authority.

## D9 — Preserve genuine failures and resume only hash-matched stages

**Choice.** Retain baseline, red-test, and intermediate semantic failures. When
outer command calls ended after completed stages, use the battery's source-bound
`--resume` receipts; finish with a clean resume invocation and aggregate exit 0.

**Why.** An interrupted wrapper is not a pass, and rerunning from scratch would
lose evidence about the actual iteration. Hash verification prevents stale
stage results from being applied to changed source.

**Rejected alternatives.** I did not edit or delete failures to make the return
look clean, and I did not count an incomplete aggregate as green.

**Probe/failure mode.** The final battery summary reports 12 green and zero
interrupted/pending stages on the final hash. Earlier command logs remain under
`checks/`.

## D10 — Prior evidence and audit boundaries

The selected task's associated-notes file was empty; no prior return was used.
The two random audit targets were read and probed only after the selected repair
was complete. Their findings are in `AUDIT.md`; neither target was modified.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-acb2d1b5083b152a:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `3742557cb43a7fda9e0eddc1dba87fbeaadc5be882ab537e2a8d9c7317ca7361`. At disposition, audited bytes match the current source.

### Current decision

Audited source is repo/generators/af373b71d67d/generator.py,unchanged SHA256 3742557cb43a7fda9e0eddc1dba87fbeaadc5be882ab537e2a8d9c7317ca7361. No issue found in bounded checked scope:97reported tests andstrict semantic gate passed. Independent300draw probe has100distinct inputs/band,all8framecolors,no validator orreplay findings;39actualRacketlabels match independent oracle. Direction/source-erasure witnesses100/100perband,frame-overwrite/top-left-anchor50/100. Canonical-fitting centered rival is refuted by generated noncentered cases. Not allseeds orundeclared hypotheses. No owner audit execution,target source change ornew approval. Exact target-local citations: `checks/audit/af373b71d67d-combined/RUNTIME_MANIFEST.json` `checks/audit/af373b71d67d-combined/checks/af373b71d67d_audit_battery_summary.json` `checks/audit/af373b71d67d-combined/checks/af373b71d67d_audit_commands.jsonl` `checks/audit/af373b71d67d-combined/checks/af373b71d67d_audit_semantic_gate.json` `checks/audit/af373b71d67d-combined/checks/af373b71d67d_audit_semantic_gate.log` `checks/audit/af373b71d67d-combined/checks/af373b71d67d_audit_semantic_gate.ok` `checks/audit/af373b71d67d-combined/checks/af373b71d67d_audit_semantic_gate.receipt` `checks/audit/af373b71d67d-combined/checks/af373b71d67d_audit_summary.json` `checks/audit/af373b71d67d-combined/checks/task_tests.xml` `checks/audit/af373b71d67d-combined/progress.log` `checks/audit/af373b71d67d-combined/result.json` `checks/audit/af373b71d67d/reference-probe.json`

### Assessment or prior finding

## af373b71d67d

**No issue found in the checked finite scope.** The audited source SHA-256 was
`3742557cb43a7fda9e0eddc1dba87fbeaadc5be882ab537e2a8d9c7317ca7361`.
The isolated audit preset executed 97 task-local tests and the strict semantic
gate; both passed (`checks/audit/af373b71d67d-combined/checks/af373b71d67d_audit_summary.json`).

I also ran the task-local independent reference probe on 100 default samples per
band (300 total). Each band produced 100 distinct inputs, all eight legal frame
colors, zero `self_check` findings, and zero nondeterministic replays. The probe
found clockwise-direction and source-erasure witnesses in 100/100 samples per
band, and frame-overwrite and top-left-anchor witnesses in 50/100 per band. It
checked 39 protected-Racket labels with zero Python-oracle mismatches. The
centered shortcut does fit all three canonical pairs, but the generator's
noncentered/frame-overwrite cases distinguish it, so this was not an actionable
shortcut in the sampled domain. Full finite evidence and limits are in
`checks/audit/af373b71d67d/reference-probe.json`.

This is not a proof against every possible rival or every seed. I did not modify
the audit target.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

## Reviewer return `review-d0dbf7ec1e680035` — native turn-direction family (2026-10-25)

Built `workspace/parametric/` around one episode-fixed parameter: `turn_direction=clockwise|counterclockwise`. The clockwise program is the exact selected canonical source (`7364b3464a5f…`); the alternative keeps the same extracted motif, frame and anchor but applies the opposite quarter-turn. Inputs are matched across settings, demonstration/query counts are independent within 2–6 and 1–4, and the four-query bank contains a substantive 30×30 boundary case.

The retained A→intermediate→B dependency is motif/frame extraction → direction-specific oriented offsets plus frame anchor → erase-and-stamp. On the qualified counterclockwise witness, replacing `[[0,0],[1,0],[2,0],[2,1]]` with the clockwise offsets changes four protected-Racket output cells.

Final evidence: 159 target tests passed; the 128-seed finite audit covered 768 episodes / 5,888 pairs with no declared query-changing survivor; minimum and maximum native qualification contributed 96 protected-Racket evaluations; 16 one-query public views and first-turn hidden-field mutations passed. Production generator and canonical authority were unchanged. Owner integration, fresh acceptance replay and training admission remain separate.

Next useful action: integrate these exact task-local bytes, rerun native qualification and witness replay, then accept only if the resulting live source binding matches the returned receipt.
