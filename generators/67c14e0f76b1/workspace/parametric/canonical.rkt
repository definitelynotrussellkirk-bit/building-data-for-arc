(rule!
  (fold-cells g g
    (lambda (out r c v)
      (if (and (= v 0) (> c 0) (< c (- w 1)) (= (at g r (- c 1)) 1) (= (at g r (+ c 1)) 1))
          (set-cell out r c 2)
          out))))