(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((hw (/ (cols g) 2)))
             (build-grid h
                         hw
                         (r c)
                         (if (and (zero? (at g r c)) (zero? (at g r (+ c hw)))) 5 0))))))