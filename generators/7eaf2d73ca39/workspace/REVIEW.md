# 7eaf2d73ca39 bounded robustness result

Repaired an object-validation hole: global green row/column counts accepted all
three built-in degenerate textures, including an L-shaped component. `self_check`
now uses the existing four-connected component helper, rejects bent green objects
and requires a nontrivial green line of each orientation. Lawful singleton extras
and diagonal contact between distinct objects remain allowed.

The before probe reproduced all three false acceptances, and a standalone expected
assertion failed on the original L shape. The final focused pytest run passed all
9 cases. Across 24 default draws (8 seeds × 3 difficulties), grids stayed identical
and passed validation. Seeded generation, VERSION, canonical rule, authority data,
root tests and approval/admission metadata were untouched.

See `checks/7eaf2d73ca39/agent_result.json` for source bindings and evidence. Two early
pytest attempts were unrun due to missing dependencies and are explicitly recorded;
the later packet-venv test run executed successfully. No Racket label execution,
full battery, control-axis census or parametric work was performed for this narrow
validation-only repair. Declared unused controls remain outside this probe's scope.
