# Native hole-threshold parametric family

Status: **reviewer-ready candidate; owner acceptance pending**.

The episode-fixed parameter is `min_holes`:

- `1` — exact canonical default: recolor every component with at least one
  enclosed background region to `8`; recolor a zero-hole component to `2`.
- `2` — nearby alternative: only components with at least two enclosed regions
  become `8`; zero- and one-hole components become `2`.

Both settings preserve the original reasoning chain. **A** extracts each
4-connected color-6 component and counts its enclosed background regions. The
input-dependent intermediate is the per-component hole count. **B** compares
that count with the episode threshold and selects output color `8` or `2`; B
cannot choose the color until A has produced the count.

Inputs are setting-independent and contain four separated objects: a non-frame
one-hole object, a two-hole object, a dense leaky zero-hole near-miss, and a
solid zero-hole object. The first two demonstrations distinguish both settings.
Demo and query streams are independent and prefix-stable. Supported requests are
2–6 demonstrations and 1–4 queries; qualification uses four queries. The fourth
query is a substantive 30×30 scene whose objects contact all four canvas borders.

Public projection contains only labeled demonstrations and unlabeled query
inputs. Settings, programs, query answers, and causal witness programs remain
private. Finite qualification and the named shortcut audit do not prove
identifiability against every imaginable program or measured training benefit.
