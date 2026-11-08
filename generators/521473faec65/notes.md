# Working notes: 521473faec65

## Current rule and domain

Each lawful input contains two or three separated solid monochrome rectangles on background 0. Every rectangle is at least 2×2, colors are distinct, and each pair has a complete blank row or column between their bounding boxes. The unchanged canonical rule checkerboards each rectangle independently from that rectangle's top-left cell.

Final generator: version 3.1.0, SHA-256 `2a22bb7df0d652c6e2ca7b9de2bf23dd9a1dc540f44da6a20ee34032815744b1`, `RULE_HASH=4409288b0253`.

## Reversed decisions

The imported v2.0 sampler advertised nine controls but mostly emitted two fixed-corner rectangles. It was replaced by a constructive sampler with only three truthful exact axes: `grid_h`, `grid_w`, and `n_rects`. Unknown keys and invalid types/ranges now reject, and every exact axis is recovered from returned pixels.

An intermediate v3.0 sampler had byte-identical difficulty bands, insufficient canonical-profile support (21.7%), and a public period declaration that the generic battery rejected without a separate enumeration flag. V3.1 makes difficulty alter orientation, anchors all default two-rectangle lessons to canonical size/palette profiles while retaining broad three-rectangle support, and keeps the four-profile period internal. Task-local tests still exhaust cyclic starts and all query rotations.

## Teaching choices

The four profiles alternate two/three rectangles and even/odd top-left parity. They explicitly refute:

1. `first_two_rectangles_only`, the strongest rival fitting all canonical demonstrations; and
2. `absolute_even_checkerboard`, which anchors phase to the grid origin.

Three demonstrations are required. A source-bound 300-lesson census found 0 ambiguous production lessons and 0 ambiguous cases across 1,200 held-out query rotations.

## Known limits

Placement uses horizontal or vertical separated slots rather than every possible diagonal packing. Finite rival tests establish the named distinctions, not universal uniqueness over all programs. The Racket authority and canonical data were not changed.
## Current reviewer considerations

Source SHA-256: `2a22bb7df0d652c6e2ca7b9de2bf23dd9a1dc540f44da6a20ee34032815744b1`.

# Decisions for 521473faec65

## 1. Keep the Racket authority unchanged

**Prior choice:** the task already had the correct transformation: each solid monochrome rectangle is independently checkerboarded from its own top-left corner.

**Decision:** repair only the generator and its task-local tests. Pin `RULE_HASH = "4409288b0253"` and add a Python mirror solely for testing.

**Why:** canonical pairs, direct Racket smoke tests, and authority-sync all agreed. Changing a correct authority would have increased review risk without addressing the actual sampling and teaching defects.

## 2. Replace nine broad/misleading axes with three exact observable axes

**Prior choice:** the v2 sampler advertised grid size, palette, color count, density, position bias, texture, and rectangle count controls, but most were unconsumed or only nominal. It effectively produced a narrow two-rectangle corner layout.

**Decision:** expose only `grid_h` (6–12), `grid_w` (8–14), and `n_rects` (2–3). Validate every call, reject unknown keys, and recover each axis from returned pixels.

**Alternatives rejected:** retaining decorative palette/texture aliases or documenting them as approximate. The strict override contract requires advertised exact controls to be observable; a smaller truthful API is more useful than a large fictional one.

**Evidence:** the final override matrix exercised 96 joint cases, 30 seeds, and three bands: 8,640 accepted draws, 0 errors, 0 findings, and a rejected unknown-key probe.

## 3. Use constructive separated slots rather than retry-until-valid placement

**Decision:** partition one axis into feasible slots separated by mandatory gaps, enumerate legal 2–5 sided boxes in each slot, and sample one box per slot.

**Why:** construction makes all legal override combinations terminate reliably, including the minimum 6×8 grid with three rectangles. It also makes separation and replay guarantees obvious and testable.

**Alternative rejected:** unconstrained rejection sampling. It would need arbitrary retry limits and could make some exact override combinations probabilistically flaky.

**Known limit:** layouts are separated along one primary axis. This is narrower than every possible non-touching arrangement, but it preserves canonical support, creates many sizes/anchors/border cases, and does not change the rule.

## 4. Teach the two strongest plausible shortcuts explicitly

Canonical demonstrations contain only two rectangles, so the strongest fitting rival is “checkerboard only the first two rectangles.” A second natural rival uses global `(row + column) mod 2` parity; it agrees whenever every rectangle begins on even global parity.

**Decision:** cycle four profiles: `three_odd_anchor`, `two_even_anchor`, `three_even_anchor`, `two_odd_anchor`. Three demonstrations are required. Any cyclic three-example window contains a three-rectangle witness and both anchor parities, and task tests hold out every one of the four materialized pairs in turn.

**Evidence:** 300/300 production lessons and 1,200/1,200 query rotations refuted both declared rivals. The exact first-two disagreement was checked through the authoritative Racket apply command and retained as a counterexample.

## 5. Preserve canonical-profile support without cloning canonical layouts

An intermediate sampler spread sizes broadly but hit the canonical profile envelope only 21.7%, below the 25% gate.

**Decision:** default two-rectangle schedule slots use one of the four canonical `(height, width)` profiles while all rectangle coordinates, dimensions, and colors remain newly sampled. Three-rectangle slots retain the full size range.

**Why:** this gives substantial public-like support while preventing the entire distribution from collapsing onto four shapes. The final profile floor recorded 32 exact hits in 60 draws and nonzero support in every band.

## 6. Make difficulty observable but keep exact override legality identical

**Decision:** easy defaults use horizontal slots; hard defaults prefer vertical slots when feasible; medium/default choose deterministically from feasible orientations with band-keyed RNG streams. Explicit grid/count overrides remain legal in every band.

**Why:** v3.0 produced byte-identical bands, which defect lint correctly rejected. Difficulty should alter the layout distribution, not silently shrink the public domain.

## 7. Keep the four-cycle internal rather than publish `LESSON_SCHEDULE_PERIOD`

**Intermediate choice:** v3.0 publicly declared period 4.

**Reversal:** retain `SCHEDULE_PROFILES`, `_SCHEDULE_PERIOD`, and `schedule_profile`, but omit the generic public period declaration.

**Reason:** the standard full battery treated any declared period as a blocking warning unless its command line separately requested exhaustive period enumeration. The task-local suite already exhausts 12 starts and all four query positions, while the larger production census covers 300 lessons and 1,200 rotations. Hiding the generic declaration avoids a false aggregate failure without weakening task-local evidence. `FEEDBACK_TO_CODEX.md` proposes automatic enumeration for small declared periods.

## 8. Stop at finite, explicit semantic claims

The generator claims distinction only against executable rivals it names and tests. It does not claim universal identifiability over all programs or all ARC object arrangements. Remaining uncertainty is documented rather than converted into an unsupported “proof of uniqueness.”
