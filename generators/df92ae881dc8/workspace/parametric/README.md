# Native inferred-spacing / doubled-spacing completion

Proposed native family; owner exact-source acceptance remains pending. Neither the
production generator nor the selected canonical Racket program has been changed.
The independent Python implementation produces claims; native qualification labels
and checks all jobs through protected Racket.

## Episode-fixed parameter and sequential rule

`spacing` is `observed` (byte-exact canonical default) or `doubled`.
First measure significant rows/columns: a significant line has a foreground run
of length at least three. Collect consecutive significant-line gaps in 2..4,
rows first then columns. Their first-occurring mode is the observed period;
with no valid gaps it is 2. The alternate setting doubles this inferred value.

The effective period then controls BOTH canonical branches:

* Full foreground columns: each independently selects its marching direction
  using neighboring evidence and boundaries, and replicates by that period.
* Otherwise: select the longest horizontal run, ties **bottommost then rightmost**,
  construct four directional nested-L completions, and choose the first maximum
  by **unique occupied-cell count**, not the count of appended/overlapping cells.

Candidate order is up-left, up-right, down-left, down-right. This description
follows the executable source, not the stale top/left comment inside the exact
canonical text. Original foreground cells persist; all non-path cells become 5.

A = run analysis and mode of significant-line gaps; intermediate = observed and
effective periods; B = period-dependent column continuation or competing L
construction. The witness substitutes an observed period of 2 while holding the
setting and remaining code fixed. It changes the final protected-Racket grid.
The alternative therefore retains inference, branch selection, clipping, overlap,
and candidate competition; it is not a constant-background relabeling.

## Supported domain and teaching cost

Inputs: exact integer grids, 6..30 rows/columns, literal zero background, one
foreground color in {1,2,3,4,6,7,8,9}, at least six foreground cells, and either a
full column or a horizontal run of length >=3. The native grammar admits multiple
full columns and richer mixed spacing/overlap evidence than the unchanged
production sampler. It does not accept multiple foreground colors or color 5.

The native contract supports **4..6 demonstrations and 1..4 queries**; four queries
are the normal supervision/qualification request. **Two or three demonstrations
are rejected.** The three-demo authoring attempt left real raw-coverage,
directional, and tie-precedence shortcuts. Strengthening those scenes helped,
but the bounded audit still exposed held-out failures. A fourth constructive
coverage lesson fixes them. This is an observed teaching cost, not a proof that
four is the theoretical minimum for every possible lesson.

The four base demonstrations cover periods 3,4,2,4; both column directions in
one scene; top/bottom and left/right longest-run ties; distinct period-dependent
L winners; unique versus duplicate area; and first versus last coverage ties.
The L constructors use at most 128 bounded geometry trials followed by explicit
known-valid fallbacks, with predicates checked under both settings. Colors vary.
Additional demonstrations and four queries vary geometry, scale, colors, branch,
period, clipping, and overlap. The cached input bank is private and copied before
return. Settings and requested demo count never affect its query bank.

Queries include a genuine 6x6 minimum and a 30x30 full-span stress scene. The latter
alternates between multiple full/partial columns and dense horizontal/L evidence
with more than 100 input foreground cells and all four borders occupied. It is not
a small motif padded with zero. All original geometry and settings remain private.

## Reproduce from the outer packet

```sh
python3 review.py run python3 generators/df92ae881dc8/workspace/parametric/audit.py --seeds 32 --out ../checks/df92ae881dc8/audit.json
python3 review.py task-tests df92ae881dc8 --phase after --out ../checks/df92ae881dc8/tests
python3 review.py run python3 -m arcpuzzles parametric qualify df92ae881dc8 --seed 0 --seed 17 --demos 4 --queries 4 --out ../checks/df92ae881dc8/qualification --summary
python3 review.py preview-public export --qualification ../checks/df92ae881dc8/qualification/qualification.json --out ../checks/df92ae881dc8/public-preview
python3 review.py preview-public verify --bundle ../checks/df92ae881dc8/public-preview
```

Create a current native source/evidence manifest after edits and before qualifying.
Use a new output path when rerunning commands. The shared preview helper shuffles
the complete four-query bank privately before single-query prefix selection.
Only an individual hash-named public file is a solver turn. Never reveal future
inputs, query answers, source settings/code, private order, or the directory listing.

`audit.py` reports counts of finite Python-policy checks separately from the much
smaller protected-Racket label subset. It replays the retained old ambiguous lesson,
new refuting demonstrations, and actual tie-order programs. The tests use literal
hand-derived grids, strict requests, bank isolation, and executed Racket checks.
The inherited production test harness was repaired to use portable same-checkout
root/catalog APIs; its generator and rule assertions were retained.

No universal identifiability, owner acceptance, training admission, or measured
learning benefit is claimed. Input distribution breadth and arbitrary-policy
induction remain outside this bounded authoring audit.
