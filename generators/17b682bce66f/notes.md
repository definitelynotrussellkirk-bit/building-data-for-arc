# Review notes: 17b682bce66f, version 3.1.0

## D1 — finite-template concentration (reproduced)
The incoming version has exactly 199 possible raw inputs and ten complete-scene
translation classes. A 300-row seed prefix covers all normalized scenes in the
next 300 rows in every band. Retain the finite bank as canonical/branch witnesses,
not the whole curriculum. Add connected asymmetric rooted polyomino clouds and
independent legal source/anchor positions. See the returned review's
`checks/baseline_exact_capacity.json`, `checks/baseline_census.json` and
`checks/final_census.json`; reusable commands are in `workspace/HANDOFF.md`.

## D2 — preserve the authority and exact witness predicates
The rule writes each anchor in row-major order, then max-merges its paint. A
later stamp may overwrite an earlier anchor, and a later anchor write may lower
previous paint. Do not substitute an anchor-protected or commutative renderer.
No Racket text, rule hash, approval ledger or existing canonical signature was
changed. Existing explicit fixed-profile overrides retain their geometry.
`strict_canonical_like` exposes the pre-existing exact predicate to the shared
gate; it does not relabel procedural examples as canonical.

## D3 — procedural support is deliberately bounded
Keep the existing 8..16 canvas, 4/5-cell clouds within radius three, 4-connected
source-plus-reference, asymmetric rotations, three/four distinct anchor colors,
and full in-bounds stamps. There is no clipping, silent fallback or global RNG.
A fixed seed/index has the same forced-procedural scene across difficulty bands;
only the mixture changes. The stress evidence therefore has 6,000 invocations
but 2,000 distinct inputs, not 6,000 independent scenes.

## Limitations
This is input-support and reference-parity evidence, not a measured Qwen model
improvement or a proof of lesson identifiability. Rare bounded-generation
exceptions remain explicit. The retained canonical-derived branch must not be
used as an independent held-out evaluation split.
## Current reviewer considerations

Source SHA-256: `1be83f9295055acdf8e86a1ce2258ad7c70891978251b31438426049ae953876`.

# Decisions: 17b682bce66f

Source identities and exact measurement protocols are in `REVIEW.md`. Decisions
below concern the assigned generator only; shared and audit-only sources remain
unchanged. This is a decision record and experimental summary, not a private
reasoning transcript.

## D1 — replace a closed template curriculum, not its witnesses

**Original rationale:** incoming documentation explicitly retained whole linked
canonical scenes and five branch-isolating scenes so canonical morphology and
collision topology would remain common. That rationale is sound for witnesses,
but it accidentally became the entire support: exactly 199 inputs and ten
normalized layouts.

**Choice:** preserve all ten fixed scene definitions, their exact observable
signatures, and their explicit override names. Add one procedural profile whose
relative geometry and source shape vary. The profile classifier recognizes exact
fixed signatures first and calls other structurally lawful scenes procedural.
The canonical predicate is not broadened.

**Rejected alternatives:** larger translations alone still teach a finite layout
table; removing all fixed cases loses reliable canonical/branch coverage; a large
precomputed bank delays rather than repairs the support problem; global color
permutation is not a nuisance transform here because anchor colors encode
rotation and paint commands. Whole-grid rotations can change row-major collision
order, so they are not assumed safe label-preserving augmentations.

**Evidence:** exhaustive fixed support enumeration; seeded before/after census;
unit tests preserving fixed-profile round trips and all retained witnesses.
The measured improvement is support diversity, not learned algorithmic skill.

## D3 — source-cloud grammar

**Original constraints retained:** four or five color-8 cells, one color-9 root,
source-plus-root 4-connectivity, offsets within three cells of the root, spanning
both axes, and four distinct quarter-turn forms. The exact pedagogical reason for
each original numeric bound is not known; no claim is made that these bounds are
optimal.

**Choice:** grow rooted polyominoes within the existing radius, remove the root to
obtain offsets, and reject symmetric/degenerate results. Frontiers are sorted
before seeded selection. Cloud size is sampled once per proposal; at most 128
whole-cloud proposals are allowed. Failure raises explicitly rather than
silently returning a fixed scene.

