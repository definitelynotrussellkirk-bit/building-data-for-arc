# Working notes: 0162460030af

## Current rule and domain

Sort all nonzero 4-connected components by leftmost occupied column. For component index `i` among `n`, paint it `8` when `(n - i)` is odd and `2` otherwise; therefore the rightmost object is always `8`. Background remains `0`. The generator supports heights 4–14, 2–9 objects, source colors 1–9, six connected shapes, spacing 2–3, and optional mixed shapes/colors. Width is constructively bounded to 30.

## Decisions and reversals

- **Baseline negative textures removed.** Version 2.1.1 advertised `single_object`, `all_same_left_edge`, and `no_objects` in the ordinary `texture` domain even though they hid the rule or failed `self_check`. Version 3.0.0 removes `texture`; unknown axes and invalid values fail before generation. Reproducer: `counterexamples/baseline_texture_no_objects.json`.
- **Retry/fallback placement replaced.** The baseline retried merge-prone layouts and silently fell back to single cells, so requested shape controls were not trustworthy. The current constructor places every declared combination directly and verifies every realized axis with `observe_overrides`.
- **Difficulty no longer narrows explicit controls.** Difficulty selects default distributions only. Exact legal overrides use the full advertised domain in every band.
- **Boolean boundary corrected.** An intermediate validator accepted only integer `0/1`; the public override checker probes literal `False/True`. Both forms are now accepted and observed as booleans.
- **Canonical-anchor diversity corrected.** An intermediate spacing-2 layout fixed objects to top/bottom rows, causing one identical `sample_index=0` grid across 40 seeds. It now chooses a seeded pair of disjoint two-row bands while preserving exact canonical profiles. Reproducer: `counterexamples/canonical_anchor_seed_collapse.json`.
- **Authority text synchronized without semantic change.** The selected base solution text now exactly matches canonical rule hash `617100877d72`; before and after behavior agreed on sampled inputs.

## Teaching contract

Every third default index is a canonical anchor; intervening indices use non-2 source colors and non-2×2 shapes. Object-count parity alternates by index. The executable rivals are: leftmost-always-8, only-color-2-objects-change, and only-solid-2×2-objects-change. `lesson_identifiable` checks that demonstrations determine the query against all declared rivals. Task-local tests exhaust starts 0–11 in all three bands and all four query holdouts.

## Measured final limits

The final 300-lesson census (100 per band) materialized 1,200 pairs and 1,200 query rotations with zero declared-rival ambiguities; 885 inputs were unique. This is finite evidence only: it does not prove uniqueness against undeclared hypotheses or all seeds. The task remains a single-operation positional recoloring rule; no extra ARC operation was added merely to increase composition complexity.

## Current maintainer source selection

Only selected `racket_target.target_code` changes are retained; original archival `raw_code`, the canonical ledger and selected canonical rule are preserved. For 0162460030af, the return rewrote the archival field too; that part was reversed. Owner static field/byte checks are recorded in `evidence/current-authority-sync.json`. Returned fresh-copy test/battery results remain reviewer-reported, and the corrected owner source has not had a new battery.
## Current reviewer considerations

Source SHA-256: `2d336cd5cc2d3e0e432f1b2aaac28ba0fe428f6040f3f0f395ed0ad69a0102e6`.

# Decisions — review-44570f1e4bbb012f

## D1 / R1 — validate the public call before constructing context

**Decision.** Require `type(seed) is int`; require `type(sample_index) is int`
and `sample_index >= 0`; require `difficulty` to be exactly `None`, `easy`,
`medium`, or `hard`. Keep the existing override validator unchanged.

**Why.** The strict-lint reproductions showed coercion/collision risk at the
identity boundary: booleans, floats, text, and negative indices were accepted.
Validating at the generator entry point fixes the source of the defect before
`gen_ctx` can normalize or hash an invalid value.

**Alternatives rejected.** Letting `gen_ctx` coerce values would preserve the
collision. Validating only the one initially reported difficulty string would
leave seed and index defects. A library-wide change was outside this task's
allowed patch; that shared improvement is F1 in `FEEDBACK_TO_CODEX.md`.

**Version choice.** `VERSION` remains `3.0.0` because valid calls generate through
the identical code path and canonical rule. The change is fail-closed behavior
for inputs that were never in the advertised contract.

## D2 / P1 — use `anchor_side` as the original-family parameter

**Decision.** Prototype one episode-level parameter with values `right` and
`left`. `right` is the canonical default; `left` preserves object extraction,
horizontal ordering, alternating colors, and output shape while changing which
end fixes the phase.

**Why this parameter.** It is small, interpretable, and meaningfully changes the
rule without replacing its reasoning pattern. It also provides a crisp
identifiability test: odd object counts are invariant, while even counts
separate the two settings.

**Alternatives rejected.** Swapping output colors duplicates the same phase
change but obscures the spatial role. Varying sort direction is algebraically
entangled with the anchor and would make the parameter less isolated. Varying
connectivity or object ordering would change the underlying object grammar,
not just one original-family rule choice.

## D3 / P1 — choose once per episode and require a demonstration witness

**Decision.** Select the anchor once from the episode seed and use it for all
three demonstrations and the query. Include even-count demonstrations in every
episode, then execute both parameter rivals against the complete episode.

**Why.** Per-pair resampling creates internally inconsistent supervision. An
odd-only demonstration set can fit both settings while an even query differs,
which is a reproducible teaching ambiguity. The evidence writer therefore
requires one setting to fit every label and any query-changing rival to be
contradicted by at least one demonstration.

**Limit.** The prototype covers two seeds and four authored input grids. It is a
runnable authoring probe, not a claim that every possible parameterized episode
is identifiable.

## D4 — isolate the proposal from canonical execution

The production generator, selected Racket authority, `RULE_HASH`, and canonical
labels were not changed. Prototype Racket and private labels live only under
`workspace/parametric/` and `checks/parametric/`. This prevents a successful
bounded repair from being mistaken for approval of a new rule family.

## D5 / L1 — retain the existing lesson schedule after source-bound verification

The production schedule uses three demonstrations and one query from consecutive
accepted indices. I retained it because the final 100-per-band census found no
ambiguity against the declared rivals in 300 production lessons or 1,200 query
rotations. The decision is limited to those rivals and sampled seeds; no
universal induction claim is made.

## D6 — stopping and evidence policy

I stopped after the final source passed 72 task tests, all 12 battery stages, the
large rotated census, a fresh visible-only solve, and both required audits. I
retained the initial and intermediate failing evidence, while using concise
summary files in the intake paths where the full report would add size without
changing the conclusion.
