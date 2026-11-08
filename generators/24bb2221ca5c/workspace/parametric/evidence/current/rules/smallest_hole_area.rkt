(rule! (let ((dummy 0)) (define dirs4 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1))) (define (component-grid obj) (let* ((bb (obj-bbox obj)) (h (+ 1 (- (third bb) (first bb)))) (w (+ 1 (- (fourth bb) (second bb))))) (for/fold ((out (empty-grid h w 0))) ((p (in-list (obj-cells obj)))) (set-cell out (- (first p) (first bb)) (- (second p) (second bb)) (obj-color obj))))) (define (binary-grid grid) (grid-from-fn (rows grid) (cols grid) (lambda (r c) (if (= (at grid r c) 0) 0 1)))) (define (holes-in-binary grid) (let loop-pos ((positions (grid-positions grid)) (seen (list)) (acc (list))) (cond ((empty? positions) acc) ((or (member? (first positions) seen) (not (= (at grid (first (first positions)) (second (first positions))) 0))) (loop-pos (rest positions) seen acc)) (else (let bfs ((queue (list (first positions))) (seen2 (cons (first positions) seen)) (cells (list)) (touches #f)) (if (empty? queue) (loop-pos (rest positions) seen2 (if touches acc (append cells acc))) (let* ((cur (first queue)) (r (first cur)) (c (second cur)) (border (or (= r 0) (= c 0) (= r (- (rows grid) 1)) (= c (- (cols grid) 1)))) (nbrs (filter (lambda (p) (and (in-bounds? (first p) (second p) (rows grid) (cols grid)) (not (member? p seen2)) (= (at grid (first p) (second p)) 0))) (map (lambda (d) (list (+ r (first d)) (+ c (second d)))) dirs4)))) (bfs (append (rest queue) nbrs) (append seen2 nbrs) (cons cur cells) (or touches border)))))))))     (define (hole-regions-in-binary grid)
      (let loop-pos ([positions (grid-positions grid)] [seen (list)] [acc (list)])
        (cond [(empty? positions) (reverse acc)]
              [(or (member? (first positions) seen)
                   (not (= (at grid (first (first positions)) (second (first positions))) 0)))
               (loop-pos (rest positions) seen acc)]
              [else
               (let bfs ([queue (list (first positions))]
                         [seen2 (cons (first positions) seen)]
                         [cells (list)]
                         [touches #f])
                 (if (empty? queue)
                     (loop-pos (rest positions) seen2
                               (if touches acc (cons (reverse cells) acc)))
                     (let* ((cur (first queue))
                            (r (first cur))
                            (c (second cur))
                            (border (or (= r 0) (= c 0)
                                        (= r (- (rows grid) 1))
                                        (= c (- (cols grid) 1))))
                            (nbrs
                             (filter
                              (lambda (p)
                                (and (in-bounds? (first p) (second p) (rows grid) (cols grid))
                                     (not (member? p seen2))
                                     (= (at grid (first p) (second p)) 0)))
                              (map (lambda (d) (list (+ r (first d)) (+ c (second d)))) dirs4))))
                       (bfs (append (rest queue) nbrs)
                            (append seen2 nbrs)
                            (cons cur cells)
                            (or touches border)))))])))
    (define candidates
      (filter
       (lambda (record) (not (empty? (second record))))
       (map
        (lambda (obj)
          (let* ((cg (component-grid obj))
                 (regions (hole-regions-in-binary (binary-grid cg)))
                 (holes (if (empty? regions) (list) (apply append regions))))
            (list obj holes regions)))
        (objects g 0))))
    (define (score record) (- 0 (length (second record))))
    (define chosen
      (if (empty? candidates)
          #f
          (for/fold ([best (first candidates)]) ([record (in-list (rest candidates))])
            (if (> (score record) (score best)) record best))))
    (if (equal? chosen #f)
        g
        (let* ((obj (first chosen))
               (holes (second chosen))
               (bb (obj-bbox obj)))
          (for/fold ([out g]) ([p (in-list holes)])
            (set-cell out (+ (first bb) (first p)) (+ (second bb) (second p)) (obj-color obj)))))
  ))