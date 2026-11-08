(rule!
 (lambda (g)
  (define h (rows g))
  (define w (cols g))
  (define marker-policy 'resolve)
  (define axis-mode 'opposite)
  (define (row-positions r color)
    (for/list ([c (in-range w)] #:when (= (at g r c) color)) c))
  (define (col-positions c color)
    (for/list ([r (in-range h)] #:when (= (at g r c) color)) r))
  (define horizontal-pairs
    (for*/list ([r (in-range h)] [color (in-range 1 10)]
                #:when (= (length (row-positions r color)) 2))
      (let ([ps (row-positions r color)])
        (list r color (first ps) (second ps)))))
  (define vertical-pairs
    (for*/list ([c (in-range w)] [color (in-range 1 10)]
                #:when (= (length (col-positions c color)) 2))
      (let ([ps (col-positions c color)])
        (list c color (first ps) (second ps)))))
  (define majority-horizontal? (> (length horizontal-pairs) (length vertical-pairs)))
  (define horizontal?
    (if (eq? axis-mode 'opposite) (not majority-horizontal?) majority-horizontal?))
  (define records (if horizontal? horizontal-pairs vertical-pairs))
  (define line-length (if horizontal? w h))
  (for/fold ([out g]) ([rec (in-list records)])
    (define line (first rec))
    (define color (second rec))
    (define a (third rec))
    (define b (fourth rec))
    (define step (- b a))
    (define markers
      (for/list ([p (in-range line-length)]
                 #:when (let ([v (if horizontal? (at g line p) (at g p line))])
                          (and (> v 0) (not (= v color)) (= (modulo (- p a) step) 0))))
        (list p (if horizontal? (at g line p) (at g p line)))))
    (define use-marker (and (eq? marker-policy 'resolve) (= (length markers) 1)))
    (define marker (and use-marker (first markers)))
    (define paint-color (if use-marker (second marker) color))
    (define positions
      (if use-marker
          (let ([lo (min a (first marker))] [hi (max b (first marker))])
            (for/list ([p (in-range lo (+ hi 1) step)]) p))
          (for/list ([p (in-range line-length)] #:when (= (modulo (- p a) step) 0)) p)))
    (recolor-cells out
      (map (lambda (p) (if horizontal? (list line p) (list p line))) positions)
      paint-color))))
