## f6b9f647b109

### AUD-F6-S1 — Reproduced strict-scalar contract defect

Audited source SHA-256: `023e6e5cdcad56b56c408f6de869573c635cd4c02802379b7f3f23d6114aad68`.

The combined audit preset passed 13/13 portable tests and the strict semantic gate (`checks/audit/f6b9f647b109-combined/result.json`). A separate `defect_lint` failed with 84 `strict-scalar` warnings (`checks/audit/f6b9f647b109-defect-lint/result.json`). The minimal source-bound reproducer is `checks/audit/f6b9f647b109/strict-scalar-reproducer.json`.

That reproducer shows all four invalid probes were accepted and produced grids that passed `self_check`: boolean `seed=true`, negative `sample_index=-1`, invalid `difficulty="__invalid_difficulty__"`, and string override `grid_h="6"`. The resulting grid SHA-256 values are, respectively, `2b4f6938f88a1192f57b0dc8b2c05da3c13b8d1174eff619acc8ad4f76f5a39d`, `f56edeafa94b2338fb78aa55202d24e3dbe842f473b25e2fcb445bb5af15ce79`, `a78841a716c31d59c62139dc2beab970293915d724530a9997b44985664cfa39`, and `137c41552314f425bbe873333bbd00f176bfa7b6fcc6fc3a0d58cf19cb9bbb10`.

This is an actionable public-call/override validation defect, not a Racket-label disagreement. No source was changed and no approval is claimed.
