(rule!
 (lambda (g)
  (define columns? #t)
  (define separator
   (first (filter (lambda (c)
     (all? (lambda (r) (= (at g r c) 4)) (range (rows g)))) (range (cols g)))))
  (define canvas (map (lambda (row) (drop row (+ separator 1))) g))
  (define marker
   (first (for*/list ([r (in-range (rows canvas))] [c (in-range (cols canvas))]
                      #:when (= (at canvas r c) 5)) (list r c))))
  (define (tile p)
   (for/list ([dr (in-range 3)])
    (for/list ([dc (in-range 3)]) (at g (+ (first p) dr) (+ (second p) dc)))))
  (define slots
   (filter (lambda (p) (any? (lambda (v) (> v 0)) (apply append (tile p))))
    (for*/list ([r (in-range 0 (- (rows g) 2) 4)]
                [c (in-range 0 (- separator 2) 4)]) (list r c))))
  (define ordered-slots
   (sort slots (lambda (a b)
    (if columns?
     (or (< (second a) (second b))
         (and (= (second a) (second b)) (< (first a) (first b))))
     (or (< (first a) (first b))
         (and (= (first a) (first b)) (< (second a) (second b))))))))
  (define (decode p)
   (let* ([cells (tile p)]
          [ink (first (filter (lambda (v) (> v 0)) (apply append cells)))]
          [mask (map (lambda (row) (map (lambda (v) (if (= v 0) 0 1)) row)) cells)]
          [motion (cond
           [(equal? mask '((1 1 0) (1 0 1) (0 1 0))) (list 0 1 3)]
           [(equal? mask '((1 0 1) (1 0 1) (1 1 1))) (list 0 -1 2)]
           [(equal? mask '((1 1 1) (0 1 0) (1 0 1))) (list 0 -1 4)]
           [(equal? mask '((1 0 1) (0 1 0) (0 1 0))) (list 1 0 2)]
           [else (error 'glyph "unknown glyph")])])
    (cons ink motion)))
  (define commands (map decode ordered-slots))
  (define instructions commands)
  (define result
   (for/fold ([state (list canvas (first marker) (second marker))]) ([cmd instructions])
    (let* ([sr (+ 1 (second state))] [sc (third state)]
           [dr (second cmd)] [dc (third cmd)] [n (fourth cmd)]
           [cells (for/list ([k (in-range n)]) (list (+ sr (* k dr)) (+ sc (* k dc))))]
           [endpoint (last cells)])
     (list (paint-cells (first state) cells (first cmd)) (first endpoint) (second endpoint)))))
  (first result)))
