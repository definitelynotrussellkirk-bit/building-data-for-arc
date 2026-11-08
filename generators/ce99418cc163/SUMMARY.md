# ce99418cc163 — simultaneous rectangle-corner completion

Version: **2.0.0**. Kind: `per_puzzle`. Canonical `RULE_HASH`: `bc2eb2b8f3e7`.

The only evidence color is red (2). Paint green (3) at an original zero cell
exactly when three original red cells support the other corners of an
axis-aligned rectangle. Preserve all occupied cells. All writes are simultaneous;
a newly painted corner never supplies additional evidence.

The input sampler covers a single L, two independent Ls, shared-rail interacting
rectangles, and a five-red chain. It varies coordinate order, spacing, transpose,
canvas dimensions, irrelevant color, ordinary distractors and occupied supported
corners. Every three consecutive **default** draws include a blocked chain that
refutes both the overwrite-occupied and iterative-completion rivals.

Exact controls: `grid_h`, `grid_w` (4–20 in every band), `layout`
(`single|separate|shared|chain`), `n_blockers` (0–1), `n_distractors` (0–6).
A blocked single L or a noise count exceeding available space is explicitly
incompatible. Old inert axes, including `missing_corner`, palette controls and
`texture`, are retired and raise `ValueError`; this is an intentional major
version change rather than silently accepting ineffective requests.

Racket alone supplies labels. Python diagnostic predictors are test/rival tools.
The canonical ledger and rule semantics were not changed. The selected archived
`target_code` was synchronized to the already-canonical `raw_code` by deleting
one redundant comment.

Scope: four red-incidence graph families, not arbitrary arrangements. Default
size is strongly weighted toward 10×12 and the distractor count toward 3–4;
blocked teaching grids are correlated with chain layout. Three-example coverage
does not survive arbitrary resampling or shortened demonstration sets.

Focused tests: `python3 run_with_racket.py python3 -m pytest generators/ce99418cc163/tests -q`.
See `workspace/README.md` for source-bound census, assembly-mutation and replay
probes. Passing checks does **not** grant training approval.
