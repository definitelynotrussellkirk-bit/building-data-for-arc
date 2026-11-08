# Working notes: 69c39a5f416b

## 2026-10-02 review diagnosis

The imported `2.0.1` generator described and emitted a vertical-gallery motif-packing task. That family is unrelated to the canonical task, whose demonstrations encode a two-row old-color→new-color key followed by a body that is recolored and cropped. The before battery reproduced the mismatch: lint/defect/distribution/override checks failed, canonical linked profiles were absent, and there was no rule hash or semantic contract.

## Repair

Version `3.0.0` is a semantic replacement rather than a local patch. It:

- emits a two-row aligned key and sparse source-colored body;
- mirrors the selected canonical Racket rule exactly and declares `RULE_HASH = d3105e4a99fb`;
- schedules the three canonical `(height, width, full-palette-size)` profiles at slots 0, 2 and 4;
- interleaves scattered-key profiles at slots 1, 3 and 5;
- makes every declared axis observable and exactly overrideable;
- includes self-checks, canonical-like checks, semantic witnesses and named rivals;
- exposes overlapping chain/swap maps so one-step replacement is distinguishable from cascading replacement;
- exposes key pairs after column 2 so the strongest canonical-compatible rival, “read only the first three columns,” is falsified by generated demonstrations.

Regression tests live in `tests/test_generator_69c39a5f416b.py`. A reusable exact shortcut probe is retained in `workspace/shortcut_probe.py` with its JSON output.

## Remaining limitations

The body is intentionally sparse and uses only keyed source colors, matching the canonical family. It does not test behavior on unkeyed foreground colors because the canonical demonstrations do not establish whether such colors should be preserved, rejected, or transformed. The six-slot schedule is deterministic by sample index; randomness remains within palette, key positions and body placement.
## Current reviewer considerations

Source SHA-256: `3b6fb73dc7a2c5203fe17a3f8af00904dc4ce2481159dc8876f20dde3ee64944`.

# Design decisions: 69c39a5f416b

## D1 — Replace, rather than patch, the imported family

**Original choice and rationale.** The imported source described a vertical-gallery motif pack. No retained note explained why that family was associated with this task, so the rationale is unknown.

**Decision.** Replace the implementation semantically. The canonical examples and selected executable rule agree on a two-row source→destination key; preserving gallery-pack machinery would only hide the root defect.

**Alternatives rejected.** Retuning gallery dimensions, colors or object counts could improve marginal profile checks but could never teach the correct transformation. Wrapping the wrong generator in a permissive self-check would make checks less informative.

**Probe.** The before battery showed 0/60 canonical-profile matches and unreachable canonical palettes; direct canonical-pair application showed the actual row-key rule.

**Failure mode.** A full replacement can accidentally overfit official examples. The remaining decisions counter that with generalized layouts, pair counts, overlap classes and named rivals.

## D2 — Preserve the selected Racket authority

**Decision.** Do not edit the canonical program. Pin `RULE_HASH = d3105e4a99fb` and make the generator conform to it.

**Rationale.** The selected Racket program solves every official pair, passes smoke tests, and has synchronized selected sources. The defect was entirely in the generator/distribution.

**Alternative rejected.** Rewriting Racket for style or to narrow its domain would create unnecessary authority drift.

**Limitation.** The executable rule preserves unkeyed body colors, but the canonical task never demonstrates them. The generator intentionally stays inside the demonstrated source-only body domain.

## D3 — Use an aligned two-row key

**Decision.** Every nonzero row-0 cell is a source; the row-1 cell in the same column is its destination. Require both entries, unique sources, unique destinations and nonidentity pairs.

**Rationale.** This is the smallest grammar that explains all official examples and is directly visible to a solver.

**Alternatives rejected.** A contiguous-only legend would preserve the canonical positional accident. Allowing half-pairs, duplicate sources or identity pairs would create ambiguity or hide whether recoloring fired.

**Probe.** Structural mutation tests remove the legend, erase half a pair, duplicate a source and create an identity pair; each must be rejected.

## D4 — Vary legend position explicitly

**Decision.** Support `left`, `shifted` and `scattered` layouts. Scattered layouts must contain a key column at index 3 or later.

**Rationale.** All official keys occupy the first three columns, so the strongest plausible shortcut is “read only columns 0–2.” Late columns are the minimal direct rebuttal.

**Alternatives rejected.** Randomizing only within columns 0–2 adds visual noise without refuting the shortcut. Always scattering would lose exact canonical-profile support.

**Probe.** The retained seed-123 sample has key columns `[1,4,6,7]`; Racket and the shortcut differ in 9 output cells.

