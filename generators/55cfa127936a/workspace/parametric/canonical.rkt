(rule!
 ;; Per column, keep only the FIRST yellow(4); everything else clears.
 (let ()
   (define (row-with-four c)
     (first (filter (lambda (r) (= (at g r c) 4)) (range h))))
   (grid-from-fn h w (lambda (r c) (if (= r (row-with-four c)) 4 0)))))