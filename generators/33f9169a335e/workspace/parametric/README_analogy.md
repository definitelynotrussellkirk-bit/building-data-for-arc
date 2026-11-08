# Proposed nested Boolean analogy

This is a separate proposed specialization inspired by public evaluation task
`4c7dc4dd`, specifically its second demonstration. It is retained with assigned
family `33f9169a335e` (training parent `54d82841`) but does not modify or claim to
implement the canonical inverted-U rule. `relationship_verified` remains false.
No evaluation query answer was read or used.

## Source evidence and scope

In public demonstration 2, one outer frame contains two 4x4 binary panels in
color 4. Their masks are complements. The other outer frame contains a partial
pair in color 2; the demonstrated output is the complement of its nonblank
panel, in color 2. Thus the complete pair establishes a relation, and the target
pair supplies both new content and the output palette. Demonstration 1 instead
shows sparse endpoints versus completed aligned connections; this prototype
does **not** claim to support that relation or to solve the full public task.
Source: `shared/data/raw/arc-agi_evaluation_challenges.json`, task `4c7dc4dd`,
visible training demonstrations only.

The prototype's source-backed case is complement with target palette. Identity
contexts and the alternative reference palette are explicitly proposed
extensions. The default is a default of this new prototype; it does not equal
the assigned family's canonical rule.

## Exact rule and domain

Two framed groups are stacked with one all-zero separator row. Each group has
two square panels side by side, with a shared vertical frame divider. For panel
side n in 3..11 the input is (2n+5) x (2n+3), hence 11x9 through 27x25. Colors
are exact integers 0..9; the two frame colors are distinct and nonzero. Each
panel contains only zero and its own frame color. Exactly one panel is blank;
the other three must be nonempty and nonfull.

Normalize the complete pair to binary masks. They must be identical or exact
complements. These operations are involutions: either reference panel ordering
identifies the same unique operation. Apply that operation to the nonblank
panel in the incomplete group. Emit only the resulting n x n panel.

The episode parameter `output_color_role` is `target` (default) or `reference`.
Foreground uses the corresponding group's frame color, with zero preserved.
The setting stays fixed across an episode. Identity/complement is different:
it is derived anew from each input's complete pair and varies within episodes.
The Racket program receives no hidden per-input operation.

Generated masks are asymmetric under all nonidentity square symmetries and the
target mask differs from both reference masks. Validation also accepts symmetric
mixed masks if the operation is uniquely identifiable. Group position, panel
ordering, colors, masks and n vary. No noise or exact 30x30 inputs are claimed.

## Why the reference pair matters

`context_counterfactual()` returns identity and complement contexts with B,
target C, frame colors and layout identical. Only A changes from B to its
complement, reversing every target output bit. A rival using B alone or ignoring
the complete pair must give the same answer to both and therefore fails one.
This is a concrete contextual dependency; it is not an iterative-state claim.
Other relevant rivals are always-identity, always-complement, copying either
reference panel, using a fixed spatial group, and choosing the wrong color role.

## Four independent queries

From the repository root:

```sh
python generators/33f9169a335e/workspace/parametric/analogy.py --seed 17 --role target --demo-count 2 --query-count 4 --out checks/analogy-target.json
python generators/33f9169a335e/workspace/parametric/analogy.py --seed 17 --role reference --demo-count 2 --query-count 4 --out checks/analogy-reference.json
```

Both counts independently accept integers 1..8, excluding booleans. The sampler
rejects duplicates across demonstrations and queries and has explicit finite
attempt limits. Accepted indices are recorded. Default 2+4 episodes alternate
identity/complement and contain six distinct full inputs. The two default demos
expose both operations; one-demo requests are allowed but explicitly record
that both operation choices are not demonstrated. Input generation depends on
`input_seed`, so both role settings can be compared on identical inputs.

`sample_episode` initially supplies Python labels and matching Racket source.
Actual Racket execution and retained labels/evidence must be produced by the
review harness. Generation alone is not Racket verification. Query labels,
parameters and reference programs must be omitted from public challenge exports.

API: `COLOR_ROLES`, `rule_source(role)`, `python_transform(grid, role)`,
`sample_grid(seed, index, cue_mode=None)`, `context_counterfactual(seed=17,
index=0)`, and `sample_episode(seed, role='target', input_seed=None,
demo_count=2, query_count=4)`; keyword-only sampler arguments are required.
