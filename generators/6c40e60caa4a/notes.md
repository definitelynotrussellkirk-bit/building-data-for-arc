# Working notes: 6c40e60caa4a — Deepest Seeded Frame

## Intended rule

Color `1` components are rectangular frame outlines. A color `2` seed makes every
containing frame in its non-branching nesting chain seeded. Fill the interior of
the deepest seeded frame in **each independent chain** with color `3`; preserve all
other cells. The canonical normalized rule hash is `e82c2d54609b`.

## Current generator contract (v2.0.0)

- Lawful scene profiles are `single`, `nested`, and `mixed` on 11–15 row/column
  grids with input palette exactly `{0,1,2}`.
- `self_check` reconstructs exact frame perimeters, containment chains, one seed
  per root, and the allowed chain signatures `(1)`, `(2)`, and `(1,2)`.
- Exact controls are `grid_h`, `grid_w`, and `scene_kind`; unknown, non-exact,
  wrong-type, and out-of-range values are rejected rather than coerced.
- Ordinary lessons use `single → mixed → nested → mixed`, five demonstrations
  plus one query. Difficulty changes keyed layout draws but not the semantic
  profile scheduled at an index.
- Declared rivals are `fill_all_seeded_frames` and
  `global_smallest_seeded_frame`. The latter fits every canonical training pair,
  so mixed scenes are mandatory teaching witnesses.

## Reversed decisions

The baseline used one oversized nested layout, surface-level palette validation,
and dead/singleton override axes. That was replaced by canonical-sized semantic
profiles, a structural validator, and three observable controls after the before
battery failed lint, defect lint, override, and authority synchronization.

An initial repaired schedule used one mixed profile per three draws. The first
300-lesson census found one query-rotation ambiguity after duplicate suppression
(seed `1144200380`, medium lesson `48`): sample `53` was rejected, and rotating
the only surviving mixed pair into the query left the global-smallest shortcut
unrefuted. The final four-slot schedule repeats `mixed`; a regression test proves
that any two rejected raw draws still leave at least two mixed witnesses in the
six accepted pairs.

## Evidence and limits

- Final generator SHA-256:
  `c3ef815111e2bfd816c98552ba722680fa525cb4386be9640ff1c20d324924cb`.
- Final battery: 12/12 green; selected tests: 39/39 pass.
- Final census: 300/300 production lessons and 1,800/1,800 query rotations clean
  against the declared rivals, with 949 unique inputs.
- Exact Racket-backed shortcut witness:
  `counterexamples/global-smallest-seeded-frame.json`.
- The selected duplicate Racket `target_code` was byte-synchronized to unchanged
  canonical `raw_code`; no rule semantics changed.
- Finite declared-rival checks do not prove unique induction against every
  possible hypothesis. The grammar intentionally excludes branching frame trees,
  multiple seeds in one root, and arbitrary frame sizes beyond the three profiles.
## Current reviewer considerations

Source SHA-256: `c3ef815111e2bfd816c98552ba722680fa525cb4386be9640ff1c20d324924cb`.

# Decisions for `6c40e60caa4a`

## D1 — Preserve the canonical rule; repair the input contract

**Prior choice:** one large nested scene with shallow palette checks.

**Decision:** keep rule hash `e82c2d54609b` unchanged and make the generated
domain explicit: exact rectangular color-1 frames, non-branching chains, exactly
one color-2 seed per independent root, and only `single`, `nested`, or `mixed`
chain signatures.

**Why:** the baseline's blank/off-grammar acceptance made every downstream
semantic claim weak. Structural validation also gives `observe_overrides` and the
rival functions one shared analysis path.

**Rejected alternatives:** patch only the blank-grid case; accept arbitrary
frame forests; add deeper/branching structures immediately. The first leaves the
root defect intact, while the latter two expand beyond canonical evidence and
would need new authority and teaching analysis.

**Failure mode/limit:** lawful-but-unmodeled arrangements are intentionally
rejected. This is a narrow training distribution, not a general frame parser.

## D2 — Use canonical-sized semantic profiles

**Decision:** default `single`, `nested`, and `mixed` grids are 11×11, 12×12,
and 13×13; exact `grid_h`/`grid_w` controls permit 11–15.

**Why:** each profile is compact, visibly rule-bearing, and hits the battery's
canonical-size/palette floor. Mixed horizontal and vertical layouts retain a
one-cell separator between roots.

**Rejected alternatives:** retain 15–21 grids; vary frame dimensions without
semantic purpose; make every scene mixed. Oversized blank margins dilute the
signal, arbitrary size variation adds nuisance entropy, and mixed-only lessons
hide the simpler base cases.

**Probe:** final battery `profile_floor`, `dist_gate`, `diversity`, and grammar
stages are green; task tests compare canonical examples exactly.

## D3 — Advertise only exact, observable controls

