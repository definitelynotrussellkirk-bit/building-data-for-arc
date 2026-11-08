(rule!
  (let ((dummy 0))
    ;; Causal ablation: skip nearest-marker assignment (Step A), so the
    ;; aggregate-selection step has no assigned-color intermediate to consume.
    g))
