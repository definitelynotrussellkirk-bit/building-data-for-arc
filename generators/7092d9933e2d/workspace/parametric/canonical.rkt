(rule!
  (grid-from-fn (rows g) (cols g)
    (lambda (r c)
      (let ((colors (filter (lambda (v) (not (= v 0))) (row-at g r))))
        (if (empty? colors) 0 (first colors))))))
