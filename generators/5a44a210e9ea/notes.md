# Working notes: 5a44a210e9ea

## Review `review-c227d9afeed2a683`

Baseline `2.1.0` generated only clean concentric frames, advertised inert or rejected controls, lacked `RULE_HASH`, and did not encode the canonical rule's connected-component validity distinction. The selected canonical examples also contain a connected frame-like object with extra cells that must be erased.

The `3.0.0` rewrite:

- pins `RULE_HASH = "8d815468fa81"`;
- exposes only exact, observable axes: `grid_h`, `grid_w`, `palette_size`, `palette_layout`, and `scene_kind`;
- validates unknown, typed, range, and joint overrides rather than silently swallowing them;
- produces clean nested frames and canonical-style connected malformed objects;
- declares executable rivals for prefix-only palette parsing, no final-colour reuse, and paint-every-component;
- provides semantic witnesses plus `lesson_identifiable`;
- uses a four-role schedule in which every wrong rule has redundant demonstration evidence;
- includes an independent Python oracle/probe and task-local regression suite.

A first repaired schedule passed the fixed-query 300-lesson census but failed 675 of 1,500 leave-one-out query rotations. The final schedule adds a combined gapped/reuse/malformed stress example; 1,500 of 1,500 rotations are identifiable. One subsequent distribution regression made the canonical maximum total palette unreachable; changing the gapped profile to four header colours restored that support.

The canonical Racket program was not changed. The selected task-specific base `target_code` differed from its own canonical `raw_code` only by one comment; removing that comment restored exact authority synchronization.

See `workspace/reference_probe.py`, `workspace/lesson_rotation_probe.py`, task tests, and the review return's `checks/` evidence. Finite declared rivals and the nested-frame grammar are measured limits, not a proof of universal induction.
## Current reviewer considerations

Source SHA-256: `6744032ebca440f0d65a74ad8965608b278dd463b6f07166cfc0e9de83adfa7f`.

# Decisions for 5a44a210e9ea

## D1 — Treat the canonical Racket program as fixed authority

**Original rationale:** unknown. The baseline generator described a simpler nested-frame transformation and did not pin `RULE_HASH`.

**Decision:** retain the canonical program and pin normalized hash `8d815468fa81`. The visible canonical examples and independent oracle agree that the rule operates on 4-connected components: only exact rectangular perimeters survive, frames are area-ranked, header colours are read left-to-right, and the last colour is reused.

**Alternatives rejected:** rewriting the Racket rule to match the baseline's “all concentric frames are valid” summary; accepting behavior-only equality while leaving source drift. Both would weaken authority rather than repair the generator.

**Probe/evidence:** canonical-pair oracle checks and real-Racket parity in `tests/test_generator.py`; `rule_smoke` and `authority_sync` in the final battery. The task-specific base `target_code` was synchronized to its already-canonical `raw_code` by removing one comment; no executable Racket behavior changed.

## D2 — Model connected-component validity, not just nested geometry

**Original rationale:** the baseline appears to have inferred the three clean canonical examples and omitted the two malformed-object examples.

**Decision:** generate two body grammars. `clean` contains 2–4 separated nested exact frames. `touching_decoy` contains 1–3 valid nested frames plus exactly one connected blue object that is not an exact rectangular perimeter. Canonical-style one-frame decoys use a frame with a full divider; the combined stress case uses an isolated plus inside the innermost valid frame.

**Alternatives rejected:** recolour every blue component; draw only isolated noise pixels; split a malformed union into multiple objects. Those alternatives do not teach the canonical object-level decision that a connected frame-like support with extra cells is one invalid component and disappears.

**Failure modes/limits:** the selected grammar has at most one malformed component and valid frames remain nested at two-cell insets. It does not prove behavior for arbitrary overlapping rectangles or arbitrary placements. The rule itself is broader than this finite training manifold.

**Probe/evidence:** `reference_probe.py`, `test_touching_decoy_is_connected_but_not_a_frame_and_is_erased`, the malformed-component witness, and the `paint_all_blue_components` rival.

## D3 — Replace the eight-axis claim with five exact observable controls

**Original rationale:** unknown. The baseline advertised controls that were inert, rejected by difficulty-local ranges, or accepted without validation.

**Decision:** expose only `grid_h` (12–18), `grid_w` (10–18), `palette_size` (2–5), `palette_layout` (`packed|gapped`), and `scene_kind` (`clean|touching_decoy`). Reject unknown keys, booleans masquerading as integers, out-of-range values, and invalid enums. Every declared cross-product is constructive and recoverable from pixels through `observe_overrides`; no incompatibility exceptions are needed.

**Alternatives rejected:** keeping diagnostic/inert texture names; silently clipping overrides to a difficulty band; declaring broad incompatibility tables to excuse constructive failures. Those choices make data requests non-reproducible.

**Probe/evidence:** the baseline override stage had 7,946 findings in the focused run; the repaired exhaustive matrix accepted and exactly observed all 21,420 draws. Boundary, type, unknown-key, all-band, and joint-axis cases are regression-tested.

