# Workspace

`probe_generator.py` is a reusable, source-bound review probe for the selected
`../generator.py`. It independently checks canonical labels, the complete public
schedule, every held-out query rotation, deterministic generation, observer
fidelity, semantic witnesses, canonical-shortcut fit/refutation, and literal
override boundaries.

Run from the packet root through the supplied runtime wrapper:

```bash
sha=$(sha256sum WORK/repo/generators/733c1bac8c45/generator.py | awk '{print $1}')
python3 review.py run python3 generators/733c1bac8c45/workspace/probe_generator.py \
  --expected-generator-sha256 "$sha" \
  --seeds-per-band 64 \
  --out ../checks/733c1bac8c45-workspace-probe/report.json
```

The independent Python oracle is diagnostic only. The canonical Racket rule
remains the label authority. Workspace drafts are never automatically selected.
