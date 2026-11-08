# Authoring workspace

The selected implementation remains `../generator.py`. Workspace prototypes
are never selected automatically and do not change approval.

- `probe_shortcuts.py`: reproduce all declared canonical-fitting shortcuts and
  one default-stream counterexample through the public Racket apply command.
- `parametric/threshold.py`: proposed episode-fixed zero-count threshold;
  see `parametric/README.md` for commands, evidence structure and scope.

From the outer review packet directory, use a new output directory:

```bash
python3 review.py run python3 generators/520fe6e64fb6/workspace/probe_shortcuts.py --seed 17 --sample-index 0 --difficulty easy --out ../checks/shortcuts-new
```

These are authoring tools that consult reference answers. Keep them closed
during a visible-only solve.
