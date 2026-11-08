(rule!
 ;; Black-framed grey/orange boxes sit beside two parallel maroon rails.
 ;; Move each box toward the farther rail by min(rail gap, remaining grey),
 ;; converting one interior cell to orange per step in the directional sweep.
 (lambda (g)
  (let ()
   (define h (rows g))
   (define w (cols g))
   (define (eligible? r c v) (or (= v 0) (= v 5) (= v 7)))
   (define (components)
    (let loop ([remaining (filter-cells g eligible?)] [acc '()])
     (if (empty? remaining)
         (reverse acc)
         (let* ([start (first remaining)]
                [region (connected-region g (first start) (second start) eligible? 4)])
          (loop (filter (lambda (p) (not (member p region))) remaining)
                (cons region acc))))))
   (define (full-row? rr c1 c2)
    (and (<= 0 rr) (< rr h)
         (for/and ([c (in-range c1 (+ c2 1))]) (= (at g rr c) 9))))
   (define (full-col? cc r1 r2)
    (and (<= 0 cc) (< cc w)
         (for/and ([r (in-range r1 (+ r2 1))]) (= (at g r cc) 9))))
   (define (frame-record cells)
    (let* ([bb (bbox-of-cells cells)]
           [r1 (first bb)] [c1 (second bb)] [r2 (third bb)] [c2 (fourth bb)]
           [ih (- r2 r1 1)] [iw (- c2 c1 1)]
           [border (filter (lambda (p)
                             (or (= (first p) r1) (= (first p) r2)
                                 (= (second p) c1) (= (second p) c2)))
                           (positions-in-rect r1 c1 r2 c2))]
           [inside (positions-in-rect (+ r1 1) (+ c1 1) (- r2 1) (- c2 1))])
     (if (and (>= ih 1) (>= iw 1)
              (for/and ([p border]) (= (at g (first p) (second p)) 0))
              (for/and ([p inside]) (member (at g (first p) (second p)) '(5 7))))
         (let* ([n-orange (count (lambda (p) (= (at g (first p) (second p)) 7)) inside)]
                [n-grey (- (* ih iw) n-orange)]
                [side-near-far
                 (cond
                  [(full-row? (- r1 1) c1 c2)
                   (let* ([near (- r1 1)]
                          [far (for/fold ([ans near]) ([rr (in-range (- near 1) -1 -1)]
                                 #:when (full-row? rr c1 c2)) rr)])
                    (list 'UP near far (- near far)))]
                  [(full-row? (+ r2 1) c1 c2)
                   (let* ([near (+ r2 1)]
                          [far (for/fold ([ans near]) ([rr (in-range (+ near 1) h)]
                                 #:when (full-row? rr c1 c2)) rr)])
                    (list 'DOWN near far (- far near)))]
                  [(full-col? (- c1 1) r1 r2)
                   (let* ([near (- c1 1)]
                          [far (for/fold ([ans near]) ([cc (in-range (- near 1) -1 -1)]
                                 #:when (full-col? cc r1 r2)) cc)])
                    (list 'LEFT near far (- near far)))]
                  [(full-col? (+ c2 1) r1 r2)
                   (let* ([near (+ c2 1)]
                          [far (for/fold ([ans near]) ([cc (in-range (+ near 1) w)]
                                 #:when (full-col? cc r1 r2)) cc)])
                    (list 'RIGHT near far (- far near)))]
                  [else (list #f 0 0 0)])]
                [side (first side-near-far)]
                [near (second side-near-far)]
                [far (third side-near-far)]
                [distance (fourth side-near-far)]
                [movement (if side (min distance n-grey) 0)]
                [dr (cond [(eq? side 'UP) (- movement)] [(eq? side 'DOWN) movement] [else 0])]
                [dc (cond [(eq? side 'LEFT) (- movement)] [(eq? side 'RIGHT) movement] [else 0])])
          (hash 'r1 r1 'c1 c1 'r2 r2 'c2 c2 'ih ih 'iw iw
                'n-orange n-orange 'n-grey n-grey 'side side 'near near 'far far
                'distance distance 'movement movement
                'nr1 (+ r1 dr) 'nc1 (+ c1 dc) 'nr2 (+ r2 dr) 'nc2 (+ c2 dc)
                'post-orange (min (* ih iw) (+ n-orange movement))))
         #f)))
   (define records
    (sort (filter (lambda (x) x) (map frame-record (components)))
          (lambda (a b)
           (let ([ar (hash-ref a 'r1)] [br (hash-ref b 'r1)]
                 [ac (hash-ref a 'c1)] [bc (hash-ref b 'c1)])
            (or (< ar br) (and (= ar br) (< ac bc)))))))
   (define (rank rec lr lc)
    (let ([ih (hash-ref rec 'ih)] [iw (hash-ref rec 'iw)] [side (hash-ref rec 'side)])
     (cond [(eq? side 'UP) (+ (* lr iw) lc)]
           [(eq? side 'DOWN) (+ (* (- ih 1 lr) iw) (- iw 1 lc))]
           [(eq? side 'LEFT) (+ (* lc ih) (- ih 1 lr))]
           [(eq? side 'RIGHT) (+ (* (- iw 1 lc) ih) lr)]
           [else (+ (* lr iw) lc)])))
   (define (render-one out rec)
    (let* ([r1 (hash-ref rec 'r1)] [c1 (hash-ref rec 'c1)]
           [r2 (hash-ref rec 'r2)] [c2 (hash-ref rec 'c2)]
           [nr1 (hash-ref rec 'nr1)] [nc1 (hash-ref rec 'nc1)]
           [nr2 (hash-ref rec 'nr2)] [nc2 (hash-ref rec 'nc2)]
           [ih (hash-ref rec 'ih)] [iw (hash-ref rec 'iw)]
           [side (hash-ref rec 'side)] [near (hash-ref rec 'near)]
           [far (hash-ref rec 'far)] [distance (hash-ref rec 'distance)]
           [movement (hash-ref rec 'movement)] [total (hash-ref rec 'post-orange)]
           [dr (cond [(eq? side 'UP) (- movement)] [(eq? side 'DOWN) movement] [else 0])]
           [dc (cond [(eq? side 'LEFT) (- movement)] [(eq? side 'RIGHT) movement] [else 0])]
           [with-border
            (for*/fold ([acc out]) ([r (in-range nr1 (+ nr2 1))]
                                    [c (in-range nc1 (+ nc2 1))]
                                    #:when (or (= r nr1) (= r nr2) (= c nc1) (= c nc2)))
             (set-cell acc r c 0))]
           [with-inside
            (for*/fold ([acc with-border]) ([lr (in-range ih)] [lc (in-range iw)])
             (set-cell acc (+ nr1 1 lr) (+ nc1 1 lc)
                       (if (< (rank rec lr lc) total) 7 5)))])
     (cond
      [(and side (> movement 0) (or (eq? side 'UP) (eq? side 'DOWN)))
       (let* ([a (for/fold ([acc with-inside]) ([c (in-range nc1 (+ nc2 1))])
                   (set-cell acc far c 9))]
              [b (if (< movement distance)
                     (for/fold ([acc a]) ([c (in-range nc1 (+ nc2 1))])
                      (set-cell acc (+ near dr) c 9)) a)]) b)]
      [(and side (> movement 0))
       (let* ([a (for/fold ([acc with-inside]) ([r (in-range nr1 (+ nr2 1))])
                   (set-cell acc r far 9))]
              [b (if (< movement distance)
                     (for/fold ([acc a]) ([r (in-range nr1 (+ nr2 1))])
                      (set-cell acc r (+ near dc) 9)) a)]) b)]
      [(and side (or (eq? side 'UP) (eq? side 'DOWN)))
       (for/fold ([acc with-inside]) ([c (in-range c1 (+ c2 1))])
        (set-cell (set-cell acc near c 9) far c 9))]
      [side
       (for/fold ([acc with-inside]) ([r (in-range r1 (+ r2 1))])
        (set-cell (set-cell acc r near 9) r far 9))]
      [else with-inside])))
   (define canonical
    (for/fold ([out (empty-grid h w 6)]) ([rec records]) (render-one out rec)))
   (define (winner key)
    (let ([best (apply max (map key records))])
     (find-first (lambda (rec) (= (key rec) best)) records)))
   (define (saturate out rec)
    (for*/fold ([acc out]) ([r (in-range (+ (hash-ref rec 'nr1) 1) (hash-ref rec 'nr2))]
                            [c (in-range (+ (hash-ref rec 'nc1) 1) (hash-ref rec 'nc2))])
     (if (member (at acc r c) '(5 7)) (set-cell acc r c 7) acc)))
   canonical)))
