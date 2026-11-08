# Workspace

The selected implementation is `../generator.py`. `reference_probe.py` is a reusable, source-bound authoring probe with an independent component/hole/packing oracle; it does not call the generator's analysis or mirror when computing expected outputs.

Run it from the packet root:

```sh
python3 repo/generators/786a759f780e/workspace/reference_probe.py \
  --per-band 60 --out checks/reference-probe.json
```

It checks deterministic replay, profile/canvas realization, strict-profile frequency, mixed-color components, input uniqueness, the Python rule mirror, and every currently declared `LESSON_COMPETITORS` entry. It is useful for fast iteration before the Racket-backed battery and production lesson census. It samples individual draws; use the shared `lesson-census --rotate-query` command for complete source-bound lesson ambiguity checks.
