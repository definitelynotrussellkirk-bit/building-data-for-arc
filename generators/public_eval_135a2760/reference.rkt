(rule!
 (let ()
   ;; A: split uniform frame lines, then infer each long-axis periodic motif.
   (define mark-errors #f)
   (define frame (at g 0 0))
   (define rs (filter (lambda (r) (and (row-uniform? g r) (= (at g r 0) frame))) (range h)))
   (define cs (filter (lambda (c) (and (col-uniform? g c) (= (at g 0 c) frame))) (range w)))
   (define boxes
     (for*/list ([ri (range (- (length rs) 1))] [ci (range (- (length cs) 1))]
                 #:when (and (>= (- (list-ref rs (+ ri 1)) (list-ref rs ri)) 4)
                             (>= (- (list-ref cs (+ ci 1)) (list-ref cs ci)) 4)))
       (list (+ (list-ref rs ri) 2) (+ (list-ref cs ci) 2)
             (- (list-ref rs (+ ri 1)) 2) (- (list-ref cs (+ ci 1)) 2))))
   (define (majority xs)
     (pick-max (sort (remove-duplicates xs) <)
               (lambda (v) (count-if (lambda (x) (= x v)) xs))))
   (for/fold ([out g]) ([box boxes])
     (let* ([r0 (first box)] [c0 (second box)] [r1 (third box)] [c1 (fourth box)]
            [horizontal (>= (- c1 c0) (- r1 r0))]
            [n (+ 1 (if horizontal (- c1 c0) (- r1 r0)))]
            [t (+ 1 (if horizontal (- r1 r0) (- c1 c0)))]
            [ring (at g (- r0 1) (- c0 1))])
       (define (cell i j) (if horizontal (at g (+ r0 j) (+ c0 i)) (at g (+ r0 i) (+ c0 j))))
       (define candidates
         (for/list ([p (range 1 (+ 1 (quotient n 2)))])
           (define motif
             (for/list ([phase (range p)])
               (for/list ([j (range t)])
                 (majority (for/list ([i (range phase n p)]) (cell i j))))))
           (define errors
             (for*/sum ([i (range n)] [j (range t)])
               (if (= (cell i j) (list-ref (list-ref motif (modulo i p)) j)) 0 1)))
           (list p errors motif)))
       ;; Earliest minimum = shortest period on a Hamming-error tie.
       (define recovered (pick-min candidates second))
       (define period (first recovered))
       (define motif (third recovered))
       ;; B consumes the recovered period and phase-specific motif.
       (for*/fold ([result out]) ([i (range n)] [j (range t)])
         (define expected (list-ref (list-ref motif (modulo i period)) j))
         (define rr (if horizontal (+ r0 j) (+ r0 i)))
         (define cc (if horizontal (+ c0 i) (+ c0 j)))
         (set-cell result rr cc
                   (if (and mark-errors (not (= (cell i j) expected))) ring expected)))))))
