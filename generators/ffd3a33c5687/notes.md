# Working notes: ffd3a33c5687

## Baseline measurement

Baseline generator SHA-256:
`6c119526bddda856119818ce9a79933844c01e0b464c9d80d4a613a1ca09be84`.
No prior return was used as a repair lead; the current pinned source and the
canonical examples were measured directly.

The before battery finished with 4 green, 1 advisory, and 7 failed stages. The
source lacked `RULE_HASH` and `self_check`, produced identity cases, did not reach
the canonical six-color profile, advertised controls that were narrowed or
silent, and exposed no executable rival contract. Randomly scattering cells also
made the intended orbit counts and teaching signal accidental.

## Repair design

The generator now constructs off-axis mirror orbits rather than placing unrelated
cells. Five exact public axes are observable from the returned grid:
`grid_h`, `grid_w`, `n_singletons`, `n_pairs`, and `n_conflicts`. Unknown or
out-of-range controls fail loudly. A five-profile deterministic schedule rotates
through every canonical shape/palette profile in every band. Ordinary draws have
one occupied different-color conflict, while callers may explicitly request
0--2 conflicts.

The canonical demonstrations leave occupied different-color conflicts
unconstrained. Two executable rivals therefore remain plausible on canonical
examples:

1. fill only blank mirror mates and preserve occupied conflicts;
2. give the right nonzero member priority.

