# Rolling-direction sampler diversity

The two episode rules and canonical default are unchanged: `direction=right|left`.
Both independently reviewed implementations materialize byte-identical programs.
This merge adds within-setting input diversity, with no extra rule or setting.

One complete original sampler is selected by episode seed: even seeds use the
six-roll curriculum; odd seeds use the four-roll, interacting-marker curriculum.
Selection never reads direction, demo count or query count. Both directions
therefore receive matched inputs, and increasing either count preserves prefixes.
The source modules and their own lesson checks are retained exactly.

The public contract supports2–6demos and1–4queries. The six-roll source still
constructs/checks its original four queries, then the wrapper selects the requested
prefix. The interacting source natively supports1–4queries. No count hint, branch,
settings, future input or query answer enters the one-query public projection.

`prototype.py`/`six_roll_adapter.py` retain the original six-roll source;
`interacting/` retains the independent source. Their detailed original scopes are
in `SIX-ROLL-README.md` and `interacting/README.md`. A four-roll curriculum is not
claimed to teach caps beyond its own four-roll query demands; the original
six-roll curriculum retains its cap1–5refutations and stress scene unchanged.
Production generator, reference authority and current approval remain unchanged.
Fresh owner acceptance of this source mixture is required before it is usable.
