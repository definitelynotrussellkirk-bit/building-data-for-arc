(rule!
 ;; Complete the four equal color-8 arms as four interlocking square spirals.
 ;; The construction is infinite in principle; draw enough turns to cover every
 ;; ARC canvas and crop naturally through the final grid lookup.
 (lambda (g)
  (let ()
   (define H (rows g))
   (define W (cols g))
   (define directions '((-1 0) (0 1) (1 0) (0 -1)))
   (define candidates
    (for*/list ([r (range 1 (- H 1))] [c (range 1 (- W 1))]
                #:when (and (= (at g r c) 0)
                            (andmap (lambda (d)
                                     (= (safe-at g (+ r (first d)) (+ c (second d)) -1) 8))
                                   directions)))
     (list r c)))
   (define center (first candidates))
   (define cr (first center))
   (define cc (second center))
   (define arm-length
    (let loop ([n 0])
     (if (= (safe-at g (- cr (+ n 1)) cc -1) 8)
         (loop (+ n 1)) n)))
   (define m (max 2 arm-length))
   (define (walk state direction steps)
    (for/fold ([st state]) ([i (range steps)])
     (define p (first st))
     (define d (list-ref directions direction))
     (define q (list (+ (first p) (first d)) (+ (second p) (second d))))
     (list q (cons q (second st)))))
   (define initial-cells
    (for/list ([i (range 1 (+ m 1))]) (list (- i) 0)))
   (define state0 (list (list (- m) 0) initial-cells))
   (define state1 (walk state0 1 2))
   (define final-state
    (for/fold ([st state1]) ([k (range 10)])
     (define q (modulo (+ 2 k) 4))
     (define a (walk st q (- m 2)))
     (define b (walk a (modulo (- q 1) 4) m))
     (walk b q (+ 6 (* 4 k)))))
   (define north (remove-duplicates (second final-state)))
   (define (rotate p turns)
    (if (= turns 0) p
        (rotate (list (second p) (- (first p))) (- turns 1))))
   ;; A: build all four complete branches before cropping them to the canvas.
   (define branches
    (for/list ([k (range 4)])
     (for/list ([p north])
      (define q (rotate p k))
      (list (+ cr (first q)) (+ cc (second q))))))
   (define all-cells (apply append branches))
   (define occupied
    (for/fold ([acc (hash)]) ([p all-cells]) (hash-set acc p #t)))
   ;; B: render the cropped union of the four A-derived branches.
   (grid-from-fn H W
    (lambda (r c) (if (hash-has-key? occupied (list r c)) 8 0))))))
