# Working notes: 0be8ff9b4144

## Current rule and authority

The first row and first column are headers; `(0,0)` is ignored. A body row is
active exactly when its first cell is green (`3`). A body column is active
exactly when its top cell is red (`2`). Every active row/column intersection is
overwritten with gray (`5`); all other cells are preserved.

The selected Racket authority was not changed. Its normalized hash remains
`138495330232`, and the generator pins that value as `RULE_HASH`.

## Defect found in imported version 3.1.1

The imported generator advertised broad exact axes but passed explicit controls
through difficulty-narrowed draws. Valid endpoints such as `grid_h=5` or
`n_top=6` could therefore fail depending on the band. Unknown keys, invalid
texture values, coercible scalar types, and invalid `sample_index` values were
not rejected consistently. Identity degenerates were advertised as ordinary
textures even though the normal teaching contract requires both marker axes.
The checker only verified that one active row and column existed.

The teaching textures were also sampled independently. A three-demonstration
lesson could omit one or more of the intended negative contrasts, leaving
canonical-fitting shortcuts alive: treating any non-background header as active,
refusing to overwrite occupied intersections, or requiring corner color `8`.

## Repair in version 5.0.0

- Validate `seed`, `sample_index`, `difficulty`, every override key, exact scalar
  type, value domain, and impossible geometry/count pair before generation.
- Honor the full documented exact domains in every difficulty band. Reserve at
  least one inactive top-header cell and one inactive left-header cell; publish
  the exact incompatible combinations.
- Remove identity fixtures from the ordinary texture domain.
- Add `observe_overrides`, a structural `self_check`, `strict_canonical_like`,
  a source-bound `rule_mirror`, and a canonical `profile_signature`.
- Use a deterministic four-profile schedule:
  `plain`, `wrong_marker`, `body_content`, `corner_var`.
- Make every rich profile carry all three contrasts at once. The texture name
  changes emphasis and the ignored-corner code, not semantic coverage.
- Declare the three canonical-fitting rivals and executable witnesses, and reject
  any lesson whose demonstrations leave one declared rival alive.

## Distribution choices

`plain` and `wrong_marker` use one of the five observed canonical shapes when
geometry is not overridden. This gives exact canonical-profile support in every
band and a 25% strict canonical-style population. Rich profiles still cover the
full legal geometry and background domains, subject only to the declared need
for one inactive header position on each side.

`wrong_marker` deliberately stays on the canonical four-color palette
`{0,2,3,8}`: top-header `3` and left-header `2` are inactive, and irrelevant
body content uses `8`. This is a second exact-profile anchor without weakening
the wrong-marker contrast.

The corner codes `8`, `3`, `4`, and `6` identify `plain`, `wrong_marker`,
`body_content`, and `corner_var` respectively. The canonical rule ignores the
corner, so this makes `texture` exactly observable without affecting active
headers.

## Strongest retained shortcut witness

The strongest shortcut considered is: activate every non-background top/left
header rather than only top `2` and left `3`. It fits all five canonical labeled
pairs because their headers contain no wrong-color non-background decoys.

The exact saved witness is
`counterexamples/semantic-shortcuts/input.json`. The canonical Racket output
changes only `(1,1)` to `5`; the shortcut also changes `(1,2)`, `(2,1)`, and
`(2,2)`. See `racket-output.json`, `reproduction.json`, and `reproduce.py` in
that directory. Every rich scheduled profile emits this semantic class.

## Known limits

The lesson contract establishes identifiability only against the three declared
rivals, not against all possible programs. The exhaustive schedule check covers
all four declared start residues at a fixed seed and every query rotation; the
larger random census samples additional seeds but is not a proof over all seeds.
The ordinary generator intentionally excludes empty-axis identity cases because
they do not help teach the selected intersection rule.
## Current reviewer considerations

Source SHA-256: `fcaff73686a0f6aac82290a52e733ddf60ccbe49b9c6473b4c5ba90bbc94a5c3`.

# Decisions for 0be8ff9b4144

## D1. Keep the selected Racket rule unchanged

**Prior choice:** The imported generator mirrored the intended header-intersection
rule but did not pin its authority hash.

