
(rule!
  (let ((dummy 0))
    (define dirs4 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))
    (define (cell< a b)
      (if (= (first a) (first b)) (< (second a) (second b)) (< (first a) (first b))))
    (define (obj-r1 obj) (first (obj-bbox obj)))
    (define (obj-c1 obj) (second (obj-bbox obj)))
    (define (obj-r2 obj) (third (obj-bbox obj)))
    (define (obj-c2 obj) (fourth (obj-bbox obj)))
    (define (obj-bbox-height obj) (+ 1 (- (obj-r2 obj) (obj-r1 obj))))
    (define (obj-cell-color grid cell) (at grid (first cell) (second cell)))
    (define (clear-cells grid cells)
      (for/fold ([out grid]) ([p (in-list cells)])
        (set-cell out (first p) (second p) 0)))
    (define (nonzero-cells grid)
      (filter (lambda (p) (not (= (at grid (first p) (second p)) 0))) (grid-positions grid)))
    (define (cells-with-color grid color)
      (filter (lambda (p) (= (at grid (first p) (second p)) color)) (grid-positions grid)))
    (define (object-color-cells grid color)
      (filter (lambda (obj) (= (obj-color obj) color)) (objects grid 0)))
    (define (blockers-except grid cells)
      (filter (lambda (p) (and (not (= (at grid (first p) (second p)) 0))
                               (not (member? p cells))))
              (grid-positions grid)))
    (define (slide-cells grid cells dr dc blockers)
      (let loop ([cur cells])
        (let ((nxt (translate-cells cur dr dc)))
          (if (and (all? (lambda (p) (in-bounds? (first p) (second p) (rows grid) (cols grid))) nxt)
                   (not (any? (lambda (p) (member? p blockers)) nxt)))
              (loop nxt)
              cur))))
    (define (direction-step marker)
      (cond [(= marker 1) (list 0 -1)]
            [(= marker 2) (list 0 1)]
            [(= marker 3) (list -1 0)]
            [(= marker 4) (list 1 0)]
            [else (list 0 0)]))
    (define (normalize-paint grid cells color)
      (paint-cells grid (normalize-cells cells) color))
    (define (firstpos row color)
      (let ((hits (filter (lambda (c) (= (list-ref row c) color)) (range (length row)))))
        (if (empty? hits) 9999 (first hits))))
    (define (row-count-value row color)
      (length (filter (lambda (v) (= v color)) row)))
    (define (paint-normal-at grid cells top left color)
      (for/fold ([out grid]) ([p (in-list cells)])
        (set-cell out (+ top (first p)) (+ left (second p)) color)))
    (define (component-from-cell grid start)
      (let* ((color (at grid (first start) (second start))))
        (let bfs ([queue (list start)] [seen (list start)] [cells (list)])
          (if (empty? queue)
              (list 'color color 'cells (sort cells cell<))
              (let* ((cur (first queue))
                     (restq (rest queue))
                     (nbrs (filter
                            (lambda (p)
                              (and (in-bounds? (first p) (second p) (rows grid) (cols grid))
                                   (not (member? p seen))
                                   (= (at grid (first p) (second p)) color)))
                            (map (lambda (d) (list (+ (first cur) (first d)) (+ (second cur) (second d)))) dirs4))))
                (bfs (append restq nbrs) (append seen nbrs) (cons cur cells)))))))
    (define (comp-hash-color comp) (second comp))
    (define (comp-hash-cells comp) (fourth comp))
    (define (multicolor-components4 grid)
      (let loop-pos ([positions (grid-positions grid)] [seen (list)] [acc (list)])
        (cond
          [(empty? positions) (reverse acc)]
          [(or (member? (first positions) seen)
               (= (at grid (first (first positions)) (second (first positions))) 0))
           (loop-pos (rest positions) seen acc)]
          [else
           (let bfs ([queue (list (first positions))] [seen2 (cons (first positions) seen)] [cells (list)])
             (if (empty? queue)
                 (let* ((sorted-cells (sort cells cell<))
                        (bb (bbox-of-cells sorted-cells)))
                   (loop-pos (rest positions) seen2 (cons (list sorted-cells bb) acc)))
                 (let* ((cur (first queue))
                        (restq (rest queue))
                        (nbrs (filter
                               (lambda (p)
                                 (and (in-bounds? (first p) (second p) (rows grid) (cols grid))
                                      (not (member? p seen2))
                                      (not (= (at grid (first p) (second p)) 0))))
                               (map (lambda (d) (list (+ (first cur) (first d)) (+ (second cur) (second d)))) dirs4))))
                   (bfs (append restq nbrs) (append seen2 nbrs) (cons cur cells)))))])))
    (define (motion-order comps dr dc)
      (cond [(= dr 1) (sort comps (lambda (a b) (> (obj-r2 a) (obj-r2 b))))]
            [(= dr -1) (sort comps (lambda (a b) (< (obj-r1 a) (obj-r1 b))))]
            [(= dc 1) (sort comps (lambda (a b) (> (obj-c2 a) (obj-c2 b))))]
            [else (sort comps (lambda (a b) (< (obj-c1 a) (obj-c1 b))))]))
    (define (gravity-slide-all grid dr dc immobile-colors remove-cells dynamic-colors)
      (define start (clear-cells grid remove-cells))
      (let loop ([out start] [fuel (* 3 (rows grid) (cols grid))])
        (if (<= fuel 0)
            out
            (let* ((movable
                    (filter
                     (lambda (obj)
                       (and (not (member? (obj-color obj) immobile-colors))
                            (or (eq? dynamic-colors #f) (member? (obj-color obj) dynamic-colors))))
                     (objects out 0)))
                   (ordered (motion-order movable dr dc))
                   (step-result
                    (for/fold ([state (list out #f)]) ([obj (in-list ordered)])
                      (let* ((cur (first state))
                             (changed? (second state))
                             (cells (obj-cells obj))
                             (blockers (blockers-except cur cells))
                             (slid (slide-cells cur cells dr dc blockers)))
                        (if (equal? slid cells)
                            (list cur changed?)
                            (list (paint-cells (clear-cells cur cells) slid (obj-color obj)) #t))))))
              (if (second step-result)
                  (loop (first step-result) (- fuel 1))
                  (first step-result))))))

    (define (projection-ray grid start dr dc)
      (let loop ([cur start] [acc (list)])
        (if (and (in-bounds? (first cur) (second cur) (rows grid) (cols grid))
                 (= (at grid (first cur) (second cur)) 0))
            (loop (list (+ (first cur) dr) (+ (second cur) dc)) (cons cur acc))
            (reverse acc))))
    (define (project-from-contacts grid contacts dr dc)
      (paint-cells
       grid
       (apply append
              (map (lambda (p)
                     (projection-ray grid
                                     (list (+ (first p) dr) (+ (second p) dc))
                                     dr dc))
                   contacts))
       4))

    (let* ((frame (first (object-color-cells g 8)))
           (obj (first (object-color-cells g 2)))
           (drdc (cond [(< (obj-c2 obj) (obj-c1 frame)) (list 0 1)]
                       [(> (obj-c1 obj) (obj-c2 frame)) (list 0 -1)]
                       [(< (obj-r2 obj) (obj-r1 frame)) (list 1 0)]
                       [else (list -1 0)]))
           (cells (obj-cells obj))
           (early-contacts
            (filter
             (lambda (p)
               (and (in-bounds? (first p) (second p) (rows g) (cols g))
                    (= (at g (first p) (second p)) 8)))
             (map (lambda (p)
                    (list (+ (first p) (first drdc)) (+ (second p) (second drdc))))
                  cells)))
           (preprojected (project-from-contacts g early-contacts (first drdc) (second drdc)))
           (slid (slide-cells g cells (first drdc) (second drdc)
                              (filter (lambda (p) (not (= (at g (first p) (second p)) 2))) (nonzero-cells g)))))
      (paint-cells (clear-cells preprojected cells) slid 2))
  ))