(rule!
  (let* ((greens (filter (lambda (obj) (= (obj-color obj) 3)) (objects g 0)))
         (key (first (filter (lambda (obj) (= (obj-color obj) 1)) (objects g 0))))
         (rank (obj-size key))
         (ordered
          (sort greens
                (lambda (a b)
                  (if (= (obj-size a) (obj-size b))
                      (cell< (first (sort (obj-cells a) cell<))
                             (first (sort (obj-cells b) cell<)))
                      (< (obj-size a) (obj-size b))))))
         (target (list-ref ordered (- rank 1))))
    (paint-cells g (obj-cells target) 6)))
