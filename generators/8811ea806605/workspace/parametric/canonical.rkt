(rule!
 ;; Per-column HISTOGRAM: count the blue(1) cells in each column and redraw
 ;; them as a bottom-aligned bar of that height.
 (grid-from-fn h w (lambda (r c)
   (let ((cnt (count-where (lambda (rr) (= (at g rr c) 1)) (range h))))
     (if (>= r (- h cnt)) 1 0)))))