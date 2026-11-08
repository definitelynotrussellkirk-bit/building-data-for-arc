# Working notes: edb34dd65185

- Repaired the retained hard-seed failure where the sum of crop heights plus separators exceeded the output height. Generation now resamples the bounded shape combination, and `self_check` rejects any overflow.
- Preserved the exact canonical Racket bytes for ascending interior-hole count. Added one nearby setting, descending interior-hole count, with the canonical area and minimum-color tie-breakers unchanged.
- Demonstrations use a constructive non-monotone 1,0,2 ordering in scan/area/color space so fixed scan, area, color, or reverse-order shortcuts cannot imitate either setting.
- Final focused tests: 20 passed. Protected-Racket parity: six episodes / 60 executions. Bounded shortcut audit: 128 episodes, no declared rival survived both demonstrations. Query 4 is 30×30.
- Authoring preflight and the wrong-intermediate causal replay passed. Public projection verification and first-turn private-field invariance also passed.
- Limit: the shortcut census is finite, and reviewer authoring preflight is not owner qualification, acceptance, or training admission.
- Next owner action: integrate this exact patch, rerun native qualification against the source-bound manifest, then perform fresh acceptance.
