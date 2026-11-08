# Border-routed stencil cascade

This native adapter keeps the color-keyed top library and body-seed lookup of
`fdffdd0bbde7` while varying one episode-fixed rule parameter.

- `single_stage` is the exact canonical Racket program byte-for-byte.
- `border_routed_cascade` first stamps the body seed's own stencil. If that
  intermediate touches any output border, it selects the next library panel;
  otherwise it selects the previous panel. It stamps that selected stencil from
  every first-stage cell, retaining the original body color.

The alternative has a real sequential dependency: A materializes an
input-dependent first-stage cell set; its border state selects B's library entry,
so B cannot be selected before A is known. Inputs are sampled independently of
the setting. Every demonstration includes both border and interior routes and
bi-axially off-center visible anchors. Two demonstrations reject the other
setting plus declared center-anchor, constant-route, swapped-route, and
skip-first-stage shortcuts. Four-query episodes include a substantive exact
30×30 input with four library entries and at least twenty body seeds.

The supported native request is 2–6 demonstrations and 1–4 queries. Query index
zero is independent of demonstration count, so one-query and four-query first
turns use identical visible bytes. This is reviewer-ready source only; native
owner acceptance and any training admission remain separate.
