(rule! (let ((dummy 0))
  (define (norm-cells cells) (sort (normalize-cells cells) cell<))
  (define (objs-color grid color)
    (filter (lambda (obj) (= (obj-color obj) color)) (objects grid 0)))
  (define (horizontal? obj)
    (equal? (norm-cells (obj-cells obj)) (list (list 0 0) (list 0 1))))
  (define targets (filter horizontal? (objs-color g 5)))
  (define chosen
    (first
      (sort targets
        (lambda (a b)
          (cell< (first (sort (obj-cells a) cell<))
                 (first (sort (obj-cells b) cell<)))))))
  (paint-cells g (obj-cells chosen) 8)))