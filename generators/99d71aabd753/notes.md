# Working notes: 99d71aabd753

## 2026-10-26 review repair

- Replaced fixed-parent canonical discovery in the portable tests with `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`.
- Confirmed the authority target and canonical ledger program are semantically identical after whitespace normalization; the ledger preserves the human-readable exact canonical source used by parametric default identity.
- Reproduced the catalog audit defect: every sampled ordinary count profile was consecutive, so a rank-plus-maximum rival reconstructed every row length.
- Ordinary generation now samples distinct positive counts containing the requested maximum and requires at least one skipped count. Four-color ordinary lessons therefore draw `max_count >= 5`; explicit boundary overrides retain exact values even when a gap is mathematically impossible.
- Added `rank_step_lengths` as a named rival and `nonconsecutive_count_profile` as a semantic witness.

Verification evidence:
- `WORK/checks/99-rank-gap-red/`: regression fails on the original consecutive sampler.
- `WORK/checks/99-rank-gap-green/`: staged portable suite passes after repair (21 tests).

## Review hardening: dimension-only overrides

A final read-only review found that the original `ordinary = not overrides`
gate accidentally disabled the nonconsecutive-count invariant for unrelated
`grid_h`/`grid_w` overrides. The generator now requires a skipped count whenever
one is mathematically feasible (`max_count > n_colors`), including exact
dimension overrides and compatible count overrides. Only exact count profiles
with `max_count == n_colors` may use consecutive counts because no alternative
exists. The regression test covers all four dimension boundaries, all three
difficulty bands, and 60 deterministic seeds per case.

## Native parametric family

The task-local family varies two episode-fixed settings: `measure` chooses
4-connected object counts versus colored-cell counts, while `alignment` chooses
right- versus left-aligned rendering. The default `objects/right` program is the
exact canonical Racket source. Every episode contains 2--6 demonstrations and
four distinct controller-side queries; inputs are independent of the hidden
setting, and the final query is a substantial edge-spanning 30x30 case.

Current reviewer evidence:

- 30/30 staged tests after RED->GREEN hardening of dimension-only overrides;
- protected self-audit with 192 Racket evaluations over all four settings,
  minimum/maximum lesson sizes, and three seeds;
- authoring preflight with 8 jobs, 48 parametric labelled pairs, 4 canonical
  pairs, and 96 protected Racket evaluations;
- protected causal witness: replacing the object-count intermediate with a
  cell-count intermediate changes row order, output width, and run lengths
  while the rendering stage remains fixed;
- 32 one-query public projections, checked for first-turn equivalence and
  hidden-label privacy; and
- a shared 960-scene property sweep across both assigned families.

Exact diagnostic count overrides retain the requested values even when a full
ordinary control profile is mathematically impossible. Ordinary and parametric
sampling carry the full nonconsecutive/object-versus-cell controls. These are
reviewer-authored checks only; owner qualification, acceptance, and any
training admission remain separate decisions.
