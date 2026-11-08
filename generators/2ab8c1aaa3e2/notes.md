# Repair notes — review-84b2c719f670fcfc

## Authority and prior evidence

Baseline v1.3.1 SHA-256:
`91ff0f670a9e5a7ec1879ac9730f34fafd990c54e330349d17b9ef3fac290258`.
Canonical rule `ad1f1fa8669a`, all canonical labels, and archived reference files
are unchanged. The prior return `review-78472a99283c57d9:v0001` in the retained
review index was used as a lead, not as a substitute for new measurements.
The old choice's pedagogical rationale is unknown; the retained notes were empty.

The old validator stopped after finding one good column. The prior audit's
pair-plus-triple grid is now deliberately accepted as an exact-count negative,
not silently grandfathered as a pair-only instance. Invalid cell values,
quadruples and unsupported column structures are rejected anywhere in the grid.

## Distribution and curriculum

Core: sample index congruent to zero modulo three. Only monochrome-pair
columns; a strong but nonexclusive preference for the five canonical dimension,
pair-count and color-count profiles. This preserves the original manifold.
Contrast: the other two residues. Two true pairs share a color; one has an
unlike interior singleton. A separate gapped triple does not fill, and a separate
column of unlike endpoints does not join. Positions, columns and palette are
randomized with keyed GenCtx streams. Additional pairs broaden object count.

Every contrast refutes `at_least_two`, `any_two`, `monochrome_column`, and
`global_two`. All four rivals fit every one of the five labelled canonical
pairs. Any four consecutive default indices contain at least two contrasts;
removing any query leaves at least one full contrast in three demonstrations.
This deterministic statement is conditional on default, consecutive draws.
Production sampling and rejected-index handling are checked separately by the
Racket-labelled lesson census; arbitrary curricula made with overrides carry
no such guarantee. Twelve names in diagnostic namespace listings represent
four behaviors, not twelve independent competitors.

## Exact overrides and feasibility

`grid_h` accepts integers 4..22; `grid_w` 4..20; `pairs` 1..12;
`n_distinct_colors` 1..9, excluding background. Bool, float and string coercions
are rejected. Unknown names fail, and None is treated as unspecified.
For width w, p pairs and k nonzero colors, the allowed union is:

* core: p <= w and k <= p;
* contrast: p + 2 <= w and 2 <= k <= p + 3 for p >= 2;
  for explicitly requested p=1, the color capacity is five.

Other axis limits still apply. A constrained draw may switch schedule branch
to honor a feasible exact override. Impossible joint settings raise
`IncompatibleOverrides` with minimal conflicting axes; they are not clamped or
silently redrawn at a different requested value. The implementation is constructive,
not retry-until-lucky. The removed `palette_kind`, `palette_size`,
`position_bias`, `density`, and `texture` controls previously advertised behavior
that did not occur. This intentional API cleanup is marked by the major bump.

## Bounded domain and self-review

Columns may be empty, singleton, pair, triple, two unlike singletons, or a pair
with one unlike interior singleton; some same-color pair must have a gap.
This covers all five canonical examples and the contrast curriculum. It does
not attempt all Racket-lawful inputs: four-plus repetitions, two same-column
pairs and overlapping fill spans remain outside the supported training domain.
That avoids adding overwrite-order subtleties to this bounded repair.

The repeated combination of contrast motifs is still a distribution restriction;
undeclared rules could exploit it. There is no claim of universal induction,
model training gain, private-query accuracy, or changed approval status.

## Verification

The return's checks include a clean 12-stage battery; 52 portable task tests;
300 production lessons/1,200 query rotations with no declared-rival ambiguity;
and the standalone diagnostic probe described in `workspace/README.md`.
All reports bind to the exact generator bytes, not just VERSION. Failed TDD and
baseline evidence is retained in the return. The Python diagnostic oracle is
not a replacement for production Racket labels.
## Current reviewer considerations

Source SHA-256: `9a831d8a28858cec55830840899f7c67d511b256328145308b9d8ecc7b9fe264`.

# Decisions — 2ab8c1aaa3e2, v2.0.0

Final generator SHA-256: `9a831d8a28858cec55830840899f7c67d511b256328145308b9d8ecc7b9fe264`.
The canonical Racket rule and all existing example labels are unchanged.

## R1: Make the API honest rather than invent new palette behavior

The baseline's palette/position/density/texture controls were decorative or
band-dependent. Original pedagogical rationale is unknown: the retained notes
were empty. The current before battery independently reproduced the failures;
no prior report was counted as a fresh measurement.

Four exact integer axes remain: rows 4..22, columns 4..20, same-color per-column
pair groups 1..12 and distinct nonzero colors 1..9. The sampler constructs the
requested counts and has an output observer. Bool, floats and numeric strings
do not silently coerce, unknown keys fail, and None is unspecified. No meaningful
old knob is silently reinterpreted. Removing the five inactive legacy keys is
an intentional compatibility change, marked with v2.0.0.

A “best effort” clamp was rejected: that would look successful while changing
the requested experiment. Instead choose a feasible layout before drawing it,
or raise a structured minimal-axis incompatibility. Core needs p<=w and k<=p;
contrast needs p+2<=w and 2<=k<=p+3 (k<=5 when an explicit p=1 is requested).
Height does not reduce these capacities in the accepted 4..22 range. This
closed-form model is separately checked against constructive draws in the probe.
One-axis extremes must remain supported in every band, but infeasible joint
settings are not misreported as accepted.

## R2: Preserve a core while actually teaching the conditional rule

