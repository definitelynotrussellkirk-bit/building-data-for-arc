# Working notes: dd038eb3d459

## 2026-10-03 review: exact interface and corner-key identifiability

The selected v2.1 source executed the intended rule but did not pin `RULE_HASH`, silently accepted unknown overrides, advertised dead or overlapping controls, and supplied no executable rival/witness contract. The before battery had 6 green, 2 advisory, and 4 failed stages (`lint`, `defect_lint`, `override`, `authority_sync`); override diagnostics contained at least 18,549 findings.

The strongest plausible canonical-fitting rival maps the top-left blue key to 180° instead of 0° while preserving TR/BR/BL. It fits all five available canonical pairs because their only TL green shape is 180°-symmetric. Version 3.0 schedules TL/TR/BR/BL across every four examples and selects TL shape pairs only when the official 0° XOR differs from the 180° rival.

The exact public controls are now canvas height `8..10`, canvas width `10..12`, corner `tl|tr|br|bl`, red size `3..5`, and green size `3..5`. Unknown or malformed overrides fail loudly. Ordinary defaults cycle through the five canonical canvas profiles, use all normalized connected 3–5-cell subsets of a 3x3 box, and place the two shapes with a one-cell Chebyshev buffer.

The independent task-local probe materialized 100 four-demo lessons per difficulty band through the canonical Racket runner: 300 lessons, 1,500 unique inputs, zero materialization errors, zero unidentifiable lessons, and zero surviving declared-rival windows. Every band had 125 examples at each corner and 100 examples at each of the five canvas profiles.

The selected bank Racket `target_code` was synchronized byte-for-byte with its retained `raw_code`; no rule semantics or canonical row changed. The final general battery is 12/12 green and the source-bound task tests are 7/7 green.

Known limits: the teaching domain intentionally stays at canonical canvas scale, uses one red and one green 3–5-cell polyomino, fixed colors, and one-cell separation. The semantic claim is limited to the declared canonical-fitting rival, not universal induction over every imaginable solver.
## Current reviewer considerations

Source SHA-256: `e873df6c30d6fc14727c9152cb2af0c64d4d7505221cf9ef3ef9b53b6d4bad09`.

# DECISIONS — dd038eb3d459

## Goal and baseline

The repair goal was not merely to make the inherited linter green. It was to make the generator's public contract true, retain the canonical task, and ensure a complete generated lesson distinguishes the intended corner-to-rotation mapping from the strongest rule that the canonical pairs leave ambiguous.

The baseline v2.1 source was treated as a lead, not as evidence. I first ran the full before battery. Its 18,629 override findings showed that the main defect was interface/coverage design rather than the XOR oracle: the generator executed the canonical pairs, but its advertised dimensions, palettes, texture aliases, and degenerates were inconsistent with what it generated or validated.

## Rule interpretation

The intended transform is:

1. locate the single blue corner key;
2. map TL/TR/BR/BL to 0/1/2/3 clockwise quarter-turns;
3. normalize red;
4. rotate and normalize green;
5. take the symmetric difference of occupied cells;
6. normalize the result and paint the tight crop cyan.

I kept the canonical Racket rule unchanged. The selected bank JSON contained semantically equivalent but textually divergent `target_code`; I synchronized it to the retained `raw_code` so exact authority checks no longer depend on duplicate comment formatting. Canonical `puzzles.jsonl` was not edited.

## Strongest rival and curriculum size

The strongest plausible rival is `top_left_is_180_degrees`: use the correct mapping for TR/BR/BL but rotate the green shape 180° for TL. It fits all five available canonical pairs because their only TL green object is a vertical three-cell bar and therefore 180°-symmetric.

I set `EXAMPLES_NEEDED = 4` and scheduled one example per corner. Four is the minimum lesson size that can show all four key values without relying on random coverage. Every TL shape pair is filtered so its official 0° answer differs from the rival's 180° answer. Therefore every cyclic four-demo window contains a direct counterexample, regardless of starting residue.

A rejected alternative was a “top-row keys use the opposite rotation” rival. It looked plausible initially but fails a canonical pair, so it was not retained as a canonical shortcut. Another rejected option was random corner sampling with a witness-rate target; a high marginal TL frequency would not guarantee that each complete lesson contains the witness.

