# 956425dc719c

Canonical rule: recolor only orange components touching exactly one grid border gray; preserve interior and corner-touching orange components and every non-orange distractor.

Kind: `per_puzzle`. Generator version: `2.0.0` (reviewed unchanged).

The task-local parametric family preserves exact canonical `post_select=none` bytes and adds `largest` and `smallest`: apply the canonical border filter first, recompute the surviving orange components, then recolor the unique largest or smallest survivor blue. Rank profiles vary across the minimum lesson, making fixed-size selection invalid, and a wrong-order program is retained as a causal counterfactual.

The family supports 2–6 demonstrations, exactly four stable queries, a disjoint six-train/four-query visible-slot namespace, and a substantive 30×30 query.

Status: reviewer-ready authoring evidence only. Owner source review, native qualification/acceptance, and any training admission remain pending.
