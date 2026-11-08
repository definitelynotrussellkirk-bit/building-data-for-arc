# Working notes: a286b2610efc

## 2026-10-02 review

The prior description said each isolated domino “grows by one cell.” That is only true for a boundary-flush pair. The canonical rule evaluates every length-3 window against the original input; an interior `0,v,v,0` pair matches two windows and grows on both sides to length 4. The old generator frequently emitted such interior pairs but neither named nor scheduled this branch, and its self-check accepted unrelated impostors.

The replacement generator uses a narrow, linked teaching grammar:

- exactly two distinct colors, each occurring in one straight adjacent pair;
- exactly one horizontal and one vertical pair;
- both pairs share one layout class (`edge` or `interior`);
- all potential extension cells are zero;
- complete output footprints are non-overlapping and separated;
- default lessons alternate edge/interior, with canonical-shape support in every difficulty band;
- only three exact, observable axes are declared: `grid_h`, `grid_w`, and `layout`.

The strongest canonical rival is “extend every pair exactly once toward the grid interior.” It reproduces all three canonical pairs because every canonical pair is boundary-flush. Interior generated examples refute it: the true rule fills both sides while the rival fills only the positive-direction side. The semantic census observed the two-sided witness on 307/600 draws and verified 60/60 rival-disagreement claims.

Evidence:

- baseline battery: 7 green, 2 advisory, 3 failed;
- first after attempt: semantic repair was correct, but defect lint exposed byte-identical difficulty bands;
- final after battery: 12/12 green;
- focused tests: 12 passed;
- canonical profile: 60/60 exact/envelope;
- strict semantic inputs: 600/600; canonical accepted: 3/3; lessons identifiable: 12/12;
- override contract: 2,700/2,700 accepted, unknown key rejected;
- rule smoke: 120/120 with Python mirror parity.

No canonical Racket rule was changed.
## Current reviewer considerations

Source SHA-256: `47e61d41c53b2b3e105c696eebc621dc7a54e3ab2cefc0e1538bd8fbc1b58f36`.

# Design decisions: a286b2610efc

## D1 — Preserve the canonical rule; repair the generator

**Original rationale:** Unknown. The prior generator was evidently designed around the informal phrase “complete dominoes to triplets,” but it did not account for overlapping windows.

**Decision:** Keep the canonical Racket program unchanged. Its behavior is internally consistent, matches every canonical pair, and passed authority sync and execution parity. Change the generator and documentation to reflect the actual original-input window semantics.

**Alternatives considered:**

1. Change the Racket rule so every connected pair receives exactly one extension. Rejected because that would contradict the selected canonical authority and erase a real local-window branch.
2. Restrict all generated pairs to boundaries, preserving the informal triplet story. Rejected because the canonical demonstrations would remain ambiguous and never falsify the strongest one-sided shortcut.

**Probe:** Exact replay of all three canonical pairs and 120 Racket smoke applications with 120/120 Python-mirror parity.

**Failure mode/limitation:** The accepted rule applies more broadly than the generator’s narrow teaching grammar; the generator is not intended to enumerate every lawful arbitrary grid.

## D2 — Use exactly one horizontal and one vertical domino

**Original rationale:** The old generator varied one to six independently colored pairs, sometimes with repeated colors and without guaranteeing both orientations. The rationale for those axes was not recorded.

**Decision:** Generate exactly two motifs, with distinct colors and opposite orientations, matching the linked structure of all canonical examples.

**Alternatives considered:**

- Preserve variable object count. Rejected because higher counts create interacting windows, make color-to-object recovery less reliable, and are not needed to identify the rule.
- Permit same-orientation lessons. Rejected for the default contract because such lessons hide one rule branch; they could be added later as an explicit profile after mixed-orientation coverage is guaranteed.

**Probe:** `self_check` mutation tests reject singleton, 2x2, same-orientation, mixed-layout, overlapping-footprint, ragged, and out-of-range impostors. The strict semantic census accepted 600/600 generated inputs and all 3 canonical inputs.

**Failure mode/limitation:** This narrows morphology and will not train arbitrary-many-object generalization by itself.

## D3 — Alternate boundary and interior layouts

**Original rationale:** The old placer reserved a three-cell footprint only to the right or down. It did not classify whether a leading/upstream zero also existed, so interior pairs silently received two extensions.

**Decision:** Make `layout` explicit. `edge` pairs have one in-grid adjacent extension; `interior` pairs have two. Alternate by `sample_index`; with `EXAMPLES_NEEDED = 3`, every consecutive lesson window contains both.

**Alternatives considered:**

- Random layout. Rejected because a three-example lesson could draw all edge cases and preserve the canonical shortcut.
- Interior-only. Rejected because the curriculum would no longer stay visibly linked to the canonical boundary examples.
- Edge-only. Rejected because it cannot disambiguate one-sided completion.

**Probe:** Sliding windows starting at sample indices 0 through 5 in every band contain exactly `{"edge", "interior"}`. The semantic gate measured both profiles in all bands and 12/12 identifiable lessons.

