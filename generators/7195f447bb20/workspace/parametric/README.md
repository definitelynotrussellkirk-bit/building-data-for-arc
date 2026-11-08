# Guarded diagonal completion with a causal cascade

The default `canonical` setting is byte-for-byte the selected task program. It
fills a down-right `4,0,4` midpoint only when the predecessor and successor on
the same diagonal are not 4. Every generated scene includes an explicit guarded
near-miss, so an unguarded shortcut no longer fits the lesson.

The `cascade` setting adds a non-collapsing sequential dependency. Step A applies
the canonical guarded diagonal completion. The input-dependent intermediate is
the set of centers newly painted by A. Step B uses only those new centers as the
left endpoint of a horizontal `4,0,4` pattern and fills its midpoint. Without A,
those horizontal triggers do not exist.

The deterministic grammar supports 2–6 demonstrations and 1–4 queries. Every
scene distinguishes both settings; the fourth query is 30×30 and contains many
independent cascades plus a guarded non-fill.
