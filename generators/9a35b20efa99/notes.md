# Working notes: 9a35b20efa99

## Current rule and authority

The input has a zero background, exactly one color-9 anchor, and one monochrome
4-connected asymmetric template in a color from 1 through 8. The selected
canonical rule crops the template and stamps its 0°, 90°, 180°, and 270°
variants around the anchor in upper-left, upper-right, lower-left, and
lower-right order. The Racket authority was not edited. Its pinned source hash
prefix is `019ee1056dff`.

## Current generator decision

Version `2.0.0` uses a constructive four-slot teaching schedule:

1. `corner_l3_above` on 13×13,
2. `branch5_below` on 15×15,
3. `corner_l4_left` on 13×15,
4. `blob6_right` on 15×17.

Each slot permits an independently randomized template color and quarter-turn.
The only advertised exact controls are `grid_h`, `grid_w`, `motif_color`, and
`motif_rotation`; all legal joint combinations are constructed exactly, and
unknown or invalid controls fail closed. Placement is sampled only from choices
that keep the input lawful and every output stamp in bounds.

This reverses the imported `1.1.1` choice to advertise palette aliases,
singleton pseudo-axes, and invalid production degenerates. The original
rationale beyond the source comments is unknown. The replacement was chosen
because the old palette/texture controls did not affect ordinary pixels, the
singletons could not demonstrate an effect, `no_anchor`/`no_motif` violated the
stated domain, many documented size overrides could not be realized, and the
old schedule always put the source motif above the anchor.

## Canonical shortcuts and teaching contract

Two executable rivals fit all four canonical pairs:

- `above_only`: apply the orbit-stamp rule only when the source template is
  above the anchor; otherwise return the input unchanged.
- `corner_l_only`: apply the rule only to a canonical corner-L template;
  otherwise return the input unchanged.

The exact branch-below witness is retained at
`counterexamples/above-only-and-corner-l-only.json`. The intended output differs
from each rival at 25 cells. Every four-slot production bundle contains three
non-above examples and two non-corner-L examples. With any one pair held out as
the query, the other three demonstrations still refute both rivals.

`lesson_identifiable` enforces three demonstrations and checks their labels
against the local rule mirror before requiring both rivals to be refuted. This
is finite evidence against declared rivals, not a proof of unique induction
over all possible hypotheses.

## Verification and retained tools

- `tests/test_generator_9a35b20efa99.py` contains portable source-bound
  regressions, including real-Racket parity.
- `workspace/reference_probe.py` supplies an independent geometry oracle,
  canonical-pair loader, rivals, witness, and real-Racket parity helper for
  future reviews.
- Final generator SHA-256:
  `235c463d52c9fb3d37e4b374011a16dbf8302e08b386f30080252b9a863d2779`.
- Portable task tests: 47/47 passed.
- Complete final battery: 12/12 green.
- Required-rotation semantic gate: 600/600 strict inputs, 12/12 lessons, and
  48/48 query rotations passed.
- Large source-bound census: 300/300 lessons materialized; 0 ambiguous
  production lessons and 0 ambiguous among 1,200 held-out query rotations;
  1,191/1,200 inputs were byte-unique.

No earlier return was used as a design lead; this repair was derived from the
pinned baseline, canonical pairs, current checks, and task-local probes.

## Known limits and open findings

The production manifold intentionally uses four small asymmetric template
families rather than arbitrary connected polyominoes. That makes the teaching
schedule inspectable and constructive but does not cover every lawful shape the
Racket program could process. The declared rival set is deliberately small and
plausible; undeclared rivals may still exist. Catalog approval and training
admission remain outside this review.
## Current reviewer considerations

Source SHA-256: `235c463d52c9fb3d37e4b374011a16dbf8302e08b386f30080252b9a863d2779`.

# Decisions — `9a35b20efa99`

## D1: Preserve the canonical Racket authority

**Prior choice/rationale:** The imported generator was paired with an existing
canonical rule. No rationale beyond the code and canonical ledger was available.

**Decision:** Do not edit canonical data or any Racket source. Pin
`RULE_HASH = "019ee1056dff"` and make the Python generator conform to the rule.

**Why:** All four canonical pairs and generated witnesses execute correctly under
the selected authority. The observed defects were in input generation,
advertised controls, and teaching coverage—not the transformation.

**Evidence:** authority-set SHA-256
`9ce8315e053e49d37c9d4d0733851f3032a6c609c97467fac1d9e64c6bd0d6ef`;
final authority sync and execution parity are green in `checks/after/`.

