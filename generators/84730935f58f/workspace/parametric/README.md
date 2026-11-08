# 84730935f58f overlap-aware parametric family

`render_mode=union` is the exact canonical selector-controlled plus/X growth.
`render_mode=overlap_highlight` first computes each selected stencil footprint,
retains per-cell coverage multiplicity, then paints count-one cells cyan and
count-two-or-more cells red. The hidden setting is fixed for the episode.

The sampler supports 2–6 demonstrations and exactly four distinct queries. For
equal seed/count requests both settings receive identical inputs. Query sizes are
10×12, 16×18, 24×27 and 30×30; the larger scenes contain multiple overlap motifs,
isolated seeds, boundary clipping and content in all four quadrants.

Focused tests from the repository root:

```bash
pytest -q generators/84730935f58f/tests
```

After creating the source inventory, reviewer qualification is:

```bash
python -m arcpuzzles.review_base_preflight 84730935f58f \
  --demos 2 --out ../checks/84730935f58f/qualification
```

This is authoring evidence only. Owner native acceptance and training admission
remain separate.
