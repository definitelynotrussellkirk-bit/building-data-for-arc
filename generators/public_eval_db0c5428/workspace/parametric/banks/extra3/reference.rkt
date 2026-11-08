(rule!
 ;; Eight filled 3x3 tiles surround a cyan 3x3 hole. Reconstruct its directional
 ;; key from each inward-facing sample; the middle keeps the modal tile base.
 ;; Reflect each original tile outward across the axes on which it lies, and
 ;; place it one tile farther out. Clip copies at the canvas; preserve input.
 ;; An optional policy uses the largest connected nonbase run of the recovered
 ;; key to select which addressed tiles reflect. Independent rings act separately.
 (lambda (g)
  (let ()
   (define output-policy "all_tiles")
   (define (signum n) (cond [(< n 0) -1] [(> n 0) 1] [else 0]))
   (define rings (filter (lambda (o) (and (= (obj-h o) 9) (= (obj-w o) 9))) (objects-multicolor g 8)))
   (define ports '((0 0) (0 1) (0 2) (1 2) (2 2) (2 1) (2 0) (1 0)))
   (for/fold ((out g)) ((o rings))
    (let* ((r0 (obj-r1 o)) (c0 (obj-c1 o)) (base (mode-in (obj-cells o) g 8))
           (keygrid (build-grid 3 3 (r c)
            (let ((dr (signum (- r 1))) (dc (signum (- c 1))))
             (if (and (= dr 0) (= dc 0)) base
              (at g (+ r0 (* 3 (+ dr 1)) (if (= dr 0) r (- 2 r)))
                    (+ c0 (* 3 (+ dc 1)) (if (= dc 0) c (- 2 c))))))))
           (runs (objects keygrid base))
           (best (if (null? runs) #f (pick-max runs obj-size)))
           (chosen
            (cond
             [(equal? output-policy "all_tiles") ports]
             [(equal? output-policy "corners") (filter (lambda (p) (and (not (= (first p) 1)) (not (= (second p) 1)))) ports)]
             [(equal? output-policy "edges") (filter (lambda (p) (or (= (first p) 1) (= (second p) 1))) ports)]
             [(equal? output-policy "second_color")
              (let* ((colors (grid-colors keygrid base))
                     (ranked (sort colors > #:key (lambda (x) (count-color keygrid x))))
                     (color (cond [(null? ranked) base] [(null? (rest ranked)) (first ranked)] [else (second ranked)])))
               (filter (lambda (p) (= (at keygrid (first p) (second p)) color)) ports))]
             [(equal? output-policy "largest_color")
              (let ((color (mode keygrid base))) (filter (lambda (p) (= (at keygrid (first p) (second p)) color)) ports))]
             [(equal? output-policy "largest_input_color")
              (let* ((marks (filter (lambda (p) (not (= (at g (first p) (second p)) base))) (obj-cells o)))
                     (color (if (null? marks) base (mode-in marks g 8))))
               (filter (lambda (p) (= (at keygrid (first p) (second p)) color)) ports))]
             [(equal? output-policy "eight_connected")
              (let ((rr (objects-8 keygrid base))) (if (null? rr) '() (obj-cells (pick-max rr obj-size))))]
             [(not best) '()]
             [(equal? output-policy "first_run") (obj-cells (first runs))]
             [(equal? output-policy "smallest_run") (obj-cells (pick-min runs obj-size))]
             [(equal? output-policy "opposite_run") (map (lambda (p) (list (- 2 (first p)) (- 2 (second p)))) (obj-cells best))]
             [(equal? output-policy "fixed_three") (if (= (obj-size best) 3) (obj-cells best) '())]
             [else (obj-cells best)]))
           (centered (for*/fold ((b out)) ((r (range 3)) (c (range 3)))
                       (set-cell b (+ r0 3 r) (+ c0 3 c) (at keygrid r c)))))
     (for/fold ((b centered)) ((p chosen))
      (let* ((dr (- (first p) 1)) (dc (- (second p) 1))
             (sr (+ r0 (* 3 (+ dr 1)))) (sc (+ c0 (* 3 (+ dc 1))))
             (tr (+ r0 3 (* 6 dr))) (tc (+ c0 3 (* 6 dc))))
       (paint-cells b
        (for*/list ((r (range 3)) (c (range 3)))
         (list (+ tr r) (+ tc c)
          (at g (+ sr (if (or (= dr 0) (equal? output-policy "unreflected")) r (- 2 r)))
                (+ sc (if (or (= dc 0) (equal? output-policy "unreflected")) c (- 2 c))))))))))))))
