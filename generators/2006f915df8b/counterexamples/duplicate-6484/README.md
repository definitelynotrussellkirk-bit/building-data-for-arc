# Retained intermediate lesson failure

`frozen_generator.py` is the exact intermediate source with SHA-256
`71e41a5d785f0dd50b18f315af279c3ad22274c1ab37e0b6d601cfa46309df84`.
The transient generator_path in the original counterexample record identifies
where that snapshot was reviewed; use this frozen file for reproduction.

Seed 6484, easy difficulty, exact grid_h=7 and grid_w=8, starting at index 1:
indices 2 and 4 duplicate, accepted indices are [1,2,3,5], and holding out index 2
leaves the fewest-turns rival consistent with every demonstration but wrong on
the query. `reproduce.py` checks this with independent Python BFS.

From the outer packet root:

```bash
python3 review.py run python3 generators/2006f915df8b/counterexamples/duplicate-6484/reproduce.py
```

The initial record honestly says Racket validation was pending when captured.
The later return evidence `checks/main-reference-racket.json` and
`checks/main-reference-validation.json` confirms all five retained inputs with
the unchanged selected Racket rule. The final generator's regression accepts
[1,2,3,4], preserves distinct witnesses, and passes every query rotation.
