(rule!
  (grid-from-fn h w
    (lambda (r c)
      (let ((v (cell-at g r c)))
        (if (and (= v 0)
                 (or
                   (and (< (+ c 2) w)
                        (= (cell-at g r (+ c 1)) 6)
                        (= (cell-at g r (+ c 2)) 6))
                   (and (>= (- c 2) 0)
                        (= (cell-at g r (- c 1)) 6)
                        (= (cell-at g r (- c 2)) 6))))
            8
            v)))))