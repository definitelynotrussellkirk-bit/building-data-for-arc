(rule!
  (let ((dummy 0))
    (define (row-nz r)
      (filter (lambda (cv) (not (= (second cv) 0)))
              (map (lambda (c) (list c (at g r c))) (range (cols g)))))
    (define (payload-row? r)
      (let ((nz (row-nz r)))
        (and (= (length nz) 2)
             (= (second (first nz)) (second (second nz)))
             (all? (lambda (c) (= (at g r c) 0))
                   (range (+ (first (first nz)) 1) (first (second nz)))))))
    (define payload-rows (filter payload-row? (range (rows g))))
    (define chosen-row (first payload-rows))
    (define chosen (row-nz chosen-row))
    (paint-cells
      g
      (map (lambda (c) (list chosen-row c))
           (range (first (first chosen)) (+ (first (second chosen)) 1)))
      (second (first chosen)))))
