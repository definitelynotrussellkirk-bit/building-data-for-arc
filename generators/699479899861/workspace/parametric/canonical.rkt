(rule!
  (for/fold ([out g]) ([obj (in-list (filter (lambda (o) (= (obj-color o) 2)) (objects g 0)))])
    (let* ((rs (remove-duplicates (map first (obj-cells obj))))
           (cs (remove-duplicates (map second (obj-cells obj))))
           (cells (for*/list ([r (in-list rs)] [c (in-list cs)])
                    (list r c))))
      (paint-cells out cells 3))))