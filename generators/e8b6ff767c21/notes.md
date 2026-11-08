# Working notes: e8b6ff767c21

## Current decision

Build the native `route_overlay` family with `none` as the byte-exact canonical default and `terminal_path` as the alternative.  Step A constructs the canonical green spiral and exposes its terminal/open-corridor geometry; step B runs deterministic right/down/left/up breadth-first search from `(1, 0)` to an open terminal neighbor and paints that route blue.

## Source review and repair

The production generator already matched the canonical blank-canvas spiral rule and was left unchanged at version 4.0.0.  Its inherited portable test used a task-local canonical-data path that does not exist in an isolated packet snapshot; the test now resolves canonical pairs through the packet's source-bound `reviewer_support` API.  The new family exhaustively checks every 5..30 height/width pair for endpoint validity and route existence.

## Retained evidence

Portable task tests pass 17/17 with 12 subtests; one inherited private-`GenCtx` deprecation warning remains non-semantic.  Authoring preflight replayed four jobs/four episodes with 32 protected-Racket evaluations.  The protected causal replay changes the route when a blank walkability map replaces the constructed spiral.  A bounded 160-episode audit found no surviving named rival and includes 30×30 stress; 16 public one-query projections passed 24 private-field invariance checks and four positive controls.

## Remaining limit and owner action

This is reviewer-ready authoring evidence, not owner acceptance or training admission.  The owner should integrate the exact task-local family, run fresh native qualification/acceptance, and optionally migrate the inherited `_drawn` assertion to the public `GenCtx` API in a later maintenance pass.
