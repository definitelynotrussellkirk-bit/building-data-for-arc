(rule!
 (let* ((kept (filter (lambda (row) (any? (lambda (v) (!= v 0)) row)) g))
        (compact (if (empty? kept) (list (make-list w 0)) kept))
        (hh (length compact))
        (ww (length (first compact))))
   (grid-from-fn hh ww
     (lambda (r c)
       (let ((v (at compact r c)))
         (if (and (!= v 0)
                  (or (and (> c 0) (!= (at compact r (- c 1)) 0))
                      (and (< c (- ww 1)) (!= (at compact r (+ c 1)) 0))))
             9
             v))))))
