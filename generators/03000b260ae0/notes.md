# Current generator account: 03000b260ae0

## Intended rule

The first 4-connected multi-cell nonzero component containing color 9 is the
template. Its anchor is the **last color-9 cell visited by the canonical BFS
component traversal** (row-major component discovery; neighbor order up, down,
left, right). Every isolated singleton 9 is a placement marker. Align the
anchor to every marker, count translated-template coverage on a fresh canvas,
and map counts `1 -> 2`, `2 -> 3`, and `>=3 -> 4`.

`RULE_HASH = "e140a6400a02"` pins the unchanged canonical Racket authority.

## Current distribution (v3.1.0)

Lawful inputs are 8–14 by 10–17 grids with one connected 4–6-cell template and
1–5 isolated markers. The exact public axes are `grid_h`, `grid_w`,
`n_markers`, `overlap={disjoint,double,triple}`, and
`texture={monochrome,multicolor,multi_anchor}`. All accepted explicit controls
are observable from the pixels and replay exactly; only marker counts too small
for requested overlap are explicitly rejected as an `n_markers`/`overlap`
conflict.

Ordinary sample indices cycle through four profiles:

1. `canonical_anchor`: canonical dimensions/palette structure, two markers,
   disjoint copies, one template 9;
2. `double_multi_anchor`: a double-overlap witness plus more than one template 9;
3. `triple_multi_anchor`: a triple-overlap witness plus more than one template 9;
4. `triple_multicolor`: a triple-overlap witness with body-color variation.

A lesson has four demonstrations plus one query. Any five consecutive schedule
slots contain all four profiles, and task tests check every cyclic start and
every possible query position. The generator declares executable rivals for
binary union, overlap capped at two, and first-template-9 anchoring.

## Reversed baseline choices

- **One template 9 only -> one or more template 9s.** The old `self_check`
  rejected a canonical input containing two 9s in the template. The new parser
  accepts it and selects the last BFS-visited 9, matching all five canonical
  labeled pairs.
- **Texture aliases/`no_markers` -> orthogonal lawful textures.** The previous
  `texture` mixed overlap settings with body-color settings and advertised a
  degenerate that violated its own invariant. The replacement separates
  multiplicity from appearance and emits no intentionally unlawful default.
- **Best-effort overrides -> exact contract.** The old declared ranges were
  wider than its draw ranges, unknown keys were swallowed, and many axis
  combinations were inert or invalid. Validation is now strict, and the full
  after-gate exercised 26,010 override draws with zero findings.
- **Random teaching support -> scheduled witnesses.** Canonical examples admit
  the shortcut “paint every copy-covered cell red.” Double and triple overlap
  plus multi-anchor profiles now refute this and the other declared rivals in
  every tested query rotation.
- **No canonical profile anchor -> one canonical-like slot.** The first repair
  draft taught semantics but missed the profile floor. The current anchor slot
  restores canonical dimensions, palette cardinality, and coarse object/color
  roles without dropping overlap witnesses from a five-pair lesson.

## Verification and retained evidence

Final generator SHA-256:
`c2212a4732610e17b7f84a4374bd6c0c2dabad040d5d386883e867c02fdfa4cb`.

- 70 task-local tests pass in the portable task-test runtime.
- All 12 after-battery stages pass under required query-rotation policy.
- A 300-lesson census (100 per band) materialized 1,500 unique pair inputs and
  checked 1,500 query rotations with zero declared-rival ambiguities.
- `counterexamples/binary_union_double_overlap.json` is an exact 8x10,
  Racket-verified counterexample to the strongest canonical shortcut.
- `workspace/probe_shortcuts.py` rematerializes that source-bound witness.

## Known limits / open findings

The rival set is finite; passing it does not prove unique induction against all
possible hypotheses. Ordinary construction keeps every translated copy fully in
bounds, so it does not sample clipping behavior, although all canonical examples
also use complete copies and `strict_canonical_like` accepts every canonical
input. The four-slot schedule is explicit in `SCHEDULE_PROFILES` but deliberately
does not declare the reserved `LESSON_SCHEDULE_PERIOD`: the current semantic gate
turns an unenumerated declaration into a warning. Exhaustive cyclic-start tests
and the larger randomized census are retained instead. No Racket authority was
changed.
## Current reviewer considerations

Source SHA-256: `c2212a4732610e17b7f84a4374bd6c0c2dabad040d5d386883e867c02fdfa4cb`.

# Decisions for 03000b260ae0

## D1 — Preserve the canonical Racket rule

**Choice.** Change only the generator distribution and tests; pin
`RULE_HASH = "e140a6400a02"`.

**Reason.** Direct replay of the five labeled canonical pairs showed the selected
canonical rule is coherent. The defects were in input parsing, distribution, and
teaching evidence, not in the authority.

**Rejected alternative.** Rewriting the Racket rule around the baseline's
“exactly one template 9” assumption. That would contradict canonical train pair
2 and change the task rather than repair the generator.

**Evidence/failure mode.** Baseline self-check rejection is in
`checks/before/checks/03000b260ae0_before_selfcheck.log`; authority-sync and 120
Racket applications pass under `checks/final-battery/`.

## D2 — Define the anchor as the last BFS-visited template 9

