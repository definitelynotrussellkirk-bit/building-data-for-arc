; General rule for public evaluation parent 38007db0.
; In every separator-bounded tile row, retain the sole tile whose complete
; pattern differs from the repeated tile, then stack those outliers vertically
; in the original row order while preserving the horizontal separator bands.
(rule!
 (lambda (g)
   (define separator (cell-at g 0 0))
   (define (solid-row? r)
     (for/and ([c (in-range (cols g))])
       (= (cell-at g r c) separator)))
   (define (solid-col? c)
     (for/and ([r (in-range (rows g))])
       (= (cell-at g r c) separator)))
   (define (runs indices)
     (if (empty? indices)
         '()
         (let loop ([remaining (rest indices)]
                    [start (first indices)]
                    [finish (first indices)]
                    [answer '()])
           (cond
             [(empty? remaining) (reverse (cons (list start finish) answer))]
             [(= (first remaining) (add1 finish))
              (loop (rest remaining) start (first remaining) answer)]
             [else
              (loop (rest remaining) (first remaining) (first remaining)
                    (cons (list start finish) answer))]))))
   (define (gaps run-list)
     (for/list ([left (in-list run-list)]
                [right (in-list (rest run-list))]
                #:when (<= (add1 (second left)) (sub1 (first right))))
       (list (add1 (second left)) (sub1 (first right)))))
   (define row-runs
     (runs (filter solid-row? (range (rows g)))))
   (define col-runs
     (runs (filter solid-col? (range (cols g)))))
   (unless (and (>= (length row-runs) 3)
                (>= (length col-runs) 4)
                (= (first (first row-runs)) 0)
                (= (second (last row-runs)) (sub1 (rows g)))
                (= (first (first col-runs)) 0)
                (= (second (last col-runs)) (sub1 (cols g))))
     (error "row-outlier: missing complete separator lattice"))
   (define row-bands (gaps row-runs))
   (define col-bands (gaps col-runs))
   (unless (and (= (length row-bands) (sub1 (length row-runs)))
                (= (length col-bands) (sub1 (length col-runs))))
     (error "row-outlier: separators must alternate with nonempty tile bands"))
   (define tile-height (add1 (- (second (first row-bands))
                                (first (first row-bands)))))
   (define tile-width (add1 (- (second (first col-bands))
                               (first (first col-bands)))))
   (unless (and (>= tile-height 2) (>= tile-width 2)
                (for/and ([band (in-list row-bands)])
                  (= (add1 (- (second band) (first band))) tile-height))
                (for/and ([band (in-list col-bands)])
                  (= (add1 (- (second band) (first band))) tile-width)))
     (error "row-outlier: unequal or degenerate tile bands"))
   (define (tile-key row-band col-band)
     (for*/list ([r (in-range (first row-band) (add1 (second row-band)))]
                 [c (in-range (first col-band) (add1 (second col-band)))])
       (cell-at g r c)))
   (define records
     (for/list ([row-band (in-list row-bands)] [row-index (in-naturals)])
       (define tiles
         (for/list ([col-band (in-list col-bands)])
           (tile-key row-band col-band)))
       (define frequencies (make-hash))
       (for ([tile (in-list tiles)])
         (hash-update! frequencies tile add1 0))
       (define uniques
         (filter (lambda (tile) (= (hash-ref frequencies tile) 1))
                 (hash-keys frequencies)))
       (define repeateds
         (filter (lambda (tile) (= (hash-ref frequencies tile)
                                   (sub1 (length tiles))))
                 (hash-keys frequencies)))
       (unless (and (= (hash-count frequencies) 2)
                    (= (length uniques) 1)
                    (= (length repeateds) 1))
         (error "row-outlier: each row needs one outlier and repeated peers"))
       (define unique (first uniques))
       (define repeated (first repeateds))
       (define difference-count
         (for/sum ([a (in-list unique)] [b (in-list repeated)])
           (if (= a b) 0 1)))
       (define repeated-frequency (make-hash))
       (for ([value (in-list repeated)])
         (hash-update! repeated-frequency value add1 0))
       (define maximum-frequency (apply max (hash-values repeated-frequency)))
       (define backgrounds
         (filter (lambda (color)
                   (= (hash-ref repeated-frequency color) maximum-frequency))
                 (hash-keys repeated-frequency)))
       (unless (= (length backgrounds) 1)
         (error "row-outlier: repeated tile background must be uniquely modal"))
       (define background (first backgrounds))
       (define foreground-count
         (length (filter (lambda (value) (not (= value background))) unique)))
       (list row-index unique repeated difference-count foreground-count)))
   (define ordered
     (sort records
       (lambda (a b)
         (if (= (fifth a) (fifth b))
             (< (first a) (first b))
             (> (fifth a) (fifth b))))))
   (define left-width
     (add1 (- (second (first col-runs)) (first (first col-runs)))))
   (define right-run (last col-runs))
   (define right-width (add1 (- (second right-run) (first right-run))))
   (define output-width (+ left-width tile-width right-width))
   (define (row-slot r)
     (for/first ([band (in-list row-bands)] [index (in-naturals)]
                 #:when (<= (first band) r (second band)))
       index))
   (grid-from-fn (rows g) output-width
     (lambda (r c)
       (define slot (row-slot r))
       (if (and slot (<= left-width c) (< c (+ left-width tile-width)))
           (let* ([band (list-ref row-bands slot)]
                  [record (list-ref ordered slot)]
                  [flat-tile (second record)]
                  [dr (- r (first band))]
                  [dc (- c left-width)])
             (list-ref flat-tile (+ (* dr tile-width) dc)))
           separator)))))
