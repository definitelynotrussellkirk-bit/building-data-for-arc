# Working notes: 2c784862f42b

## Review outcome

- Baseline SHA-256: `dac8d2fa9781ca9987734f4d7d3acf929f992a4d5f9acdde17ba595ff467d7a2`.
- Final SHA-256: `b036d188d0f5e63b0f467ae32fbbfa55d678e4b76a69bb6d6719f79e2841e691`.
- Canonical rule unchanged; normalized hash pinned as `e8e6e0187218`.
- Final focused tests: 28/28 passed.
- Final source-bound battery: 12/12 stages green.
- Final lesson census: 300 lessons, 1,200 pairs, 1,200 query rotations; zero ambiguities, hook warnings, scoring errors, or materialization errors.

## Important retained failures

1. Untouched baseline: missing rule pin, collapsed/unprobed axes, four dead helpful textures, ordinary/negative texture overlap, silent override failures, and disconnected-prototype acceptance.
2. First repair: difficulty bands were identical (`checks/tdd-red-dead-bands.txt`).
3. First curriculum: ordinary lessons were clean, but 283/1,200 leave-one-out rotations lacked full opcode evidence (`checks/lesson-census-v1-warning.json`).

## Final design

Normal draws expose only one exact pixel-observable axis, `prototype_cells=4..8`. Prototypes are 4-connected keyed-growth shapes. Three deterministic code profiles have disjoint omitted opcode pairs, so any two profile types cover all six operations. Every draw refutes independent-step, swapped-quarter-turn, and swapped-reflection rivals.

## Limitations

The lesson census is finite and rival-bounded. Source colors are selected from nonzero opcodes and targets outside the opcode set; prototypes are limited to connected 4–8-cell, two-dimensional masks. Hidden solve labels remain unknown.
## Current reviewer considerations

Source SHA-256: `b036d188d0f5e63b0f467ae32fbbfa55d678e4b76a69bb6d6719f79e2841e691`.

# Decisions — 2c784862f42b

## D1 — Keep the canonical authority unchanged and pin it

**Input choice.** Preserve the selected Racket rule and set `RULE_HASH = "e8e6e0187218"`; add a Python mirror and an independent task-local oracle.

**Original rationale.** Unknown. The v1.1.0 baseline had no rule pin and no executable Python mirror. Its implementation shape suggested the intended rule, but that was not source synchronization evidence.

**Alternatives considered.** Rewriting the Racket rule was rejected because all five canonical pairs are already solved by the selected authority. Trusting only the baseline sampler was rejected because it could drift while still returning structurally plausible inputs.

**Probes.** Normalize and hash the selected canonical source; run the independent oracle and production mirror on all five public pairs; run `rule_smoke` and `authority_sync` in the final battery.

**Failure modes and limitations.** Hash equality detects authority text drift, not every semantic issue in the Python mirror. Canonical examples are finite, so generated draws and independent semantic rivals are also tested.

## D2 — Replace nominal controls with one exact pixel-observable axis

**Input choice.** Advertise only `prototype_cells`, with exact valid values 4–8 and `observe_overrides` support.

**Original rationale.** Unknown. The baseline exposed fixed dimensions, singleton role labels, hidden shape/sequence indices, four ignored palette names, and negative fixtures inside the ordinary texture domain.

**Alternatives considered.** Retaining `shape` and `sequence` numeric IDs was rejected because the IDs were implementation indices rather than semantic pixel measurements. Retaining palette aliases was rejected because defect lint proved all four were byte-identical to the default draw. Keeping negative textures in `AXES` was rejected because they are not lawful training examples.

**Probes.** Exact overrides 4 and 8 in every band; complete domain coverage through the override checker; misspelled, Boolean, float, string, and out-of-range values; pixel recovery with `observe_overrides`.

**Failure modes and limitations.** Cell count alone does not expose morphology. Morphology remains diverse through constructive growth but is intentionally not promised as an exact override.

## D3 — Generate connected asymmetric prototypes constructively

**Input choice.** Grow a 4-connected set inside the full 5×5 frame, require at least two rows and two columns, and return only shapes that refute all declared rivals. Keep one checked fallback per cell count.

**Original rationale.** The baseline selected from five static shapes and only counted nonzero cells. It did not reject a disconnected equal-cardinality impostor.

