(rule!
 ;; Every input row is a solid stripe and the final row repeats the stripe
 ;; directly above it.  Read one color from each row except that duplicate.
 ;; Those colors, in order, are the outside-to-inside layers of an even square.
 (lambda (g)
   (let* ([layers
           (for/list ([r (in-range (- (rows g) 1))])
             (at g r 0))]
          [side (* 2 (length layers))])
     (build-grid side side (r c)
       (list-ref layers
                 (min r c (- side 1 r) (- side 1 c)))))))
