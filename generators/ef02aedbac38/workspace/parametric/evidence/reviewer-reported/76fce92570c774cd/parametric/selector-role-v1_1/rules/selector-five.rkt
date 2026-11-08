(rule! (lambda (g)
         (let* ((other (find-first (lambda (v) (!= v 5)) (grid-colors g))))
           (cellmap g (r c v) (if (= v 5) other 0)))))