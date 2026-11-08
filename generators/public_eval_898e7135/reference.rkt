(rule!
 ;; Infer the common integer scale of the outside colored pieces. Match their
 ;; shapes, under rotation/reflection, to the holes of the unique perforated
 ;; full-border rectangle. Color each hole, then enlarge the completed template.
 (lambda (g)
  (let ()
    (define os (objects g 0))
    ;; A frame has a complete rectangular perimeter and at least one zero cavity.
    (define frame
      (for/first ((o os)
                  #:when
                  (and (> (obj-h o) 2) (> (obj-w o) 2)
                       (for/and ((p (positions-in-rect (obj-r1 o) (obj-c1 o) (obj-r2 o) (obj-c2 o))))
                         (if (or (= (first p) (obj-r1 o)) (= (first p) (obj-r2 o))
                                 (= (second p) (obj-c1 o)) (= (second p) (obj-c2 o)))
                             (= (at g (first p) (second p)) (obj-color o))
                             (or (= (at g (first p) (second p)) 0)
                                 (= (at g (first p) (second p)) (obj-color o)))))
                       (> (count-color (subgrid g (obj-r1 o) (obj-c1 o) (obj-r2 o) (obj-c2 o)) 0) 0)))
        o))
    (define frame-color (obj-color frame))
    (define template (subgrid g (obj-r1 frame) (obj-c1 frame) (obj-r2 frame) (obj-c2 frame)))
    (define holes (objects template frame-color))
    (define pieces (filter (lambda (o) (not (equal? o frame))) os))
    (define (expanded cells k)
      (for*/list ((p (normalize-cells cells)) (dr (range k)) (dc (range k)))
        (list (+ (* (first p) k) dr) (+ (* (second p) k) dc))))
    (define (matching hole k)
      (define target (sort (expanded (obj-cells hole) k) cell<))
      (filter (lambda (o) (member target (all-transforms (obj-cells o)))) pieces))
    ;; A single scale must fit EVERY cavity, not just the first or largest one.
    (define scale
      (for/first ((k (range 1 (+ 1 (quotient 30 (max (rows template) (cols template))))))
                  #:when (for/and ((hole holes)) (not (null? (matching hole k))))) k))
    (define solved
      (for/fold ((out template)) ((hole holes))
        (recolor-cells out (obj-cells hole) (obj-color (first (matching hole scale))))))
    (build-grid (* scale (rows solved)) (* scale (cols solved)) (r c)
      (at solved (quotient r scale) (quotient c scale))))))
