# Current notes: b8259d813f79

## Intended rule and authority

For every 4-connected nonzero object, erase the input and place one cell of the
same color at the floor midpoint of that object's tight bounding box. Canonical
rule hash: `60b82500e77c`. The Racket authority was not changed.

## Reversed baseline decisions

The v1.3.1 generator assigned a distinct color to every object and advertised
nine partly decorative controls. A 3,000-draw baseline probe found no repeated-
color disconnected objects, so “one center per color” fit both the canonical
pairs and every measured generated input. The v2.0.0 generator instead exposes
four exact observable controls (`grid_h`, `grid_w`, `n_blobs`,
`n_distinct_colors`) and constructively places all requested objects.

## Teaching design

A period-3 schedule alternates one canonical profile with two repeated-color,
asymmetric-witness profiles. Three executable canonical-fitting rivals are
tracked: global per-color center, rounded cell centroid, and upper bbox midpoint.
The retained easy seed `20261008`, sample index `1`, refutes all three under the
Racket authority. Reproducer: `workspace/shortcut_probe.py`; retained evidence:
`counterexamples/shortcut-{input,racket,probe}.json`.

## Verification and limits

Final generator SHA-256:
`04a460fa23de19ca3a1ac8d6f710b1798a4c55f415ddf07a76a72c3d856fd3c2`.
Battery 12/12 green; focused and portable tests 75/75; 300 production lessons
and 1,200 query rotations have zero ambiguity against declared rivals. The
ordinary grammar is intentionally limited to 3–4 compact objects, 2–3 colors,
and 3×3 or 2×4 bboxes. Finite named-rival results do not prove universal
identifiability.
## Current reviewer considerations

Source SHA-256: `04a460fa23de19ca3a1ac8d6f710b1798a4c55f415ddf07a76a72c3d856fd3c2`.

# Decisions for `b8259d813f79`

## D1 — Keep the selected Racket authority unchanged

**Prior choice:** the baseline did not pin `RULE_HASH` or provide a Python
mirror, so source/authority identity was implicit.

**Decision:** retain the canonical per-object rule and pin rule hash
`60b82500e77c`. Add a Python mirror and require parity on all four canonical
pairs and generated smoke inputs.

**Why:** the canonical outputs consistently collapse each 4-connected object
to the floor midpoint of its tight bbox. The defect was in the generated input
distribution and contract, not in the selected rule. The final battery's
`rule_smoke` and `authority_sync` stages are green; no Racket file changed.

## D2 — Replace probabilistic growth with constructive isolated footprints

**Prior choice:** random blob growth and placement attempted a requested count
but could produce fewer connected components through contact or failed placement.

**Decision:** place 3 or 4 nonoverlapping 3×4 footprints by deterministic
backtracking, then draw a connected five- or six-cell shape inside each.

**Alternatives rejected:** retrying random placement, accepting fewer objects,
or repairing contacts after generation. Those options make an exact `n_blobs`
axis probabilistic and complicate source-bound reproduction.

**Evidence/failure mode:** exact joint-boundary tests cover both blob counts,
both color counts, three dimension profiles, and all four difficulty values.
`self_check` rejects empty, merged, malformed, and center-colliding impostors.

## D3 — Reduce the public API to four exact observable axes

**Prior choice:** nine axes mixed real controls, aliases, decorative values, and
degenerates. Unknown values could be silently ignored.

**Decision:** expose only `grid_h`, `grid_w`, `n_blobs`, and
`n_distinct_colors`; all are observable from the returned grid. Reject unknown
or invalid values and allow every legal joint combination.

**Alternatives rejected:** retaining `palette_kind`, density, position bias,
texture aliases, or a shape-size range merely for nominal diversity. None was
needed to teach the rule, and several could not be verified exactly from an
input. Degenerates are excluded from the ordinary contract rather than silently
accepted by `self_check`.

## D4 — Use a period-3 semantic schedule

**Decision:** schedule `canonical`, `witness_a`, `witness_b` by
`sample_index % 3`. Canonical profiles preserve the imported scale/manifold;
both witness profiles repeat colors and include the same asymmetric 2×4 object.

**Why three slots:** lessons use three demonstrations. A four-pair materialized
lesson may hold out any pair as query. With two witness slots in every four
consecutive samples, every three-demo rotation retains at least one witness.
A single witness slot per period would fail when that item became the query.

**Evidence:** focused tests exhaust cyclic windows and query positions;
`lesson-census-schedule.json` exhausts the three declared start residues across
all bands at seed 0 and scores all 36 query rotations.

## D5 — Preserve a measured canonical floor without making all data canonical

**Decision:** canonical profile every third sample; `MIN_STRICT_FRAC = 0.20`.

**Rationale:** the imported examples use three distinct colors, three objects,
3×3 bboxes, and one of four dimension pairs. That support is important for
continuity, but making it universal recreates the shortcut. The final semantic
census measured 198/600 strict hits (33.0%), and profile-floor measured 21/60
exact profiles with a hit in each band.

## D6 — Declare the three strongest canonical-fitting rivals

1. `one_center_per_color`: ignores connectivity and emits one center globally
   per color.
2. `nearest_cell_centroid`: uses rounded component centroid rather than bbox.
3. `upper_bbox_midpoint`: uses ceil/upper midpoint on even bboxes.

All fit 4/4 usable canonical pairs. Repeated colors refute the first; the fixed
asymmetric 2×4 shape refutes the latter two. The retained easy seed `20261008`,
sample index `1`, refutes all three under Racket.

**Alternative rejected:** declaring only the shortcut caught by current
canonical colors. The geometry alternatives are equally plausible and cheap to
cover once even bboxes are introduced.

## D7 — Require query rotations, not only ordered production

**Decision:** lesson reports use three demonstrations, one query, and
`rotation_policy=require`. Report ordered production and query rotations
separately.

**Why:** a deterministic schedule can look identifiable in its default query
position yet fail when a witness is held out. Required semantic smoke, a
300-lesson census, and declared-period enumeration all passed.

**Limits:** these checks cover the declared rival set and sampled/fixed schedule
support. They do not prove universal induction or every seed.

## D8 — Add a reusable source-bound shortcut probe

`workspace/shortcut_probe.py` discovers the current generator's
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, verifies canonical fit, checks a
retained Racket receipt, and measures finite default-domain refutations. It
fails if declarations drift, the source hash no longer matches the receipt, or
the retained witness stops refuting a shortcut.

The exact counterexample and receipt live under `counterexamples/`; full review
logs remain under `checks/` so future agents can rerun the small probe without
reconstructing this review.

## D9 — Known domain restrictions

Ordinary data has 8..14 rows, 10..16 columns, 3..4 objects, 2..3 colors, five or
six cells per object, and 3×3 or 2×4 bboxes. This is narrower than the complete
Racket domain. The restriction is intentional: it makes all controls jointly
constructive and keeps every lesson compact enough to inspect.

Potential undeclared shortcuts remain possible. The current evidence bounds
claims to the three named rivals and tested schedules; it does not claim formal
uniqueness of the natural-language rule.
