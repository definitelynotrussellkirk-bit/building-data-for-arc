(rule!
  (let ((dummy 0))
    (define (list-key< a b)
      (cond [(empty? a) #f]
            [(< (first a) (first b)) #t]
            [(> (first a) (first b)) #f]
            [else (list-key< (rest a) (rest b))]))
    (define (paste grid pat top left)
      (for*/fold ([out grid]) ([r (in-range (rows pat))] [c (in-range (cols pat))])
        (let ((v (at pat r c)) (rr (+ top r)) (cc (+ left c)))
          (if (and (not (= v 0)) (in-bounds? rr cc (rows out) (cols out)))
              (set-cell out rr cc v)
              out))))
    (define (crop-cells grid cells)
      (let ((bb (bbox-of-cells cells)))
        (subgrid grid (first bb) (second bb) (third bb) (fourth bb))))
    (define (hstack-center grids gap)
      (let* ((h (apply max (map rows grids)))
             (w (+ (apply + (map cols grids)) (* gap (- (length grids) 1)))))
        (let loop ([xs grids] [left 0] [out (empty-grid h w 0)])
          (if (empty? xs)
              out
              (let* ((piece (first xs))
                     (top (quotient (- h (rows piece)) 2)))
                (loop (rest xs) (+ left (cols piece) gap)
                      (paste out piece top left)))))))
    (define (vstack-center grids gap)
      (let* ((w (apply max (map cols grids)))
             (h (+ (apply + (map rows grids)) (* gap (- (length grids) 1)))))
        (let loop ([xs grids] [top 0] [out (empty-grid h w 0)])
          (if (empty? xs)
              out
              (let* ((piece (first xs))
                     (left (quotient (- w (cols piece)) 2)))
                (loop (rest xs) (+ top (rows piece) gap)
                      (paste out piece top left)))))))
    (define (crop-color grid)
      (apply min (filter (lambda (v) (not (= v 0))) (apply append grid))))
    (let* ((crops (map (lambda (obj) (crop-cells g (obj-cells obj))) (objects g 0)))
           (controller
            (first
             (sort crops
                   (lambda (a b)
                     (list-key< (list (- (rows a)) (- (cols a)) (crop-color a))
                                (list (- (rows b)) (- (cols b)) (crop-color b)))))))
           (control-color (crop-color controller))
           (horizontal? (= (modulo control-color 2) 0))
           (sorted
            (if horizontal?
                (sort crops
                      (lambda (a b)
                        (list-key< (list (cols a) (rows a) (crop-color a))
                                   (list (cols b) (rows b) (crop-color b)))))
                (sort crops
                      (lambda (a b)
                        (list-key< (list (rows a) (cols a) (crop-color a))
                                   (list (rows b) (cols b) (crop-color b))))))))
      (if horizontal?
          (hstack-center sorted 1)
          (vstack-center sorted 1)))))
