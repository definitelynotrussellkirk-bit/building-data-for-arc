(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (cellmap g
                    (r c v)
                    (cond
                      ((and (zero? r) (zero? c)) (at g 1 2))
                      ((and (zero? r) (= c (- w 1))) (at g 2 2))
                      ((and (= r (- h 1)) (zero? c)) (at g 1 1))
                      ((and (= r (- h 1)) (= c (- w 1))) (at g 2 1))
                      (else 0))))))