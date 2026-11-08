# Workspace

`probe_curriculum.py` is a retained task-local authoring probe.  It measures:

- valid/unique ordinary inputs by band, with an explicit 90% uniqueness floor;
- whether every declared canonical shortcut fits every usable canonical pair;
- each declared semantic rival's agreements, refutations, and errors; and
- every requested sliding three-example window under the generator's actual
  consecutive-sample lesson policy.

It uses the generator's public Python hooks and mirror, so it deliberately does
**not** claim reference authority.  Run the shared Racket battery and
`arcpuzzles lesson-census` separately.

From a packet root:

```sh
python3 run_with_racket.py python3 generators/f84f23e456ac/workspace/probe_curriculum.py \
  --per-band 100 --window-starts 100 \
  --out ../checks/curriculum-probe-final.json
```

The JSON records the generator source hash, seed, profile/motif counts,
canonical-shortcut results, rival results, and ambiguous-window reproducers.
Do not use this probe or any canonical-data helper during a visible-only solve.
