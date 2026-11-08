# Workspace

The selected implementation is `../generator.py`.

`domain_probe.py` is a reusable, source-bound reviewer tool. It enumerates all 3,000 combinations of the four declared exact axes across all difficulty bands, checks `self_check` and `observe_overrides`, and records finite polyomino-bank support. From the packet root:

```sh
python3 review.py run python3 generators/094e0794786c/workspace/domain_probe.py \
  --out ../checks/domain-probe.json
```

The portable regression suite in `../tests/test_generator.py` independently checks canonical labels, deterministic generation, validation mutations, semantic rivals, lesson identifiability, exact overrides, and this probe. Workspace drafts are never automatically selected.
