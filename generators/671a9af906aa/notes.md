# Working notes: 671a9af906aa

## Current rule and domain

The unchanged canonical Racket rule (`RULE_HASH = "09280085884a"`) finds the shortest orthogonal start-2 to goal-3 route while tracking key-4 possession. Door 5 is passable only after collecting the key. Traversed zeros become 7; markers are preserved. An unreachable goal produces identity output, explicitly admitted with `ALLOW_IDENTITY_OUTPUT = True`.

Version `2.0.1` retains the previous constructive perfect-maze sampler, exactly one key/door, strict validation, observable `grid_h`, `grid_w`, and `route_mode` controls, executable rivals/witnesses, and five-demonstration lesson diagnostic. Its route cycle remains `key_detour, key_bypass, key_detour, key_bypass, unreachable`. Each consecutive five scenes contains every profile. Python mirrors/probes support tests; Racket remains the label authority.

## Current repair decisions

**Remove the height/reachability shortcut.** Version `2.0.0` enlarged only sample indices congruent to 4 modulo 5, exactly the unreachable route slot. The new failing regression measured detour 10 canonical/0 enlarged, bypass 10/0, unreachable 0/5 over 25 default medium draws. Height therefore predicted reachability perfectly. A rival that applies the correct solver at height 7 and returns identity for every taller maze fit every previous default scene.

The enlarged slot now rotates across the five route slots: `(4 - sample_index // 5) % 5`. The 25-scene size cycle enlarges residues 4, 8, 12, 16, and 20. Every route profile receives 80% canonical-size and 20% enlarged support. Any six-scene window, including the period boundary, contains at most two enlarged grids, preserving `MIN_STRICT_FRAC = 0.60`. This reverses the old fixed-size slot without changing route frequencies, exact override domains, or the reference rule. Default scenes now include both enlarged reachable routes and canonical-size unreachable routes.

**Validate output colors before equality.** Python list equality considered float labels (for example `8.0`) and zero cells replaced by `False` equal to valid integer labels. `_pair_errors` now applies the existing structural/color validator to provided outputs before comparison. This guard covers demonstration and labeled-query outputs while preserving optional unlabeled queries.

## Fresh focused evidence

Current generator SHA-256: `d8f73a03d424429172711492b4c6251cc82ac2adecc6f8fa28f81e004392095a`.

- `WORK/checks/671a9af906aa/regression_before.log`: three intended failures before the fixes (size/profile crossing and float/Boolean output rejection).
- `WORK/checks/671a9af906aa/task_tests_after/result.json`: all 37 selected task tests pass, including existing profile, override, determinism, canonical-pair, and lesson checks.
- `workspace/shape_support_probe.py` with `WORK/checks/671a9af906aa/shape_support_racket.json`: one complete 25-scene default cycle in each difficulty band (75 generated grids). Each band has detour 8 canonical/2 enlarged, bypass 8/2, unreachable 4/1; minimum six-scene strict fraction is 2/3. The dimension-gated rival disagrees on four scenes per band.
- The same probe executes unchanged canonical Racket on one representative of every size/profile combination in every band (18 cases), plus all four canonical pairs. All agree with the independent probe and production mirror. `counterexamples/shape_reachability.json` retains medium-band enlarged-detour and canonical-unreachable Racket witnesses with exact seeds, indices, grids and source/rule hashes.

The final staged task-test receipt is explicitly labeled `phase: after` and binds the current source hash. No full battery or large census was rerun for this revision.

## Inherited evidence and limits

The prior v2.0.0 source (`5c868e79812bee3fc908cac7f14dd115b3f372e57ddfb34e7cd7c4ea1a38f52f`) had reviewer-reported 34 focused tests, a 12-stage battery, and a 300-lesson census. Those results describe those earlier bytes and are not fresh checks of v2.0.1. Their retained witnesses and review index remain provenance.

Coverage remains limited to one key and one door in perfect mazes. There is no claim for multiple keys/doors, cyclic topology, every malformed object type, arbitrary subsets of the five-example lesson, or undeclared competitors. The 25-cycle removes perfect size/profile confounding over the full cycle; a short individual lesson can still have accidental correlations. Topology can collide across seeds; this repair did not repeat the earlier uniqueness census or establish a new uniqueness rate. Changing source bytes requires a new exact-source review decision; inherited approval does not approve this revision automatically.
