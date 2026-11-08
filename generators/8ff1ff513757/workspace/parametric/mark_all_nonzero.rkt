(rule!
 (let* ((kept (filter (lambda (row) (any? (lambda (v) (!= v 0)) row)) g))
        (compact (if (empty? kept) (list (make-list w 0)) kept))
        (hh (length compact))
        (ww (length (first compact))))
   (grid-from-fn hh ww
     (lambda (r c)
       (if (!= (at compact r c) 0) 9 0)))))
