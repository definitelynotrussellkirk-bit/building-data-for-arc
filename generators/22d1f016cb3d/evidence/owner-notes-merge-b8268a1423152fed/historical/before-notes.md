# Working notes: 22d1f016cb3d

## Rule authority

`RULE_HASH = 2219db85ca5f` remains the whitespace-normalized hash of the canonical Racket program. The selected Racket source and all three canonical input/output pairs are unchanged: for each color-5 cell, both opposing cardinal pairs map to 2, neither maps to 1, exactly one maps to 4, and every non-5 cell is preserved.

## Baseline defects

The untouched strict battery had 9 green stages, 2 advisories, and one failure. Strict defect lint found 33 accepted invalid scalars: booleans, floats, and numeric strings for `seed`/`sample_index`, plus negative `sample_index`, across difficulty bands. Canonical-envelope support was 6/60 (10%), below the required 15/60 floor, and no executable semantic contract was declared.

## Canonical generator repair

Version `3.4.0` now:

- accepts only literal integer `seed` and nonnegative literal integer `sample_index`;
- rejects near-full modal-foreground impostors that had been misclassified as lawful generalized scenes;
- keeps explicit `scene_profile` control over every declared public/general profile;
- exposes executable witnesses, canonical-fitting rivals, lesson competitors, and `lesson_identifiable` without changing labels; and
- uses a deterministic period-12 default curriculum.

The period-12 curriculum places `mixed_shapes` at slots 0/4/8, a second irregular refuter at 2/6/10, exact public profiles at 1/5/9, and a broad non-teaching profile at 3/7/11. Every four consecutive candidates therefore contain two local-rule refuters and two guaranteed multi-object examples (public plus mixed). Holding out any accepted pair leaves demonstrations that refute both the canonical-fitting neighbor-degree shortcut and generic first/topmost-object selection shortcuts. The broad pool excludes teaching profiles, so the materializer's duplicate filter cannot erase both guarantees.

`neighbor_degree_zones` fits all canonical solid rectangles but fails on straight degree-2 segments. `counterexamples/degree-straight-segment.json` retains a lawful 5×5 hollow-frame witness with 12 differing cells, bound to final generator SHA-256 `26f3491ab54d2e4cd38590da33f59a567f140c2e8a342a1dcfd5ab59f701abbd`. `collapse_edges_to_ends` is refuted by every lawful profile because self-check requires an exactly-one-opposing-pair output cell.

## Reversals and retained failures

An initial bbox/puncture rival was rejected because rotation safety would have required a repetitive punctured-block curriculum. A first period-4 schedule then failed 3/1,200 rotated queries after duplicate filtering removed a teaching pair; the compact reproducer is `checks/intermediate-lesson-ambiguities.compact.json`. A first period-12 schedule fixed that defect but still produced five strict semantic warnings when a public multi-object example was held out; `checks/intermediate-object-selection-ambiguities.compact.json` and `checks/task1d-red.console` retain those cases. Moving one `mixed_shapes` example into every four-candidate window fixed the root cause.

## Final measured state

On final source SHA-256 `26f3491ab54d2e4cd38590da33f59a567f140c2e8a342a1dcfd5ab59f701abbd`:

- 51/51 task-local tests pass;
- all 12 strict after-battery stages pass with complete period enumeration and required query-rotation identifiability;
- 300/300 random lessons materialize, and all 1,200 query rotations have zero ambiguity, hook warnings, materialization errors, or scoring errors; and
- canonical `RULE_HASH` remains `2219db85ca5f`.

These are finite checks against declared and bounded diagnostic rivals, not a proof of universal identifiability.

## Parametric prototype

`workspace/parametric/` is prototype-only and is not imported by production. It chooses one fixed-per-episode `boundary_palette`: canonical/default `ends1_edges4`, or proposed `ends4_edges1`, which swaps only the zero-pair and exactly-one-pair output colors. Color 2, source color 5, geometry, local pair tests, and every non-5 cell remain invariant. Both complete Racket programs execute under the pinned bridge; all ten retained demo/query pairs distinguish the settings and match the Python assertion mirror. Public challenge files hide the parameter, Racket source, and query label. This is evidence for a bounded family, not production approval.


## Current external prototype follow-up

Public filenames directly encode boundary_palette as ends1_edges4_public.json / ends4_edges1_public.json. The prototype build_episode fixes four demonstrations plus one query and exposes no independent query-count control. The exact reviewer prototype remains unchanged and unapproved. External follow-up must use visible-content public identifiers and independently requested demonstration/query counts, then Racket-label four distinct queries against shared demonstrations with focused writer/count regressions. Evidence and exact source binding: `generators/22d1f016cb3d/evidence/parametric-external-followup-1760770181476aa0/manifest.json`. Owner inspection was static; full reviewer batteries were not rerun.
## Current reviewer considerations

Source SHA-256: `26f3491ab54d2e4cd38590da33f59a567f140c2e8a342a1dcfd5ab59f701abbd`.

# Decisions: 22d1f016cb3d

## D1 — Preserve canonical authority

**Decision.** Keep the canonical Racket text, canonical pairs, and normalized rule hash `2219db85ca5f` unchanged.

