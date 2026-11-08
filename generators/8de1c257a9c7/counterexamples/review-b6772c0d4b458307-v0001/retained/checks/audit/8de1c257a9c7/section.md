## 8de1c257a9c7

**Finding: reproduced cardinality shortcut; medium-priority distribution/domain
question. No incorrect generated label found.** This is a findings-only audit;
the target generator, tests, notes, and Racket authority were not edited.

The audited generator SHA-256 is
`ab38bc7be7f5af70dad4fb92ba28c237b5105c3258a99ea669088c0522189a1f`
(`VERSION=3.1.1`). The canonical Racket hash remains `c539e2039994`.

The six declared cyan templates have distinct cardinalities: cross 4, hook 6,
stair 8, fork 9, diamond 10, and arch 14. Consequently a solver can count cyan
cells, select a memorized offset bitmap, and stamp it at the red markers without
examining the green anchor's location or the cyan cells' coordinates. The audit
implements that rival independently in `probe_count_shortcut.py`. The shortcut
is a property of the finite bank, not an accidental correlation in the sampled
seeds. It removes the intended source-relative geometry extraction step.

The rival matched all eight public canonical authoring pairs, 192 default
inputs (eight seeds, all three difficulty bands, all eight schedule slots), and
48 exact-control boundary combinations. Generated comparisons used an
independent pixel-based oracle. Across 192 five-pair cyclic lessons and all
960 single-query holdouts, no existing declared rival survived, but the
count-lookup rival survived every rotation. Exact seed sets were
`0,1,2,3,50000,50001,50002,50003`; control probes used seed 77/sample 1 and
every template with height/width 10 or 22 and one or five red markers.

**Executed witness.** `same-count-witness.json` retains a 13x13 hook and its
horizontal reflection, each with six cyan cells, one green anchor at `(6,6)`,
and red markers at `(3,3)` and `(9,9)`. They have identical color histograms,
both source shapes are connected, and every stamp fits. Public `Catalog.apply`
executed the canonical Racket rule on both. The count lookup matches the hook
but disagrees with the reflected hook in 16 output cells. The ordinary hook
passes the current generator validator; the reflected hook is rejected solely
because its offsets are outside the declared template bank. This demonstrates
the semantic distinction and the support limitation; it does **not** establish
that the generator violates its declared finite-bank domain.

**Other checks.** The focused production, scalar-contract, and control-probe
suite passed 40/40 tests. All 192 default draws and 48 control combinations
passed the sampled grammar/control checks. Direct canonical Racket execution
covered 34 inputs: all eight ledger pairs, all eight default slots in every band
at seed 0, and both handcrafted witness inputs. All 34 returned valid grids and
agreed with the independent offset-stamping oracle. The target source hash was
unchanged after execution.

**Proposed follow-up.** If training is intended to teach reading arbitrary cyan
geometry, include at least two geometrically different templates with the same
cell count and add the count-lookup rival to lesson checks. Preserve canonical
profiles, in-bounds stamps, and the existing overlap witnesses. If the finite
bank is intentional, retain this limitation explicitly rather than treating
success against the current rival set as proof that the source geometry must
be read. No target repair is included in this return.

Evidence is under `WORK/checks/audit/8de1c257a9c7/`:
`summary.json`, `probe-records.json`, `canonical-racket-execution.json`,
`same-count-witness.json`, `focused-tests.log`, and `commands.json`.
The exact command, from the outer extraction directory, was:

```sh
WORK/.venv-review/bin/python review.py run env PYTHONDONTWRITEBYTECODE=1 ../.venv-review/bin/python ../checks/audit/8de1c257a9c7/probe_count_shortcut.py
```

This bounded audit does not measure learner performance, prove absence of other
shortcuts, or review the separate parametric prototype. Cyclic holdouts reuse
the eight stored schedule-slot inputs, and do not claim byte identity with
production calls at later sample indices. No solve-private labels were read.
