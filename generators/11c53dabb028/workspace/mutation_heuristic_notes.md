# Generic mutation warnings and this task's input domain

## Measured evidence

The retained before battery reported `selfcheck-power` rejection of 13/44
mutations and `selfcheck-minimal-impostor` acceptance of short_line 6/6,
singleton 6/6, and solid_2x2 5/6. See
`checks/before/checks/11c53dabb028_before_defect_lint.log` from the packet root.
Those warnings were measured on baseline generator SHA-256
`c55085227ebb6f0047bc7346cc85782659de57aa435f6533d5756d8cfcf89106`.

The separate authoring probe `check_lawful_mutations.py` exercised all 13 cases
in `lawful_mutations.json` through public `Catalog.apply` with the canonical
Racket authority. All 13 were accepted by the baseline self-check and all 13
matched the independently written complement-tiling expression. The full
reference receipt and checked expected outputs are retained under
`checks/lawful-mutations/`. Its normalized executed/catalog rule hash is
`573d7b5ea64c`; its exact executed text SHA-256 is
`d576f4bd17ef387d8a0a1dcb4a39fca1b96951591a88c0c4c726d5f9bf88905f`.

Exact command, from the packet root (the wrapper executes its payload in `repo`):

```bash
python3 run_with_racket.py python3 generators/11c53dabb028/workspace/check_lawful_mutations.py --out ../checks/lawful-mutations
```

Exit status was 0; the denominator is 13 explicit fixtures, not randomly sampled
lessons or a general induction claim. Use a fresh output directory to rerun the
same source-bound probe after further source edits.

## Why the tested shapes are lawful

The input contract is a nonempty rectangle of integer ARC colors 0..9, each
dimension at most 15, containing at least one zero and one nonzero. Let `nz` be
the first nonzero in row-major order. The reference builds a `2h` by `2w` grid,
using `nz` where the corresponding input cell modulo `(h,w)` is zero and using
zero elsewhere. This expression contains no object, connectivity, line-length,
symmetry, or minimum-foreground-area precondition. Every input in the declared
domain has a defined `nz`, bounded output dimensions, and legal output colors.

Cell permutations and square transposes preserve the domain. Swapping nonzero
labels also preserves it; when the first nonzero changes, the output's nonzero
color changes accordingly. A singleton, a short line, or a 2x2 patch on a
larger uniform background remains lawful whenever zero and nonzero cells both
remain present. This holds with either zero or a nonzero color as the modal
background. A stomp is lawful only when it retains both presence classes; a
stomp removing the last zero or the last nonzero must be rejected.

The fixtures cover each of those distinctions, including both modal-background
cases. The focused task tests keep them as must-accept inputs, alongside genuine
must-reject type, palette, size, all-zero and all-nonzero cases.

## Mechanism of the false positives

In `shared/tools/generator_defect_lint.py`, `_mutations` supplies cell shuffle,
transpose, 2x2 stomp, color swap, and the five `_minimal_impostors` shapes.
`probe_selfcheck_power` counts all of them as candidate negatives and warns when
fewer than 30% are rejected. `probe_selfcheck_minimal_impostors` separately warns
for any accepted named minimal shape, except a singleton shape observed in the
canonical training geometry. That singleton exception does not affect the
power denominator, and there is no equivalent check for lawful short lines or
2x2 patches.

For a mixed square mask where the six other probes retain zero and nonzero,
only all_background and full_one_color are invalid: the correct rejection rate
is 2/8, or 25%. An analogous nonsquare mask has 2/7, or approximately 28.6%.
Thus the current 30% threshold can penalize an exact input validator. These are
illustrative counts explaining the mechanism; the actual before-battery count
is the separately retained 13/44 above.

`mutation_fixtures()` already supplies an independent task-local must-reject
contract and reports accepted declared negatives as errors. It does not support
must-accept fixtures. `LAWFUL_DEGENERATE_TEXTURES` calibrates texture probes,
not either mutation detector. Neither should be used to obscure these results.

## Proposed shared-tool improvement

A narrowly safe first change is to exclude unchanged mutations and exact,
independently trusted positive inputs from both negative-probe denominators,
while reporting their counts as lawful or uninformative controls. Canonical
inputs supply one such trusted set. Additional positive fixtures should require
independent reviewer acceptance bound to task, rule, generator and fixture
hashes; a generator author's list of exempt mutation names is insufficient.
Keep `mutation_fixtures()` errors independent so a real declared-negative
failure cannot be suppressed by positive calibration.

An exact-positive filter alone will not establish every shuffled or recolored
mask as lawful. A complete calibration for this task needs a reviewed domain
statement or transformation closure supported by positive and negative witnesses,
and should preserve coverage/acceptance counts rather than silently waive a
mutation class. Successful Racket execution by itself is also insufficient to
prove a task's intended input grammar in general. No shared source or detector
threshold was changed in this review; these warnings remain reported evidence.
