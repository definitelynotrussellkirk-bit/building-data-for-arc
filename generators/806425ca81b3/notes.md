# Working notes: 806425ca81b3

The selected rule fills zero cells between the first and last anchors of each
nonzero color independently in each row. The canonical Racket rule is unchanged.

The public schedule now names the accepted `scene_profile` values directly.
Concrete integer controls require literal Python integers; `None` retains the
existing no-override meaning, negative integer seeds remain legal, and sample
indices must be nonnegative. The validator rejects booleans and malformed color
values before hashing or sorting them. VERSION stays at 2.0.0 to preserve keyed
random draws; the return's source hashes identify this repair.

The curriculum requires four consecutive demonstrations before the query.
Do not treat the ordered lesson guarantee as permission to choose any query
position. The retained final census found no ambiguity in 300 ordered lessons
against the declared rivals, but 450 of 1,500 query rotations were ambiguous.
The existing four-phase schedule remains; no optional period declaration is
added. The review records why a proposed declaration was withdrawn.

Ordinary generation retains its documented 8..14 by 9..14 size support and
disjoint repeated-color spans. Validator acceptance up to 30x30 is a broader
domain statement, not a promise that ordinary sampling emits those sizes.

`workspace/probe_contracts.py` is a portable finite API/validator/parity probe.
`workspace/parametric/` contains a separate, unapproved prototype with row/column
orientation and a minimum of two/three anchors, real Racket verification, large
queries, and public challenge exports. It does not change production selection
or training admission. See its README for its bounded evidence and commands.

Full decisions, source-bound counts, failures, audit findings and solve exposure
records belong to the review return rather than this current-state note.

## Current owner source and evidence limits

Accepted version2.0.0 schedule labels matching the public scene_profile axis, exact integer controls and malformed palette-cell rejection. None sentinels and signed integer seeds retain their behavior. Canonical Racket and random sampling are unchanged;192 legal draws are reported byte-identical. The reviewer reports12 green stages and73 staged tests repeated in a fresh354-file dependency closure, with no skips. Profile support15/60;strict support143/600. Ordered four-demo lessons are clean across300 lessons/1500 unique inputs, while450/1500 diagnostic query rotations are ambiguous; arbitrary holdouts remain unsupported. An intermediate period declaration was withdrawn after the strict receipt loader rejected diagnostic rotation evidence; failed iterations remain retained. The row/column and minimum-two/three-anchor prototype has4 complete episodes,76 Racket calls,72 mirror comparisons and12 alternative-setting refutations. Default row/two is exact canonical source. Public challenge order is shuffled with its mapping retained privately. Its30x30 queries use24 active lines and change587 or305 cells, rather than padding a small operation. Finite seeds/rivals only. Owner checked source hashes and public/private projection statically; reviewer tests and labels were not rerun. No production parameter API, variant approval or training admission.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-bd22d04aaf51157f:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `d3a7a33a9d137607cc970a7eaa6c04f553f88557f267e82f93f12800f3dccb56`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly classify the prior report as no_issue within its bounded old-source ordered-policy scope:14 tests,3072 rolling windows and64 Racket comparisons reported clean. It never qualified arbitrary holdouts;current450/1500 rotation failures stay explicit. No new owner execution or new-source certification follows.

### Assessment or prior finding

## 806425ca81b3

**No issue found.** I left this target unchanged.

The audited generator SHA-256 is `d3a7a33a9d137607cc970a7eaa6c04f553f88557f267e82f93f12800f3dccb56`; its declared/executed rule hash is `c27cec63afa0`. I checked:

- all four canonical pairs for validator acceptance and exact Python-mirror output;
- every corner combination of `grid_h` (8/14), `grid_w` (9/14), `active_rows` (1/5), four scene profiles, and three bands: 96 exact override cases;
- 3,072 rolling four-demonstration lesson windows over seeds `0..127`, starts `0..7`, and all three bands, covering 3,838 unique generated inputs;
- every named canonical shortcut, semantic witness/rival, and malformed mutation fixture;
- 64 generated inputs through the supported Racket `apply` path, all valid and all byte-equal to the Python mirror;
- the target's portable task suite: 14/14 tests passed.

Evidence: `checks/audit/806425ca81b3/probe.json`, `checks/audit/806425ca81b3/parity-summary.json`, `checks/audit/806425ca81b3/racket.json`, and `checks/audit/806425ca81b3/task-tests/result.json`.

