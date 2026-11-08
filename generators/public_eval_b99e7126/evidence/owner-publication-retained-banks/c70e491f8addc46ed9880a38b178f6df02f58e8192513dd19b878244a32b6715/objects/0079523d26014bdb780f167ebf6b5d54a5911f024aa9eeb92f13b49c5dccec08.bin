(rule!
 ;; A modal-color separator lattice contains one ordinary tile pattern and
 ;; repeated copies of one anomalous tile.  The anomalous tile introduces one
 ;; new ink color.  Its ink cells form a micro mask; translate that same mask
 ;; over macro-tile coordinates so that it covers every anomalous clue tile,
 ;; then copy the complete anomalous tile into every selected macro position.
 (lambda (g)
  (let ()
   (define scope-mode 1)
   (define bg (pick-max (grid-colors g) (lambda (v) (count-color g v))))
   (define sep-rows
    (filter (lambda (r) (all? (lambda (c) (= (at g r c) bg)) (range 0 (cols g))))
            (range 0 (rows g))))
   (define sep-cols
    (filter (lambda (c) (all? (lambda (r) (= (at g r c) bg)) (range 0 (rows g))))
            (range 0 (cols g))))
   (define (bands separators)
    (filter (lambda (p) (<= (first p) (second p)))
     (for/list ((i (range 0 (- (length separators) 1))))
      (list (+ (list-ref separators i) 1)
            (- (list-ref separators (+ i 1)) 1)))))
   (define row-bands (bands sep-rows))
   (define col-bands (bands sep-cols))
   (define records
    (for*/list ((ri (range 0 (length row-bands)))
                (ci (range 0 (length col-bands))))
     (let ((rb (list-ref row-bands ri)) (cb (list-ref col-bands ci)))
      (list ri ci (subgrid g (first rb) (first cb) (second rb) (second cb))))))
   (define base-record
    (pick-max records
     (lambda (rec)
      (count-if (lambda (other) (equal? (third rec) (third other))) records))))
   (define base (third base-record))
   (define anomalies (filter (lambda (rec) (not (equal? (third rec) base))) records))
   (define anomaly (third (first anomalies)))
   (define base-colors (grid-colors base))
   (define ink
    (first (filter (lambda (v) (not (member v base-colors))) (grid-colors anomaly))))
   (define full-mask (find-color anomaly ink))
   (define mask-grid (paint-cells (empty-grid (rows anomaly) (cols anomaly) 0) full-mask 1))
   (define components (objects mask-grid 0))
   (define selected-mask
    (if (= scope-mode 0)
        full-mask
        (obj-cells (pick-max components obj-size))))
   (define clues (map (lambda (rec) (list (first rec) (second rec))) anomalies))
   (define anchors
    (for*/list ((ar (range 0 (+ 1 (- (length row-bands) (rows anomaly)))))
                (ac (range 0 (+ 1 (- (length col-bands) (cols anomaly)))))
                #:when
                (all? (lambda (q)
                        (member (list (- (first q) ar) (- (second q) ac)) full-mask))
                      clues))
     (list ar ac)))
   (define anchor (first anchors))
   (define paints
    (apply append
     (for/list ((p selected-mask))
      (let* ((mr (+ (first anchor) (first p)))
             (mc (+ (second anchor) (second p)))
             (rb (list-ref row-bands mr))
             (cb (list-ref col-bands mc)))
       (for*/list ((r (range 0 (rows anomaly))) (c (range 0 (cols anomaly))))
        (list (+ (first rb) r) (+ (first cb) c) (at anomaly r c)))))))
   (paint-cells g paints))))
