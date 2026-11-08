# ec23789c7821 native parametric family

`finish=vertical` returns the byte-exact canonical program: every interior
horizontal length-three run is turned into a vertical length-three run, while
all non-target colored cells are preserved. In `finish=plus`, stage A computes
that same full canonical intermediate. Stage B then detects exact vertical
triples in the intermediate and adds a left and right arm at each center.
Consequently, stage B obtains both its colors and its locations from stage A;
applying it directly to the raw H3 input produces a different result.

The deterministic, setting-independent sampler supports the full declared
7×7–30×30 rectangle range. Even at 7×7 it constructively places at least two
separated horizontal targets without allowing preserved distractors to overwrite
them. The larger fixed episodes include a substantive 30×30 query with targets
in all four quadrants.

The adapter supports 2–6 demonstrations and 1–4 queries. Its certificate checks
those count bounds, verifies every label, requires one uniquely identified
setting from demonstrations alone, and rejects duplicate inputs across train and
test. Focused tests, native preflight, and the reusable boundary audit replay
both settings with protected Racket; owner acceptance and training remain
separate steps.
