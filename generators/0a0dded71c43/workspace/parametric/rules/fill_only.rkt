(rule!
  (grid-from-fn h w
    (lambda (r c)
      (let ((v (cell-at g r c)))
        (if (and (= v 0)
                 (or (and (> c 0) (< c (- w 1))
                          (= (cell-at g r (- c 1)) 6)
                          (= (cell-at g r (+ c 1)) 6))
                     (and (> r 0) (< r (- h 1))
                          (= (cell-at g (- r 1) c) 6)
                          (= (cell-at g (+ r 1) c) 6))))
            7
            v)))))