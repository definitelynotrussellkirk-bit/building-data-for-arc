# Working notes: 6af5c333e5c1

## Current decision

Retain the production generator and selected canonical rule unchanged. The task-local native family is ready for owner source review under `workspace/parametric/`; it is not owner-accepted and has not been admitted to training.

## Family built

- Parameter: `fill_policy`.
- `all_pairs` is the exact canonical source, byte-for-byte: every row containing exactly two blue endpoints is filled inclusively between them.
- `top_span_threshold` is the nearby composed branch: scan for the topmost exact-pair row, measure its endpoint span, then fill only exact-pair rows whose spans are at least that input-dependent threshold.
- The sampler is setting-neutral and matched across settings, deterministic, global-RNG isolated, prefix-stable, and supports 2–6 demonstrations plus 1–4 queries. Four-query episodes use 8×11, 14×18, 22×26, and substantive 30×30 queries.

## Teaching and causal design

Rows 0 and 1 are singleton/triple distractors before the first valid pair row. Each scene has at least four exact-pair rows, the top threshold lies strictly between the minimum and maximum observed span, and the bottom-pair threshold differs from the top threshold. Executable rivals cover all pairs, bottom-anchor threshold, longest-only, short-or-equal, top-row-only, and “two or more” rows. A bounded demonstration-only audit over seeds 0, 17, and 97 leaves no rival that fits the demonstrations and changes a query answer.

The required sequential dependency is: A finds the topmost exact-pair row and measures its span; the intermediate records the selected row, threshold, and observed spans; B decides which rows to fill using that threshold. The protected counterfactual substitutes the bottom exact-pair span and changes the final grid. Evidence is in `checks/6af5c333e5c1/causal/`.

## Verification retained

- Focused task-local suite: 23 passed.
- Full changed-target task suite: 23 passed.
- Three complete Racket programs passed strict one-form parsing.
- Compatibility authoring preflight: 4 setting/seed jobs, 40 protected-Racket evaluations, passed.
- Causal witness: protected intended/counterfactual replay, `reviewer_replayed`.
- Public projection: 4 episodes, 16 one-query views; 24 private-field invariance checks and 4 visible-change controls passed.
- Source inventory: `workspace/parametric/evidence/manifest.json`.

The shared `arcpuzzles.review_base_preflight` currently assumes every canonical `test` member is a list. This task’s selected bank record stores one labeled test pair directly as a mapping, producing `TypeError: string indices must be integers, not 'str'`. The original failure is retained under task-local evidence. `authoring_preflight.py` is a tested compatibility wrapper that preserves the shared source binding, original-label replay, ordinary generation, protected parametric execution, and standard receipt schema while normalizing only list-versus-single-mapping pair iteration.

A final contract pass also repaired an initial 3-demo minimum; the current adapter and promotion contract now support the required 2–6 range, and every source-bound receipt was regenerated after that edit.

## Next owner action

Review the parameter semantics and compatibility wrapper, replay the packaged qualification and causal witness, then run native qualification and acceptance on the integrated bytes. Preserve `all_pairs` as the canonical default. Owner acceptance and training admission remain pending.
