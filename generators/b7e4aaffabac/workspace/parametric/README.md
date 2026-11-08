# b7e4aaffabac overlap-policy prototype

This native adapter keeps the canonical two-solid-rectangle grammar fixed and
varies one episode-level parameter:

- `trimmed` (default): paint color 8 across the gap on the one-cell-inset
  interior of the shared facing span. Its program is byte-for-byte the selected
  canonical Racket rule.
- `full`: perform the same object ordering and gap derivation, then paint color
  8 across the entire raw shared facing span.

The sampler supports 2–6 demonstrations and exactly four queries. Inputs are
matched across settings, demonstration prefixes are stable, and the four query
profiles do not depend on demonstration count. The final query is 30×30.
Qualification and retained evidence are authoring checks only; owner acceptance
and training admission remain separate downstream decisions.
