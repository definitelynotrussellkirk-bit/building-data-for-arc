(rule!
 ;; Keep only the COLUMNS whose header (row 0) is yellow(4); header dropped.
 (let ((keep (filter (lambda (c) (= (at g 0 c) 4)) (range 0 w))))
   (for/list ((r (in-range 1 h)))
     (for/list ((c (in-list keep))) (at g r c)))))