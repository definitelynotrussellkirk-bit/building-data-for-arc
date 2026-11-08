# Working notes: 3f26d45b9f51

## Intended rule and authority

The input is a square lattice of `K × K` uniform 2×2 coarse cells, separated by one-pixel divider lines. The divider is identified by its modal nonzero lattice role; canonical divider colors include 1, 8, and 4. For each non-divider marker color, fill every inclusive coarse-cell interval from the minimum to maximum same-color marker coordinate in each shared coarse row and each shared coarse column. Apply colors independently. A marker with no same-color peer in its row or column is preserved. The selected canonical Racket rule was not changed; `RULE_HASH = 54129d31ff5b`.

## Retained earlier decisions

The prior v3 design correctly made divider color role-based, required horizontal and vertical evidence, included a dual-axis color and an unconnected marker, excluded cross-color span overlap, and retained three demonstrations per lesson. Those decisions remain. Associated notes `GNOTE-004117` through `GNOTE-004121` document their original rationale.

## v4 defect and repair

The strongest remaining canonical-compatible rival was **nearest-pair-only**: for each occupied row or column of a marker color, connect only the closest adjacent pair. It fits all four canonical pairs. Before v4 it also matched all 1,200 generated probes because production never placed three same-color markers on one line.

Version 4 makes the first secondary active color a three-collinear-marker pattern on every ordinary generated scene. Its outer endpoints are at least three coarse cells apart, so the nearest-pair rival leaves part of the authoritative min-to-max interval blank. The exact lawful counterexample is retained in `counterexamples/nearest_pair_only.json`; canonical Racket application differs from the rival at eight pixels. The task-local reusable probe is `workspace/semantic_probe.py`.

The exact integer axes `K` and `n_colors` now use strict integer draws. Strings, floats, and booleans are rejected rather than truncated or coerced. The deterministic divider/color-count branch schedule has period 12 (`lcm(4,3)`); `LESSON_SCHEDULE_PERIOD` and `SCHEDULE_PROFILES` now state it explicitly.

## Distribution and controls

- `K`: exact integer 7..9.
- `n_colors`: exact integer 2..4.
- Divider colors cycle `(1, 8, 4, 5)` by sample index.
- Unoverridden marker-color counts cycle 2..4 with a difficulty offset.
- Every ordinary scene has an L-shaped primary color, a three-collinear secondary color, and an unconnected marker. Four-color scenes add a second two-endpoint line.
- Connection spans of different colors remain disjoint so color application is order-independent.

## Known limits

The validator intentionally excludes cross-color span overlap because canonical evidence does not define overwrite precedence. Marker colors occupy one to four coarse cells; arbitrary larger marker sets are outside the generated grammar even though the Racket rule may process them. The finite rival set checks six named alternatives and is not a proof of unique induction against every imaginable rule. Schedule enumeration at seed 0 covers declared start residues, not every seed or all random layouts.

## Current evidence

The checks below are retained reviewer-produced evidence, not maintainer reruns. Paths are relative to this generator's home:

- Before-repair rival probe: `counterexamples/current-shortcut/checks/repair-probe-before/result.json`.
- Exact-axis and schedule-residue stress: `counterexamples/current-shortcut/checks/axis-stress/result.json`.
- Canonical Racket counterexample replay: `counterexamples/current-shortcut/checks/counterexample-racket/`.
- Production and query-rotation census: `counterexamples/current-shortcut/checks/lesson-census-summary.json` and the compressed full report `lesson-census.json.gz` in the same directory. `compressed-evidence-manifest.json` binds compressed and restored hashes; `restore_compressed_evidence.py` restores the retained report.
- Current implementation and reusable checks: `generator.py`, `tests/test_generator_3f26d45b9f51.py`, and `workspace/semantic_probe.py`.

The reviewer also reported 16 task tests, all 12 battery stages, and 36 schedule windows / 144 rotations passing. Their full repository run reported 615 tests plus 48 subtests passing and four failures outside this repair: archival identity drift for `defba1ab4f90`, missing archival self-check rejection for `d982cffd80f8`, a Racket setup-error regex mismatch, and a resource-guard pipe timeout (-9 versus expected 0). These broader results have not been independently rerun; the current review packet excludes the resource guard.

