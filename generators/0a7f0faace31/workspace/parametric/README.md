# Proposed selection-order parameter (isolated prototype)

This prototype preserves the original family’s object roles, guide relationship,
center test, connectivity, scan order, and raw-crop transformation. It varies one
small hidden rule parameter once per episode:

- `selection_order = first | last`

`first` is the original/default setting and materializes the selected canonical
Racket program byte-for-byte. `last` changes only the eligible-object selection
site to search the same row-major object list in reverse. Every retained episode
contains three labeled demonstrations and one query, all sharing one setting.
All four inputs use the existing compound teaching construction, so the alternate
setting changes every output and is refuted under every query rotation.

Run from the outer extraction directory:

```bash
python3 review.py run python3 \
  generators/0a7f0faace31/workspace/parametric/prototype.py \
  --out ../checks/parametric
```

The command executes both exact Racket programs through the protected bridge,
checks an independent Python mirror, retains one complete episode per setting in
`WORK/checks/parametric/evidence.json`, and writes public challenge views under
`WORK/checks/parametric/public/`. Public views omit the hidden parameter, Racket
program, counterfactual outputs, and query answer.

This is a proposed task-local prototype only. It does not change the selected
production generator’s canonical rule, authority hash, or approval state.