**Choice.** Parse one multi-cell nonzero component containing at least one 9; use
the last 9 in the authority-compatible BFS order as anchor. Other singleton 9s
are markers.

**Reason.** This is the only tested interpretation that accepts and reproduces
all canonical examples, including the multi-9 template. It also provides a
meaningful anchor-selection rival.

**Rejected alternatives.** Exactly one template 9 (canonical rejection), first
template 9 (wrong on generated multi-anchor witnesses), or row-major-last 9
without component traversal (not the authority's semantics).

**Probe.** Canonical replay tests plus `first_template_nine` semantic rival.

## D3 — Make overlap an exact geometric property

**Choice.** Construct complete in-bounds translated footprints and solve for
maximum multiplicity exactly 1, 2, or 3 according to `overlap`.

**Reason.** The baseline could satisfy stacking attempts inconsistently and did
not expose an observable contract. The count palette is the task's core concept;
requested overlap must actually appear on canvas.

**Rejected alternatives.** Random placement followed by hoping for overlap;
clipped copies whose requested multiplicity occurs only outside the grid; or
silently reducing requested overlap.

**Failure mode/limit.** Constructive search can fail only after exhausting a
bounded lawful search and then raises. Ordinary data intentionally omits clipping;
that is documented rather than silently conflated with exact overlap.

## D4 — Separate appearance from overlap

**Choice.** Replace the old mixed `texture` values with
`monochrome|multicolor|multi_anchor`; keep overlap on its own axis. Remove
`no_markers` from the accepted domain.

**Reason.** The old `texture` duplicated overlap and made joint overrides inert.
`no_markers` violated the selected task's own marker invariant and produced a
blank, uninformative target.

**Rejected alternative.** Keep degenerate textures as “valid but special.” The
after policy requires lawful inputs and truthful controls; intentionally invalid
boards belong in explicit negative probes, not production generation.

## D5 — Add a canonical-like anchor profile

**Choice.** One schedule slot uses a canonical dimension/profile, two markers,
monochrome body color 7, and disjoint copies.

**Reason.** The first semantic schedule passed rival checks but failed the
canonical profile floor and coarse structure comparison. The anchor profile
restores canonical linkage while the other slots carry counterexamples.

**Rejected alternatives.** Make every sample canonical-like (would starve
multiplicity/anchor witnesses) or rely on random exact profile hits (insufficient
per-band support).

**Evidence.** Final profile floor: all bands supported, 17 exact hits and 27
envelope hits across 60 draws.

## D6 — Use a four-profile, five-pair teaching window

**Choice.** `EXAMPLES_NEEDED=4` and a four-slot cycle:
`canonical_anchor`, `double_multi_anchor`, `triple_multi_anchor`,
`triple_multicolor`.

**Reason.** With four demonstrations plus one query, any five consecutive slots
contain all four profiles. The duplicate profile in the fifth slot ensures that
holding out any single query still leaves enough evidence against the finite
rival set.

**Rejected alternatives.** A two-slot schedule lacked canonical linkage; a
three-slot schedule could lose a necessary witness under query rotation; purely
random lesson assembly made guarantees seed-dependent.

**Tests.** Every cyclic start, every query position, every band; 300-lesson census
with 1,500 rotations.

## D7 — Declare executable rivals and witnesses

**Choice.** Retain `binary_union`, `cap_at_two`, and `first_template_nine`, with
witnesses for double overlap, triple overlap, and multiple template 9s.

**Reason.** `binary_union` and `cap_at_two` both fit every canonical pair. They
must be explicitly refuted before generated lessons can be called teachable.
`first_template_nine` protects the newly supported multi-anchor semantics.

**Limit.** This is finite falsification, not proof of unique human or model
induction. Unknown undeclared rivals remain possible.

## D8 — Enforce exact overrides and strict scalar validation

**Choice.** Validate seed/sample index/difficulty and all override types/domains;
reject unknown keys; recover every accepted axis from pixels; declare only the
low-marker/overlap conflicts.

**Reason.** The baseline accepted typos and invalid sample-index scalars, rejected
values inside advertised domains, and had inert combinations.

**Evidence.** Final override gate: 26,010 draws, 270 declared conflicts, zero
findings. Task tests include domain corners, replay, invalid types, and unknown
keys.

## D9 — Do not declare the reserved schedule period yet

**Choice.** Keep the four-profile tuple explicit and exhaust its cyclic starts in
task tests, but omit `LESSON_SCHEDULE_PERIOD`.

**Reason.** The current semantic gate reports a warning whenever a declared
period was not separately enumerated; after-phase policy treats warnings as not
fully green. The normal census does not enumerate the reserved period flag. The
schedule itself remains testable through `SCHEDULE_PROFILES` and
`schedule_profile`.

**Rejected alternative.** Suppress the warning in reports or claim period
coverage from random sampling. Instead, document the tool interaction honestly
and retain exhaustive local tests plus the required 300-lesson rotation census.

## D10 — Add reusable authoring evidence

**Choice.** Add `workspace/probe_shortcuts.py` and a compact source-bound
counterexample JSON.

**Reason.** Future reviewers can rematerialize the strongest shortcut witness
without reverse-engineering test internals. The script labels its Python output
as a mirror and requires separate supported `arcpuzzles apply` validation.
