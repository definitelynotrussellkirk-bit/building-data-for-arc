# Working notes: 8291f3ee7e54

## Current decision

- Current production generator: version `3.1.0`, accepted-repair SHA-256 `5e1e28490be83e36d8e8243e23082015d5110e9ed98a3a189941476443fcb2af`.
- Keep the canonical transformation unchanged: rule hash `d9bb03e0e2ec`; exact canonical program SHA-256 `79951c1fb8d60053930868df5a4f183a5ed50884fe0e479e954ea446b7b8b6bb`.
- The 2026-10-24 ticket changes only task-local parametric sources, tests, and notes. It does not change the production generator or canonical Racket, and it does not activate training data.

## Production repair

The prior generated support rejected detached same-color cells, so the intended “largest 4-connected component per color” rule was observationally equivalent to the easier rival “take the union bbox of every cell of that color.” The repair adds a `distractor` layout that inserts one detached same-color singleton outside the answer-bearing component bbox. It also extends `self_check` narrowly enough to accept one such external singleton for an affected color while preserving canonical occlusion fragments; two external same-color singletons are rejected.

The generated branch requires exactly one teaching distractor across the returned grid. The canonical linked profiles remain distractor-free and the canonical Racket source is unchanged. Focused evidence is under `checks/repair/8291f3ee7e54-distractor-v3/`: a hand-authored witness plus generated 12×12/3-layer and 22×22/5-layer cases all pass `self_check`, execute the canonical Racket, and disagree with the union-bbox rival.

## Native parameter extension — reviewer ready, owner acceptance pending

`workspace/parametric/prototype.py` version `1.1.0` (current SHA-256 `b23df7042167ba2ecce51a78233de647d9959b56a75010ce51758c9b4086ed62`) and the native adapter add the episode-level parameter `ring_order` without changing production behavior:

- `largest_outside` is the exact canonical Racket source (SHA-256 `79951c1fb8d60053930868df5a4f183a5ed50884fe0e479e954ea446b7b8b6bb`).
- `smallest_outside` keeps the same span-ranked ring geometries but reverses the color sequence assigned outside-in (Racket SHA-256 `999edfc4160d3e08946dc45bce5542a0a0120113766abc85d0c6ed21c40d6ca7`).

The transfer is inspired by public evaluation task `45a5af55` (challenge SHA-256 `08adaedc3b2ae02781394888ed2fef2f0223ca07f149c484464f93d4c922f7ff`), whose stripe order controls concentric depth. This is unverified inspiration, not a lineage or difficulty claim.

The native family supports 2–6 independently requested demonstrations and 1–4 independently requested queries. Slots are fixed before count slicing, so the first query is identical in one-query and four-query use. Inputs are setting-independent. The first query is a substantive 30×30 five-component case with selected spans `[11, 9, 7, 5, 3]`, four boundary contacts, and a detached same-color singleton that distinguishes largest-component selection from a union-bbox shortcut.

Focused tests cover exact canonical-default bytes, both Racket settings, count boundaries, ten distinct maximum-size episode inputs, query-count stability, setting-independent inputs, public/private projection, and duplicate visible-ID rejection. A bounded protected-Racket audit executes four plausible rivals per setting: opposite ring order, union bbox per color, numeric-ascending colors, and numeric-descending colors. All are refuted by the two visible demonstrations and disagree on queries in the retained audit. Native qualification passed four jobs (two settings × seeds 0 and 17) with three demonstrations and four queries each; exact-source owner acceptance remains pending and `training_admitted` is false.

## Supplementary tickets

- `ticket-2ab1017821a17a99`: a deterministic three-task allocation sample supports a 12-task readiness/cost-stratified pilot, not a global allocation change. Report: `checks/tickets/ticket-2ab1017821a17a99/report.json`.
- `ticket-a721c20bac781478`: the pinned peer prototype passes source/hash/privacy/Racket checks, but retained episodes expose only 3 demonstrations + 1 query. Follow-up is to separate counts and retain four simultaneous queries per fixed setting. Report: `checks/tickets/ticket-a721c20bac781478/report.json`.

## Remaining limits and next action

No full production battery or corpus-wide allocation census was run because the assignment calls for changed-scope checks. Maintainer replay should first evaluate the candidate generator patch and focused counterexample; separately review the proposed parameter extension before any approval or training decision. The existing test harness still emits a deprecation warning because canonical-profile bookkeeping touches private `GenCtx._draw_bounds`; that pre-existing interface use was not broadened in this repair.

## Resolved prototype public emission-order follow-up

The retained writer now constructs and validates the complete two-episode batch before publishing either episode. Visible challenge IDs are checked for uniqueness first, rows and physical writes use the same sorted visible-ID order, and `verify_tree` checks that order. A duplicate-ID regression confirms that no public challenge or private episode file is left behind. The superseded pending manifest is retained as `workspace/parametric/evidence/reviewer-original-manifest.json`; the current source-bound inventory is `workspace/parametric/evidence/manifest.json` (SHA-256 `d3fc5ea373d861cf576da7929645cc803e0395efaf59a0e957bd7104947396ce`).

## Sequential dependency

Step A selects the largest-span 4-connected component for each nonzero color and sorts the resulting layers by span. Its intermediate is the input-dependent ordered list of colors, selected bounding boxes, and selected spans. Step B consumes that list to choose the output size, centered ring offsets, and outside-to-inside color assignment. A two-case protected-Racket witness replaces Step A's selected component boxes with disconnected same-color union boxes; both qualified settings then produce a different final output. This is bounded causal evidence, not a universal depth proof.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/8291f3ee7e54/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
