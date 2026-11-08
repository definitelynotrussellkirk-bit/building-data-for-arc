(rule!
  (grid-from-fn (rows g) (cols g)
    (lambda (r c)
      (let* ((vals (filter (lambda (v) (not (= v 0))) (row-at g r)))
             (start (- (cols g) (length vals))))
        (if (< c start) 0 (list-ref vals (- c start)))))))