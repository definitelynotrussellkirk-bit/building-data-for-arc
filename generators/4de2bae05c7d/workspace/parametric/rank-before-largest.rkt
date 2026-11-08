(rule!
  (let ((dummy 0))
    (define (cell<? a b)
      (or (< (first a) (first b))
          (and (= (first a) (first b)) (< (second a) (second b)))))
    (define forms
      (list (list (list 0 0) (list 1 0) (list 1 1))
            (list (list 0 1) (list 1 0) (list 1 1))
            (list (list 0 0) (list 0 1) (list 1 0))
            (list (list 0 0) (list 0 1) (list 1 1))))
    (define original-blue
      (filter (lambda (o) (= (obj-color o) 1)) (objects g 0)))
    (define chosen-before
      (if (null? original-blue) #f (pick-max original-blue obj-size)))
    (define stage1
      (for/fold ([out g]) ([obj (filter (lambda (o) (= (obj-color o) 4)) (objects g 0))])
        (let ((n (sort (normalize-cells (obj-cells obj)) cell<?)))
          (if (and (= (obj-size obj) 3) (member? n forms))
              (paint-cells out (obj-cells obj) 1)
              out))))
    (if chosen-before
        (paint-cells stage1 (obj-cells chosen-before) 2)
        stage1)))