All five canonical pairs can be explained by several wrong simpler rules:
fill when a color occurs at least twice; fill any two nonzero endpoints; fill
only wholly monochrome columns; or count pairs globally rather than per column.
The old generator repeatedly reinforced this equivalence. Merely fixing the
validator would not teach which condition matters, so that alternative was
rejected.

One third of default indices are pair-only core draws. They favor canonical
size/palette/count profiles while resampling locations and colors—not copying
grids. There is broad nonzero support outside those profiles. The other two
thirds are contrast draws: a gapped triple, unlike endpoints, a pair containing
an unlike singleton, and two gap-bearing pairs sharing a color in different
columns. Each contrast refutes all four declared rivals. Core-only would leave
the rivals indistinguishable; contrast-only would abandon canonical support.

Rare independently sampled witnesses were rejected because high marginal
witness frequency does not guarantee a complete lesson. The period-three
core/contrast/contrast schedule makes each four-consecutive-draw lesson contain
at least two full contrasts. Holding out any one pair still leaves a contrast
among three demonstrations. All small cyclic residues and holdouts are checked
by tests/probe; actual production materialization and query rotations are
checked with Racket labels in the 300-lesson census. Constrained overrides may
switch branches to honor their exact settings and are explicitly not covered
by the default teaching guarantee.

## R3: Admit a deliberate negative, not an accidental validator hole

The retained audit lead is `review-78472a99283c57d9:v0001`, with selected baseline
source SHA-256 `91ff0f670a9e5a7ec1879ac9730f34fafd990c54e330349d17b9ef3fac290258`.
Only its indexed audit text was available; the original return ZIP was not
opened, so no unavailable ZIP digest is invented. The index's original path
ends `0001-9cbf2962edaa/original.zip`; that prefix is not claimed to be a full hash.

It described a valid early pair hiding an invalid later triple under the old
pair-only invariant. The new domain intentionally includes that triple because
the unchanged Racket rule leaves it alone and it is precisely the useful
counterexample to “at least two.” The validator now checks every cell and every
column, rejects malformed types/palette/ragged shapes and unsupported counts,
and requires a real nonempty pair gap. The regression preserves both halves:
legal triple remains unchanged; an added fourth marker is rejected.

## Domain boundary and possible new shortcuts

Empty/singleton/pair/triple, two unlike endpoints, and pair-with-interior-noise
are the supported column structures. More than three same-color markers,
two different paired colors in one column, overlapping spans and their overwrite
ordering are Racket-lawful possibilities not taught here. Adding all of them
would materially enlarge the lesson language; silently declaring them supported
without witnesses would be worse than this explicit boundary.

Contrast motifs deliberately co-occur, so an undeclared rule could exploit that
co-occurrence. No proof of universal induction, latent model capability, hidden
solve accuracy or training safety follows from the finite rival census. The
geometric-template shortcut found in A2 reinforces why passing only declared
competitors cannot establish such a proof. Do not equate all passing gates with
changing `approved` or `train_safety`; this return changes neither.

## Iterations actually observed

The first new regression suite on baseline source had 31 failures and 6 passes
(`checks/logs/tests-red.log`). On the first repaired source run, 36 passed and
one failed because the test incorrectly unpacked a dictionary from public
`canonical_pairs` as an input/output tuple (`tests-green-initial.log`). The test
was corrected to use its documented dictionary keys; generator semantics did
not change to accommodate the test. The initial corrected suite passed 37/37;
additional boundary/metamorphic/purity tests brought the final suite to 52/52.
All genuine failure logs remain. Their exact early launch argv was not separately
captured; the retained logs and counts are not presented as fully source-frozen
replay runs. The final portable suite and fresh replay have exact command and
source records.

Final evidence: 12/12 battery, 52/52 task tests twice, 300/300 production lessons,
1,200 Racket-labelled query rotations, 20,160 override attempts, and 3,888 joint
corner settings. Individual populations, overlaps and source identities are
in `REVIEW.md`, `RESULTS.json` and their cited check files.

## Audit-only scope

A1 rejects every canonical input; A2 allows dimension-based lookup to bypass
reference-scale inference. Both have exact public-API Racket evidence and
bounded reproduction scripts, but neither audited generator was edited. A2's
scale-mutated case is outside its deliberately frozen template grammar, so it
is a demonstrated shortcut/domain restriction, not an in-domain label crash.

## Current parametric proposal — exact-two directional composition

Production v2.0.0 and its selected canonical rule are unchanged. The separate
`workspace/parametric/` native adapter adds `vertical_then_horizontal` alongside
exact canonical `vertical_only`. Stage B uses the completed vertical grid's
exact per-row counts; the owner-facing wrong-order witness distinguishes the
order through protected Racket. Settings share identical input draws.

Self-review found three finite teaching gaps: horizontal-first/simultaneous fit
canonical demonstrations, a repeated VH cycle fit some alternate lessons, and
>=2 horizontal filling could be masked by overlapping paints. The two-demo
curriculum now has a protected empty-cell witness and a separate offset-pair
witness. No demonstration-count increase. Frozen before grids and Racket labels
are retained in `evidence/current/teaching-regressions.json`; the supplied audit
can replay them from checks. The first two layouts intentionally restrict geometry;
colors/reflections vary and later demos/queries broaden interactions and scale.

Native contract: 2..6 demonstrations (default 3), 1..4 prefix-stable queries
(authoring uses 4), substantive 30x30 stress. The 32-seed sweep has no failures
against its 13 declared policies; this is not universal learnability. Final
owner qualification/acceptance is separate; no training admission is claimed.