This is a bounded clean audit, not a proof against every possible rival. The reviewed schedule does explicitly cover its four documented shortcut families in every rolling four-example window.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-bd22d04aaf51157f-v0001/audit_assets.json), manifest SHA-256 `7ad3cfd1630dd8a811da1a54ef899325eee8d54b978ceb3030114889601a3295`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `15ddb9a1f91a75f47cced693400aae0f952ff10032d7880e2ac36996ad981c66`.

# Decisions for review-3fce6bff913adf98

## Scope and authority

The immutable draw selected 806425ca81b3, original ARC task 22168020. The separate
blind solve was completed before inspecting repair or audit source. The assigned
audits were drawn once, both completed, and left findings-only. The canonical
Racket authority remains unchanged: declared rule hash `c27cec63afa0`, raw rule
text SHA-256 `273f6af5073985a3d3dec10d8ba8e42702a9d3848277bd79db64799eb76a7d77`,
executed callable SHA-256 `3d48949a1de9b13498198861e53713de9c9b98d0e80aa472b4af41d9922471ee`.
Those hash representations are distinct and must not be compared for equality.

Parameterization was developed in parallel with canonical review, before making
the canonical repair. It remained a task-local prototype rather than a new
production authority. No audit target, shared harness, catalog, approval index,
assignment or frozen root test was edited.

## Canonical repair choices

1. Use `SCENE_PROFILES` as the public schedule labels. `canonical_anchor` was
   advertised but rejected by the exact `scene_profile` axis, which accepts
   `canonical_rows`. This repairs replay metadata without changing the sampler.
2. Require `type(value) is int` for seed, nonnegative sample index and concrete
   integer axes. Python booleans are integers by inheritance but are not integer
   controls in this API. Fractional values and numeric strings must not be
   silently coerced. Preserve `None` as the documented no-override sentinel and
   preserve negative integer seeds. The 224-case preservation check covers
   explicit `None` controls. Negative integer seeds remain permitted by the
   unchanged integer-seed path; no retained negative-seed acceptance test is claimed.
3. Reject malformed colors before hashing or sorting. Lists and dictionaries
   formerly raised incidental type errors; booleans could act as ARC colors.
   An early palette error makes the validator deterministic and safe for those
   inputs. Other row/color semantics remain unchanged.
4. Keep VERSION 2.0.0. The keyed random generator uses the version, so a version
   bump would unnecessarily change valid draws. Full source hashes identify the
   repair. The 192 retained ordinary draws are identical before and after.

The baseline probe found 98 contract failures across schedule, scalar and grid
cases. The final probe found none, while preserving all 96 legal exact override
cases. Initial red tests and the intermediate prototype cleanup failure are
retained under `checks/regressions-before/` and `checks/task-tests-final/`.
The final combined suite is `checks/task-tests-verified/` (73 passed).

## Distribution and lesson contract

Keep the existing repeated-color spans disjoint. Overlapping spans would require
teaching color precedence in addition to the intended independent gap filling;
that is outside the current generated grammar. Singletons do not generate spans.
Mixed-color, singleton and edge profiles provide observable counterexamples to
the declared row-global, exactly-two-anchor, singleton-expansion and interior-only
rivals. No new restriction was introduced by this repair.

The production contract uses four consecutive ordered demonstrations and the
following query. Four-phase scheduling supplies each witness within those four
demos. Do not advertise arbitrary query rotations: the final Racket-labelled
census has 300/300 ordered lessons without tested-rival ambiguity but 450/1,500
ambiguous rotations. These rotations reuse the same bundles and are not 1,500
independent generated lessons. Evidence is finite and rival-bounded.

The canonical sampler remains within its documented height 8..14, width 9..14
and active-row 1..5 controls. The validator accepts a broader lawful 6..30 domain.
A lawful 30×30 validator input or a Python mirror check does not establish
ordinary generated support at that size. Real 30×30 Racket evidence belongs to
the separate prototype, where 24 active lines create substantial new fill work.

### Rejected optional period declaration

