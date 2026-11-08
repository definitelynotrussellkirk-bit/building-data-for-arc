(rule! (lambda (g)
  (let ((h (rows g)) (w (cols g)))
    (grid-from-fn h w
      (lambda (r c)
        (let ((v (at g r c))
              (row-selected? (and (= 4 (at g r 0)) (= 4 (at g r (- w 1)))))
              (column-selected? (and (= 4 (at g 0 c)) (= 4 (at g (- h 1) c)))))
          (if row-selected?
              (cond ((zero? v) 8)
                    ((= v 8) 0)
                    ((= v 6) 7)
                    ((= v 7) 6)
                    (else v))
              v)))))))
