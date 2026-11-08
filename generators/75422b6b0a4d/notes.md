# Working notes: 75422b6b0a4d

## Rule and initial defect

The selected Racket authority treats each color 1..4 cell as a seed and flood-fills through original cells equal to 0 or the seed color. Other colors are barriers. The issued v2.0.1 generator omitted `RULE_HASH`, advertised axes it did not honor, used a permissive validator, and generated only straight complete wall rows/columns. Therefore the canonical-compatible rival “fill rectangular regions between complete wall lines” fit every generated example.

## Repair

Version 3.1.0 exposes exactly four constructive, observable axes: `grid_h` 7..18, `grid_w` 8..20, `wall_color` 5..9, and `n_rooms` 2..4. Unknown or invalid overrides are rejected. Every generated grid has one connected wall network with a full border, exactly 2..4 connected chambers, one seed and at least one zero per chamber.

The three-slot production schedule is:

1. `canonical_anchor`: straight gray-wall, four-room, 7x8/9/10 examples matching canonical profiles while varying seed positions.
2. `shortcut_witness`: non-gray stepped/partial walls with three rooms.
3. `broad`: broad dimensions and room counts, but also non-gray stepped/partial walls.

The broad slot originally allowed a canonical-compatible example. A 300-lesson query-rotation census then found 48/1,200 ambiguous rotations even though production order was 0/1,200 ambiguous. Version 3.1.0 deliberately duplicates both decisive cues in the broad slot, so every four-pair window retains at least one shortcut-killing demonstration when any one pair is moved to query. The final census reports 0/1,200 production ambiguities and 0/1,200 rotation ambiguities against the declared rivals.

## Authority hygiene

The selected solution JSON had `target_code` differing from canonical `raw_code` only by an extra comment. `target_code` was synchronized byte-for-byte to `raw_code`; executable semantics and canonical data were not changed.

## Retained evidence and limits

- Counterexample: `counterexamples/complete-wall-lines-only.json` (seed 1, index 1, easy), independently checked by Racket; the rival differs on 29 cells.
- Task-local tests: independent flood oracle, canonical parity, exact override domains, malformed inputs, schedule coverage, rival fit/refutation, counterexample replay, and all query positions across cyclic starts/bands.
- The finite semantic gate and census test the two declared canonical-fitting rivals, not every possible hypothesis.
- Explicit user overrides remain exact and lawful; arbitrary hand-assembled override-only lesson sequences are not claimed rotation-identifiable. The claim is for the default production schedule.
## Current reviewer considerations

Source SHA-256: `d3eb1f64cba0b39b7c7dc2d1ed4fa33008ea74092bf98b989c1cdcb6a36b5134`.

# Decisions for 75422b6b0a4d

## D1 — Replace the misleading surface instead of pretending to support it

The issued generator advertised seven axes plus degenerate textures, but `generate` only meaningfully sampled dimensions and straight wall placements; even named overrides such as `grid_h`, `grid_w`, `wall_color`, `n_rooms`, `palette_size`, and `position_bias` were ignored or not constructively enforced. I replaced that surface with four axes whose values are exact and directly observable: height, width, wall color, and chamber count.

Rejected alternative: retain all legacy axes and bolt on acceptance checks. That would preserve meaningless knobs (`position_bias` had one value, `palette_size` did not describe the actual per-room seed assignment) and make override semantics harder to audit. Degenerate examples were also removed from production because they violate the lawful one-seed-per-chamber domain rather than teach the authoritative transformation.

## D2 — Preserve canonical support but schedule explicit counterexamples

The canonical examples are small gray-wall rectangular partitions. A generator that only reproduces that geometry permits the simpler rival `complete_wall_lines_only`: detect complete wall rows/columns and fill only the resulting rectangles. I retained one `canonical_anchor` every three samples and added `shortcut_witness` examples with stepped/partial, non-gray walls. The anchor prevents repair drift away from the observed source distribution; the witness demonstrates the actual connectivity rule.

Rejected alternative: abandon canonical profiles entirely in favor of maximum geometry diversity. That would make canonical acceptance a validator-only property and weaken the lesson’s connection to the source task.

## D3 — Make the broad slot independently decisive

