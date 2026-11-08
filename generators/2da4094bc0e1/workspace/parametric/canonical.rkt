(rule!
  (grid-from-fn h w
    (lambda (r c)
      (let ((v (cell-at g r c)))
        (if (and (= v 0)
                 (or
                   (and (< (+ c 3) w)
                        (= (cell-at g r (+ c 1)) 4)
                        (= (cell-at g r (+ c 2)) 4)
                        (= (cell-at g r (+ c 3)) 4)
                        (or (= (+ c 4) w)
                            (not (= (cell-at g r (+ c 4)) 4))))
                   (and (>= (- c 3) 0)
                        (= (cell-at g r (- c 1)) 4)
                        (= (cell-at g r (- c 2)) 4)
                        (= (cell-at g r (- c 3)) 4)
                        (or (< (- c 4) 0)
                            (not (= (cell-at g r (- c 4)) 4))))))
            6
            v)))))