# Direction-parametric rule prototype

This prototype tests one episode-level rule parameter without changing the selected canonical generator or authority. The hidden parameter is `direction ∈ {down, up}`. It is selected once for a complete episode; it is never changed between demonstrations and query.

- `down` is the exact selected canonical rule (`03fbcf596117`).
- `up` changes only the target row from `r + 1` to `r - 1` and changes the safe source-row range accordingly.
- Both materializations are complete executable Racket `rule!` forms.
- Every retained fixture makes both rules act, and their outputs differ.
- Private episode files retain the parameter, source, hashes, and query label.
- Public episode files retain demonstrations and the unlabeled query only.

From the packet root, execute both materializations through the actual Racket bridge and retain evidence with:

```bash
python3 review.py run python3 generators/382eb0e592eb/workspace/parametric/direction.py \
  --out-dir ../checks/parametric/direction-run
```

The replay writes:

- `WORK/checks/parametric/direction-run/summary.json`
- `WORK/checks/parametric/direction-run/racket/{down,up}.rkt`
- `WORK/checks/parametric/direction-run/episodes/{down,up}/private.json`
- `WORK/checks/parametric/direction-run/episodes/{down,up}/public.json`

This is a prototype-only family. The production generator continues to use the fixed `down` rule and its unchanged selected hash.
