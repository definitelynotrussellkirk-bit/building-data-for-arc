(rule!
 ;; Recover noisy, occluding rectangular layers from long straight runs.
 ;; Remove color specks and restore nonzero corruptions. Original zero cells
 ;; inside the reconstructed layers are holes. Surround chosen holes with
 ;; the other rectangle color, including outside edges, then mark centers 8.
 ;; The alternative keeps every largest four-connected hole cluster.
 (lambda (g)
  (let ()
   (define scope 'all)
   (define colors (filter (lambda (k) (not (= k 0))) (grid-colors g)))
   (define candidates (filter (lambda (o) (>= (obj-size o) 9)) (objects g 0)))
   (define (row-run? o r)
    (for/or ([c (range (obj-c1 o) (- (obj-c2 o) 1))])
     (and (member (list r c) (obj-cells o))
          (member (list r (+ c 1)) (obj-cells o))
          (member (list r (+ c 2)) (obj-cells o)))))
   (define (col-run? o c)
    (for/or ([r (range (obj-r1 o) (- (obj-r2 o) 1))])
     (and (member (list r c) (obj-cells o))
          (member (list (+ r 1) c) (obj-cells o))
          (member (list (+ r 2) c) (obj-cells o)))))
   (define rects
    (filter (lambda (v) v)
     (for/list ([o candidates])
      (let ([rs (filter (lambda (r) (row-run? o r)) (range (obj-r1 o) (+ (obj-r2 o) 1)))]
            [cs (filter (lambda (c) (col-run? o c)) (range (obj-c1 o) (+ (obj-c2 o) 1)))])
       (if (or (null? rs) (null? cs)) #f
        (list (obj-color o) (apply min rs) (apply min cs) (apply max rs) (apply max cs)))))))
   (define (overlap-votes a b color)
    (for*/sum ([r (range (max (second a) (second b)) (+ (min (fourth a) (fourth b)) 1))]
               [c (range (max (third a) (third b)) (+ (min (fifth a) (fifth b)) 1))])
     (if (= (at g r c) color) 1 0)))
   (define edges
    (filter (lambda (v) v)
     (for*/list ([i (range (length rects))] [j (range (+ i 1) (length rects))])
      (let* ([a (list-ref rects i)] [b (list-ref rects j)]
             [na (overlap-votes a b (first a))] [nb (overlap-votes a b (first b))])
       (cond [(or (= (first a) (first b)) (= na nb)) #f]
             [(< na nb) (list i j)] [else (list j i)])))))
   (define ordered
    (let loop ([done '()])
     (if (= (length done) (length rects)) done
      (let ([ready (find-first
                    (lambda (i) (and (not (member i done))
                     (for/and ([e edges]) (or (not (= (second e) i)) (member (first e) done)))))
                    (range (length rects)))])
       (if ready (loop (append done (list ready))) done)))))
   (define restored
    (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([i ordered])
     (let ([a (list-ref rects i)])
      (for*/fold ([acc out]) ([r (range (second a) (+ (fourth a) 1))]
                              [c (range (third a) (+ (fifth a) 1))])
       (set-cell acc r c (first a))))))
   (define holes
    (for*/list ([r (range (rows g))] [c (range (cols g))]
                #:when (and (= (at g r c) 0) (not (= (at restored r c) 0))))
     (list r c (at restored r c))))
   (define hole-mask
    (grid-from-fn (rows g) (cols g)
     (lambda (r c) (if (and (= (at g r c) 0) (not (= (at restored r c) 0))) 1 0))))
   (define clusters (objects hole-mask 0))
   (define largest (if (null? clusters) 0 (apply max (map obj-size clusters))))
   (define selected-cells
    (apply append (map obj-cells (filter (lambda (o) (= (obj-size o) largest)) clusters))))
   (define selected
    (if (eq? scope 'all) holes
     (filter (lambda (p) (member (list (first p) (second p)) selected-cells)) holes)))
   (define painted
    (for/fold ([out restored]) ([p selected])
     (let ([other (first (filter (lambda (k) (not (= k (third p)))) colors))])
      (for*/fold ([acc out]) ([dr '(-1 0 1)] [dc '(-1 0 1)])
       (let ([r (+ (first p) dr)] [c (+ (second p) dc)])
        (if (and (<= 0 r) (< r (rows g)) (<= 0 c) (< c (cols g)))
         (set-cell acc r c other) acc))))))
   (for/fold ([out painted]) ([p selected]) (set-cell out (first p) (second p) 8)))))
