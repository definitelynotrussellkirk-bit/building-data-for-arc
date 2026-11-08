(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (cellmap g
                    (r c v)
                    (if (or (zero? (mod r 5)) (zero? (mod c 5))) 0 (if (= v 8) 0 2))))))