**Prior choice:** multiple dead or singleton axes, with behavior not faithfully
observable.

**Decision:** expose only `grid_h`, `grid_w`, and `scene_kind`; reject unknown
keys, booleans, numeric strings, floats, and out-of-range values before drawing.

**Why:** these three controls alter the returned grid independently and can be
recovered exactly through `observe_overrides`.

**Rejected alternative:** permissive `int(...)` coercion. It makes an exact
control silently differ from the caller's value and is the same defect found in
random audit target `16491c603ea5`.

## D4 — Separate semantic scheduling from layout randomness

**Decision:** `schedule_profile` determines scene type, while a difficulty-keyed
RNG changes placement/orientation inside that profile. Same seed/index/band is
fully deterministic, fresh, and global-RNG pure.

**Why:** difficulty bands must not be byte-identical, but changing the lesson's
semantic witness by band would make curriculum analysis harder.

**Rejected alternative:** let difficulty select the profile. That can remove a
required rival-refuting witness from a lesson.

## D5 — Repeat the mixed witness in a four-slot cycle

**Initial repaired choice:** `single → nested → mixed`.

**Failure:** intermediate source
`22aa9de6132024436b1d7b4fadc57032ea421fae58a2876c55338d9ee2500948`
passed the ordinary 300 lessons but failed 1 of 1,800 rotations. In medium lesson
48 (seed `1144200380`), duplicate sample 53 was rejected; rotating sample 50 into
the query left no mixed demonstration, so `global_smallest_seeded_frame` survived.

**Final choice:** `single → mixed → nested → mixed`, five demonstrations and one
query. A focused combinatorial test removes any two of the first eight raw draws
and verifies that the six accepted profiles still contain at least two mixed
witnesses. The production-materializer regression retains the exact failing seed.

**Why:** mixed scenes are the only declared witness that forces independent
per-chain selection. Two copies are needed because one can be rejected and one
can be the query.

**Final probe:** 300/300 production lessons and all 1,800 query rotations were
clean against every declared rival, with 949 unique generated inputs.

## D6 — Declare plausible rivals and keep an authoring probe

**Decision:** declare `fill_all_seeded_frames` and
`global_smallest_seeded_frame` in both semantic and lesson contracts; declare the
latter as a canonical shortcut. Retain
`workspace/probe_declared_rivals.py`, which discovers these mappings dynamically
rather than hard-coding names.

**Why:** individual valid grids do not establish a teachable lesson. The probe
first checks whether a claimed shortcut really fits every canonical training pair,
then searches generated inputs for a disagreement.

**Limit:** the fast probe uses the Python mirror. Retained claims are confirmed
with supported Racket `apply`; finite declared rivals do not enumerate all rules.

## D7 — Synchronize duplicate authority text without changing semantics

**Decision:** set the selected Racket `target_code` text byte-for-byte equal to
its unchanged `raw_code`.

**Why:** authority sync failed because two representations of the same rule had
drifted in comments/format. The raw code SHA-256 remains
`0113985cefa1eef2b3011482465b19240b41bc81186e5dbf38dd5bb7135cccea`;
after synchronization the target has the same digest.

**Rejected alternative:** rewrite Racket logic to mirror generator restrictions.
The Racket authority defines the transformation, not the generator's sampling
domain, and rule-smoke already showed its outputs were correct.

## Native parametric family review — 2026-10-25

### P1 — Preserve the canonical default and vary frame selection scope

The native adapter keeps `frame_scope=deepest` byte-identical to the selected
canonical Racket program.  The nearby `frame_scope=all_seeded` setting reuses the
same seeded-frame analysis but selects every seeded frame rather than only the
innermost seeded frame in each chain.  The variant therefore changes a genuine
input-derived intermediate (the selected bounding-box set), not a cosmetic scalar.

Inputs are setting-independent.  The family supports 2–6 demonstrations and 1–4
queries, with four private controller-side queries.  The fourth query is a 30×30
scene containing a nested seeded chain plus an independent seeded frame; it makes
both the scope distinction and per-chain reasoning visible without changing the
canonical generator's ordinary domain.

### P2 — Retained adversarial and causal evidence

Bounded self-review tested the opposite scope, identity, global-smallest selection,
and fixed-first-deepest shortcuts over seeds 0 and 17 and demonstration counts
2, 3, and 6.  No checked rival fit all demonstrations while changing a query.
A protected Racket witness on the nondefault setting replaces the all-seeded
intermediate with the deepest-only set and changes the final output.  Public
projection checks cover all 16 one-query views and verify first-turn invariance.

The current manifest and authoring-preflight receipt bind the exact adapter,
programs, implementation, tests, and evidence bytes.  This is reviewer-ready
prototype evidence only: owner qualification, fresh acceptance on integrated
source, and any training admission remain separate.
