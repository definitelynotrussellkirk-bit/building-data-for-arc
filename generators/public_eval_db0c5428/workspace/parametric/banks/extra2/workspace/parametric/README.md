# public_eval_db0c5428: authoring-ready native family

Default `expand` is byte-identical to the task's `reference.rkt`.
Alternate `center_majority` is a separate, episode-fixed rule. See ../../notes.md
for the grammar, causal dependency, supplied-gold exposure and explicit limits.
No owner registration, acceptance, or training admission is implied.

From WORK (choose new output directories when rerunning):

```sh
python run_with_racket.py python generators/public_eval_db0c5428/workspace/parametric/audit.py --seeds 64 --out ../checks/public_eval_db0c5428/new-audit
python run_with_racket.py python -m arcpuzzles.review_public_creation preflight public_eval_db0c5428 --root . --out ../checks/public_eval_db0c5428/new-preflight
```

The native `adapter.generate(seed, {"finish": "expand"}, demos=3, queries=4)`
returns private claimed labels and exact Racket source. Its complete four-query
bank is shuffled before prefix selection. Execute labels with the preflight or
auditor; never present this private episode directly to a learner.
`adapter.public_view(episode, index)` gives one input-only query with visible
demonstrations. `adapter.public_io.export` validates the entire batch, then writes
hash-named files in sorted hash order. The export directory is controller-only;
revealing its listing or all files would expose future queries/counts.

The returned `checks/verify_handoff.py` validates source bindings, builds the
existing official causal-witness schema from an exact authoring-preflight case,
and replays source from a relocated checkout. It needs the declared Python/Racket
runtime; it does not perform native acceptance. Its negative tests cover drift,
path traversal, missing files, duplicate bindings, and symlinks.
