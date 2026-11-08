# Working notes: 6c5bf76aa982

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Native parametric build — signal-selected border count

**Decision.** Preserve exact canonical `exactly_one` as the default and add
`signal_target`. The alternative counts the connected color-8 signal and uses
its size as the target number of distinct canvas borders touched by an orange
component before recoloring matching components green.

**Why this parameter.** It retains canonical component extraction, distinct-edge
counting, and recoloring while adding one input-dependent selection step. Inputs
are setting-neutral and contain orange components with touch counts zero through
three, so demonstrations teach the changed rule instead of a changed grammar.
The first two demonstrations use targets two and three; four query profiles
extend through a substantive 30×30 scene.

**Self-review.** The bounded audit covers both settings and nine named rivals
(fixed targets, zero-border, broad threshold rules, signal offsets, any-border,
and boundary-cell count). Across 64 seeds and demonstration counts 2, 3, and 6
it found no harmful survivor or public-projection failure. This is finite
evidence, not a universal uniqueness claim.

**Portable test repair.** The inherited task-local test used a fixed parent depth
and private generator loader, so copied-runtime preflight could not locate the
canonical ledger. It now uses `reviewer_support.find_root`, `canonical_path`,
`canonical_pairs`, and `load_selected_generator`, while retaining the original
semantic and exact-source assertions. The copied-runtime controller passes.

**Causal claim.** Step A measures signal size; the intermediate is the target
border count and component inventory; step B recolors matching orange
components. A protected-Racket wrong-target counterfactual on the same qualified
input changes the final output. Owner exact-source qualification and acceptance
remain pending; training remains disabled.