Both are declared under `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and
`LESSON_COMPETITORS`. The ordinary schedule refutes both. `reference_probe.py`
implements the intended law and rivals independently of production code.

## Test-first evidence

- Initial task-local contract: 18 failed, 2 passed against the baseline.
- Metadata regression: 1 failed, 19 passed before aligning
  `SCHEDULE_PROFILES` with `schedule_profile()` IDs.
- Final source-bound portable task tests: 26 passed.
- Final inherited battery: 12/12 green at generator SHA-256
  `419d368c4fae796aaeaa52c5d2ee1965b106960f53e73f8a9980208d6a900ae7`.
- Shared census materialized 300 lessons / 1,200 pairs and 1,200 query rotations
  with zero ambiguity or scoring error. Its report remains `error` because its
  canonical reader rejects the normal unlabeled test query. The task-local
  fail-closed verifier accepts only that exact reader limitation, validates all
  saved lessons and source hashes, checks four labeled canonical pairs, and
  reports no other error.

## Remaining limits

The rival census is finite and covers declared competitors, not all possible
induction rules. Generated defaults do not place nonzero center-axis cells;
center preservation is present in a canonical labeled demonstration but is not
re-exercised by ordinary generated lessons. The generator remains unapproved;
this review does not alter approval or training-admission state.
## Current reviewer considerations

Source SHA-256: `419d368c4fae796aaeaa52c5d2ee1965b106960f53e73f8a9980208d6a900ae7`.

# Decisions: ffd3a33c5687

## D1 — Preserve and pin the canonical authority

**Choice.** Keep the Racket rule unchanged and add
`RULE_HASH = "4276b16a10bb"` to the generator.

**Rationale.** The canonical examples and independent Racket applications agree
with row-wise left-priority mirror completion. The baseline problem was input
distribution and contract quality, not authority behavior.

**Alternatives rejected.** Rewriting the Racket rule would add needless review
risk and could invalidate canonical provenance. Treating the prose “copy every
nonzero” as conflict-order agnostic was rejected because the executable authority
has deterministic left priority.

**Probe and failure mode.** Task tests compare all labeled canonical pairs and
nine generated conflict cases against an independent Python oracle and the public
Racket `Catalog.apply` path. Authority sync is green. A later catalog rule change
must update the pin and rerun those checks.

## D2 — Construct mirror orbits instead of scattering cells

**Choice.** Build disjoint off-axis mirror slots and assign exact singleton,
same-color-pair, and different-color-conflict types.

**Original rationale.** The baseline sought sparse asymmetry and visual variety,
but unrelated random placements made semantic coverage accidental and allowed
identity cases.

**Alternatives rejected.** Rejection-sampling random grids until counts happened
to match was slower, harder to reason about, and could bias joint support.
Post-hoc mutation of random grids was rejected because it obscures which controls
are exact.

**Probe and failure mode.** `observe_overrides()` recovers all five controls from
the grid. Endpoint tests cover minimum and maximum values in every band. The
constructor checks slot capacity and validates its own output. Future range edits
must preserve assignment capacity and color diversity.

## D3 — Advertise only exact, observable controls

**Choice.** Replace the baseline's broad style controls with five structural
integer axes: height, width, singleton count, same-pair count, and conflict count.
Reject unknown, boolean-as-integer, noninteger, and out-of-range values.

**Rationale.** These are task-domain facts visible in the returned input. They
allow direct boundary tests and avoid pretending that a latent “bias” is exact.

**Alternatives rejected.** Keeping `palette_kind`, `position_bias`, and similar
soft controls would retain ambiguous observability and combinatorial override
interactions. A direct `palette_size` axis was omitted because exact orbit/color
counts plus canonical profile scheduling already constrain it; adding it would
need a larger compatibility table.

**Limit.** The generated color cardinality is scheduled rather than a public
exact override. Center-axis marks are validator-lawful but not generated by a
public axis.

## D4 — Rotate all canonical profiles through every band

**Choice.** Use a five-state schedule containing every canonical
`(height, width, palette-size)` profile and rotate it by difficulty.

**Rationale.** The baseline never reached the six-color canonical profile, and
band-specific shape ranges caused profile-floor failures. Rotation preserves
support while still changing sequence order.

**Alternatives rejected.** Narrow easy/hard supports were rejected because they
made canonical support band-dependent. Pure random profile choice was rejected
because short lesson windows could miss rare profiles.

**Probe and failure mode.** Ten consecutive default draws in each band cover all
five profiles exactly twice. The schedule metadata regression was caught by a
red test when `SCHEDULE_PROFILES` initially exposed tuples instead of the IDs
returned by `schedule_profile()`.

## D5 — Make conflict semantics ordinary, not opt-in

**Choice.** Every default profile contains one occupied different-color mirror
conflict. Explicit callers may request 0–2.

**Rationale.** All labeled canonical examples are compatible with the shortcut
“fill a blank mate, but preserve an occupied conflict” and with right priority.
A conflict is the smallest direct witness for the actual tie-break.

**Alternatives rejected.** Relying on a rare random conflict was rejected because
three-demo lessons could remain ambiguous. Making conflicts a special texture was
rejected because the production sampler would not necessarily select it.

**Probe and failure mode.** The 300-lesson census and all 1,200 rotations refute
both rivals. This covers declared rivals only; an undeclared rule may still fit a
finite curriculum.

## D6 — Add executable structural and semantic contracts

**Choice.** Add `self_check`, `strict_canonical_like`, `rule_mirror`,
`semantic_observables`, `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`,
`LESSON_COMPETITORS`, `CANONICAL_SHORTCUTS`, `lesson_identifiable`, and mutation
fixtures.

**Rationale.** Prose alone cannot be exercised by the battery or census.
Executable rivals make teaching ambiguity measurable.

**Alternatives rejected.** A validator that accepted any rectangular ARC grid
would not detect distribution drift. A validator that required a conflict would
incorrectly reject the legal `n_conflicts=0` boundary, so conflict teaching is a
default-schedule property rather than a universal lawful-input requirement.

**Limit.** `strict_canonical_like` currently shares the lawful generator grammar
with `self_check`; it is not a classifier for every possible canonical-looking
scene outside the selected distribution.

## D7 — Keep an independent probe and test-first evidence

**Choice.** Implement the oracle/rivals again in `workspace/reference_probe.py`
and test public behavior through the source-bound staged runtime.

**Rationale.** Comparing a production helper with itself would not establish
correctness. The initial contract failed 18 of 20 tests on the baseline; the
metadata mismatch failed 1 of 20 before its fix; the final expanded suite passes
26 of 26.

**Alternatives rejected.** Tests that import private runner internals or private
labels were rejected. Frozen baseline fixtures were left untouched.

**Limit.** The independent probe is still written by the reviewer and is not a
formal proof; Racket authority checks provide the external executable anchor.

## D8 — Preserve the shared census error and verify around it

**Choice.** Do not patch shared source in the allowed task delta. Retain the
shared census as `error`, then use a narrow task-local verifier that accepts only
the exact unlabeled-query reader failure.

**Rationale.** The census had already completed all 300 lessons and rotations;
its sole error arose while reading a canonical test item with no output. Changing
shared files would violate the selected-task edit boundary.

**Alternatives rejected.** Manually adding a private query output, editing the
canonical ledger, or rewriting the shared report to `pass` would falsify evidence.
Discarding the completed census would lose 1,200 Racket-backed pair results.

**Probe and failure mode.** Six unit tests ensure the verifier rejects any extra
top-level error, ambiguity, rival shortfall, lesson error, or runtime-bootstrap
failure. `checks/feedback/F1-lesson-census-unlabeled.patch` proposes the shared
fix separately and passes `git apply --check` against this packet.

## D9 — Prior evidence use

No prior selected-task return was used as a repair lead. For audit target
`e3a2ff6ea587`, its current-hash `review_index.json` was used as a hypothesis lead;
all claimed behavior was independently reproduced against the current source and
public Racket authority before inclusion in `AUDIT.md`.

## D10 — Native parametric conflict priority with a causal guide

**Choice.** Add a separate native adapter whose exact default remains the
canonical left-priority Racket program.  The alternate setting adds one
center-marked guide row: locating its one-sided signal produces an
input-dependent `left`/`right` intermediate, which is then consumed to resolve
all occupied mirror conflicts.  Matched settings share inputs; the first two
demonstrations use opposite guide sides; requests support 2–6 demonstrations
and exactly four distinct queries, ending with a substantive 30×30 case.

**Why this parameter.** It stays inside the original mirror-orbit reasoning
while adding a real A-to-B dependency rather than a palette reskin or unrelated
composition.  A right-guide case makes skipping A (hard-coding canonical left
priority) change the final grid.  The production generator and canonical rule
are intentionally unchanged.

**Adversarial check and limits.** `workspace/parametric/audit.py` independently
tests fixed-side, opposite-guide, preserve-conflict, numeric-min/max,
singleton-majority, and first-conflict shortcuts over two seeds, demonstration
counts 2/3/6, both settings and all four query positions.  This is a finite
rival census, not universal uniqueness.  Native qualification and a protected
Racket counterfactual witness are required in the return; owner-side exact-byte
replay and acceptance remain pending and no training admission is implied.