**Failure mode guarded:** silently changing labels to accommodate an easier
sampler.

## D2: Replace eight nominal axes with four exact observable controls

**Prior choice:** `grid_h`, `grid_w`, `palette_kind`, `palette_size`,
`position_bias`, `n_distinct_colors`, `density`, and `texture` were advertised.
`texture` also exposed `no_anchor`, `no_motif`, and a symmetric motif.

**Original rationale:** Unknown beyond comments describing combinatorial axes and
degenerate fixtures.

**Decision:** Advertise only `grid_h`, `grid_w`, `motif_color`, and
`motif_rotation`. Require exact types and values; reject unknown controls.

**Why:** The palette aliases did not alter ordinary pixels; three controls were
singletons; invalid degenerates contradicted the stated domain; dimensions were
documented more broadly than the layout could construct. Color and rotation are
real visible variables, and the chosen dimensions are all constructively
supported.

**Alternative rejected:** Keep old axis names but label them diagnostic. This
would preserve a misleading public surface without adding training diversity.

**Probe:** Full legal boundary cross-product across default/easy/medium/hard:
4 bands × 2 heights × 3 widths × 2 color boundaries × 4 rotations = 192 cases,
all exact and lawful (`checks/schedule-probe.json`).

**Failure modes guarded:** ignored overrides, singleton pseudo-axes, accidental
acceptance of typos, and generation-time crashes after accepting a legal value.

## D3: Use a four-slot teaching schedule rather than independent shape sampling

**Prior choice:** Random 3–5-cell growth placed every source motif above the
anchor.

**Decision:** Cycle through `corner_l3_above`, `branch5_below`,
`corner_l4_left`, and `blob6_right`; offset the starting role by difficulty while
preserving complete four-role windows.

**Why:** All canonical motifs are corner-Ls above the anchor. Independent random
sampling could produce valid labels yet leave canonical-fitting shortcuts alive.
The schedule guarantees side and topology counterexamples in every lesson-sized
four-pair bundle.

**Alternatives rejected:**

1. **Pure random side/shape sampling.** More superficially diverse, but requires
   rejection/resampling and offers no per-lesson witness guarantee.
2. **Add only a below example.** Refutes `above_only` but not `corner_l_only`.
3. **Increase demonstrations.** More expensive and unnecessary once three of any
   four scheduled roles refute both declared rivals.

**Probes:** 80 cyclic windows (20 starts × 4 bands), every one of 320 possible
query holdouts, plus the 300-lesson source-bound census.

**Failure modes guarded:** ordered-only teaching success, query-position
sensitivity, and valid-but-ambiguous lessons.

## D4: Restrict production to four asymmetric connected template families

**Prior choice:** A random walk could make many 3–5-cell connected shapes,
including forms with accidental rotational symmetry or ambiguous analysis.

**Decision:** Use two corner-Ls, a branch, and a compact asymmetric six-cell
blob, each with all four quarter-turns.

**Why:** These shapes are independently recognizable, remain 4-connected,
exercise different crop dimensions/topologies, and give explicit witnesses for
the declared rivals. Their finite set makes exact validation and constructive
placement tractable.

**Alternative rejected:** Arbitrary polyomino enumeration. It would broaden the
domain but substantially enlarge placement, equivalence, and symmetry logic
without being needed to repair the demonstrated teaching defect.

**Known cost:** The generator covers a strict lawful subset of motifs accepted by
the Racket program. This is documented rather than presented as exhaustive.

## D5: Use four canonical dimension profiles

**Prior choice:** Easy emitted 11×12, hard 13×14, and medium mostly 11–13 by
12–14. Easy and hard had zero exact canonical-profile support in the 20-draw
baseline audit.

**Decision:** Schedule 13×13, 15×15, 13×15, and 15×17—the four canonical
height/width profiles—while still allowing each supported height and width in
any legal override combination.

**Why:** This guarantees exact canonical-profile support in every band and gives
sufficient margin for every rotated stamp.

**Alternative rejected:** Preserve the old broad 10–18 declarations. Most joint
values were not constructible under the old placement assumptions, and larger
sizes added no semantic branch.

**Failure modes guarded:** profile-floor misses and clipping near boundaries.

## D6: Enumerate legal placements instead of retrying random coordinates

**Prior choice:** Nested retry loops attempted motif and anchor positions and
could fail after many attempts.

**Decision:** Cache all legal `(anchor_r, anchor_c, source_r, source_c)` choices
for the requested grid, shape rotation, and assigned side, then sample one.

