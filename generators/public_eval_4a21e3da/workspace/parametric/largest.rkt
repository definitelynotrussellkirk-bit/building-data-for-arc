(rule!
 (lambda (g)
  (define intersection? #f)
  (define h (rows g))
  (define w (cols g))
  (define bg (at g 0 0))
  (define markers
   (for*/list ([r (in-range h)] [c (in-range w)]
    #:when (and (or (= r 0) (= r (- h 1)) (= c 0) (= c (- w 1)))
                (not (= (at g r c) bg)))) (list r c)))
  (define ray (at g (first (first markers)) (second (first markers))))
  (define fg (first (filter (lambda (v) (and (not (= v bg)) (not (= v ray)))) (apply append g))))
  (define points (for*/list ([r (in-range h)] [c (in-range w)] #:when (= (at g r c) fg)) (list r c)))
  (define vertical (filter (lambda (p) (or (= (first p) 0) (= (first p) (- h 1)))) markers))
  (define horizontal (filter (lambda (p) (or (= (second p) 0) (= (second p) (- w 1)))) markers))
  (define vc (if (null? vertical) -1 (second (first vertical))))
  (define hr (if (null? horizontal) -1 (first (first horizontal))))
  (define vs (if (null? vertical) 0 (if (= (first (first vertical)) 0) -1 1)))
  (define hs (if (null? horizontal) 0 (if (= (second (first horizontal)) 0) -1 1)))
  (define rays
   (append
    (if (= vc -1) '()
     (let* ([hits (map first (filter (lambda (p) (= (second p) vc)) points))]
            [lo (if (= vs -1) 0 (apply min hits))]
            [hi (if (= vs -1) (apply max hits) (- h 1))])
      (for/list ([r (in-range lo (+ hi 1))]) (list r vc))))
    (if (= hr -1) '()
     (let* ([hits (map second (filter (lambda (p) (= (first p) hr)) points))]
            [lo (if (= hs -1) 0 (apply min hits))]
            [hi (if (= hs -1) (apply max hits) (- w 1))])
      (for/list ([c (in-range lo (+ hi 1))]) (list hr c))))))
  (define anchors (filter (lambda (p) (or (= (first p) hr) (= (second p) vc))) points))
  (define region-specs
   (filter (lambda (x) (not (equal? x #f)))
    (for*/list ([rs (if (= hr -1) (list vs) (list -1 1))]
                [cs (if (= vc -1) (list hs) (list -1 1))])
     (let* ([cells (filter (lambda (p)
                     (and (not (= (first p) hr)) (not (= (second p) vc))
                      (or (= hr -1) (if (= rs -1) (< (first p) hr) (> (first p) hr)))
                      (or (= vc -1) (if (= cs -1) (< (second p) vc) (> (second p) vc))))) points)]
            [touch-v (and (not (= vc -1)) (= rs vs))]
            [touch-h (and (not (= hr -1)) (= cs hs))]
            [keep (if intersection? (and (or (= vc -1) touch-v) (or (= hr -1) touch-h)) (or touch-v touch-h))])
      (if (or (null? cells) (not keep)) #f
       (list rs cs cells (apply min (map first cells)) (apply max (map first cells))
                         (apply min (map second cells)) (apply max (map second cells))))))))
  (define placements (if (null? region-specs) '() (list (for/fold ([best (first region-specs)]) ([spec (rest region-specs)]) (if (> (length (third spec)) (length (third best))) spec best)))))
  (define blank (for/list ([r (in-range h)]) (for/list ([c (in-range w)]) bg)))
  (define base (paint-cells (paint-cells blank rays ray) anchors fg))
  (for/fold ([out base]) ([spec placements])
   (let* ([dr (if (= (first spec) -1) (- (fourth spec)) (- (- h 1) (list-ref spec 4)))]
          [dc (if (= (second spec) -1) (- (list-ref spec 5)) (- (- w 1) (list-ref spec 6)))]
          [shifted (map (lambda (p) (list (+ (first p) dr) (+ (second p) dc))) (third spec))])
    (paint-cells out shifted fg)))))
