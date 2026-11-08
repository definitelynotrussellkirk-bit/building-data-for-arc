(rule!
 ;; Recolor every blue(1) below the header row with the header's FIRST
 ;; non-zero color; everything else clears.
 (let ((color (first (filter (lambda (v) (!= v 0)) (first g)))))
   (grid-from-fn h w (lambda (r c) (if (and (> r 0) (= (at g r c) 1)) color 0)))))