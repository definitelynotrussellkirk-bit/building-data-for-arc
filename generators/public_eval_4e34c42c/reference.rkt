(rule!
 ;; Assemble disconnected fragments by translating shared colored patterns.
 ;; Background cells inside an observed fragment are constraints, not wildcards;
 ;; regions outside its rectangle are unknown. A join must completely match at
 ;; least one monochrome component from either fragment. Prefer maximum colored
 ;; overlap, then minimum area, minimum displacement, and row/column order.
 ;; Repeat using the merged drawing as the next alignment intermediate, crop,
 ;; and retain the original background. No rotations or palette ordering.
 (lambda (g)
  (let ()
    (define bridge-after-assembly #f)
    (define bg (mode g -1))
    (define (known-at x rr cc)
      (if (and (<= 0 rr) (< rr (rows x)) (<= 0 cc) (< cc (cols x))) (at x rr cc) -1))
    (define (foreground x)
      (for*/list ([rr (in-range (rows x))] [cc (in-range (cols x))]
                  #:when (and (not (= (at x rr cc) bg)) (not (= (at x rr cc) -1))))
        (list rr cc (at x rr cc))))
    (define (mono x)
      (objects (grid-from-fn (rows x) (cols x)
                 (lambda (rr cc) (if (= (at x rr cc) -1) bg (at x rr cc)))) bg))
    (define (rank-better? a b)
      (cond [(null? a) #f] [(null? b) #t]
            [(> (first a) (first b)) #t]
            [(< (first a) (first b)) #f]
            [else (rank-better? (rest a) (rest b))]))
    (define (merge-at a b dr dc)
      (define r0 (min 0 dr)) (define c0 (min 0 dc))
      (define nr (- (max (rows a) (+ dr (rows b))) r0))
      (define nc (- (max (cols a) (+ dc (cols b))) c0))
      (grid-from-fn nr nc
        (lambda (rr cc)
          (let ([v (known-at a (+ rr r0) (+ cc c0))])
            (if (= v -1) (known-at b (- (+ rr r0) dr) (- (+ cc c0) dc)) v)))))
    (define (alignment a b)
      (define af (foreground a)) (define bf (foreground b))
      (define ac (mono a)) (define bc (mono b))
      (define offsets
        (remove-duplicates
          (for*/list ([p af] [q bf] #:when (= (third p) (third q)))
            (list (- (first p) (first q)) (- (second p) (second q))))))
      (for/fold ([best #f]) ([delta offsets])
        (define dr (first delta)) (define dc (second delta))
        (define score
          (for/sum ([q bf])
            (if (= (known-at a (+ dr (first q)) (+ dc (second q))) (third q)) 1 0)))
        (define consistent
          (for*/and ([rr (in-range (rows b))] [cc (in-range (cols b))])
            (let ([av (known-at a (+ rr dr) (+ cc dc))] [bv (at b rr cc)])
              (or (= av -1) (= bv -1) (= av bv)))))
        (define anchor
          (and consistent
            (or
              (for/or ([o ac])
                (for/and ([p (obj-cells o)])
                  (= (known-at b (- (first p) dr) (- (second p) dc)) (obj-color o))))
              (for/or ([o bc])
                (for/and ([p (obj-cells o)])
                  (= (known-at a (+ (first p) dr) (+ (second p) dc)) (obj-color o)))))))
        (if (and (> score 0) anchor)
            (let* ([nr (- (max (rows a) (+ dr (rows b))) (min 0 dr))]
                   [nc (- (max (cols a) (+ dc (cols b))) (min 0 dc))]
                   [rank (list score (- (* nr nc)) (- (+ (abs dr) (abs dc))) (- dr) (- dc))])
              (if (or (not best) (rank-better? rank (first best)))
                  (list rank (merge-at a b dr dc)) best))
            best)))
    (define pieces
      (for/list ([o (objects (grid-from-fn (rows g) (cols g)
                              (lambda (rr cc) (if (= (at g rr cc) bg) 0 1))) 0)])
        (define box (obj-bbox o))
        (grid-from-fn (+ 1 (- (third box) (first box))) (+ 1 (- (fourth box) (second box)))
          (lambda (rr cc)
            (let ([r (+ rr (first box))] [c (+ cc (second box))])
              (if (member (list r c) (obj-cells o)) (at g r c) bg))))))
    (define joined
      (let loop ([ps pieces])
        (cond [(null? ps) g] [(null? (rest ps)) (first ps)]
              [else
               (define best
                 (for*/fold ([best #f]) ([i (in-range (length ps))] [j (in-range (+ i 1) (length ps))])
                   (define proposal (alignment (list-ref ps i) (list-ref ps j)))
                   (if (and proposal (or (not best) (rank-better? (first proposal) (first best))))
                       (list (first proposal) i j (second proposal)) best)))
               (if (not best) (error "no consistent jigsaw alignment")
                   (loop (append (for/list ([p ps] [k (in-naturals)]
                                             #:unless (or (= k (second best)) (= k (third best)))) p)
                                 (list (fourth best)))))])))
    (define assembled
      (grid-from-fn (rows joined) (cols joined)
        (lambda (rr cc) (if (= (at joined rr cc) -1) bg (at joined rr cc)))))
    (if (not bridge-after-assembly) assembled
      (for/fold ([out assembled]) ([color (grid-colors assembled)] #:unless (= color bg))
        (define points (find-color assembled color))
        (if (not (= (length points) 2)) out
          (let* ([p (first points)] [q (second points)]
                 [same-r (= (first p) (first q))] [same-c (= (second p) (second q))]
                 [span (cond [same-r (for/list ([cc (in-range (min (second p) (second q)) (+ 1 (max (second p) (second q))))]) (list (first p) cc))]
                             [same-c (for/list ([rr (in-range (min (first p) (first q)) (+ 1 (max (first p) (first q))))]) (list rr (second p)))]
                             [else '()])])
            (if (and (not (null? span))
                     (for/and ([s span]) (or (= (at assembled (first s) (second s)) bg)
                                             (= (at assembled (first s) (second s)) color))))
                (for/fold ([acc out]) ([s span]) (set-cell acc (first s) (second s) color)) out))))))))
