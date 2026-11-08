(rule!
 ;; A long nonzero vertical separator divides run codes from an empty field.
 ;; Each contiguous nonzero run supplies a color and a period equal to its length.
 ;; Starting adjacent to the separator, emit one pulse per period. Runs closer
 ;; to the separator paint last and win collisions. Zero gaps have no period.
 ;; Source rows may lie on either side; the direction always points away from
 ;; the code. Preserve the code, separator, and every unaffected input cell.
 (lambda (g)
  (let ()
   (define pulse-phase 'leading)
   (define (column-score c)
    (let loop ([r 0] [previous -1] [run 0] [best 0])
     (if (= r (rows g)) best
      (let* ([v (at g r c)] [n (if (= v 0) 0 (if (= v previous) (+ run 1) 1))])
       (loop (+ r 1) v n (max best n))))))
   (define separator (pick-max (range (cols g)) column-score))
   (define (run-records xs)
    (if (null? xs) '()
     (let* ([color (first xs)]
            [length (let count ([ys xs] [n 0])
                      (if (or (null? ys) (not (= (first ys) color))) n
                          (count (rest ys) (+ n 1))))]
            [tail (run-records (drop xs length))])
      (if (= color 0) tail (cons (list color length) tail)))))
   (for/fold ([out g]) ([r (range (rows g))])
    (define left (take (row g r) separator))
    (define right (drop (row g r) (+ separator 1)))
    (define facing-right (ormap (lambda (v) (not (= v 0))) left))
    (define source (if facing-right left (reverse right)))
    (define target-length (if facing-right (- (cols g) separator 1) separator))
    ;; A produces color/period records; B cannot construct pulse masks without them.
    (define records (run-records source))
    (for/fold ([painted out]) ([record records])
     (define period (second record))
     (define phase (if (equal? pulse-phase 'leading) 0 (- period 1)))
     (for/fold ([canvas painted]) ([k (range target-length)]
                                 #:when (= (modulo k period) phase))
      (set-cell canvas r (+ separator (* (if facing-right 1 -1) (+ k 1))) (first record))))))))