## Public controls

I removed controls that were aliases, singleton claims, diagnostics masquerading as generation axes, or unlawful degenerates. The final five controls are exact and observable from the returned grid: height, width, corner, red size, and green size.

I chose height `8..10` and width `10..12`, not the old broad 8–18-style description, because these ranges match the five retained canonical profiles and every advertised value can be produced exactly. The first revised draft still advertised wider canvas ranges than ordinary sampling supported; defect lint caught that mismatch, and I narrowed the declarations rather than manufacturing token support solely to satisfy metadata.

Unknown keys are rejected instead of ignored. Invalid types reject booleans as integers, out-of-range values reject before sampling, and unsupported difficulty names reject explicitly. No incompatible override pairs are needed because all Cartesian combinations of the five final domains are lawful.

## Shape distribution

For each size 3, 4, and 5, the generator enumerates every normalized 4-connected subset of a 3×3 box: 6, 17, and 37 shapes respectively. This gives a finite, auditable bank with substantially more structural variety than hand-selected templates while keeping output crops and placements easy to validate.

I rejected two alternatives:

- Canonical-only object templates would preserve profile appearance but make shape memorization too easy.
- Arbitrary large polyomino growth would add breadth but complicate exact override support, placement feasibility, and lesson verification without addressing the identified corner-map ambiguity.

Red and green are placed in opposite canvas regions with a one-cell Chebyshev buffer. This is constructive rather than retry-heavy, so every exact override combination remains fast and deterministic.

## Canvas and difficulty schedule

The five canvas profiles are `(8,10)`, `(9,11)`, `(10,10)`, `(9,12)`, and `(10,12)`. Defaults cycle through these profiles by sample index. Red and green sizes cycle through 3–5 with a difficulty-aware phase shift; difficulty changes curriculum ordering without changing task semantics.

The corner schedule is independent of seed and visible in the input itself. Although sample-index periodicity exists, memorizing it is not a viable grid-only shortcut: the blue key supplies the same information directly, and the episode sampler does not expose sample indices to a solver.

## Performance decision

The first correct revision was too slow under exhaustive contract probing because it repeatedly rebuilt all lawful shape pairs and searched placements. I retained the failed/interrupted evidence, cached `_shape_pairs(red_size, green_size, code)`, and replaced exhaustive placement enumeration with bounded constructive placement. The optimized generator remained test-identical and reduced local generation cost by roughly two orders of magnitude in the retained benchmark notes.

## Tests and reusable probe

Tests were written to fail before the production repair. The red run failed specifically for the missing rule pin, schedule, observer, semantic rival, and exact override behavior. The final seven tests cover canonical ownership, boundaries, malformed calls, deterministic purity, diversity, and every cyclic four-demo lesson window.

`workspace/lesson_probe.py` is intentionally declaration-driven: it iterates the selected generator's actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, verifies that claimed shortcuts fit the canonical pairs, materializes labels through Racket, and records exact first counterexamples. This avoids a stale hard-coded rival list in future reviews.

## Failure evidence retained

I retained failed or incomplete invocations rather than rewriting history:

- the before battery and its four failed stages;
- TDD red results;
- the first slow defect-lint run and the intermediate axis-span warning;
- two incorrectly rooted lesson-probe launches;
- the first full-after launch that rejected a pre-created output directory;
- the noninteractive after run interrupted by orchestration after three passing stages;
- the invalid audit generate call using `--test 0`.

Only `checks/after-full/` is used as the completed final battery.

## Limitations and stopping decision

The repaired domain intentionally stays close to the canonical grammar: fixed colors, one blue corner, one red and one green connected object, 3–5 cells each, canonical-scale canvases, separation, and nonempty XOR. It does not claim to teach multi-object parsing, color permutation, touching objects, giant shapes, or arbitrary canvas scale.

The large probe tested 300 lessons and the declared rival. It does not prove universal program induction. I stopped because the exact interface, canonical authority, task tests, full battery, large lesson probe, post-repair solve, audits, and fresh-handoff replay all had concrete acceptance criteria; adding unrelated axes would weaken rather than strengthen this focused repair.
