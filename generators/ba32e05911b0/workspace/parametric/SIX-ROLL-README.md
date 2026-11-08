# Left/right rolling ladders (proposed, owner acceptance pending)

Design: preserve the byte-exact canonical right-rolling program; the left setting
reflects input and output around that same program. The first roll produces a
new column; the next obstacle/stop is selected only by tracing from that column.
No canonical generator or authority is modified.

Build/check plan: (1) restore portable canonical tests, (2) add test-first native
adapter with two settings, 2–6 demos and four distinct queries, (3) constructive
multi-roll/top-exit and blocked/edge-stop demos, (4) protected-Racket causal
counterexample and public one-query projection, (5) native inventory and
qualification at demo counts 2, 3, 6, (6) bounded optional peer reviews.

Both settings use identical inputs for the same seed. Queries are sampled on a
separate stream and include the 14×14 minimum and a substantive 30×30, six-roll
ladder. Off-path orange distractors do not change either setting's route.
The first two demonstrations cover multiple markers, six consecutive rolls, obstruction,
edge stops and top exits. Teaching checks fit finite rivals to demos alone;
no assertion of universal identifiability or measured training benefit is made.

## Run from the outer packet directory

```sh
python3 review.py run python3 -m pytest -q generators/ba32e05911b0/tests
python3 review.py run python3 generators/ba32e05911b0/workspace/parametric/verify.py \
  --seed 17 --demos 3 --out ../checks/ba32e05911b0/verified \
  --qualification ../checks/ba32e05911b0/qualification/qualification.json
python3 WORK/check_public_exports.py WORK/checks/ba32e05911b0/verified/public --queries 1 --demos 3
```

`adapter.generate(seed, settings, demos, queries)` accepts exact-integer seeds
0..2^63-1, demo counts 2..6, and exactly four queries. `settings` contains exactly
`{"direction":"right"}` (canonical default) or `{"direction":"left"}`. The left
rule is horizontal input/output reflection of the complete canonical function;
all decisions still read immutable input. Markers stay on the bottom row.

The private episode holds all four query inputs and labels. Only
`public_turn(episode, query_index)` is model-visible. It has the ordinary
`train`/`test` schema with exactly one query and no ordinal, settings, seed,
program, answer, future input or total-count hint. Its first view is byte-identical
to the first view of the corresponding single-query episode. Public filenames
are full SHA-256 digests of the exact canonical visible bytes. Never give the
private export index or the whole directory listing to the actor.

`verify.py` refuses existing output paths, re-executes every label with the
checkout's protected Racket backend before writing, and retains source/runtime
hashes plus private setting mappings. With `--qualification`, it also constructs
two source-bound wrong-intermediate witnesses and invokes the packet's native
witness replay. A replay is evidence, not owner acceptance.

Eleven Python rival families are fitted to demonstrations only: straight climb,
at-most-one roll, ignore obstruction, ignore edge stop, reuse the old column,
first marker only, cap the reached run at two cells, and stop after two, three, four or five rolls. Both parameter settings
are checked as alternatives. These are bounded tests, not universal uniqueness.
The causal ablation and ordinary labels additionally execute real Racket.

The inherited canonical sampler's seed-10 clear-climb lesson ambiguity is NOT
silently resolved by this separate native family. Existing canonical source,
authority, approval bytes and audit dispositions are unchanged. The new family
constructs the missing distinguishing demos instead. Existing tests now locate
the selected runtime portably and compare minified archival programs by the
same whitespace normalization as the existing rule-hash contract. The adapter's
default program still receives an exact byte-for-byte authority assertion.

Final self-review caught a fixed-two-roll shortcut: the original two-demo
lesson never exceeded two rolls, while its stress query required six. The
first demo now has six causally chained rolls on a 28×30 canvas, without
increasing the demo count. Explicit caps 1–5 are tested and refuted.