Version 3.0.0 used a decisive witness but allowed the broad slot to be canonical-compatible. The first 300-lesson census found 0/1,200 ambiguities in production order but 48/1,200 ambiguities when each of four pairs was rotated into the query. Root cause: removing the sole witness left three examples on which both canonical-compatible rivals still fit.

Version 3.1.0 makes the broad slot stepped/partial and non-gray by default as well. Thus every four-pair production window contains at least two decisive examples, and removing any one pair still leaves a refutation. The final source-bound census at `checks/lesson-census-v31.json` reports 300/300 lessons materialized, 0/1,200 production ambiguities, and 0/1,200 query-rotation ambiguities. This is evidence only against the declared rivals, not a proof over all hypotheses.

## D4 — Use a constructive partition, then validate the semantic contract

The sampler builds a full outer border plus either a straight or stepped primary divider and an optional complete/partial secondary divider. This construction guarantees 2..4 connected chambers without rejection-heavy random wall carving. Seed placement happens after connected components are known, with exactly one seed and at least one remaining zero in each chamber.

`self_check` independently rederives the wall color, border, connected wall network, chambers, seed counts, and zero counts. It rejects malformed/ragged/non-integer grids rather than crashing. `observe_overrides` only operates on a valid grid and returns all four advertised values.

Rejected alternative: random maze walls. It gives more topological diversity, but would add failure-prone connectivity repair and substantially expand the semantic domain without evidence that the extra complexity improves this task’s teaching objective.

## D5 — Keep the authoritative rule unchanged

The selected solution JSON’s `target_code` contained an extra explanatory comment absent from its `raw_code`, causing strict source-divergence lint despite sampled behavior parity. I synchronized `target_code` byte-for-byte to the already-preserved canonical `raw_code`. No executable Racket expression, canonical input/output, or rule hash changed.

## D6 — Test from independent behavior, not implementation internals

Task-local tests use an independent flood-fill oracle and `reviewer_support.canonical_pairs`, not the generator’s own mirror as the sole oracle. They cover canonical parity, all override bands/endpoints, invalid override rejection, malformed inputs, schedule witnesses, canonical-shortcut fit, default distribution, seed diversity, saved Racket counterexample replay, and every query position across cyclic starts in easy/medium/hard bands.

A saved counterexample at `repo/generators/75422b6b0a4d/counterexamples/complete-wall-lines-only.json` binds seed/index, source hashes, input, intended output, real Racket output, and rival output. It differs from the rival on 29 cells.

## D7 — Scope of the lesson claim

The production lesson claim is for the default three-slot schedule assembled into four-pair windows with any one pair eligible as query. Explicit override calls remain exact and lawful, but arbitrary user-assembled override-only lesson sequences are not promised to contain the scheduled contrast. The two named rivals are finite diagnostics; an unknown shortcut could still exist.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/75422b6b0a4d/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## D8 — Add a native flood-then-largest-boundary family

The reviewer prototype at `workspace/parametric/` preserves the canonical flood program byte-for-byte as `finish=flood`. Its nearby nondefault setting, `finish=outline_largest`, first executes that flood, derives the unique largest chamber's filled region and seed color, and then recolors only wall cells four-adjacent to that region. This is a non-collapsing A→intermediate→B dependency: choosing the smallest chamber instead changes a different spatial wall boundary, not merely a color remap.

The constructive sampler supports 2–6 demonstrations and independent 1–4 query prefixes while materializing four novel queries at 14x16, 20x23, 26x28, and 30x30. Both settings receive identical inputs. Minimum lessons refute the other setting plus six plausible selectors/masks. During a 16-seed endpoint audit, seed 8 exposed that `outline_seed_touch_only` could collapse to canonical flood when the selected seed had no adjacent wall. The sampler now constructively requires a nonempty seed-wall contact; a regression test retains that case. The bounded endpoint audit then completed 64/64 requests with 448 finite-rival checks and no failures. This finite audit does not establish uniqueness against every possible rule.

Promotion remains reviewer-ready rather than accepted. The returned source-bound manifest, native qualification, protected-Racket causal witness, and public-projection checks are the owner handoff; the owner must requalify and accept exact integrated bytes before admission.
