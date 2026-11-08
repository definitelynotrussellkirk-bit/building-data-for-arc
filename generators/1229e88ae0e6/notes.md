# Working notes: 1229e88ae0e6

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review 2026-09-27 — review-50944a880a82e844

The original generator's 600-draw census had no single-axis moves despite three
of four canonical pairs using one. Canvas size was fixed by difficulty; the
hard band produced only 12 normalized supports in 200 draws. Its own 33 focused
tests and morphology/profile gates did not expose these omissions.

Version 3.0.0 uses all four canonical canvases per band and a finite catalog of
connected, bbox-spanning, non-solid supports. It adds north/east/south/west source
controls while preserving the original four quadrant controls and `color_mode`.
The reference program, rule hash, canonical records, and review-safety ledgers
are unchanged.

Every consecutive four-demo window has two diagonal and two single-axis sources,
two multicolor examples, an interior source, an odd-slack tie, and a multi-cell
move. Direction is phased by `seed % 8`; witness roles by `(seed // 8) % 4`;
color phase by `(seed // 8 + seed // 32) % 4`. The latter separates all three
factors over the 128-seed period while providing all direction/color pairs over
the measured seed block 0..31 at a fixed query index. Explicit overrides are individually
validated, but an all-mono or single-zone override need not form an identifiable
four-demo lesson.

Two intermediate schedule repairs were rejected: index-only direction fixed the
first query direction, and joint direction/witness phasing kept northwest queries
permanently border-only. Regression tests retain both discoveries. A diagnostic
flip probe was corrected to respect the difference between the nonidentity
teaching domain and the wider executable rule: reflecting a source can make it
already centered. No invariant or quality gate was loosened to hide this.

The final candidate passes Python-side tests and an independent-coordinate
stress probe. The mandatory Racket-dependent battery stages remain blocked by a
missing Racket executable; attempted installation/download failed. Do not promote
this candidate or treat diagnostic Python outputs as admitted training labels.
Run the full battery with Racket and perform recipient-side review first.

## Review 2026-10-02 — review-9bce45fa2127c175

The inherited version 3.0.0 passed the complete 12-stage Racket-backed battery,
but a broader episode-level rival search found an identifiability defect outside
the existing rival bank. Across 1,536 ordinary episodes (three bands, seeds
0..511), centering the correct support and sorting colors in row-major order fit
all four demonstrations in 50 episodes and failed the query in 23. Descending
sorting survived 60 episodes and failed 28 queries. Packing the original
row-major color sequence into the first N cells of the centered bounding box
survived and failed one episode. Exact evidence is retained in
`checks/shortcut_audit_before.json` in the review return.

The root cause was a distinction between feature presence and correspondence.
Two multicolor demonstrations guaranteed palette preservation against a
single-color rival, but random arrangements could both be monotone. Likewise,
every motif had a hole, but all four demonstration supports could accidentally
be row-major prefixes. Version 3.1.0 keeps the same rule, canvases, axes, and
four-slot curriculum. Geometry slot 1 now excludes row-major-prefix supports;
color slot 1 repairs only a monotone multicolor draw, permuting the same color
multiset into a sequence with both an ascent and descent. No rejection loops,
new colors, changed frequencies, or output-label information are introduced.

Three semantic rivals and two witnesses now make the intended distinction
executable: ascending color sort, descending color sort, and centered bbox hole
packing. Tests were written first and produced seven targeted failures (three
bands for each witness plus rival declaration); after the repair, all 82 focused
tests passed. The retained `workspace/shortcut_audit.py` also probes undeclared
generic rivals. It reproduces the baseline failures and reports zero surviving
four-demo episodes for all probed rivals after the repair.

Independent diagnostics covered 16,164 exhaustive colored placements, 1,920
override cases, 4,968 seeded samples, and 4,140 sliding lessons with no failures.
The final Racket-backed battery reports 12 green stages and no advisory, failed,
interrupted, or pending stage. The selected Racket program, rule hash, canonical
records, archival bank, and safety/approval state were not changed.

Remaining limitation: the shortcut bank is finite. It materially expands exact
cell-correspondence coverage but cannot prove that no unmodeled learner shortcut
exists. Diagnostic Python outputs are not admitted labels and do not replace the
Racket authority receipts.
## Current reviewer considerations

Source SHA-256: `cb00482a92a8dd74d160b8ee530caca6fe5041354c0fab6b45f5a733dd261c3e`.

# Design decisions: 1229e88ae0e6 review

## D1 — Treat exact cell correspondence as the missing lesson property

**Observed input choice.** Version 3.0.0 intentionally guaranteed two multicolor
examples and non-solid supports in every lesson. The prior rationale was to
refute recoloring and solid-bbox shortcuts while retaining broad random color
and support variation.

**Finding.** Those are feature-presence guarantees, not correspondence
guarantees. A multicolor pattern can already be sorted, and a holed support can
already occupy the first N row-major bbox cells.

**Alternatives considered.** I considered adding only more random samples,
forcing balanced color counts, or declaring the new rivals without changing the
distribution. More random samples reduce but do not bound the collision;
balancing frequencies does not prevent monotonic order; declarations alone
would make ordinary lessons fail their own gate.

**Decision.** Add one deterministic witness opportunity for color-cell binding
and one for exact hole positions per quartet. This directly targets the causal
ambiguity while leaving the rest of the distribution random.

**Probe.** `workspace/shortcut_audit.py` reproduces the baseline survivors and
measures the repaired lessons on identical seed/band ranges.

**Limitation.** The chosen rival bank cannot enumerate all possible learned
representations of correspondence.

## D2 — Reuse geometry curriculum slot 1 rather than add examples or an axis

