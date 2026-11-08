(rule!
  (let* ([key-cells (find-color g 7)]
         [ka (first key-cells)]
         [kb (second key-cells)]
         [kr1 (first ka)] [kc1 (second ka)]
         [kr2 (first kb)] [kc2 (second kb)]
         [key-horizontal (= kr1 kr2)]
         [key-length (if key-horizontal
                         (+ 1 (- (max kc1 kc2) (min kc1 kc2)))
                         (+ 1 (- (max kr1 kr2) (min kr1 kr2))))])
    (define (paint-color out color)
      (let ([cells (find-color g color)])
        (if (not (= (length cells) 2))
            (paint-cells out cells color)
            (let* ([a (first cells)]
                   [b (second cells)]
                   [r1 (first a)] [c1 (second a)]
                   [r2 (first b)] [c2 (second b)]
                   [horizontal (= r1 r2)]
                   [vertical (= c1 c2)]
                   [segment-length
                    (if horizontal
                        (+ 1 (- (max c1 c2) (min c1 c2)))
                        (+ 1 (- (max r1 r2) (min r1 r2))))]
                   [matches-key
                    (and (or (and key-horizontal horizontal)
                             (and (not key-horizontal) vertical))
                         (= segment-length key-length))])
              (cond
                [(and horizontal matches-key)
                 (paint-cells out
                              (for/list ([c (in-range (min c1 c2) (+ (max c1 c2) 1))])
                                (list r1 c))
                              color)]
                [(and vertical matches-key)
                 (paint-cells out
                              (for/list ([r (in-range (min r1 r2) (+ (max r1 r2) 1))])
                                (list r c1))
                              color)]
                [else (paint-cells out cells color)])))))
    (for/fold ([out (empty-grid (rows g) (cols g) 0)])
              ([color (in-list (grid-colors g 0))])
      (paint-color out color))))
