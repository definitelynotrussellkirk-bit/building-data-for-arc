# Working notes: 334cbd1692c7

## Current decision

The version `3.1.0` base generator and canonical Racket rule were retained unchanged. Across 240 ordinary draws spanning `difficulty=None`, `medium`, and `hard`, every scene passed its self-check and parsed as one large rectangle, one interior marker, and one isolated radius-2 outside key. The authoring preflight also replayed every supplied original label and two ordinary staged draws.

## Parametric family

`extension_mode` has two episode-fixed values:

- `to_edges` — exact canonical/default program; erase the outside key, stamp its colored footprint at every rectangle marker, and extend the four extracted arm colors to each rectangle edge.
- `key_only` — erase the outside key and stamp only its extracted footprint at every rectangle marker, without extending arms to the edges.

Input generation is independent of the setting. Demo and query streams are independently seeded and prefix-stable for 2–6 demonstrations and 1–4 queries. Scenes vary dimensions, palette, key-arm lengths, marker positions, and one to three rectangles. Every four-query bank contains one substantive 30×30 scene with three rectangles, three markers, and a 12-cell key.

The causal chain is: locate and grow the outside key, extracting its colored relative offsets and four direction-to-color assignments → retain that input-dependent footprint/mapping as the intermediate → erase the key and stamp/extend the extracted pattern at rectangle markers. A protected-Racket `wrong_intermediate` witness rotates the direction-color assignments and changes 13 cells on the retained 30×30 case.

## Checks and limits

- 17/17 staged task tests passed, including 240 base draws and protected-Racket parity for both settings.
- Both Racket programs passed complete-expression checks.
- A 16-seed audit checked 160 generated pairs, all count prefixes, two-demo identification, `no_key_erase` and rotated-color attacks, 240 ordinary base draws, and a 30×30 stress scene in every full query bank.
- Authoring preflight passed 4 jobs and 32 protected-Racket evaluations; it is not owner qualification or acceptance.
- Public projection produced 16 single-query views; 24 first-turn private-field invariance mutations passed.

Finite demonstrations rule out the tested rivals, not every conceivable hypothesis. Next owner action: review the unchanged base and new task-local family, integrate the exact files, then run native qualification and fresh acceptance.
