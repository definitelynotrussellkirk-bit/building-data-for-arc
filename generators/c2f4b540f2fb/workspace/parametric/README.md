# c2f4b540f2fb local-tier parametric family

Private episode parameters choose the local coordinate axis (`u` or `v`) and
extreme (`max` or `min`) whose complete tied tier is transferred from the source
frame to the target frame. The default `axis=u, extreme=max` returns the selected
canonical Racket source byte-for-byte. Inputs are sampled independently of the
setting; two demonstrations are the declared minimum and every episode has four
distinct private queries, including a substantive 30×30 scene.

From `WORK/repo` after running the packet setup:

```bash
python3 -m pytest generators/c2f4b540f2fb/tests -q
python3 generators/c2f4b540f2fb/workspace/parametric/adversarial_probe.py \
  --out generators/c2f4b540f2fb/workspace/parametric/evidence/current/adversarial.json
python3 -m arcpuzzles parametric manifest c2f4b540f2fb \
  --evidence generators/c2f4b540f2fb/workspace/parametric/evidence \
  --reported-checks 'task tests and bounded protected-Racket adversarial probe'
```

Owner source review, native qualification/acceptance and training admission are
separate from this proposed task-local family.
