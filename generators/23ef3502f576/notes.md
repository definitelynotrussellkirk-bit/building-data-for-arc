# Working notes: 23ef3502f576

## 2026-10-25 native parametric build

Built `workspace/parametric/adapter.py` with one episode-fixed parameter,
`selector_measure`:

- `marker_count` returns the exact selected canonical Racket source unchanged.
- `marker_runs` counts horizontal runs among the header markers, uses that
  input-derived integer as the panel index, then performs the same whole-panel
  crop and cyan recoloring.

The shared sampler supports 2--6 stable-prefix demonstrations and 1--4
stable-prefix queries on matched inputs.  Query four is exactly 30x30 and has a
three-row header plus three dense 8x30 candidate panels rather than padding.

The first two-demonstration design admitted `header_span` and
`rightmost_bucket` shortcuts under the canonical setting.  The first teaching
header was changed constructively from columns `(0,1,5)` to `(0,1,4)`, after
which the declared 15-policy audit found no query-changing survivor across 128
seeds, both settings, and every demonstration count from two through six.

Staged task tests passed after replacing the legacy test's fixed parent-depth
fixture lookup with bounded `reviewer_support` helpers.  Protected-Racket native
qualification passed at 2, 3, and 6 demonstrations.  The retained causal witness
uses a qualified `marker_runs` query where the correct run count selects panel
1; substituting total marker count selects panel 3 and changes the output.

Limits: finite declared rivals and bounded seeds do not prove universal
identifiability or training value.  The prototype is reviewer-ready only;
owner exact-source qualification/acceptance and any training-admission decision
remain separate.
