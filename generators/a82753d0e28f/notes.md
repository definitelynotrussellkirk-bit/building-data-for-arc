# Current notes: `a82753d0e28f`

## Intended rule

Scan all nonzero seed cells in row-major order. For each seed, paint the seed and every in-bounds chess-knight destination in that seed's color. Later seeds overwrite earlier paint at collisions. The selected canonical Racket authority is unchanged and is pinned by `RULE_HASH = "bf05263117e5"`.

## Decision reversal

Version 2.0.0 assumed seeds had to be Chebyshev-separated by more than four so knight halos could not overlap. That was a sampler restriction, not a task law, and it caused `self_check` to reject canonical examples. Version 3.0.0 removes the separation rule from ownership and instead deliberately constructs overlaps that expose row-major precedence.

The old generator also advertised palette, density, position, color-count, and texture axes that were ignored, fixed, aliased, or produced hand-written degenerates. Those controls were retired. The only public axes are now exact and observable in every difficulty band: `grid_h` 7–10, `grid_w` 8–12, and `seeds` 2–4. Difficulty changes weighting only.

## Shortcut and witness

All three canonical labels fit the plausible wrong rule `max_color_wins`, which keeps the largest numeric color at every collision. Every normal generated input now contains a protected shared halo cell where an earlier higher color is overwritten by a later lower color. The minimal retained example is `counterexamples/max_color_wins.json`: seeds 8 at `(2,2)` and 3 at `(4,6)` disagree at `(3,4)`.

`SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, and `lesson_identifiable` make that teaching requirement executable. Lessons use two demonstrations and one query; the 300-lesson rotation census reported no ambiguity against the declared rival.

## Assumptions and limits

- Inputs are rectangular 7–10 by 8–12 ARC grids with 2–4 singleton seeds and exactly two nonzero colors.
- `self_check` validates that broad owned manifold; it does not require the training-only overlap witness.
- Every ordinary sample contains a collision witness. This is intentional curriculum emphasis, not an exhaustive distribution over all lawful task inputs.
- Finite tests cover the declared max-color rival and shared generic rivals; they do not prove unique induction against every possible program.
- Pure geometry helpers are cached; RNG-dependent choices and generated grids are not.
- `seed` and `sample_index` must be exact integers (`bool` excluded), and `sample_index` must be nonnegative.

## Verification

Final generator SHA-256: `2f7a1a84530d666e1896d1f40bb0805e9cb4643fd8a072d41f5adabedfcdbed5`.

- Full after battery: 12/12 stages green (`checks/after/checks/a82753d0e28f_after_battery_summary.json`).
- Selected task tests: 56/56 passed (`checks/after-task-tests-final/result.json`).
- Override contract: 5,580 accepted, zero findings/warnings.
- Profile floor: 13/60 exact and 15/60 envelope, with exact support in all bands.
- Semantic gate: 600/600 strict draws and 600/600 witness hits.
- Lesson census: 300 lessons, 900 unique inputs, 900 query rotations, zero declared-rival ambiguity.

No selected-task blocker remains. Imported historical notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `2f7a1a84530d666e1896d1f40bb0805e9cb4643fd8a072d41f5adabedfcdbed5`.

# Decisions for `a82753d0e28f`

## D1 — Preserve the selected Racket authority

**Prior choice:** the generator description treated knight halos as independent objects and avoided overlap, but the selected Racket rule scans seeds row-major and naturally resolves collisions by later overwrite.

**Decision:** leave the Racket rule and canonical data byte-for-byte unchanged. Pin `RULE_HASH = "bf05263117e5"` and make the Python sampler/tests conform to it.

**Reason and probe:** the public `Catalog.apply(..., reference="canonical")` result matched an independent row-major knight oracle for all three canonical inputs and the retained counterexample. Authority sync, rule smoke, Racket lint, and execution parity all passed in `checks/after/`. The authority file still has its baseline SHA-256 `11db3f852c5e67efcbee2155bcdb8c24bff13f3dec79f04cc7351c0f65eace3d`.

**Rejected alternative:** changing the Racket rule to make halos non-overlapping or resolve by color rank would rewrite the task to match a flawed sampler and would invalidate canonical semantics.

## D2 — Remove fake axes instead of emulating them

**Prior choice:** version 2.0.0 advertised `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` in addition to dimensions and seed count. Several were ignored, fixed constants, aliases, or bypasses into hand-written degenerate grids.

**Decision:** expose only `grid_h` (7–10), `grid_w` (8–12), and `seeds` (2–4). Values are observable directly from the returned grid, exact overrides work in every band, and retired/unknown keys fail loudly.

**Reason and probe:** the strict override checker exercised 62 cases and 5,580 accepted draws with zero findings/warnings (`checks/after/checks/a82753d0e28f_after_override_results.json`). Focused tests also cover endpoints, invalid types, retired keys, and `None` default semantics.

**Rejected alternative:** preserving the old metadata while quietly ignoring controls would keep the contract dishonest. Re-implementing all old palette/texture knobs would add complexity unrelated to the canonical rule and reintroduce invalid no-seed/corner-only distributions.

## D3 — Constructively refute `max_color_wins`

**Observation:** all three canonical demonstrations are also produced by a rule that paints each seed/halo and keeps the numerically greatest color at collisions.

**Decision:** every normal generated input contains at least one shared halo cell where an earlier, higher-colored seed is overwritten by a later, lower-colored seed. Extra seeds are placed so they cannot overwrite the designated witness.

**Reason and probe:** the 7×9 fixture in `counterexamples/max_color_wins.json` differs only at the designated policy-sensitive cell `(3,4)`. The Racket authority returns 3 there; the rival returns 8. The semantic gate saw the witness in 600/600 draws and validated 60/60 sampled witness-to-rival claims.

**Rejected alternatives:** random overlaps were rejected because they can miss the witness, especially in a small lesson. Forcing only a same-color overlap was rejected because it exercises geometry but not precedence. Making the later color always larger was rejected because it would continue to agree with `max_color_wins`.

## D4 — Keep legal override domains identical across difficulty bands

**Prior choice:** easy fixed two seeds and smaller shapes while hard required three or four seeds and larger shapes. An override legal in one band could be impossible in another.

**Decision:** every band accepts the same endpoint-complete domains. Difficulty only reweights default choices toward smaller/fewer or larger/more cases.

**Reason and probe:** exact controls at minimum, canonical-like middle, and maximum settings pass in `None`, easy, medium, and hard. Profile-floor results remain healthy: 6/20, 4/20, and 3/20 exact canonical-profile hits by band.

**Rejected alternative:** band-specific validation would make a public exact axis context-dependent and would fail the strict contract gate.

## D5 — Separate broad ownership from constructive training support

**Prior choice:** `self_check` encoded the sampler’s “far apart” design rather than the task’s lawful input grammar, so it rejected canonical examples.

**Decision:** `self_check` and `strict_canonical_like` validate structural ownership: rectangular ARC grids in the supported shape range, 2–4 singleton seeds, and exactly two nonzero colors. The generator itself adds the stronger later-lower overlap guarantee, and semantic hooks test that guarantee.

**Reason and probe:** all canonical inputs are accepted, malformed grids return diagnostics instead of exceptions, and every sampled normal draw is both structurally valid and shortcut-refuting.

**Rejected alternative:** putting the overlap witness into `self_check` would again confuse “lawful task input” with “preferred curriculum sample” and reject valid canonical inputs that do not expose the rival.

## D6 — Use a two-demonstration declared-rival lesson contract

**Decision:** set `EXAMPLES_NEEDED = 2`; declare `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS` for `max_color_wins`; add `later_lower_overlap` and `lesson_identifiable`.

**Reason and probe:** each generated pair individually refutes the rival, so two demonstrations are conservative while matching the lesson assembler’s two-demo/one-query policy. The 300-lesson census materialized 900 unique inputs. Production lessons and all 900 one-pair-held-out rotations had zero ambiguity, warnings, or scoring errors.

**Limit:** this proves the finite declared-rival checks over sampled lessons, not universal identifiability. The same callable is exposed under three framework-facing declaration names, but the census correctly records one unique rival identity.

## D7 — Cache pure geometry after measuring repeated work

**Observation:** construction and defect scanning repeatedly enumerate the same halo sets and valid overlapping seed pairs for a small finite collection of shapes.

**Decision:** use unbounded `lru_cache` on pure `_halo`, `_painted_cells`, and `_pair_candidates` helpers.

**Reason and probe:** cached values depend only on immutable dimensions/cells/profile and cannot alter RNG order or output. Determinism tests compare repeated calls exactly, and the full defect scanner plus battery complete green on the final source.

**Rejected alternative:** caching generated grids or RNG-dependent choices would risk hiding state or collapsing diversity; only pure geometry is cached.

## D8 — Retain failed evidence and fix API boundaries test-first

**Sequence:** initial focused tests failed because canonical examples were rejected. After the main repair, defect lint found that `seed` and `sample_index` still accepted coercible non-integers and negative indices. Dedicated tests were added and observed failing before `_validate_call_arguments` was implemented.

**Decision:** require exact Python integers (excluding `bool`) and require nonnegative `sample_index`. Keep the RED/GREEN logs and interrupted battery journal in the return.

**Reason:** deterministic generation APIs should not silently equate `True`, `1`, and `1.0`, and negative indices are outside the public schedule domain. Evidence is in `checks/tdd-red-call-scalars.log`, `checks/tdd-green-call-scalars.log`, `checks/after-defect-lint-v3.log`, and the final task-test result.

## Distribution limitations accepted in this repair

The sampler uses exactly two nonzero colors and guarantees a precedence conflict in every normal draw. This intentionally over-samples the concept that the canonical set leaves ambiguous. It still varies 2–4 seeds, 40 shape combinations in the declared domain, clipped/full halos, colors, positions, and difficulty weights. Expanding to every lawful number of colors or to lessons without collisions is deferred because it would weaken the teaching guarantee without addressing an assignment requirement.
