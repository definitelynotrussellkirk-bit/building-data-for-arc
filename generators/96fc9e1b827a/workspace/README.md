# Workspace

The selected implementation is `../generator.py`.

## Reusable shortcut probe

Run from the repository root:

```bash
python3 generators/96fc9e1b827a/workspace/probe_shortcuts.py \
  --seed 91337 --starts 4 \
  --out generators/96fc9e1b827a/workspace/shortcut_probe.json
```

The probe loads the selected generator, iterates its actual
`CANONICAL_SHORTCUTS` declarations, verifies each against every labelled canonical
pair, searches the production sampler for exact disagreements, and audits every
query rotation in four schedule residues across all three difficulty bands. It
embeds the exact grids and both predictions so a future reviewer can pass a witness
to the supported Racket `arcpuzzles apply` command.

`shortcut_probe.json` is the retained report for generator SHA-256
`25ca3f14554efa28e82b60c8fd8576ece2e605e706de10e5f600aa71952dd2eb`.
The probe is finite evidence against declared rivals, not a proof against all
possible alternative rules.
