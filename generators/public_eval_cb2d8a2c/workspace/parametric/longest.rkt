(rule!
 ;; A green boundary source travels inward past edge-attached red barriers.
 ;; Each barrier's blue markers encode clearance equal to their count plus one.
 ;; Turn that far BEFORE its row, then pass that far beyond its free tip.
 ;; Continue in original travel order; all blue markers become red.
 ;; The alternate scope retains the longest lateral segment of the complete
 ;; inferred route, with the earliest-in-travel-order tie break.
 (lambda (g)
  (let ()
   (define scope 'longest)
   (define selector 'length)
   (define fixed-clearance -1)
   (define margin 1)
   (define starts (find-color g 3))
   (define (turn x n) (if (= n 0) x (turn (rotate-cw x) (- n 1))))
   (if (not (= (length starts) 1)) g
    (let* ((source (first starts)) (rr (first source)) (cc (second source))
           (k (cond ((= rr 0) 0) ((= cc 0) 1)
                    ((= rr (- (rows g) 1)) 2) (else 3)))
           (t (turn g k)) (H (rows t)) (W (cols t))
           (start (first (find-color t 3)))
           (sr (first start)) (sc (second start)))
     (define walls
      (for/list ((r (range H))
        #:when (for/or ((c (range W))) (member (at t r c) '(1 2))))
       (define cs (filter (lambda (c) (member (at t r c) '(1 2))) (range W)))
       (list r (apply min cs) (apply max cs)
             (count (lambda (c) (= (at t r c) 1)) cs) (length cs))))
     (define (make-legs ws from)
      (if (null? ws) '()
       (let* ((wall (first ws)) (n (list-ref wall 3))
              (d (if (> fixed-clearance 0) fixed-clearance (+ n margin)))
              (to (if (= (second wall) 0) (+ (third wall) d) (- (second wall) d))))
        (cons (list (- (first wall) d) from to n (list-ref wall 4))
              (make-legs (rest ws) to)))))
     (define legs (make-legs walls sc))
     (define (cross leg)
      (for/list ((c (range (min (second leg) (third leg))
                           (+ 1 (max (second leg) (third leg))))))
       (list (first leg) c)))
     (define clean (recolor t 1 2))
     (define drawn
      (if (eq? scope 'full)
       (let ((state
        (for/fold ((st (list clean sr sc))) ((leg legs))
         (define near
          (paint-cells (first st)
           (for/list ((r (range (min (second st) (first leg))
                                (+ 1 (max (second st) (first leg))))))
            (list r (third st))) 3))
         (list (paint-cells near (cross leg) 3) (first leg) (third leg)))))
        (paint-cells (first state)
         (for/list ((r (range (second state) H))) (list r (third state))) 3))
       (if (null? legs) clean
        (let ((winner
          (cond ((eq? selector 'first) (first legs))
                ((eq? selector 'last) (last legs))
                ((eq? selector 'markers) (pick-max legs (lambda (x) (list-ref x 3))))
                ((eq? selector 'width) (pick-max legs (lambda (x) (list-ref x 4))))
                ((eq? selector 'initial-span) (pick-max legs (lambda (x) (abs (- (third x) sc)))))
                (else (pick-max legs (lambda (x) (abs (- (third x) (second x)))))))))
         (paint-cells clean (cross winner) 3)))))
     (turn drawn (modulo (- 4 k) 4)))))))
