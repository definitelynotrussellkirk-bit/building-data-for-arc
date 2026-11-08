# Symmetry Precedence Parametric Family — Implementation Plan

**Goal:** Add a native two-setting parametric family for task `9c5259babb4b` that preserves the exact canonical top-bottom precedence and adds a left-right-first alternative, with 2–6 demonstrations and exactly four matched-input queries.

**Architecture:** A task-local prototype loads the approved generator, samples setting-independent symmetry scenes by split/index, and labels them with a small independent precedence mirror. Exact Racket programs live beside the adapter. Focused tests cover the contract, prefix stability, matched inputs, teaching sufficiency, diagonal connectivity, edge contact, and exact 30×30 stress. A bounded audit writes public one-query projections and finite-rival evidence; native qualification re-executes every label in protected Racket.

**Tech stack:** Python 3.12+, pytest, bundled protected Racket, native `arcpuzzles parametric` tooling.

## Tasks

1. Write failing tests for exact canonical program identity, the alternate program, strict settings/count validation, deterministic matched inputs, prefix-stable demos/queries, and sole-survivor teaching at 2–6 demos.
2. Implement `prototype.py`, exact Racket sources, `adapter.py`, and `promotion.json` minimally to pass those tests.
3. Add tests and implementation for query roles: ordinary transfer, varied geometry, border contact, and substantive exact 30×30 stress; require a diagonal-only asymmetric witness in the teaching core.
4. Build a bounded finite-rival/public-projection audit, then create the source-bound manifest.
5. Run staged task tests, protected-Racket native qualification, produce a source-bound causal counterfactual witness, update notes/results/review, and package the delta.