**Original rationale.** The four geometry slots were already independently
phased from source direction: slot 0 carries odd-slack and long-translation
evidence, slot 2 carries interior-source evidence, and the remaining slots were
unrestricted.

**Alternatives considered.** Increasing `EXAMPLES_NEEDED` would alter dataset
shape and cost; adding a public `support_mode` axis would enlarge the override
contract for an internal teaching obligation; filtering every support would
needlessly reduce morphology diversity.

**Decision.** Make slot 1 reject only supports equal to the row-major prefix of
their bbox. `_supports_for_slot` is a cached finite filter, and `_layouts`
checks feasibility before sampling. No rejection loop or query-label feedback is
used.

**Failure modes checked.** Every band/zone/slot still has feasible layouts;
all four canonical canvases remain covered; the morphology census and 142-shape
finite stress domain remain intact.

**Limitation.** Slot 1 addresses one high-plausibility packing convention. Other
canonicalizations require separate rivals.

## D3 — Repair only monotone designated multicolor draws

**Original rationale.** Random per-cell coloring, with every requested palette
color realized at least once, avoided artificial balance and kept frequency
variation. The color schedule was independently phased from direction and
geometry roles.

**Alternatives considered.** Hard-code an alternating color pattern, sort then
rotate every multicolor sample, force three colors, or resample until a
non-monotone ordering appears. Hard-coded patterns create a new shortcut;
changing every sample distorts the distribution; three colors excludes useful
two-color cases; retry sampling complicates determinism and can hide feasibility
bugs.

**Decision.** Preserve the random assignment unless designated color slot 1 is
monotone in row-major support order. In that one case, permute the same multiset
so it has both an ascent and descent. For duplicate minima use
`low, high, low`; otherwise use `high, low, next`. This works for every motif of
at least three cells with at least two colors.

**Failure modes checked.** Tests cover easy/medium/hard, seeds 0..31, a negative
seed, and a value above 2^63. A separate frequency test confirms colors are not
forced equal. Palette values and counts are unchanged.

**Limitation.** The deterministic repair introduces a small conditional pattern
in one slot. If future models exploit that slot marker, the schedule should be
re-audited with additional permutation rivals.

## D4 — Make the missing shortcuts executable semantic rivals

**Original rationale.** The existing rival bank encoded eight plausible errors:
ceil centering, border-only behavior, solid bbox, recolor-first, one-axis moves,
diagonal-only moves, and one-step motion.

**Alternatives considered.** Keep the extra checks solely in tests or only in an
external audit. That would permit future schedule edits to regress lesson
identifiability while the generator's own semantic contract remained green.

**Decision.** Add ascending color sort, descending color sort, and centered-bbox
hole packing to `SEMANTIC_RIVALS`; add two witnesses and link them through
`WITNESS_RIVALS`. Existing `lesson_identifiable` and stress logic then enforce
them without a parallel contract.

**Limitation.** Rivals use Python diagnostic mirrors. Racket remains authority;
Racket parity is established by the separate battery rather than by these
functions.

## D5 — Do not change the canonical/Racket rule

**Evidence.** The baseline rule already matched all canonical pairs and the
complete before battery was green. The failure arose solely from which inputs
co-occurred in a lesson.

**Alternatives considered.** No rule rewrite was justified. Changing comments or
canonical code merely to create a diff would add authority risk without fixing
the distribution.

**Decision.** Keep `RULE_HASH=5e5cb5402934`, the canonical row, and archival bank
unchanged. Bump only the generator version from 3.0.0 to 3.1.0 because seeded
outputs intentionally change.

**Verification.** Racket rule smoke, Racket lint, and authority sync all pass in
the after battery.

## D6 — Retain a generic-rival tool, not just the one-off exploratory script

**Original rationale.** Existing `review_probe.py` emphasized movement classes
and `stress_review.py` enforced declared rivals. Neither could discover a rival
that was absent from the generator dictionary.

**Alternatives considered.** Keep `/tmp/audit_centering_rivals.py` only as a log,
or add the generic rivals permanently to the shared repository. The first is not
reusable; the second is outside this task's permitted edit scope and requires
cross-task design.

**Decision.** Add task-local `workspace/shortcut_audit.py`. It merges declared
rivals with generic color, support, orientation, palette, and source-copy
competitors; uses ordinary indices 0..4; records first seeds; and offers
`--require-none` for CI use. A focused test verifies the repaired generator has
zero survivors over a bounded census.

**Limitation.** It is centering-family-specific and diagnostic. Shared tooling
should eventually generalize the episode-survival interface while keeping
family-specific rival libraries.

## D7 — Preserve deterministic finite sampling and avoid rejection loops

**Original rationale.** The prior review deliberately replaced fragile retries
with finite catalogs and independent seed phases.

**Decision.** All new geometry restrictions are catalog filters. The color
repair is a total deterministic transformation of an already drawn multiset.
No global RNG, unbounded loop, reference output, or Racket label influences input
generation.

**Verification.** Determinism/global-RNG tests, exact override tests, exhaustive
placement checks, and all battery stages pass.

## D8 — Interpret verification honestly

The first attempted `selfcheck` command after adding tests stayed green because
that stage does not run the task-local pytest file; it was not counted as the RED
proof. I prepared the portable runtime, ran the focused test file, observed the
seven expected failures, then implemented the repair and observed 82 passes.
The earlier command and tool friction are documented rather than rewritten as a
successful TDD signal.

The initial baseline launches that were externally killed before completion are
also not presented as check results. The retained completed before and after
runs both exited 0 and have battery summaries. Diagnostic Python specifications
are labeled non-Racket throughout.
