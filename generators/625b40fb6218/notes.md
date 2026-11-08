# Current notes: 625b40fb6218

## Canonical behavior and sampling

Version 2.0.0; canonical RULE_HASH 53f987296312. A centered full-height color-5 separator divides equal-width panels. Left-only cells become 2, right-only cells become 1, and all other positions retain the left value. Canonical programs, rows and the input sampler remain unchanged in review-80324849a7320b6c.

The constructive grammar retains exact height, panel width, palette size, and four occupancy-branch counts. Foreground colors are 3,4,6,7,8,9. Overrides use the same bounds in every difficulty band. Eight profiles retain canonical shape/palette anchors and boundary coverage; the profile formula is seed + 2*sample_index + band_offset modulo eight. This replaced the earlier aliased formula and should remain tested with paired seed/index sweeps. Ordinary draws always contain unequal overlaps; explicit zero-conflict overrides preserve canonical support.

## Lesson gate: repaired color-priority omission

Previously the gate considered only equal-overlap-only and right-priority shortcuts. The retained audit review-eb6777d8142a596c:v0001 demonstrates another failure: seed 11180556991150295210, demos 6–9, query 10. Prefer-yellow-on-overlap fits all demos, but changes query coordinate (1,6) from 3 to 4. The prior gate accepted it.

The gate now also checks a favorite-color competitor for each legal foreground color. It rejects only a competitor that fits every demonstration and changes the query answer. The original SEMANTIC_RIVALS and CANONICAL_SHORTCUTS sets remain unchanged; the larger LESSON_COMPETITORS set is an explicit teaching-gate extension.

The baseline source SHA-256 was 686b9f2d186723ef95a977fe43eb0f3829c023ab1de49e19e51272b89eceb632; repaired source SHA-256 is 7e1ea8eabb20d0d126d52648217fcd31552f438c90bcf111419051f4c17b9429. Fresh evidence in this return: 15 Racket-verified labels covering eight canonical occurrences, the five-pair retained witness, and two minimal pairs; 32 baseline/current sampled inputs match exactly. The minimal task-owned fixture is counterexamples/color-priority-gate.json.

This is a gate repair, not a claim that every ordinary lesson is now identified. The existing small diagnostic contains 19 rejected query rotations out of 60 under the expanded gate. Its tests now independently check the missing color-conflict coverage instead of assuming universal acceptance. Consumers must enforce the gate or construct distinguishing demonstrations.

The retained audit's status was not edited: the demonstrated repair and source-bound evidence are ready for explicit maintainer assessment. Broader inherited batteries/censuses were not rerun for this bounded change.

## Proposed parameter family

workspace/parametric/prototype.py adds one episode-fixed conflict_policy: left (the exact canonical program), right, or erase. Only unequal occupied overlaps change. This preserves panel alignment, exclusive-cell marking, equal-overlap behavior and output dimensions.

Two constructive teaching demonstrations use disjoint three-color cycles, exposing every foreground color on both sides of a conflict. Separate count controls support 2..8 demonstrations and 1..16 distinct queries. The standard comparison command in the adjacent README produces all three policies with the same input seed and four queries per episode.

Saved labels come from protected Racket. The verifier reexecutes them, checks source/program/runtime identity and lineage, and recomputes a demonstration-only certificate over 14 declared alternatives. Public files use the shared visible-byte projection and content hashes; private settings, programs, query answers and certificates remain separate. Duplicate visible payloads are rejected.

Independent review found missing checks for schema, parent lineage and stored runtime metadata; focused failing regressions preceded the fix. Runtime paths may relocate while the stable content hashes and security claims must match the live verifier.

This remains an opt-in proposed prototype, not production registration, variant approval or training admission. Finite rivals do not establish uniqueness against arbitrary programs. Sparse scenes and the existing profile schedule remain distribution limits; hidden generation metadata must stay private.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: generators/625b40fb6218/evidence/supplementary-current.json. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
