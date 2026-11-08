(rule!
 (let ()
   (define (yellow-rows c)
     (filter (lambda (r) (= (at g r c) 4)) (range h)))
   (define anchor-column
     (first (filter (lambda (c) (= (length (yellow-rows c)) 1))
                    (range w))))
   (define anchor-row (first (yellow-rows anchor-column)))
   (define (closer? a b)
     (let ([da (abs (- a anchor-row))]
           [db (abs (- b anchor-row))])
       (or (< da db)
           (and (= da db) (< a b)))))
   (define (nearest-row c)
     (first (sort (yellow-rows c) closer?)))
   (grid-from-fn h w
     (lambda (r c)
       (if (= r (nearest-row c)) 4 0)))))
