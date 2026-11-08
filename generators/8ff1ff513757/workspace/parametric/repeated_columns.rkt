(rule!
 (let* ((kept (filter (lambda (row) (any? (lambda (v) (!= v 0)) row)) g))
        (compact (if (empty? kept) (list (make-list w 0)) kept))
        (hh (length compact))
        (ww (length (first compact))))
   (grid-from-fn hh ww
     (lambda (r c)
       (let* ((v (at compact r c))
              (occupied
                (length
                  (filter
                    (lambda (rr) (!= (at compact rr c) 0))
                    (range 0 hh)))))
         (if (and (!= v 0) (>= occupied 2)) 9 v))))))
