# generic_resize_gen3

gen3: NON-UNIFORM scale — each row repeated by a per-row ratio and each
column by a per-col ratio (various ratios 1..3, fixed per task). Program:
(scale-map g (list row-ratios...) (list col-ratios...)). All pairs in a task
share input dims so the same ratio lists apply; content varies. Covers
asymmetric/stretch resizes (different vertical vs horizontal blow-up).

Kind: `generic`. Imported version: `1.0.0`.
Approval is derived by the catalog from current code and retained evidence.