The `checks/...` references in the decision text below name the reviewer's original transport paths. Only the evidence listed above was retained during compaction; the separate schedule census, TDD logs and full battery logs were not retained here.
## Current reviewer considerations

Source SHA-256: `1bd4448f9ff51545858cb402a42521bd7238925667727911e797a8259ee06f5a`.

# Decisions for 3f26d45b9f51 v4.0.0

## D1 — Preserve the canonical Racket rule

**Choice.** Keep rule hash `54129d31ff5b` unchanged.

**Reason.** All four canonical pairs are accepted, the Python mirror agrees with them, and the defect was in what generated lessons taught—not in the authoritative transformation. The exact counterexample also receives the expected min-to-max output from the public canonical Racket runner (`checks/counterexample-racket/`).

**Rejected alternative.** Changing the rule to nearest-pair behavior would contradict the existing authority and would solve a curriculum defect by changing the task.

## D2 — Add a three-collinear witness to every ordinary scene

**Choice.** The first secondary active color now has three collinear markers with outer endpoints at least three coarse cells apart. Its full span is reserved against other colors.

**Reason.** Nearest-pair-only fit 4/4 canonical pairs and 1,200/1,200 pre-repair generated scenes. A three-marker line is the smallest direct observation distinguishing adjacent-pair filling from outermost min-to-max filling. It is present in all 972 exact-axis/schedule stress cases after repair.

**Rejected alternatives.** Merely declaring the rival without changing production would leave the teaching defect. Making the witness rare would allow complete lessons without it. Raising `EXAMPLES_NEEDED` would waste examples without fixing a support gap shared by every old scene. Four or more collinear markers were unnecessary.

## D3 — Retain the existing L, unconnected-marker, and disjoint-span grammar

**Choice.** Keep an L-shaped primary color, preserve an unconnected marker, and reject cross-color span overlap.

**Reason.** These features independently refute one-axis, bounding-box, drop-distractor, and overwrite-order shortcuts. They remain compatible with the new collinear witness. Cross-color overlap would introduce precedence behavior not established by canonical evidence.

## D4 — Make integer axes exact in type as well as value

**Choice.** Use `draw_int_strict` for `K` and overridden `n_colors`.

**Reason.** The v3 source silently accepted `K="7"` and truncated `n_colors=2.9`. An exact public axis should not map invalid caller values to a different lawful request. Six focused red cases failed before the change and passed after it (`checks/tdd-red-strict/`, `checks/tdd-green-strict/`).

## D5 — Declare the actual deterministic schedule period

**Choice.** Set `LESSON_SCHEDULE_PERIOD = 12`, profiles `0..11`, and `schedule_profile = sample_index % 12`.

**Reason.** Divider choice has period 4 and unoverridden marker-color count has period 3; secondary direction's period 2 divides 4. Twelve is therefore the complete period of deterministic slot branches. The focused schedule test first failed without the declaration and then passed.

## D6 — Keep three demonstrations and require query-rotation evidence

**Choice.** Retain `EXAMPLES_NEEDED = 3`, test production lessons as three demonstrations plus one query, and require every materialized pair to work as the held-out query in the census.

**Reason.** Three examples already carry all named cues once each individual scene contains the new witness. Production and rotation results are reported separately; finite named-rival success does not establish universal identifiability.

## D7 — Retain a source-bound reusable probe

**Choice.** Add `workspace/semantic_probe.py` and the exact JSON counterexample.

**Reason.** Future agents can rerun canonical-rival fit, Racket-independent axis stress, strict-type probes, and the exact disagreement without reconstructing the case from prose. The tool records the generator SHA-256 in its report. A fresh-packet replay exposed that the first draft depended on wrapper-provided `PYTHONPATH`; a red subprocess test reproduced the missing `reviewer_support` import, and the final probe now bootstraps that helper in both source and portable-runtime layouts.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/3f26d45b9f51/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Proposed parametric extension: `connection_axes` (unapproved)

**Current decision.** Keep production v4.0.0 and canonical rule hash `54129d31ff5b` unchanged. The isolated prototype adds one episode-fixed hidden parameter, `connection_axes`, with values `both`, `horizontal`, and `vertical`. `both` is the default and returns the canonical Racket source byte-for-byte; the alternatives preserve the same lattice, marker grouping, color roles, and min-to-max filling rule while enabling only one connection direction.

