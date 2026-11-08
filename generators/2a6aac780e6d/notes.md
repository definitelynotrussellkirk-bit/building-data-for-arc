# Working notes: 2a6aac780e6d

## Review `review-fb122afeebaf6bb8`

- The base generator source remains unchanged at version `2.0.0`. Its canonical
  rule is preserved byte-for-byte (`4f90f10302a9…`). The only base-side repair
  was making the task test locate the packet root portably instead of assuming a
  fixed `/tmp` layout.
- Added the native parameter `fill_scope`:
  - `all_qualifying` is the exact canonical program and fills every row having
    two same-color endpoints with zero cells between them.
  - `key_selected` reads a unique `8 … 5 … 8` key row. The horizontal distance
    from the left `8` to `5` is a one-based rank into qualifying rows ordered
    top-to-bottom; only the selected row is filled.
- Sequential dependency: A computes the rank-selected payload-row record; B
  consumes that row's endpoints and color to paint the span. The protected
  `always_first.rkt` counterfactual substitutes the first payload row and changes
  the qualified output.
- The family supports 2–6 demonstrations and exactly four distinct queries,
  preserves matched inputs across settings, and includes a substantive 30×30
  case with eight payload rows plus guard rows.
- Bounded self-review at seeds 0 and 17 refuted seven named shortcuts:
  canonical-all, always-first, always-last, off-by-one, largest/smallest gap,
  and highest-color. A later five-seed sweep exercised all demo counts and both
  settings without retries or duplicate inputs.
- Source-bound authoring preflight, protected witness replay, 16-view public
  projection, and 24 first-turn invariance checks passed. These are reviewer
  artifacts only; they do not grant owner acceptance or training admission.

Next action: integrate these exact bytes, rerun native owner qualification, and
freshly accept the family if the semantic review agrees with the claimed A→B
dependency.
