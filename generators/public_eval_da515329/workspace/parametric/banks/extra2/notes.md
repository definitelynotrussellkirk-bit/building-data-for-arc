# Current design — public_eval_da515329

Canonical rule: find the unique zero center with four equal color-8 radial arms.
Each arm seeds a rotation of the same square-spiral branch. The branch continues
outside the finite grid; the final answer is the union of all four completed
branches cropped to the original dimensions. The closed construction reproduces
all three official demonstrations and the official test gold under both the
Python engine and protected Racket; it does not store any supplied answer.

Episode parameter: `finish=spiral_only|highlight_most_visible`. The alternate
first completes and crops all four branches, derives their visible in-bounds cell
counts, and recolors the unique maximum branch 9. The retained counterfactual
substitutes a fixed north branch for that input-dependent count argmax. This is a
real A → visible branch populations → B dependency.

Sampler: 18–30 canvases, arm lengths 1–6, asymmetric legal centers selected from
a deterministic constructive bank, four distinct visible counts, independent
query presentation, and an exact 30×30 final stress query. The first two
teaching examples force different winning branches, defeating fixed-direction
highlighting from the minimum two-demo prefix. The complete branches
always extend outside the canvas before cropping. Supported counts are 2–6
demonstrations and 1–4 returned queries from an always-materialized four-query
private bank.

Evidence is bounded to official labels, eight executable rivals, focused
regressions, public-projection mutation checks and generated placement support. It is not a universal uniqueness
claim. Owner registration, native qualification, exact-source acceptance and any
training admission remain pending.
