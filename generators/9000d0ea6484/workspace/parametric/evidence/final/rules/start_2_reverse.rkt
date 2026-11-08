(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (sec (lambda (si r c) (at g r (+ (* si 5) c))))
                (priority (list 2 1 0 3)))
           (build-grid h
                       4
                       (r c)
                       (let* ((hit (find (lambda (si) (!= (sec si r c) 0)) priority)))
                         (if hit (sec hit r c) 0))))))