(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (cellmap g (r c v) (if (= 1 (length (unique (col g c)))) 5 0)))))
