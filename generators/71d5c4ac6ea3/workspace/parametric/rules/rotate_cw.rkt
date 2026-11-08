(rule!
 (let ((dummy 0))
   (define (points-of grid color)
     (sort (find-color grid color) cell<))
   (define (rotate-offset d)
     (list (second d) (- (first d))))
   (define (stamp-offsets out anchor offsets color)
     (paint-cells
      out
      (filter
       (lambda (p)
         (in-bounds? (first p) (second p) (rows out) (cols out)))
       (map
        (lambda (d)
          (list (+ (first anchor) (first d))
                (+ (second anchor) (second d))))
        offsets))
      color))
   (let* ((origin (first (points-of g 9)))
          (ones (points-of g 1))
          (as-drawn
           (map
            (lambda (p)
              (list (- (first p) (first origin))
                    (- (second p) (second origin))))
            ones))
          (offsets (map rotate-offset as-drawn))
          (seeds (points-of g 2)))
     (for/fold ((out (empty-grid (rows g) (cols g) 0)))
               ((seed (in-list seeds)))
       (stamp-offsets out seed offsets 8)))))