**Failure mode/limitation:** The guarantee depends on consecutive sample indices, which is the repository lesson materializer’s current contract; arbitrary external subsampling could break it.

## D4 — Declare only exact, observable axes

**Original rationale:** The old metadata exposed palette, count, density, position, distinct-color, and texture axes that were ignored, redundant, or admitted negative fixtures.

**Decision:** Keep only `grid_h`, `grid_w`, and `layout`. Validate values before creating `GenCtx`, reject unknown keys, route every axis through a keyed draw, and recover all three through `observe_overrides`.

**Alternatives considered:** Keep diagnostic or alias axes. Rejected because they add no teaching value and previously produced thousands of false contract combinations.

**Probe:** 54 explicit axis combinations across all three bands in focused tests, plus the repository’s 2,700-draw override matrix. Unknown override rejection is explicitly checked.

**Failure mode/limitation:** Users of removed legacy axes must migrate rather than receiving silent compatibility behavior; fail-loud is intentional.

## D5 — Stay on the canonical shape envelope by default

**Original rationale:** The old hard band expanded to 9–12 by 10–13, leaving zero hard-band canonical-profile support.

**Decision:** Default height is 7 and width cycles through 8/9, the canonical shapes. Overrides allow small extrapolations to heights 8/9 and width 10 without changing the grammar.

**Alternatives considered:** Preserve broad shapes with a probabilistic canonical prior. Rejected as unnecessary complexity for a basic local rule and less reliable for a three-example lesson.

**Probe:** Canonical profile floor improved from 4/60 exact/envelope with zero hard support to 60/60 exact/envelope.

**Failure mode/limitation:** Default shape diversity is two shapes rather than the old nine; content/placement/palette diversity remains high.

## D6 — Make bands live without changing semantics

**Original rationale:** None recorded. The first repaired version correctly ignored difficulty, and strict defect lint identified all bands as byte-identical.

**Decision:** Apply deterministic cyclic rotations to the two nonzero colors by band (`0`, `+3`, `+6` modulo the nine nonzero ARC colors). This guarantees distinct grids for the same seed/index while preserving structure and difficulty-independent rule semantics.

**Alternatives considered:** Increase dimensions or object counts by band. Rejected because dimensions would damage profile support and object count would enlarge the semantic interaction surface. Band-specific keyed placement alone was rejected because random collisions would remain theoretically possible.

**Probe:** A regression test requires three distinct grids for each of eight sample indices while `self_check` and layout observations remain identical. Final defect lint is green.

**Failure mode/limitation:** “Hard” is not conceptually harder; the band is live but palette-based. This is preferable to dishonest structural difficulty.

## D7 — Encode the strongest rival as executable evidence

**Original rationale:** The old generator contained only prose comments about possible rivals and declared no machine-checkable semantic contract.

**Decision:** Implement `one_sided_triplet_completion`, which extends each pair exactly once in the positive direction (or the only in-grid direction at a boundary). Declare it consistently as a semantic rival, lesson competitor, and canonical shortcut. Declare interior two-sided completion as the witness that refutes it.

**Alternatives considered:** Use weaker rivals such as horizontal-only or fixed-color extension. Rejected because canonical examples already refute them; they do not expose the real ambiguity.

**Probe:** The rival reproduces all three canonical outputs, disagrees with every generated interior instance, and was verified by the semantic gate on 60/60 sampled witness/rival checks.

**Failure mode/limitation:** Other contrived rules can always interpolate finite examples. The contract targets the strongest simple mechanism-level rival supported by the canonical evidence.

## D8 — Add an episode-fixed repeated-completion parameter

**Decision:** Keep `rounds=1` as the byte-exact canonical program and add
`rounds=2`, which applies the same simultaneous pass to its own first-pass
result. The setting is private and fixed for the episode; sampler inputs are
identical across settings and prefix-stable for 2–6 demonstrations and 1–4
queries.

**Why this parameter:** It stays adjacent to the original mechanism while adding
a non-collapsing sequential dependency. Step A produces completed segments;
Step B must inspect that input-dependent intermediate before it can extend those
segments again. A one-pass counterfactual changes the retained 30×30 query label.

**Teaching design:** Every generated scene contains six scheduled motif classes:
horizontal left/top, horizontal right/bottom, vertical top/right, vertical
bottom/left, horizontal interior, and vertical interior. Additional separated
motifs scale with area, and isolated singleton distractors avoid accidental
completion. Demo/query dimensions range from 14×16 through a substantive 30×30
fourth query, touching every boundary and quadrant.

**Bounded evidence:** The protected audit executed 12 native jobs and 136 labels,
plus 31 additional Racket evaluations. All 20 checks from six plausible rival
programs were refuted by the first two visible demonstrations; the 12-seed
construction census passed 72/72 requests; eight min/max boundary labels and all
three canonical labels matched. Public projection checks retained eight
one-query views with content-only IDs and private future-query ordering.

**Limits:** These checks cover only the finite rivals and seeds named in the
retained evidence. They do not prove universal identifiability, measured training
gain, owner acceptance, or training admission. Exact-source owner qualification
and acceptance remain required after integration.
