(rule!
  (fold-cells g g
    (lambda (out r c v)
      (if (or (= v 0) (= v 5))
          out
          (let turn ([cc (- c 1)] [acc out])
            (if (and (>= cc 0) (= (at g r cc) 0))
                (turn (- cc 1) (set-cell acc r cc v))
                acc))))))