**Alternatives considered.** An expanded static shape bank was simpler but preserved a finite morphology shortcut. Uniform arbitrary cell subsets were rejected because disconnected or one-dimensional shapes are common. Rejection without a bounded fallback was rejected because it leaves a low-probability nontermination/failure path.

**Probes.** Disconnected mutation regression; 96 default draws in each of four band settings; freshness, determinism, global RNG isolation, hash-seed independence, and authority parity.

**Failure modes and limitations.** The growth distribution is not uniform over polyominoes. Shapes are restricted to 4–8 cells and at least two rows/columns. The fallback library is finite, although it is reached only after 256 failed rival-separating attempts and is revalidated before return.

## D4 — Use a semantic three-profile opcode curriculum

**Input choice.** Schedule `codes_0124`, `codes_0345`, and `codes_1235` by `sample_index mod 3`; each sequence has four distinct opcodes. Their omitted pairs are disjoint, so any two profile types cover all six opcodes.

**Original rationale.** The baseline randomly selected one of five sequence indices. It declared no `EXAMPLES_NEEDED`, rivals, witnesses, or lesson-identifiability hook.

**Alternatives considered.** Fully random sequences were rejected because complete lesson coverage would be probabilistic. Replaying canonical sequences was rejected because it would narrow training to public examples. The first repair used profile sets that covered all opcodes across the default three consecutive examples, but the rotated census showed that a held-out pair could remove the only occurrence of an opcode; that design was superseded.

**Probes.** Every cyclic three-profile start; each generated input against three rivals; `lesson_identifiable`; 300 source-bound four-pair lessons; all 1,200 leave-one-out query rotations.

**Failure modes and limitations.** The schedule is periodic and covers only the declared three semantic rivals. It does not prove that no more exotic shortcut can fit a finite lesson.

## D5 — Make difficulty change priors without clipping exact controls

**Input choice.** Easy, medium, and hard use different weighted priors over the same full 4–8 domain. Explicit overrides retain all exact values in every band.

**Original rationale.** The baseline clipped shape and sequence indices by difficulty. The first repair accidentally ignored difficulty entirely, producing byte-identical draws for each seed.

**Alternatives considered.** Band-exclusive ranges were rejected because they would make exact values unavailable in some bands. Pure uniform draws in every band were rejected after `dead-bands` reproduced identical instances.

**Probes.** Retained failing linter and focused test, then 64 default draws per band showing ordered mean cell counts; exact 4 and 8 overrides in all bands; final defect lint.

**Failure modes and limitations.** Bands overlap substantially and encode only prototype size priors, not a calibrated model difficulty score.

## D6 — Declare and execute concrete semantic rivals

**Input choice.** Add rivals for independent rather than cumulative steps, swapped quarter-turn direction, and swapped reflection axes; expose matching witnesses and lesson competitors.

**Original rationale.** Unknown; the baseline had none.

**Alternatives considered.** A generic “output differs from input” check was rejected because it says nothing about opcode interpretation. Declaring rivals by name without executable functions was rejected because the lesson census could not score them.

**Probes.** Every normal draw is required to differ from all three rival outputs; canonical pairs verify none is an honest `CANONICAL_SHORTCUT`; semantic gate and lesson census execute the declarations.

**Failure modes and limitations.** Rival coverage is hypothesis-driven, not exhaustive. `CANONICAL_SHORTCUTS` is intentionally empty because none of these rivals fits every public pair.

## D7 — Separate reusable independent probes from production code

**Input choice.** Put canonical loading, normalized hash calculation, independent transforms, structural extraction, and rival output helpers in `workspace/reference_probe.py`; tests may point it at a retained candidate with `GENERATOR_UNDER_TEST`.

**Original rationale.** The task workspace was empty.

**Alternatives considered.** Importing production `_transform` into tests was rejected because a mirrored bug could pass both implementation and test. Copying full canonical data into tests was rejected because it would duplicate authority and make drift harder to see.

**Probes.** Baseline red run through an external candidate path; final direct and portable task-test runs; all five canonical pairs loaded from the repository ledger.

**Failure modes and limitations.** The probe still relies on repository file locations and the selected canonical JSON schema. It is task-local rather than a generic cross-task oracle.
