# Working notes: 9dc70dbec7cf

## 2026-10-25 native parametric review

- Repaired the retained generator contract: removed ignored `palette_size` and
  `n_distinct_colors` controls, stopped advertising unlawful `no_pairs` /
  `single_pair` textures, and made `n_pairs` plus `palette_kind` exact.
- Preserved the catalog-selected canonical Racket program byte-for-byte as
  `horizontal_then_vertical`; added `vertical_then_horizontal` as the only new
  rule setting.
- Sequential interpretation: A constructs every inclusive ordered L-path;
  the intermediate is the complete per-color path set with duplicate bend
  multiplicity; B aggregates coverage and maps counts to 3/6/9.
- The first implementation accidentally copied the archival all-rules Racket
  bundle.  The exact-source regression failed, so `canonical.rkt` was replaced
  from `Catalog(...)["program_solution"]` before manifesting or qualifying.
- Sampler supports 2–6 demonstrations and 1–4 queries, uses matched inputs
  across settings, is deterministic and prefix-stable, and includes a
  substantive 30×30 query.
- Bounded demo-only audits at seeds 0, 17, and 97 found no tested rival that fit
  demonstrations while changing a private query.  This is finite evidence, not
  a uniqueness proof.
- Protected authoring preflight, wrong-order causal replay, sequential public
  export, first-turn invariance, and task-local tests all passed.  Evidence is
  under `WORK/checks/9dc70dbec7cf/` and
  `WORK/checks/9dc70dbec7cf-task-tests/`.
- Next action: owner reviews the exact two Racket sources and sampler grammar,
  then runs fresh native qualification/acceptance.  No owner acceptance or
  training admission is claimed here.


## Owner control-contract repair

Explicit integer controls now use the full advertised AXES bounds at every
difficulty; difficulty bands only select ordinary values. The generator version
and unoverridden draw bounds are unchanged to preserve seeded examples. Values
outside AXES and non-integer controls fail closed before geometry generation.
Callable diagnostic textures remain outside the lawful AXES contract and can
fail self_check. Only listed axes are supported; removed palette/count controls
are not restored.

Focused owner regressions cover each scalar endpoint at None/easy/medium/hard,
ordinary seeds 17/43, and invalid values. This is finite evidence, not an
exhaustive Cartesian or historical override-battery claim. The retained old
audit's targeted ignored-control/domain findings are addressed by these source
changes; its other historical findings and original evidence remain retained
for explicit owner disposition, not automatically marked resolved.
