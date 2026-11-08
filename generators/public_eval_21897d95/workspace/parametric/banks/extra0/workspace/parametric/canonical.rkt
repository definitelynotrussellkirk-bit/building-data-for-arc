(rule!
 ;; Solid color rooms contain four-cell color-1 T arrows.  The stem points two
 ;; cells toward a target room; the plurality around the glyph identifies the
 ;; source room.  A color-1 center transfers the source color, while a non-1
 ;; center is an explicit payload.  Erase each arrow to its source, flood its
 ;; target room, and transfer the selected color.  An optional isolated five-cell
 ;; L is erased to its local room and rotates the completed grid: left arm = CCW,
 ;; right arm = CW.
 (lambda (g)
  (let ()
    (define payload-mode 'payload)
    (define h (rows g))
    (define w (cols g))
    (define dirs
      (hash 'up (list -1 0) 'right (list 0 1)
            'down (list 1 0) 'left (list 0 -1)))
    (define (cell-member? p cells) (and (member p cells) #t))
    (define (neighbors p)
      (for/list ([d (in-list cardinal-deltas)])
        (list (+ (first p) (first d)) (+ (second p) (second d)))))
    (define (adjacent-counts cells)
      (define counts (make-hash))
      (for* ([p (in-list cells)] [q (in-list (neighbors p))]
             #:when (and (in-bounds? (first q) (second q) h w)
                         (not (cell-member? q cells))
                         (not (= (at g (first q) (second q)) 1))))
        (hash-update! counts (at g (first q) (second q)) add1 0))
      counts)
    (define (candidate center bar direction)
      (define delta (hash-ref dirs direction))
      (define dr (first delta))
      (define dc (second delta))
      (define stem (list (+ (first center) dr) (+ (second center) dc)))
      (define target (list (+ (first center) (* 2 dr)) (+ (second center) (* 2 dc))))
      (cond
        [(or (not (in-bounds? (first stem) (second stem) h w))
             (not (in-bounds? (first target) (second target) h w))) #f]
        [(or (not (= (at g (first stem) (second stem)) 1))
             (= (at g (first target) (second target)) 1)) #f]
        [else
         (define cells (remove-duplicates (append bar (list stem))))
         (define ranked
           (sort (hash->list (adjacent-counts cells))
                 (lambda (a b) (> (cdr a) (cdr b)))))
         (cond
           [(empty? ranked) #f]
           [(and (> (length ranked) 1) (= (cdr (first ranked)) (cdr (second ranked)))) #f]
           [else
            (define source (car (first ranked)))
            (define target-color (at g (first target) (second target)))
            (if (= target-color source) #f
                (hash 'center center 'stem stem 'direction direction 'delta delta
                      'payload (at g (first center) (second center))
                      'source source 'target target-color 'target-seed target
                      'cells (sort cells cell<) 'score (cdr (first ranked))))])]))
    ;; A1: enumerate valid T interpretations, then greedily retain disjoint best
    ;; arrows so accidental overlapping T fragments cannot become commands.
    (define raw-arrows
      (append
       (filter values
         (append*
          (for*/list ([r (in-range 1 (- h 1))] [c (in-range w)]
                      #:when (and (= (at g (- r 1) c) 1) (= (at g (+ r 1) c) 1)))
            (define center (list r c))
            (define bar (list (list (- r 1) c) center (list (+ r 1) c)))
            (list (candidate center bar 'left) (candidate center bar 'right)))))
       (filter values
         (append*
          (for*/list ([r (in-range h)] [c (in-range 1 (- w 1))]
                      #:when (and (= (at g r (- c 1)) 1) (= (at g r (+ c 1)) 1)))
            (define center (list r c))
            (define bar (list (list r (- c 1)) center (list r (+ c 1))))
            (list (candidate center bar 'up) (candidate center bar 'down)))))))
    (define (direction-name arrow) (symbol->string (hash-ref arrow 'direction)))
    (define sorted-arrows
      (sort raw-arrows
        (lambda (a b)
          (cond [(not (= (hash-ref a 'score) (hash-ref b 'score)))
                 (> (hash-ref a 'score) (hash-ref b 'score))]
                [(not (= (first (hash-ref a 'center)) (first (hash-ref b 'center))))
                 (< (first (hash-ref a 'center)) (first (hash-ref b 'center)))]
                [(not (= (second (hash-ref a 'center)) (second (hash-ref b 'center))))
                 (< (second (hash-ref a 'center)) (second (hash-ref b 'center)))]
                [else (string<? (direction-name a) (direction-name b))]))))
    (define arrows
      (reverse
       (foldl
        (lambda (arrow chosen)
          (define cells (hash-ref arrow 'cells))
          (if (ormap (lambda (other)
                       (ormap (lambda (p) (cell-member? p (hash-ref other 'cells))) cells))
                     chosen)
              chosen
              (cons arrow chosen)))
        '() sorted-arrows)))
    (define arrow-cells (remove-duplicates (append* (map (lambda (a) (hash-ref a 'cells)) arrows))))
    ;; A2: find an isolated 5-cell L after masking arrow glyphs.
    (define masked
      (grid-from-fn h w
        (lambda (r c) (if (cell-member? (list r c) arrow-cells) 99 (at g r c)))))
    (define (cue-from-object obj)
      (define color (obj-color obj))
      (define cells (obj-cells obj))
      (define box (obj-bbox obj))
      (if (or (= color 1) (not (= (length cells) 5))
              (not (= (- (third box) (first box)) 2))
              (not (= (- (fourth box) (second box)) 2)))
          #f
          (let* ((degrees
                  (for/list ((p (in-list cells)))
                    (list p (count (lambda (q) (cell-member? q cells)) (neighbors p)))))
                 (endpoints (map first (filter (lambda (row) (= (second row) 1)) degrees))))
            (if (not (= (length endpoints) 2))
                #f
                (let ((corners
                       (filter values
                         (for/list ((p (in-list cells)))
                           (define vectors
                             (map (lambda (e)
                                    (list (- (first e) (first p)) (- (second e) (second p))))
                                  endpoints))
                           (if (and
                                (andmap (lambda (v)
                                          (and (= (+ (abs (first v)) (abs (second v))) 2)
                                               (or (= (first v) 0) (= (second v) 0))))
                                        vectors)
                                (ormap (lambda (v) (= (first v) 0)) vectors)
                                (ormap (lambda (v) (= (second v) 0)) vectors))
                               (list p vectors)
                               #f)))))
                  (if (not (= (length corners) 1))
                      #f
                      (let* ((corner-record (first corners))
                             (corner (first corner-record))
                             (vectors (second corner-record))
                             (adjacent-values
                              (for*/list ((p (in-list cells)) (q (in-list (neighbors p)))
                                          #:when (and (in-bounds? (first q) (second q) h w)
                                                      (not (cell-member? q cells))
                                                      (not (cell-member? q arrow-cells))
                                                      (not (= (at g (first q) (second q)) 1))
                                                      (not (= (at g (first q) (second q)) color))))
                                (at g (first q) (second q)))))
                        (if (empty? adjacent-values)
                            #f
                            (let ((horizontal
                                   (find-first (lambda (v) (not (= (second v) 0))) vectors)))
                              (hash 'color color 'cells cells 'corner corner 'vectors vectors
                                    'background (mode-list adjacent-values)
                                    'turn (if (< (second horizontal) 0) 'ccw 'cw)))))))))))
    (define cue-candidates
      (filter values (map cue-from-object (objects masked 99))))
    (define cue (if (empty? cue-candidates) #f (first cue-candidates)))
    ;; B: erase all annotations using A's records, transfer into target-room
    ;; components of that cleaned base, then consume A's optional rotation.
    (define cue-clean
      (if cue (paint-cells g (hash-ref cue 'cells) (hash-ref cue 'background)) g))
    (define clean
      (for/fold ([out cue-clean]) ([arrow (in-list arrows)])
        (paint-cells out (hash-ref arrow 'cells) (hash-ref arrow 'source))))
    (define transferred
      (for/fold ([out clean]) ([arrow (in-list arrows)])
        (define seed (hash-ref arrow 'target-seed))
        (define target-color (at clean (first seed) (second seed)))
        (define target-cells
          (connected-region clean (first seed) (second seed)
                            (lambda (r c value) (= value target-color)) 4))
        (define payload (hash-ref arrow 'payload))
        (define paint
          (if (or (equal? payload-mode 'source_only) (= payload 1))
              (hash-ref arrow 'source) payload))
        (paint-cells out target-cells paint)))
    (cond [(not cue) transferred]
          [(equal? (hash-ref cue 'turn) 'ccw) (rotate-ccw transferred)]
          [else (rotate-cw transferred)]))))
