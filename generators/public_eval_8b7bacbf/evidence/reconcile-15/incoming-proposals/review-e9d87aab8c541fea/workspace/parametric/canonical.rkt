(rule!
 ;; Small monochromatic-boundary background regions are pockets.  A singleton
 ;; payload embedded in at least three neighboring cells of one carrier color
 ;; activates that carrier route.  Trace 8-connected carrier components through
 ;; adjacent pockets; same-color components separated by one intervening cell
 ;; are also joined so a route may continue through a crossing.  Fill every
 ;; reached pocket with the payload and preserve all other cells.
 (lambda (g)
   (let ()
     (define bridge-short-gaps #t)
     (define height (rows g))
     (define width (cols g))
     (define cardinal '((-1 0) (1 0) (0 -1) (0 1)))
     (define all-eight
       '((-1 0) (1 0) (0 -1) (0 1) (-1 -1) (-1 1) (1 -1) (1 1)))
     (define (inside? p)
       (and (<= 0 (first p)) (< (first p) height)
            (<= 0 (second p)) (< (second p) width)))
     (define (value-at p) (at g (first p) (second p)))
     (define (neighbors p deltas)
       (for/list ([d (in-list deltas)]
                  #:when (inside? (list (+ (first p) (first d))
                                       (+ (second p) (second d)))))
         (list (+ (first p) (first d))
               (+ (second p) (second d)))))
     (define colors (grid-colors g))
     (define background
       (for/fold ([best (first colors)]) ([candidate (in-list (rest colors))])
         (define candidate-count (count-color g candidate))
         (define best-count (count-color g best))
         (if (or (> candidate-count best-count)
                 (and (= candidate-count best-count) (< candidate best)))
             candidate best)))
     (define (boundary-of cells)
       (remove-duplicates
        (filter (lambda (p) (not (= (value-at p) background)))
                (apply append
                       (for/list ([p (in-list cells)])
                         (neighbors p cardinal))))
        equal?))
     (define pockets
       (filter
        (lambda (x) x)
        (for/list ([cells (in-list (find-0-regions g background))])
          (define boundary (boundary-of cells))
          (define boundary-colors
            (remove-duplicates (map value-at boundary)))
          (and (<= (length cells) (quotient (* height width) 3))
               (>= (length boundary) 3)
               (= (length boundary-colors) 1)
               (list cells boundary (first boundary-colors))))))
     (define components (objects-8 g background))
     (define (chebyshev a b)
       (max (abs (- (first a) (first b)))
            (abs (- (second a) (second b)))))
     (define (near? left right limit)
       (for*/or ([a (in-list left)] [b (in-list right)])
         (<= (chebyshev a b) limit)))
     (define (frequency value values)
       (for/sum ([item (in-list values)]) (if (= item value) 1 0)))
     (define sources
       (filter
        (lambda (x) x)
        (for/list ([component (in-list components)] [component-index (in-naturals)])
          (if (not (= (obj-size component) 1))
              #f
              (let* ([position (first (obj-cells component))]
                     [payload (obj-color component)]
                     [neighbor-colors
                      (for/list ([p (in-list (neighbors position all-eight))]
                                 #:when (and (not (= (value-at p) background))
                                             (not (= (value-at p) payload))))
                        (value-at p))]
                     [candidate-colors (remove-duplicates neighbor-colors)])
                (if (empty? candidate-colors)
                    #f
                    (let* ([carrier
                            (for/fold ([best (first candidate-colors)])
                                      ([candidate (in-list (rest candidate-colors))])
                              (define candidate-count (frequency candidate neighbor-colors))
                              (define best-count (frequency best neighbor-colors))
                              (if (or (> candidate-count best-count)
                                      (and (= candidate-count best-count)
                                           (< candidate best)))
                                  candidate best))]
                           [support (frequency carrier neighbor-colors)]
                           [starts
                            (for/list ([other (in-list components)] [index (in-naturals)]
                                       #:when (and (= (obj-color other) carrier)
                                                   (near? (list position)
                                                          (obj-cells other) 1)))
                              index)])
                      (and (>= support 3) (not (empty? starts))
                           (list payload carrier starts position component-index)))))))))
     (define (component-pocket-nodes component-index)
       (define cells (obj-cells (list-ref components component-index)))
       (for/list ([pocket (in-list pockets)] [pocket-index (in-naturals)]
                  #:when (near? cells (second pocket) 1))
         (list 'pocket pocket-index)))
     (define (bridge-component-nodes component-index carrier)
       (if bridge-short-gaps
           (let ([cells (obj-cells (list-ref components component-index))])
             (for/list ([other (in-list components)] [other-index (in-naturals)]
                        #:when (and (not (= component-index other-index))
                                    (= (obj-color other) carrier)
                                    (near? cells (obj-cells other) 2)))
               (list 'component other-index)))
           '()))
     (define (pocket-component-nodes pocket-index carrier)
       (define boundary (second (list-ref pockets pocket-index)))
       (for/list ([component (in-list components)] [component-index (in-naturals)]
                  #:when (and (= (obj-color component) carrier)
                              (near? (obj-cells component) boundary 1)))
         (list 'component component-index)))
     (define (reachable-pockets source)
       (define carrier (second source))
       (define starts
         (map (lambda (index) (list 'component index)) (third source)))
       (let bfs ([queue starts] [seen starts] [found '()])
         (if (empty? queue)
             (reverse found)
             (let* ([node (first queue)]
                    [kind (first node)]
                    [index (second node)]
                    [neighbors
                     (if (eq? kind 'component)
                         (append (component-pocket-nodes index)
                                 (bridge-component-nodes index carrier))
                         (pocket-component-nodes index carrier))]
                    [fresh
                     (filter (lambda (candidate)
                               (not (member candidate seen)))
                             neighbors)])
               (bfs (append (rest queue) fresh)
                    (append seen fresh)
                    (if (eq? kind 'pocket) (cons index found) found))))))
     (define assignments
       (for/fold ([answer '()]) ([source (in-list sources)])
         (for/fold ([current answer])
                   ([pocket-index (in-list (reachable-pockets source))])
           (if (assoc pocket-index current)
               current
               (append current (list (list pocket-index (first source))))))))
     (for/fold ([out g]) ([assignment (in-list assignments)])
       (paint-cells out
                    (first (list-ref pockets (first assignment)))
                    (second assignment))))))
