(rule! (lambda (g)
         (let ((h (rows g))
               (w (cols g))
               (colors (row-at g 0)))
           (grid-from-fn h
                         w
                         (lambda (r c)
                           (if (< r 2) (at g r c) (nth colors (mod (- w (mod (- r 2) w)) w))))))))
