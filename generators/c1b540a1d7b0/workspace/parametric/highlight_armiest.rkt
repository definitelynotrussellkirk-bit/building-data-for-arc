(rule! (lambda (g)
  ;; Stage A is the exact canonical arm/room classifier. Stage B counts the
  ;; red arm cells in each completed multicolor component and highlights the
  ;; cyan cells of the unique armiest component in yellow(4).
  (let* ((stage ((lambda (g)
  ;; A gray(5) blob = 2x2 "nodes" joined by 1-wide arms. Recolor node cells cyan(8)
  ;; and arm cells red(2). Each arm is a straight run of exactly 3 cells: seeded at
  ;; a degree-1 tip (extend 3 toward its neighbor) or, for a bridge thin cell (not
  ;; in any 2x2), extend 3 toward a thick neighbor (tie-break up,left,down,right).
  (let* ((h (rows g)) (w (cols g))
         (dirs (list (cons -1 0) (cons 0 -1) (cons 1 0) (cons 0 1))))
    (define (sh? a b) (and (>= a 0) (< a h) (>= b 0) (< b w) (= (cell-at g a b) 5)))
    (define (in2x2? a b)
      (for*/or ((da (list -1 0)) (db (list -1 0)))
        (and (sh? (+ a da 0) (+ b db 0)) (sh? (+ a da 0) (+ b db 1))
             (sh? (+ a da 1) (+ b db 0)) (sh? (+ a da 1) (+ b db 1)))))
    (define red (make-hash))
    (define (add-arm a b da db)
      (for ((k (list 0 1 2)))
        (let ((x (+ a (* da k))) (y (+ b (* db k))))
          (when (sh? x y) (hash-set! red (cons x y) #t)))))
    ;; tip arms
    (for* ((a (range h)) (b (range w)))
      (when (sh? a b)
        (let ((nb (filter (lambda (d) (sh? (+ a (car d)) (+ b (cdr d)))) dirs)))
          (when (= (length nb) 1)
            (add-arm a b (car (first nb)) (cdr (first nb)))))))
    ;; bridge arms: thin cells not yet covered
    (for* ((a (range h)) (b (range w)))
      (when (and (sh? a b) (not (in2x2? a b)) (not (hash-has-key? red (cons a b))))
        (let ((chosen (findf (lambda (d)
                               (and (sh? (+ a (car d)) (+ b (cdr d)))
                                    (in2x2? (+ a (car d)) (+ b (cdr d)))))
                             dirs)))
          (when chosen (add-arm a b (car chosen) (cdr chosen))))))
    (grid-from-fn h w
      (lambda (r c)
        (if (sh? r c) (if (hash-has-key? red (cons r c)) 2 8) (cell-at g r c)))))) g))
         (objs (objects-multicolor stage 0)))
    (if (empty? objs)
        stage
        (let* ((red-count
                (lambda (o)
                  (count-where
                   (lambda (p)
                     (= (cell-at stage (first p) (second p)) 2))
                   (obj-cells o))))
               (winner (pick-max objs red-count))
               (cyan-cells
                (filter
                 (lambda (p)
                   (= (cell-at stage (first p) (second p)) 8))
                 (obj-cells winner))))
          (recolor-cells stage cyan-cells 4))))))
