(rule!
  (fold-cells g g
    (lambda (out r c v)
      (if (= v 0) out (set-cell out c r v)))))