**Why:** Existence is known before sampling, exact overrides remain reliable,
and the output-stamp margin is established by construction.

**Alternative rejected:** Increase retry counts. That reduces but does not remove
failure probability and obscures whether a control combination is truly
supported.

**Failure modes guarded:** stochastic `ValueError`, clipped output, and partial
honoring of an accepted override.

## D7: Declare executable rivals and a lesson-identifiability hook

**Prior choice:** No semantic hooks, witnesses, rivals, or lesson checks.

**Decision:** Declare the same `above_only` and `corner_l_only` functions in
`SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`; map explicit
witnesses to them; require three correctly labelled demos that refute both.

**Why:** Both rivals fit all four canonical pairs. Naming and executing them turns
a narrative concern into a regression target and lets shared semantic tooling
score lessons directly.

**Alternative rejected:** Rely only on shape/side frequency. Frequency does not
establish that each assembled lesson contains a discriminating demonstration.

**Limits:** Passing these competitors is finite evidence only. It does not prove
there is no other plausible shortcut.

## D8: Separate authority, mirror, and independent oracle

**Decision:** Keep Racket as label authority; retain a production-local
`rule_mirror` for hooks; build `workspace/reference_probe.py` independently of
production geometry; require real-Racket parity in task tests.

**Why:** A mirror is useful for fast semantic hooks but could repeat the same bug.
The independent probe and real-Racket run provide two additional comparison
paths.

**Tests:** The 47 portable cases cover public declarations, four canonical pairs,
192 joint control boundaries, fail-closed invalid calls, 320 lesson rotations,
exact counterexamples, 640 generated samples, malformed/destructive inputs,
determinism, Python hash-seed independence, global-random isolation, and 37
real-Racket parity grids.

## D9: Retain interrupted evidence without using it as proof

The original before run and later redundant full-battery retries were interrupted
by outer execution limits. They remain under `checks/before/` and
`checks/after-final/`. Claims use only terminal reports: the completed 12/12
aggregate in `checks/after/`, fresh `checks/task-tests-final/`, fresh
`checks/required-rotations/`, the completed census, and fresh-packet replay.
This avoids turning checkpoint output into an unsupported completion claim.

## Native parametric design

Build `orientation_frame = fixed | source_side` in a separate native workspace.
The fixed setting returns the exact canonical bytes. The alternative first
locates the template relative to the anchor, binds above/right/below/left to
0/1/2/3 clockwise turns, and constructs an oriented crop. The existing four-stamp
assembly then consumes that crop and its new dimensions. Rectangular left/right
examples distinguish recomputed dimensions from stale original dimensions.
The supplied public-evaluation focus `142ca369` motivates deriving direction from
visible object/context relationships; this is inspiration, not verified lineage
or a claim of equivalent rules.

Use four mandatory demonstrations, one for each source side, plus up to two
optional examples. A three-demo prefix cannot explicitly cover all four side
branches with this one-template grammar; restricting queries would remove the
desired full-side transfer. Matched geometry pairs expose the effect of source
side while different template families prevent a fixed-crop shortcut. Construct
complete six-demo/four-query banks, independently shuffle the complete query
bank, and only then slice requested counts. Settings share input banks.

Extend only the native domain to 6..30 rectangular canvases and connected
monochrome templates with 2..14-cell bbox axes. The unique color-9 anchor is
separated from the template on one aligned cardinal side. Conservative margins
keep both settings' stamps in bounds; any same-color overlap follows canonical
nonzero-paste union semantics. Crop from motif cells, excluding the anchor.
The native alternative is a contextual orientation dependency, not a claim of
iterative state evolution. Focused tests, protected shortcut review, substantive
30x30 labels, native qualification, causal replay and public permutation checks
will establish reviewer readiness; owner acceptance remains separate.

## Native reviewer readiness

91 focused tests passed. The protected baseline shortcut audit refuted all 80
comparisons on demonstrations; an independent four-rival structural review
refuted 14 of 16 comparisons, with two finite-consistent comparisons and no
query conflicts. Twenty maximum-count/max-seed labels matched protected Racket.
Native qualification passed all four setting/seed jobs with 48 Racket evaluations.
Both causal counterfactuals were replayed against exact qualified programs.
Sixteen saved public views preserve paired query permutation, single-query
early-stop identity and private-field independence; four corruption probes
were rejected. The source inventory and checks retain exact bounded evidence.
This completes reviewer construction and self-review, not owner acceptance or
training admission. The owner must qualify and freshly accept the exact
integrated source.
