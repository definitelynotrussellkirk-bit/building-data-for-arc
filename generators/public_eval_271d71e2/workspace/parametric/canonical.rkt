(rule!
 ;; Slide each black fuel box toward the fixed maroon rail facing its mobile
 ;; maroon rail. Each cell of travel spends one gray cell, turning it orange.
 ;; Stop at the rail or exhausted gray fuel. The leading-edge fill order is
 ;; clockwise-covariant: upward row-major, rightward top-down columns, and
 ;; their half-turn counterparts. Other rails and the magenta field survive.
 ;; Optional longest-move highlighting uses the computed, fuel-capped travel.
 (lambda (g)
  (let ()
   (define output-policy "all_moves")
   (define dirs '((-1 0) (0 1) (1 0) (0 -1)))
   (define frames (filter (lambda (o) (and (= (obj-color o) 0)
                         (>= (obj-h o) 3) (>= (obj-w o) 3))) (objects g 6)))
   (define (rail o dr dc)
    (cond [(= dr -1) (for/list ((c (range (obj-c1 o) (+ 1 (obj-c2 o))))) (list (- (obj-r1 o) 1) c))]
          [(= dr 1) (for/list ((c (range (obj-c1 o) (+ 1 (obj-c2 o))))) (list (+ (obj-r2 o) 1) c))]
          [(= dc -1) (for/list ((r (range (obj-r1 o) (+ 1 (obj-r2 o))))) (list r (- (obj-c1 o) 1)))]
          [else (for/list ((r (range (obj-r1 o) (+ 1 (obj-r2 o))))) (list r (+ (obj-c2 o) 1)))]))
   (define (maroon? ps) (and (not (null? ps)) (for/and ((p ps)) (= (safe-at g (first p) (second p) -1) 9))))
   (define (shift ps dr dc n) (map (lambda (p) (list (+ (first p) (* dr n)) (+ (second p) (* dc n)))) ps))
   ;; frame rows: black object, mobile rail, direction, gap, gray cells, travel.
   (define data
    (for/list ((o frames))
     (let* ((d (or (for/first ((d dirs) #:when (maroon? (rail o (first d) (second d)))) d) '(0 0)))
            (dr (first d)) (dc (second d)) (rr (rail o dr dc))
            (gap (if (equal? d '(0 0)) 0 (or (for/first ((n (range 1 31)) #:when (maroon? (shift rr dr dc n))) n) 0)))
            (gray (filter (lambda (p) (= (at g (first p) (second p)) 5))
                          (positions-in-rect (obj-r1 o) (obj-c1 o) (obj-r2 o) (obj-c2 o)))))
      (list o rr dr dc gap gray (min gap (length gray))))))
   (define (travel f) (list-ref f 6))
   (define (score f)
    (let ((o (first f)) (fuel (length (list-ref f 5))) (dist (travel f)))
     (cond [(equal? output-policy "max_gap") (list-ref f 4)]
           [(equal? output-policy "max_fuel") fuel]
           [(equal? output-policy "min_remaining") (- dist fuel)]
           [(equal? output-policy "max_final_orange") (+ (- (* (- (obj-h o) 2) (- (obj-w o) 2)) fuel) dist)]
           [(equal? output-policy "largest_box") (* (obj-h o) (obj-w o))]
           [(equal? output-policy "shortest_move") (- dist)]
           [else dist])))
   (define winner (if (null? data) #f
     (cond [(equal? output-policy "first") (first data)]
           [(equal? output-policy "last") (last data)]
           [else (pick-max data score)])))
   (define cleared (for/fold ((out g)) ((f data))
     (let ((o (first f))) (recolor-cells out (append (positions-in-rect (obj-r1 o) (obj-c1 o) (obj-r2 o) (obj-c2 o)) (second f)) 6))))
   (for/fold ((out cleared)) ((f data))
    (let* ((o (first f)) (dr (third f)) (dc (fourth f)) (n (travel f))
           (gray (list-ref f 5))
           (key (lambda (p)
              (cond [(= dr -1) (+ (* 31 (first p)) (second p))]
                    [(= dr 1) (- (+ (* 31 (first p)) (second p)))]
                    [(= dc 1) (+ (* -31 (second p)) (first p))]
                    [else (- (* 31 (second p)) (first p))])))
           (spent (take (sort gray < #:key key) n))
           (highlight (and (not (equal? output-policy "all_moves")) (equal? f winner)))
           (painted
            (for/fold ((b out)) ((p (positions-in-rect (obj-r1 o) (obj-c1 o) (obj-r2 o) (obj-c2 o))))
             (let ((v (at g (first p) (second p))))
              (set-cell b (+ (first p) (* dr n)) (+ (second p) (* dc n))
                (cond [(and highlight (= v 0)) 8] [(member p spent) 7] [else v]))))))
     (recolor-cells painted (shift (second f) dr dc n) 9))))))
