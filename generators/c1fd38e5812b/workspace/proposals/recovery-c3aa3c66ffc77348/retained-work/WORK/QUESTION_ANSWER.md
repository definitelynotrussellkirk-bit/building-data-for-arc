# Qwen3.5-9B data-quality gate

Add an **independent-control counterfactual gate**. For every generator that
declares two or more semantic controls, automatically construct a small
matched set in which one control changes while the others are held fixed, then
require (a) the observer to recover the intended setting and (b) the selected
rule to produce the expected output for each member.

The reproducible failure it catches here is axis coupling. The old generator
had lessons with both row and column spans uniform or both nonuniform, but no
lesson with only one axis uniform. A model could learn “choose one shared
chunking regime for both axes” and never be contradicted. The witness with row
spans `[2,2,2,2,2,2]` and column spans `[4,8]` makes that shortcut return a
6-by-3 grid instead of the correct 6-by-2 logical grid.

A possible false positive is a lawful symmetry or degeneracy: changing a
control may leave the output unchanged for a square/symmetric input, or two
controls may intentionally be coupled by the task definition. The gate should
therefore search a few seeds for a distinguishing witness and allow generators
to declare an intentional dependency, rather than requiring every individual
sample to differ.

The cheapest test is not a full battery. Enumerate each declared control pair,
try two to four deterministic seeds per direction, call `generate` with
explicit overrides, recover the setting through `observe_overrides`, and run
the existing oracle. Fail only when no distinguishing, correctly observed
counterfactual is found. This would have exposed the missing mixed-axis cases
in seconds.
