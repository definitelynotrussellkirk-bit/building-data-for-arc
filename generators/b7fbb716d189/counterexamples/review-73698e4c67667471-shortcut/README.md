# Corner-shortcut counterexample

This ordinary, validator-lawful generated input fixes the transform token at the
bottom-left while using token value `2` (clockwise rotation).  The wrong
canonical-fit shortcut maps bottom-left to identity and therefore disagrees with
the selected Racket rule.  `python_probe.json` binds seed, sample index,
overrides, generator hash and rule hash; `racket.json` is the supported
`arcpuzzles apply` record.