## D4 — Keep dimensions and palettes broad enough to cover canonical marginals

**Original rationale:** the baseline dimensions and palette claims were not consistently tied to generated pixels.

**Decision:** total input dimensions range from 12–18 by 10–18. Header palettes contain 2–5 distinct colours selected from 2–9. The four-colour gapped profile preserves the canonical maximum total palette of six colours when background/source colours are counted; canonical-decoy profiles preserve exact canonical shape/palette combinations.

**Alternatives rejected:** only replaying the five canonical grids; fixing all profiles to one square shape; using arbitrary body colours. Exact replay provides no useful distribution and arbitrary source colours would change the selected rule's colour-1 object semantics.

**Failure discovered and repaired:** the first redundant schedule used only 2–3 header colours, so `dist_gate` reproduced `canonical_palette_unreachable: gen=4..5 vs canon=6`. The final four-colour gapped profile restores that support.

## D5 — Use zero gaps as semantic evidence, not decoration

**Original rationale:** all clean baseline palettes were effectively readable as a contiguous prefix, allowing a wrong “stop at first zero” rule.

**Decision:** `palette_layout=gapped` always puts a real colour at column 0, an explicit zero at column 1, and remaining colours later in row 0. A useful gapped example has at least two valid frames, so later colours affect the output.

**Alternatives rejected:** random zero placement without ensuring later colours are consumed; gapped decoy scenes with only one valid frame. The latter looked diverse but did not actually refute the prefix rival and caused the first cyclic-redundancy fix attempt to fail.

**Probe/evidence:** `test_gapped_palette_defeats_contiguous_prefix_shortcut`, the gapped witness/rival claim, and the semantic gate's 60/60 checked rival claims.

## D6 — Teach final-colour reuse explicitly

**Original rationale:** canonical examples do not require more valid frames than palette colours, so a “drop deeper frames” rule fits all five canonical pairs.

**Decision:** include clean profiles with 3–4 frames and only two palette colours. The selected output repeats the second colour on every deeper frame.

**Alternatives rejected:** rely on written summaries; use a single-frame example with an unused extra palette colour. Neither creates an input/output counterexample to the no-reuse rival.

**Probe/evidence:** `test_more_frames_than_palette_reuses_last_palette_colour`, `no_last_palette_reuse`, and the `last_palette_reuse` semantic witness.

## D7 — Make lesson evidence redundant across query roles

**Original rationale:** the initial repair used four roles—one clean canonical-like, one decoy, one gapped, and one reuse example—which was sufficient only when the query position remained fixed.

**Decision:** use four roles: `palette_reuse`, `canonical_decoy`, `gapped_palette`, and `combined_stress`. The combined stress input simultaneously has a gapped palette, more valid frames than colours, and a malformed component. Across every five-pair window, each declared wrong rule is refuted by at least two pairs; removing any one pair still leaves evidence in the demonstrations.

**Alternatives rejected:** trust the fixed production query slot; duplicate all four examples; increase lesson length. Query-slot trust hid ambiguity, duplication reduces diversity, and longer lessons cost tokens. A combined witness gives redundancy at the existing four-demo budget.

**Probe/evidence:** the first schedule passed 300/300 fixed-query lessons but failed 675/1,500 query rotations. The final schedule passes 300/300 fixed-query lessons and 1,500/1,500 rotations. See `workspace/lesson_rotation_probe.py` and the paired rotation reports.

## D8 — Use an independent oracle and mutation-sensitive tests

**Original rationale:** baseline self-checking could agree with the same mistaken helper logic used by generation.

**Decision:** keep geometry/oracle code in `workspace/reference_probe.py` independent from production helpers, compare it with canonical pairs and real Racket, and test destructive mutations, unknown overrides, determinism across Python hash seeds, rival counterexamples, schedule coverage, and all query rotations.

**Alternatives rejected:** test only `self_check(generate(...))`; import production `_solve` into tests; rewrite the frozen root fixture. Those approaches can preserve shared bugs or violate packet scope.

**Probe/evidence:** 41 source-bound task tests, including real-Racket parity. The initial selected test subset failed 17 cases on the baseline before production changes.

## D9 — Stop after measured gates, not after eliminating every duplicate output

The diversity smoke reports 81% unique inputs and 48% unique outputs across 300 pairs, flagging repeated output geometries as advisory. I did not add random off-manifold layouts merely to raise that number: repeated canonical-sized frame geometries are intentional, while colours, palette positions, decoy orientation, dimensions, and semantic roles still vary. The 300-lesson census contains 1,093 unique inputs across 1,500 pair slots.

**Remaining limitation:** duplicate outputs reduce marginal data efficiency, especially for one-frame decoys. A future task-local expansion could vary valid-frame placement and decoy geometry while retaining exact profile support, but it should be justified by a learning experiment rather than by the advisory percentage alone.