**Failure mode.** A late key that is unused in the body would not teach anything. `self_check` therefore requires every source to occur below the key.

## D5 — Include disjoint, chain and swap mappings

**Decision.** Make mapping overlap an explicit observable axis.

**Rationale.** Disjoint mappings alone cannot distinguish simultaneous one-pass replacement from iterative/cascading replacement. A chain or swap makes the distinction observable.

**Alternatives rejected.** Identity pairs were rejected because they weaken evidence. Arbitrary many-to-one destinations were not used because the canonical examples use unique destinations and uniqueness makes the mapping visually legible.

**Probe.** The overlapping-mapping witness fires in 374/600 after-battery semantic draws; the cascading rival is checked on 60/60 claims.

**Limitation.** The generator does not cover duplicate destinations, so it does not teach behavior outside the canonical permutation-like key grammar.

## D6 — Use a six-slot deterministic curriculum

**Decision.** Schedule profiles by `sample_index mod 6`; place canonical-linked profiles at 0, 2 and 4 and rebuttal profiles at 1, 3 and 5.

**Rationale.** Deterministic coverage prevents unlucky batches from omitting a canonical profile or a shortcut witness. Interleaving ensures every three-example window contains relevant evidence.

**Alternatives rejected.** Pure random profile selection can produce three demonstrations that all preserve the same shortcut. A longer schedule adds complexity without improving the three-demo guarantee.

**Probe.** Tests enumerate sliding windows and assert lesson identifiability against every registered competitor.

**Failure mode.** The profile identity is predictable. This is acceptable because nuisance details remain seeded and profile scheduling is curriculum control, not a puzzle clue exposed in-grid.

## D7 — Match linked canonical profiles, not only marginal ranges

**Decision.** Profiles 0, 2 and 4 target exact `(height, width, full palette size)` signatures `(8,8,7)`, `(8,9,5)` and `(9,9,6)`.

**Rationale.** The old generator could not reach official linked morphology. Matching only individual ranges could still pair the wrong size with the wrong palette.

**Alternatives rejected.** A broad uniform size/palette draw would pass some marginal gates while undersampling exact official combinations.

**Probe.** The profile-floor stage improved from 0/60 exact and 0/60 envelope to 30/60 exact and 33/60 envelope.

## D8 — Keep bodies sparse but vary geometry

**Decision.** Use connected small motifs on canonical-linked profiles and dispersed repeated cells on rebuttal profiles. Keep at most 20 foreground body cells and require at least two occupied rows.

**Rationale.** Connected motifs preserve official visual scale; scattered repetitions show that object topology is irrelevant and ensure all mappings are exercised.

**Alternatives rejected.** Dense random fills would depart from the canonical visual family. A single occurrence per color would permit object-count and positional memorization.

**Limitation.** The body family is still intentionally sparse; the task does not test high-density recoloring.

## D9 — Expose only exact, observable controls

**Decision.** Public axes are dimensions, pair count, legend layout and mapping kind. All use `GenCtx`, round-trip through `observe_overrides`, accept their full declared domains in every difficulty band and reject unknown names.

**Rationale.** The old source exposed dead aliases, silently ignored values and band-local incompatibilities, causing 11,223 findings.

**Alternatives rejected.** Palette labels and body-geometry names were kept as seeded nuisance variation rather than pseudo-axes because exact observation would be fragile or semantically weak.

**Probe.** Boundary cross-product tests cover all difficulty bands and combinations. The after override gate accepted 16,110/16,110 draws with 0 findings.

## D10 — Make semantic shortcuts executable

**Decision.** Register four rivals and four witnesses, plus `lesson_identifiable`.

**Rationale.** Structural validity alone cannot establish that demonstrations teach the intended operation. Executable rivals turn claims into falsifiable tests.

**Alternatives rejected.** Natural-language counter-hypotheses without code cannot be automatically checked. Registering every imaginable wrong rule would be unbounded; the selected four cover crop, recolor, key-span and replacement-order errors.

**Probe.** The semantic gate reports 600/600 strict draws, 4/4 witnesses, 4/4 rival claims and 12/12 identifiable lessons.

## D11 — Retain a reusable exact shortcut probe

**Decision.** Add `workspace/shortcut_probe.py`, its Racket-backed episode and machine-readable result.

**Rationale.** Future reviewers should be able to replay the strongest shortcut disagreement without reconstructing the case or trusting prose.

**Alternative rejected.** Keeping only a unit assertion proves behavior but does not give a compact exact input/output artifact for human review.

**Limitation.** The script imports the task-local generator and expects the retained episode path; it is deliberately task-specific rather than a general audit framework.
