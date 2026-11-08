# Workspace

`probe_cyclic_lessons.py` is a source-bound regression tool for this generator's
four-slot curriculum. It checks every requested consecutive lesson start against
the selected generator's own schedule declaration and every named
`LESSON_COMPETITORS` rival, recording the generator hash and exact input hashes.
It complements (rather than replaces) the Racket-backed battery and shared
lesson census.

Example from the packet root:

```sh
python3 run_with_racket.py python3 generators/0994294912bf/workspace/probe_cyclic_lessons.py \
  --seeds 17,4242,424242 --starts 32 --out ../checks/cyclic-lessons.json
```

Workspace drafts and probes are never automatically selected. The selected
implementation is `../generator.py`.