**Episode contract.** Each retained episode fixes one setting, uses three labelled demonstrations and four distinct unlabelled queries, and is generated from the existing lawful scene grammar. Setting cycles every seed while difficulty advances only after a complete three-setting block; the evidence builder aligns to that block so its three comparison episodes share one difficulty. In the retained evidence, demonstrations leave exactly the chosen setting alive and every query answer differs from both rival settings. Public challenge files contain demonstration inputs/outputs and query inputs only. Their filenames are SHA-256 hashes of the exact visible bytes; settings, seeds, Racket programs, executors, and query outputs remain private.

**Implementation and evidence.** The prototype is in `workspace/parametric/prototype.py`; the protected-Racket evidence builder is `workspace/parametric/verify.py`; focused regressions are in `tests/test_parametric_connection_axes.py`; and usage is in `workspace/parametric/README.md`. Retained evidence is under `checks/parametric/connection-axes-v1/`, with independent parity/privacy attacks in `checks/parametric/adversarial/audit-report.json`. Source identities at review time were:

- production generator: `1bd4448f9ff51545858cb402a42521bd7238925667727911e797a8259ee06f5a` (unchanged),
- prototype: `af56f194b9b6c11e17cd4f7c2f9fd923fd42c9dd5ec5b77ad5648017804c09e8`,
- verifier: `b8292140848b99f8a47eae896588feb02decccc39f5e4cf8c9707a9044f79e5c`,
- focused test: `20ffe2e018aa64bdd408e51b7ddfb6178b924edc68dfef70bdd9c9f695457aa8`.

**Limits and next action.** This is bounded prototype evidence, not production approval, catalog approval, or training admission. The two alternate programs are deliberately derived from exact canonical edit points and fail closed when those points drift; a future canonical rewrite would require a reviewed structured variant mechanism rather than silently reusing these edits. Coverage is three retained episodes plus a 24-grid unseen-seed parity sweep, not an exhaustive grammar census. The next useful action is maintainer review of the parameter semantics and public/private contract; only after explicit approval should the setting enter a production generator or catalog.

## Current prototype public export follow-up

Public filenames match visible bytes, but verify.py still writes during private setting/seed enumeration before sorting report rows. Keep exact accepted code and Racket-backed evidence; precompute/validate the complete batch, then emit in public-ID order with one focused regression. No variant/training approval. Source-bound static receipt: `generators/3f26d45b9f51/evidence/parametric-public-export-inspection-1fad91fbb005e239/manifest.json`.

## Current proposed extensions — review-b2a31c0567f62dd1

The v4.0.0 generator and canonical rule `54129d31ff5b` remain byte-for-byte
unchanged. The missing parametric extension is now an opt-in prototype in
`workspace/parametric/lattice_axes.py`: one fixed `both|rows|columns` setting,
executed matching Racket, independent demonstration/query counts, exact public
IDs and replay. At least two demonstrations are required to cover opposite
triple-collinear axes and reject the nearest-pair shortcut; four distinct queries
are the default. Certificates cover only the explicitly declared finite rivals.

The public-evaluation focus `a6f40cea` supplies a separate exterior-context
occlusion/crop mechanism in `occluded_rectangles.py`, with `outline|filled`
painting and standalone Racket. It is not lineage or canonical equivalence.
One rear solid rectangle is supported; alternating-color turn/phase behavior
remains unresolved and multiple rear objects are outside this grammar.

Adversarial checks drove repairs for boolean query labels/counts, duplicate
visible payloads with different metadata, false status/origin claims and typed
certificate substitutions. The public/private boundary is checked before export
and replay. `workspace/packet_preflight.py` is a local proposal for future packet
consumers after an inode shortage blocked ordinary extraction.

Run commands and support limits: `workspace/parametric/README.md`. Next useful
action is maintainer replay of the final source-bound exports and assessment of
the separate proposed families. No production default, audit status or training
admission changes follow from these checks.


Owner disposition: exact additional lattice/occlusion code and tests selected via owner docs merge; the prior connection_axes prototype and its public write-order follow-up remain unchanged and unresolved. Only lattice is related to this assigned canonical rule; occlusion is a separate proposed inspired family with no lineage/approval/training claim. Capacity preflight is not required or shared setup; retain the helper only as an optional passive integrity proposal. Receipt: `generators/3f26d45b9f51/evidence/owner-docs-merge-b2a31c0567f62dd1/manifest.json`.