**Decision:** Preserve the canonical Racket program exactly and add
`RULE_HASH = "138495330232"` plus a Python mirror tested against all five
canonical labeled pairs.

**Reason/evidence:** The authority itself is coherent; the defects were in the
generator contract and teaching distribution. `checks/after/` and
`generators/0be8ff9b4144/counterexamples/semantic-shortcuts/racket-output.json`
bind the final source and witness to that authority.

**Rejected alternative:** Edit the Racket rule to accommodate generator quirks.
That would change the task rather than repair the generator.

## D2. Treat advertised axes as exact public controls

**Prior choice:** `AXES` advertised `grid_h=5..16`, `grid_w=6..18`, and marker
counts `1..6`, but explicit values were sent through difficulty-specific narrow
ranges. Unknown and coercible controls were accepted inconsistently.

**Decision:** Validate calls before constructing the generation context, reject
unknown keys and non-literal scalar types, and draw explicit values against the
full declared domains in every band. Publish all impossible geometry/count
pairs in `INCOMPATIBLE_OVERRIDE_COMBINATIONS`.

**Probe:** The initial contract tests failed 57 cases; the final 70-test suite
covers every single-axis endpoint in every band, representative compatible
joint combinations, all declared conflicts, invalid keys/types, and exact
observation. The public override stage passes.

**Rejected alternative:** Narrow `AXES` to the old easy/medium/hard defaults.
That would make documentation honest but discard useful, lawful support.

## D3. Reserve inactive header positions

**Decision:** Require `n_left <= grid_h - 2` and `n_top <= grid_w - 2`.

**Reason:** Rich lessons need at least one inactive position on each header to
place wrong-color decoys. Allowing every body row or column to be active would
make the advertised rich contract impossible for that tuple.

**Limitation:** Endpoint counts remain individually reachable, but not with
incompatible minimum dimensions; those combinations are explicitly declared
rather than silently clipped.

## D4. Remove identity degenerates from the ordinary texture domain

**Prior choice:** `no_top_markers` and `no_left_markers` were public textures.

**Decision:** Set ordinary and lawful-degenerate texture declarations empty.

**Reason:** Identity examples do not demonstrate the Cartesian-product paint
operation and conflict with the normal invariant that both active axes exist.
They are useful as private negative fixtures, not as training lessons.

**Rejected alternative:** Keep them at low probability. Even rare identity
examples complicate the lesson contract and exact override semantics without
teaching a needed branch.

## D5. Use a four-residue curriculum, with all contrasts in every rich example

**Prior choice:** Helpful textures were sampled independently. Three examples
could therefore miss a contrast.

**Decision:** Schedule `plain`, `wrong_marker`, `body_content`, `corner_var` by
`sample_index mod 4`. `EXAMPLES_NEEDED` remains three. Every rich profile now
contains: wrong-color header decoys, occupied active content that must be
overwritten, preserved off-intersection content, and a non-`8` corner.

**Reason/evidence:** Any three of the four consecutive schedule residues include
at least two rich examples. Task tests enumerate every schedule start and every
query rotation. The required semantic gate checks 12 production lessons and
all 48 rotations with zero ambiguous rotations against the three declared
rivals.

**Rejected alternative A:** Give each texture only its named contrast. A
three-example window or query rotation can omit a needed witness.

**Rejected alternative B:** Increase the mandatory demonstration count to four.
That would work but changes the task interface unnecessarily; redundancy inside
rich profiles makes three sufficient.

## D6. Add exact canonical support without collapsing diversity

**Failed iteration 1:** Broad weighted geometry produced no exact canonical
profile in medium/hard during the 20-draw gate.

**Failed iteration 2:** Anchoring only `plain` produced 13/60 exact/envelope
hits, below the blocking 25% envelope floor.

**Decision:** Anchor both `plain` and `wrong_marker` to one of the five observed
canonical shapes when geometry is not overridden. Keep `plain` strict; make
`wrong_marker` use only canonical palette colors while retaining all rich
semantic contrasts.

**Evidence:** `checks/focused-profile-v3/` passes. The final semantic sample has
150/600 strict inputs (25%). Rich profiles continue to cover broad dimensions,
counts, backgrounds, and body placements.

