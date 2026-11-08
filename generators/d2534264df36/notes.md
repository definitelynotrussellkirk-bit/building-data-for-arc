# Working notes: d2534264df36

## Decision

Retained audit `review-fc348b89038d388a-v0001` showed that the selected
training grammar always supplies same-color side witnesses in pairs: a
`paired_only` rival matched 1,050/1,050 generated inputs, while the canonical
Racket authority independently propagates a singleton side source. I left the
approved canonical generator and canonical rule unchanged and built a separate
native parametric family under `workspace/parametric/`.

## Family

The episode-fixed parameter is `cross_stop`:

- `complete_only`: byte-exact canonical rule.
- `nearest_hit`: complete rings, select the nearest nonzero hit on the completed
  north hub ray, then use that hit's row/color to fill only blank cells of the
  interior orthogonal cross.
- `farthest_hit`: the same composition using the farthest hit.

The minimum two demonstrations are both 19x19 and each contains a
singleton-row, singleton-column, and paired side witness. This repairs the
paired-only induction hole without introducing a size cue. Query sizes include
23, 27, 30, and 19; supported requests are independently bounded to 2-6 demos
and 4-8 queries. Inputs are matched across parameter settings.

## Sequential dependency

Step A executes canonical ring completion. The intermediate is the ordered set
of nonzero hits on the completed north hub ray, including the selected hit row
and side color. Step B uses that intermediate to choose the cross extent and
fill color. The raw source has a blank hub ray; a protected-Racket skip-A
counterfactual therefore removes every hit and changes the final output.

## Evidence and verification

- Focused parametric suite: 11/11 passed.
- Staged portable target suite: 22/22 passed. This run found and repaired fixed
  repository-depth assumptions in both the inherited canonical test and the new
  parametric test.
- Native qualification: 6/6 jobs passed (3 settings x seeds 71 and 83, each
  with 3 demonstrations and 4 queries); 78 protected-Racket evaluations.
- Self-audit: all five authored rivals (`paired_only`, `row_axis_only`,
  `column_axis_only`, `fixed_middle_hit`, `corner_color_cross`) are contradicted
  by the visible minimum demonstrations for every setting.
- Bounded structural sweep: 256 seeds / 768 setting episodes / 3,840 authored
  rival checks, plus 32 maximum-count episodes, passed without ambiguity or
  collisions. This sweep uses the independent Python oracle; protected Racket
  remains label authority.
- Sequential witness: two 30x30 skip-A cases replayed through protected Racket;
  the static admission validator accepted the source-bound witness.
- Final binding: source-binding SHA-256
  `ad6d678397c553d62b482a521b9dcf18ea0f05d68997395f52a83e18a7e66f92`;
  manifest SHA-256
  `de7a6fdeb6ac8f08f92e845aa8da5e1f6eb870bafbced56209d0fc6dce47f74a`.

## Status and limits

Reviewer-ready / owner-pending. The native qualifier reports `qualified`, not
`accepted`; training is not admitted. Finite seeds and authored rivals do not
prove universal identifiability or measured training gain. Optional peers
`11ebef5b0986` and `151f4dc0c08f` were left unchanged after completing MAIN.