An intermediate source, SHA-256
`a82044b852102b649239c25e06532ad49a26b9d00709257bcefccb1bce96d6b0`,
added `LESSON_SCHEDULE_PERIOD=4` for fixed-seed exhaustive start enumeration.
`checks/after/` records the missing-census semantic warning, which the strict
battery treats as a failed stage (11 green, one failed; command exit 1). The subsequent census
(`checks/schedule-census.json`) covers all four start residues at seed zero in
each band: 12 clean ordered lessons, 60 pair/rotation checks, 18 ambiguous
rotations, and 20 unique inputs. This is not an all-seed proof.

`checks/after-final/` preserves the failed attempt to consume that receipt. The
shared semantic gate requires a blocking rotation policy for a declared-period
receipt, while this curriculum is intentionally ordered. The optional new
declaration was therefore withdrawn, leaving the existing schedule and lesson
semantics intact. The final source has no period declaration, and the final
12-stage battery succeeds under its established ordered policy. This is an
explicit narrowing of the proposed metadata change; it does not resolve or hide
rotation ambiguity. F2 proposes policy-aware receipt support without weakening
required-rotation evaluation. The retained earlier solve stays bound to the
intermediate source; a new final-source solve was completed afterward.

## Parameterization assessment: suitable, proposed prototype

Choose exactly two meaningful parameters: `axis` in `{row, column}` and
`min_anchors` in `{2, 3}`. These change the transformation itself, not just colors
or grid dimensions. A common lawful input produces four distinct Racket outputs.
The canonical setting is row/two and uses the unchanged canonical text exactly.
The other instantiated raw-text hashes are:

| Setting | Racket SHA-256 |
| --- | --- |
| row / 3 | `f973cce88fdabed030ff00482d7bd5f8ca270bae845100765a8802dabc5638f4` |
| column / 2 | `82db4df0a58300ba526d7117a636ad5a7007b7809fbf008f1651b7a99af9002c` |
| column / 3 | `fd9bccaab4a5fdc8e4602b7c314b205b5dbe6632969ca3d6228e4f50131db281` |

An episode samples a single setting explicitly; default APIs retain the canonical
setting. Three demonstrations distinguish the four settings. Their palette and
locations vary while the setting remains fixed. The query scales the same
operation to 30×30 with 24 active lines. Both dimensions support 6..30 inside the
prototype; disjoint spans avoid conflicting color assignments in its sampling
grammar. A general mirror regression also checks the canonical sorted-color
precedence outside that grammar rather than silently assuming first-seen order.

Racket supplies labels and alternative-setting predictions. Python is a checked
mirror and convenience interface, not the label authority. All 72 recorded
Racket/Python comparisons pass; all four original canonical pairs pass; there
are 76 actual Racket calls including replay checks. Four retained episodes at
seed 20261023 yield 12 demonstrations, four queries, 12 refuted parameter rivals
and zero ambiguous queries. This does not certify untested seeds or other
plausible hypotheses. No training admission or production parameter integration
is implied.

Public export uses an explicit allowlist: demonstration input/output grids and
query inputs. It omits parameters, seeds, source text, provenance and hidden query
labels. Private evidence remains in the verification report, separate from
`public_challenges.json`. The runtime helper uses the public snapshot/bridge APIs
and removes only newly imported snapshot modules on exit, preserving caller
modules. The cleanup regression caused one genuine failed staged run before the
final 73-test pass; both receipts remain.

## Reusable tools and evidence handling

The task patch carries `workspace/probe_contracts.py`, the parameterized sampler,
the real-Racket verifier and portable tests. Each audit carries its source-bound
probe, actual Racket outputs, rivals and reproducible counterexamples. These
tools use public generator loading and portable root discovery.

Only the two 22 MB full lesson censuses are compressed, losslessly, after their
original commands completed. `checks/evidence-archives.json` records original
and compressed sizes/hashes using the existing retention schema. All other
historical receipts remain at their original paths. The small restore helper
verifies both representations and writes only to a new output directory; it
imports no generator or rival code. This satisfies the return budget without
discarding the only copy of any failure or bundling an installed runtime.

The exact source patch was applied using the public replay command in a fresh
354-file declared-runtime-dependency closure from the 98,737-file packet. The
replay verified the exact Git root and all 10 changed file hashes. This is an
explicit partial scope. A new environment in that checkout passed all 73 task
tests separately; the replay tool itself never executes tests. The final handoff
binds both results to the tested source patch hash in
`checks/final-verification.json`. Final packaging adds only report/evidence bytes.
