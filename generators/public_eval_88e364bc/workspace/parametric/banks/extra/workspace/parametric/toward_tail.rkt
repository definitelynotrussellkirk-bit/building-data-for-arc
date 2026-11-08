(rule!
 (lambda (g)
  (define reverse? #t)
  (define h (rows g))
  (define w (cols g))
  (define deltas '((-1 -1) (-1 0) (-1 1) (0 -1) (0 1) (1 -1) (1 0) (1 1)))
  (define (inside? r c) (and (<= 0 r) (< r h) (<= 0 c) (< c w)))
  (define (value p) (at g (first p) (second p)))
  (define panels
   (filter (lambda (obj) (ormap (lambda (p) (= (value p) 2)) (obj-cells obj))) (objects-multicolor g 0)))
  (define decoded
   (for/list ([obj panels])
    (let* ([cells (obj-cells obj)] [box (obj-bbox obj)]
           [wall (at g (first box) (second box))]
           [heads (filter (lambda (p) (= (value p) 2)) cells)]
           [tail (value (first (filter (lambda (p) (and (not (= (value p) wall)) (not (= (value p) 2)))) cells)))]
           [direction
            (first (filter
             (lambda (d)
              (andmap (lambda (p)
               (andmap (lambda (k)
                (let ([r (- (first p) (* k (first d)))] [c (- (second p) (* k (second d)))])
                 (and (inside? r c) (= (at g r c) tail)))) '(1 2))) heads)) deltas))])
     (list wall (first direction) (second direction)))))
  (define mask
   (for/list ([r (in-range h)]) (for/list ([c (in-range w)]) (if (member (at g r c) '(0 4)) 1 0))))
  (define rooms
   (filter (lambda (obj) (ormap (lambda (p) (= (value p) 4)) (obj-cells obj))) (objects mask 0)))
  (define region-specs
   (for/list ([obj rooms])
    (let* ([cells (obj-cells obj)]
           [wall
            (first (for*/list ([p cells] [d '((-1 0) (1 0) (0 -1) (0 1))]
              #:when (let ([r (+ (first p) (first d))] [c (+ (second p) (second d))])
                       (and (inside? r c) (not (member (at g r c) '(0 4))))))
             (at g (+ (first p) (first d)) (+ (second p) (second d)))))]
           [key (first (filter (lambda (x) (= (first x) wall)) decoded))]
           [direction (if reverse? (list (- (second key)) (- (third key))) (rest key))]
           [tokens (filter (lambda (p) (= (value p) 4)) cells)])
     (list wall direction cells tokens))))
  (define bound-regions region-specs)
  (define tokens (apply append (map fourth region-specs)))
  (define clean (paint-cells g tokens 0))
  (for*/fold ([out clean]) ([spec bound-regions] [token (fourth spec)])
   (let* ([dr (first (second spec))] [dc (second (second spec))] [cells (third spec)]
          [end
           (let walk ([r (first token)] [c (second token)])
            (if (and (member (list (+ r dr) (+ c dc)) cells)
                     (or (= dr 0) (= dc 0)
                         (and (member (list (+ r dr) c) cells) (member (list r (+ c dc)) cells))))
                (walk (+ r dr) (+ c dc)) (list r c)))])
    (paint-cells out (list end) 4)))))
