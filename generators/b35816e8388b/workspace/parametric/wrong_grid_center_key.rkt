(rule!
  (let ()
    (let* ((anchor (first (find-color g 9)))
           (key-row (first anchor))
           (key-color (at g key-row (quotient (cols g) 2)))
           (payloads
             (filter (lambda (obj)
                       (and (= (obj-color obj) key-color)
                            (> (obj-size obj) 1)))
                     (objects g 0)))
           (target (first payloads)))
      (paint-cells (empty-grid (rows g) (cols g) 0)
                   (obj-cells target)
                   8))))
