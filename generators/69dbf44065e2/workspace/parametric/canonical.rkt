(rule!
  (fold-cells g g
    (lambda (out r c v)
      (if (or (= v 0) (= v 5))
          out
          (let smear ([rr (+ r 1)] [acc out])
            (if (and (< rr (rows g)) (= (at g rr c) 0))
                (smear (+ rr 1) (set-cell acc rr c v))
                acc))))))