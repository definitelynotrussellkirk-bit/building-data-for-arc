(rule!
 ;; Every cyan(8) takes its ROW's leading-cell header color (empty headers
 ;; leave the 8 unchanged).
 (grid-from-fn h w (lambda (r c)
   (let ((key (at g r 0)) (v (at g r c)))
     (if (and (> c 0) (= v 8) (!= key 0)) key v)))))