**Rejected alternative:** Force all profiles into canonical shapes. That would
meet the profile gate but overfit morphology and weaken scale/generalization
coverage.

## D7. Make texture exactly observable through an irrelevant corner code

**Decision:** Use stable corner values `8`, `3`, `4`, and `6` for the four
textures and recover them in `observe_overrides`.

**Reason:** The rule ignores `(0,0)`, so this exposes an exact texture control
without leaking activation information into the top or left header. It also
ensures a requested texture can be verified mechanically.

**Risk if wrong:** A learner could condition on the texture code. The rich
profiles all carry the same three semantic contrasts, so such conditioning does
not create a rival that survives within the declared lesson contract.

## D8. Name and test the canonical-fitting shortcuts

The retained competitors are:

1. Any non-background header cell activates its row/column.
2. Paint only active intersections that were background; preserve occupied ones.
3. Apply the rule only when the corner is `8`.

All fit the canonical labeled pairs. Their witnesses and mappings are executable
through `SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, and
`lesson_identifiable`. The first rival's exact Racket-checked counterexample is
saved under `generators/0be8ff9b4144/counterexamples/semantic-shortcuts/`.

## D9. Preserve honest solve records

The required blind pre-repair solve for `34f8510e39d0` was completed from visible
examples only and declared no prior exposure. The post-repair solve for this task
was also visible-only, but declares prior exposure because the generator and rule
had already been studied. Neither episode consulted its reference during the
solve phase; both first implementations passed all visible demonstrations.

## Review review-6af8dbbf06cb1bf3 — native parametric family

### D10. Parameterize intersection selection, not input cosmetics

The native adapter adds one immutable episode setting,
`intersection_policy = all | same_parity | opposite_parity`. `all` returns the
exact canonical Racket program byte-for-byte. Every setting uses the same header
grammar and first decodes exact color-3 row headers plus exact color-2 column
headers. The alternatives then select intersections by parity of the decoded
row/column **ranks**, rather than raw coordinates. This preserves the canonical
object/relationship structure while making the nearby rules materially
 different.

Rejected alternatives were palette swaps, marker recoloring, geometry-only
parameters, and absolute coordinate checkerboards. Those either change nuisance
axes or let the second operation ignore the decoded ordered intermediate.

### D11. Make two demonstrations sufficient and four queries independently useful

The adapter supports 2–6 demonstrations and 1–4 queries. Inputs are matched
across settings, every pair is distinct within an episode, and the first query is
identical whether one or four queries are requested. Marker positions deliberately
break rank/coordinate parity equivalence; wrong-color header decoys, occupied
selected intersections, preserved body content, and irregular active-axis counts
appear in the curriculum. Query shapes are 12x14, 18x25, 25x18, and 30x30; the
30x30 case has six active rows and columns, boundary markers, occupied
intersections, and broad distractor content.

Focused tests cover every setting, all demonstration counts, three seeds, query
prefix stability, strict request typing, public/private projection, and five
plausible rivals. The final staged run passed 145 tests.

### D12. Retain a bounded adversarial self-audit

The visible demonstrations and queries refute five declared shortcuts:
absolute-coordinate parity, rank-diagonal-only, single-axis parity, treating any
non-background header as active, and preserving occupied selected cells. The
retained self-audit covers all three settings on seeds 0, 17, and 91 and includes
an exact protected-Racket witness for the strongest parity shortcut. This is a
finite rival set, not a universal uniqueness proof.

### D13. Bind causal depth to the qualified source

Step A produces ordered active-row and active-column lists. Step B consumes their
list indices to decide rank-parity intersections. The protected-Racket causal
witness uses the qualified `same_parity` program and a counterfactual that only
reverses the six-column intermediate. That wrong intermediate changes 24 final
cells, while the unaltered program hash remains
`b202066305eb3a9305bae07e3175c7c1c5fb8768d53d4184e4228a5ba1881eec`.

Native qualification passed all three settings on required seeds 0 and 17. The
source inventory hash is
`7ff56bca814861fdaaf5fe697f0728e6c0691f52734363edd8b85c8903bb9cfd`.
Reviewer status is ready only; owner integration, fresh qualification, and native
acceptance remain mandatory. No training admission is claimed.