**Alternatives:** independent cyan noise would violate the connected-source
lesson grammar; a tiny hardcoded cloud set would leave another memorization
bottleneck; unrestricted size/radius could create new difficulty or clipping
semantics beyond this review's evidence.

**Checks/limits:** deterministic replay and morphology tests; 2,000 distinct
forced-procedural stress inputs; real authority parity on the described subset.
Rooted polyomino growth is not uniform over shapes. No claim of shape-uniformity
or exhaustive stochastic reliability is made.

## D3 — canvases, reference and anchors

**Choice:** sample height and width independently in 8..16, using the inherited
canvas bounds. Choose the reference among centres fitting the entire source;
choose three or four distinct anchor colors from 2..5 and legal centres fitting
their entire rotated stamps. Occupied input cells cannot be reused. Reference
location, anchor positions, and relative layout are no longer a shared scene
translation. Positions are sampled sequentially and thus are not independent
in the probabilistic sense after the occupancy constraint.

**Preserved cases:** paint-paint overlap, stamp-anchor interaction, adjacency,
edge-touching complete stamps, and all command subsets are permitted. There is
no stamp clipping. The fixed branch witnesses retain predictable access to these
behaviors even when procedural draws are sparse.

**Failure policy:** lack of a legal centre or an accidental exact fixed-signature
match raises a visible error. The override is never quietly mislabeled procedural.
No such exception was seen in the final stress run. These guards make failures
inspectable; they are not a proof that every possible seed succeeds.

## D1 — difficulty mixture

Final canonical / fixed-generalized / procedural weights are **40/20/40% easy**,
**20/20/60% medium**, and **12.5/12.5/75% hard**. They retain canonical examples and
explicit branch access while increasingly allocating draws to novel scenes.
The original rationale for band-specific witness weighting is retained; these
new exact weights are reviewer choices, not empirically tuned model optima.

Forcing the procedural profile yields the same scene for a seed/index across all
three bands. This keeps overrides reproducible and makes mixture the only band
difference for that family. Do not count those three calls as independent
samples. Truly difficulty-conditioned cloud complexity is deferred until there
is a measured need rather than arbitrary extra knobs.

## D2 — authority and canonical contract

No Racket code, rule hash, authority source, approval ledger, or canonical input
was edited. The existing mirror and source authority retain sequential
row-major anchor writes and paint max-merging. Anchors are not globally
protected. Documentation that implied universal anchor preservation was clarified.

The old `is_canonical_profile` predicate already expresses exact translated
canonical membership. `strict_canonical_like` simply exposes it to the shared
semantic gate. This repairs missing contract discovery instead of weakening
semantic checks to green the battery. The canonical-derived branch remains
teaching material, not independent held-out data.

## Tests, reusable tools and scope

Test loading now works both from the source tree and the true staged layout.
Regression tests were first run against the missing behavior; retained red logs
show the failures. `review_probe.py` stages portable runtimes, measures normalized
support, and compares the actual Racket authority. Its 40% medium novelty threshold
is an opt-in local policy, not a universal requirement for every ARC generator.
`fixed_bank_capacity.py` separates exact support enumeration from Monte Carlo
coverage. `audit_findings.py` keeps counterexample grids for the two audit targets.
`verify_fixture_repair.py` tests the shared fixture proposal in a temporary copy.

The shared fixture problem T1 is not patched in the repository because that is
outside the immutable assignment. The isolated repair, not just prose advice,
is supplied for maintainer integration. Audit-only findings likewise remain
findings rather than cross-assignment source changes.

## S1 — stop without using hidden feedback

The required Python solve was prepared only after the generator was frozen.
Earlier rule exposure is declared. The visible examples determine the tested
rotation mapping but do not distinguish several collision policies; two distinct
predictions remain for masked query 2. `solve/public_probe.py` records that public
ambiguity without opening query labels. The submitted one-revision solver is
retained, rather than retrospectively tuned to authority or hidden answers.
The episode is not training-admitted and cannot demonstrate blind generalization.
