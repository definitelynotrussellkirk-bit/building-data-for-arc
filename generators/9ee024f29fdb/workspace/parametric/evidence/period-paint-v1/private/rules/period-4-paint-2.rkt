(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (cellmap g
                    (r c v)
                    (if (or (zero? (mod r 4)) (zero? (mod c 4))) 0 (if (= v 8) 0 2))))))