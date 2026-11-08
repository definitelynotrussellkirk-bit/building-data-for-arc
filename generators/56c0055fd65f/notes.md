# Working notes: 56c0055fd65f

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `95e384de3665722c749cfb6772ea776d5a0298d001edf6382021be53737acf1e`.

# Decisions: 56c0055fd65f

## D1 — keep the topology rule and Racket authority unchanged

**Original rationale:** retained evidence says all five canonical examples are
solved by counting enclosed zero-background regions in each yellow component,
with 0/1/2 holes mapped to 2/3/8. Authority parity and exact synchronization
were already green for the selected task.

**Decision:** no Racket edit. Keep `RULE_HASH = "d0be87fb4806"` and verify the
Python mirror against the canonical authority.

**Alternatives rejected:** changing the oracle to match a morphology lookup, or
adding behavior for unrelated hole counts. Both would alter a correct task
rather than improve teaching data.

**Probe / failure mode:** after battery rule-smoke and authority-sync are green.
The finite generator grammar still covers only exactly one 0-, 1-, and 2-hole
component; behavior outside that grammar is not claimed.

## D2 — devote one of four profiles to literal canonical morphology

**Original rationale:** version 2 made every ordinary row a strong shortcut
counterexample by pairing 0- and 1-hole components with equal area and bounding
box. That was useful, but it eliminated the canonical solid 2x3 0-hole body from
ordinary sampling while calling the whole grammar canonical-like.

**Decision:** profile 0 is now the literal canonical solid/ring/two-hole triple,
unrotated, and appears at the existing 25% schedule rate.

**Alternatives considered:**

1. Keep all four profiles noncanonical. Rejected because canonical support was
   only nominal and the profile-floor check could not guarantee the actual
   morphology.
2. Add a fifth profile. Rejected for this repair because it would change lesson
   period and require redesigning the 3-demo/1-query curriculum.
3. Make every row canonical. Rejected because area, box, and template shortcuts
   would again fit all training data.

**Probe / failure mode:** `test_profile_zero_replays_canonical_component_morphology`
checks exact areas and boxes. Profile 0 intentionally does not refute canonical
morphology shortcuts by itself; the other three schedule rows do.

## D3 — retain three equal-area/equal-box topology witnesses

**Original rationale:** all canonical pairs admit simple area, bounding-box, and
normalized-template lookup rivals. Equal-area/equal-box 0/1 pairs make the
correct distinction topological rather than geometric size lookup.

**Decision:** profiles 1–3 retain paired 0/1 shapes with the same area and box,
while the two-hole branch remains present in every row.

**Alternatives rejected:** relying on only one witness row. A single witness can
become the held-out query; using three means any 3-of-4 rotation still contains
at least two witnesses.

**Probe / limitation:** task tests iterate the generator's actual
`CANONICAL_SHORTCUTS`; the 100-per-band census tests declared competitors only.
An undeclared contrived rival may still exist.

## D4 — separate morphology scheduling from semantic layout scheduling

**Original rationale:** version 2's profile selected both shape and a fixed
corner map. Across seeds, a given shape profile always placed hole-count roles
in the same vertical order, creating a learnable position/profile correlation.

**Decision:** use `(seed + sample_index) % 4` for layout, independent of
`sample_index % 4` morphology. Four role maps move each branch through different
slots, while a seed offset lets every fixed morphology occupy all four layouts
across generated lessons.

**Alternative rejected:** independently randomize every row's role map. An
intermediate attempt made the lesson hook fail on some query rotations because
three demonstrations did not reliably vary positions. The final deterministic
cycle gives both variation and coverage. That transient console output was not
retained; the TDD red run and final exhaustive rotation probe are retained.

**Probe / limitation:** `checks/schedule-stress.json` reports four orders for
each morphology across 40 seeds and zero failures over 4,320 rotations. Within a
single seed, morphology and layout both advance cyclically with a fixed offset;
indices are not learner-visible, but this is still a finite schedule.

## D5 — use constructive separated slots rather than backtracking

**Original rationale:** retained notes record that tighter dimensions and
candidate placement caused boundary rejections. Exact advertised overrides must
be reliable and bounded.

**Decision:** partition each axis into two 5-cell bands separated by at least one
blank row/column. Randomly distribute extra margin/gap space and horizontally
jitter each pattern inside its slot.

**Alternatives rejected:** unbounded rejection sampling and reducing the honest
11..18 dimensions. The former harms reproducibility; the latter discards valid
coverage.

**Probe / limitation:** all 4,608 exact override combinations pass. Components
remain top-aligned inside their local slots, so the generator does not claim
uniform free placement over the whole grid.

## D6 — make canonical-data tests portable

**Original rationale:** unknown; the imported test used a repository-depth guess
that happened to work in one layout.

**Decision:** use `reviewer_support.find_root` and `canonical_pairs`, as required
by the portable task-test runtime.

**Alternatives rejected:** copying canonical JSON into the test, or adjusting a
hard-coded parent count. Both would be fragile or duplicate authority data.

**Probe:** baseline portable task-test preflight failed; the final staged command
runs and passes 22 collected cases. The runner intentionally collects the same
11 logical tests from the selected task and frozen fixture namespaces.

## D7 — preserve the four-profile lesson period

**Original rationale:** three demonstrations plus one query need at least four
morphologies so template lookup cannot simply replay a demonstrated shape.

**Decision:** retain period four and prove all four holdout rotations.

**Known limitation:** a 3-demo + 2-query assembly wraps on the second query, so
that query repeats profile 0. `solve/summary.json` reports this honestly. Adding
multi-query novelty would require a longer profile schedule and a new design,
not a silent local tweak after final checks.
