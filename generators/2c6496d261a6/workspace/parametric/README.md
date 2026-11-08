# Parametric row-selection family

The canonical default is byte-identical to the selected `2c6496d261a6` Racket
rule. `row_selection` chooses `one_row_only` or `fewest_rows`; inputs are matched
across settings for the same seed and count request.

Sequential dependency: A counts the distinct occupied rows of every nonzero
color and, for `fewest_rows`, derives the input-dependent minimum. B consumes
that threshold to retain exactly the colors attaining it. The protected witness
uses threshold one as a `wrong_intermediate` counterfactual.

The deterministic sampler supports 2–6 demonstrations and 1–4 queries. The
second demonstration supplies positive one-row action while the first separates
the settings; the four-query schedule ends with a substantive exact 30×30 scene.
`audit.py` checks a finite plausible rival set and grants no owner acceptance or
training admission.
