(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (cellmap g
                    (r c v)
                    (if (or (zero? (mod r 3)) (zero? (mod c 3))) 0 (if (= v 8) 0 2))))))