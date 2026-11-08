# Working notes: f4a7ad69b9f2

## 2026-10-04 review

The prior return `review_response_external-local-random_0fd82003404a_x` was used
only as a lead: it correctly identified the canonical `(width,height,color)`
shortcut and established the four-profile schedule. All claims were remeasured
against this packet's pinned baseline.

The baseline's `lex_shape` profile exposed its answer in crop cell 0. A stronger
bounded-prefix probe showed that `(width,height,crop[:1],color)` and then
`(width,height,crop[:2],color)` each fit all four canonical pairs and all 1,200
sampled generated inputs, yet failed lawful counterexamples. Version 3.2.0 uses
tied 3x4 shapes sharing two leading zeros, declares both shortcuts as executable
rivals, and retains the full-crop authority unchanged.

A 100-lessons-per-band census then found the ordinary four-demo lessons clear but
450/1,500 legal query rotations ambiguous. A first seven-demo repair removed all
rotation ambiguities but exceeded the serializer contract (`EXAMPLES_NEEDED`
must be 2..5), and the retained battery records that failure. Version 3.3.0 uses
a six-pair lesson instead: both width profiles now refute width and height
shortcuts, while the lex-shape and lex-color slots are each duplicated. Five
demonstrations therefore retain all four witness types after any one query is
held out.

Reusable evidence and probes are under `workspace/` and packet-level `checks/`.
Finite rival checks do not prove universal identifiability; longer bounded-prefix
or wholly different synthesized rivals remain a general tooling question.
## Current reviewer considerations

Source SHA-256: `bebd770f37d0e7ddc3ff3d37102966ad34cefc2032f225378683bf64482fd5e8`.

# Decisions for f4a7ad69b9f2

## D1 — Preserve the canonical authority

The canonical Racket rule and `RULE_HASH = 16e822df83e5` were left unchanged.
Canonical execution, the Python mirror, and all four official pairs already
agreed; the defect was in what the generated lessons taught, not in the labels.
The imported return `review_response_external-local-random_0fd82003404a_x` was
used only as a lead and all claims were remeasured on the pinned packet baseline.

## D2 — Treat bounded crop-prefix rules as real competitors

The baseline lex-shape profile always revealed its decisive geometry in crop cell
0. The rival `(width,height,crop[:1],color)` fit 4/4 canonical pairs and
1,200/1,200 sampled generated inputs, while a lawful counterexample made it
disagree with the authority (`checks/prefix-shortcut-before.json`). Delaying the
first distinction by one cell killed that rival but exposed the adjacent
`crop[:2]` shortcut, which again fit 4/4 canonical and 1,200/1,200 generated
inputs (`checks/prefix2-shortcut-before.json`).

The final 3x4 tied shapes share two leading zero cells and first differ at flat
index 2. Both bounded-prefix rivals are executable declarations in
`SEMANTIC_RIVALS`, `WITNESS_RIVALS`, and `CANONICAL_SHORTCUTS`. On final source
SHA-256 `bebd770f37d0e7ddc3ff3d37102966ad34cefc2032f225378683bf64482fd5e8`,
each rival still fits 4/4 canonical pairs but is refuted by all 402 lex-shape
rows in a 1,200-input census; 798/1,200 non-lex-shape rows agree as expected.
Evidence: `checks/prefix-shortcut-final-source.json` and
`checks/prefix2-shortcut-final-source.json`.

Rejected alternative: changing only colors would kill the known color shortcut
but leave the shallow geometry feature exposed. Rejected alternative: adding a
single fixed adversary would improve one seed but not make the profile contract
structural or reusable.

## D3 — Make legal query rotations identifiable within the serializer limit

The first 300-lesson census showed 0 ordinary ambiguities but 450/1,500 ambiguous
query rotations (`checks/lesson-census.json`). Holding out the sole lex-shape or
lex-color example removed the only discriminator for a named rival.

A first repair used seven demonstrations/eight total pairs, giving two copies of
each profile. It achieved 0/2,400 ambiguous rotations
(`checks/lesson-census-final.json`) but the final battery correctly rejected
`EXAMPLES_NEEDED=7`: worker returns serialize only 2..5 demonstrations. That
failed iteration is retained in `checks/after-too-long/` and
`checks/tdd-red-serializable-schedule/`.

The accepted design uses five demonstrations plus one query. Its six-slot
schedule is:

`width_primary, height_tie, lex_shape, lex_shape, lex_color, lex_color`.

Both width profiles now contain a smaller-width object plus an unequal-height
same-width pair, with colors chosen so each refutes both `color_only_order` and
`width_then_color_skips_height`. The two lex profiles are duplicated. Therefore
each six-pair lesson contains every required witness twice, and holding out any
one pair leaves all witnesses. The final 100-lessons-per-band census materialized
300 lessons/1,800 unique inputs and found 0 production ambiguities and 0/1,800
ambiguous rotations, warnings, or scoring errors
(`checks/lesson-census-serializable.json`).

Rejected alternative: a new all-in-one lex profile would require three width-4
objects, incompatible with the smallest 12-column canvas under the current
side-by-side input layout. Rejected alternative: removing rotation checks would
hide a real downstream teaching ambiguity. Rejected alternative: extending the
serializer contract was outside the selected-task patch boundary.

## D4 — Preserve canvas, palette, and rule semantics

Canvas profiles, exactly three distinct nonzero colors, object separation,
top-aligned packing, and one-column output gaps remain unchanged. Difficulty
continues to affect morphology rather than the rule. The width-primary canonical
shape anchor was removed because its three distinct widths cannot supply the
secondary height witness required by the rotation-robust schedule; the procedural
width-primary family remains varied and fits every existing canvas.

## D5 — Tests and reusable tooling

Task-local regressions cover delayed two-cell prefixes, explicit one- and
two-cell rivals, exact override recovery, deterministic replay, serializer lesson
bounds, joint width/height witnesses, every cyclic production start, and every
query rotation. The reusable probe
`repo/generators/f4a7ad69b9f2/workspace/probe_prefix_shortcut.py` constructs a
lawful adversary, measures canonical/generated fit for prefix lengths 1 or 2,
and records source hash, command, sample range, and exact disagreements.

## Remaining limitations

The declared-rival and finite-census results are strong regression evidence, not
a proof that every imaginable alternative rule is excluded. Prefix depths beyond
two and non-prefix feature compressions remain candidates for shared synthesized
rival tooling. The final schedule intentionally spends two slots on each lex
branch; this is a data-quality choice that increases repeated semantic profiles
but stays within the five-demonstration contract.