**Reason.** Every canonical example and the local cardinal-neighbor interpretation agree. The reproduced defects were in generator contracts, scene grammar, and lesson assembly—not labels.

**Rejected alternative.** Relabeling or broadening the Racket rule to match accidental generator cases would have converted invalid input-domain behavior into authority drift.

## D2 — Validate scalar arguments by exact Python type

**Decision.** Require `type(seed) is int`, `type(sample_index) is int`, and `sample_index >= 0`.

**Reason.** The baseline accepted booleans, floats, numeric strings, and negative indices in 33 strict-lint probes. Exact type checks reject `True`/`False`, which `isinstance(value, int)` would incorrectly accept.

**Evidence.** Baseline: `checks/before/checks/22d1f016cb3d_before_defect_lint.log`. Final: task tests and the green `defect_lint` stage under `checks/after-final-v3/`.

## D3 — Make the scene grammar explicit

**Decision.** Require a background margin for generalized profiles except `border_rectangles`, and require every `border_rectangles` component to touch a border.

**Reason.** A majority-5 canvas with a tiny zero hole/slit was accepted as a punctured or orthogonal scene because profile inference considered only 5-components. This was not a meaningful generalization of the documented family.

**Rejected alternative.** A global “background must be 0-majority” rule would also reject lawful border rectangles and some deliberate dense scenes. The profile-specific condition is narrower and testable.

## D4 — Teach the local rule in the actual accepted lesson

**Decision.** Use a deterministic period-12 default schedule with two distinct local-rule refuters and two guaranteed multi-object examples in every four consecutive candidates. Preserve explicit `scene_profile` access to every declared profile.

**Reason.** The export materializer can reject duplicates. Witness frequency in raw draws does not guarantee that the final 3-demo/1-query lesson still teaches the distinction after filtering and holdout rotation.

**Reversals retained.**

1. A bbox/puncture rival was rejected because making every rotation refute it would force an overly repetitive punctured-block curriculum.
2. A period-4 schedule passed simple reasoning but failed **3/1,200** accepted-pair rotations after duplicate rejection removed a teaching pair (`checks/intermediate-lesson-ambiguities.compact.json`).
3. The first period-12 schedule fixed that shortcut but still produced **5** strict generic object-selection warnings when the public multi-object pair was queried (`checks/intermediate-object-selection-ambiguities.compact.json`, `checks/task1d-red.console`).
4. Guaranteeing both public and `mixed_shapes` multi-object evidence in every four-candidate window resolved those cases; the final census is zero-warning/zero-ambiguity.

**Rejected alternative.** Sampling teaching profiles independently at a high marginal rate was cheaper but could not prove each accepted lesson retained a witness.

## D5 — Declare executable rivals instead of prose-only intent

**Decision.** Add pure executable witnesses, canonical shortcuts, lesson competitors, and `lesson_identifiable`.

**Reason.** `neighbor_degree_zones` is a plausible shortcut that fits all supplied solid rectangles. The hollow-frame counterexample differs on 12 cells and makes the missing distinction concrete. `collapse_edges_to_ends` covers a separate lesson-level degeneration.

**Limit.** These declarations are finite. Passing them does not rule out undeclared programs.

## D6 — Keep the parametric variant isolated

**Decision.** Implement `boundary_palette` only under `workspace/parametric/`, with allowed values `ends1_edges4` and `ends4_edges1`; do not import it from production.

**Reason.** Swapping end/corner and edge colors changes the executed rule while preserving the core local cardinal-pair reasoning. The canonical value exactly preserves the selected task. Selecting once per episode gives demonstrations a meaningful hidden-rule inference problem.

**Rejected alternatives.** Size, placement, or profile weights were not accepted as rule parameters because they alter input sampling rather than transformation semantics. Changing source color or interior color would add avoidable role ambiguity and risk colliding with preserved decoys.

**Evidence.** `checks/parametric/boundary-palette-evidence.json`, two retained Racket files, two public challenge files, and six focused tests.

## D7 — Treat audit work as findings-only

**Decision.** Leave `7536972d536d` and `a631936f7715` unchanged and return source-bound reproducers.

**Reason.** The assignment permits only selected-task edits. Both defects are direct, deterministic override-contract failures and do not require speculative source changes to establish.

## D8 — Evidence and prior material

**Decision.** Use current-source measurements as authority. No prior return was used to justify the main repair. For `a631936f7715`, an existing index was checked only after independent reproduction to avoid mislabeling a known unresolved issue as new.

The return keeps the final battery, portable tests, full final 300-lesson census, prototype evidence, audit probes, baseline receipt, and compact decisive failed iterations. Larger superseded duplicate reports remain local rather than consuming the 25 MiB return budget; the compact files preserve the exact source binding, failed rotations, rival identities, and witness grids needed to reproduce the design reversals.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/22d1f016cb3d/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->


## Current unselected prototype correction

A returned public-ID/four-query/Racket-label correction is retained as an unselected candidate at `generators/22d1f016cb3d/workspace/proposals/review-b8268a1423152fed/manifest.json`. Its prototype/test preimages match, but the returned notes collide with current owner notes. Preserve the current source until those notes are explicitly rebased; this is not a demonstrated semantic conflict in the candidate. Reported36focused passes and Racket examples remain reviewer-reported, and variants remain unapproved.
