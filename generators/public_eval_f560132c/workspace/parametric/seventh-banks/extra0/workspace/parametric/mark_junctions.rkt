(rule!
 ;; Assemble the scattered jigsaw pieces into their square without reflection.
 ;; The multicolored piece carries a square color key and anchors the upper left.
 ;; Fill the key's backing (including its zero entry), then rotate the other
 ;; pieces into an exact cover. Sort assembled centroids into rows and columns
 ;; and recolor pieces according to the key. Geometry, not source color, binds
 ;; a piece to its key entry. All search and coloring are input-derived.
 (lambda (g)
  (let ()
   (define raw (objects-multicolor g 0))
   (define keyed (find-first (lambda (o)
     (> (length (remove-duplicates (map (lambda (p) (at g (first p) (second p))) (obj-cells o)))) 1)) raw))
   (define anchor (obj-cells keyed))
   (define backing (argmax (lambda (v) (count (lambda (p) (= (at g (first p) (second p)) v)) anchor))
                           (remove-duplicates (map (lambda (p) (at g (first p) (second p))) anchor))))
   (define ink (filter (lambda (p) (not (= (at g (first p) (second p)) backing))) anchor))
   (define kr0 (apply min (map first ink)))
   (define kc0 (apply min (map second ink)))
   (define kr1 (apply max (map first ink)))
   (define kc1 (apply max (map second ink)))
   (define key (subgrid g kr0 kc0 kr1 kc1))
   (define k (rows key))
   (define (norm cells)
     (let ([r0 (apply min (map first cells))] [c0 (apply min (map second cells))])
       (sort (map (lambda (p) (list (- (first p) r0) (- (second p) c0))) cells) cell<)))
   (define filled (remove-duplicates (append anchor (for*/list ([r (range kr0 (add1 kr1))] [c (range kc0 (add1 kc1))]) (list r c)))))
   (define shapes (cons (norm filled) (map (lambda (o) (norm (obj-cells o))) (filter (lambda (o) (not (equal? o keyed))) raw))))
   (define area (apply + (map length shapes)))
   (define n (find-first (lambda (n) (= (* n n) area)) (range 1 31)))
   (define (rotate cells) (norm (map (lambda (p) (list (second p) (- (first p)))) cells)))
   (define (variants cells)
     (let* ([b (rotate cells)] [c (rotate b)] [d (rotate c)]) (remove-duplicates (list cells b c d))))
   (define full (sub1 (arithmetic-shift 1 (* n n))))
   (define (bits cells) (for/sum ([p cells]) (arithmetic-shift 1 (+ (* n (first p)) (second p)))))
   (define (search occupied remaining placed)
     (if (= occupied full) placed
       (let* ([gap (for/first ([i (range (* n n))] #:when (zero? (bitwise-and occupied (arithmetic-shift 1 i)))) i)]
              [fr (quotient gap n)] [fc (remainder gap n)])
         (for/or ([entry remaining])
           (for/or ([shape (second entry)])
             (let* ([dc (- fc (second (first shape)))]
                    [cells (map (lambda (p) (list (+ fr (first p)) (+ dc (second p)))) shape)])
               (and (andmap (lambda (p) (and (<= 0 (first p)) (< (first p) n) (<= 0 (second p)) (< (second p) n))) cells)
                    (zero? (bitwise-and occupied (bits cells)))
                    (search (bitwise-ior occupied (bits cells))
                      (filter (lambda (other) (not (= (first other) (first entry)))) remaining)
                      (append placed (list cells))))))))))
   (define assembled (search (bits (first shapes))
     (for/list ([i (range 1 (length shapes))]) (list i (variants (list-ref shapes i)))) (list (first shapes))))
   (define (cy cells) (/ (apply + (map first cells)) (length cells)))
   (define (cx cells) (/ (apply + (map second cells)) (length cells)))
   (define by-row (sort assembled < #:key cy))
   (define ordered (apply append (for/list ([r (range k)]) (sort (take (drop by-row (* r k)) k) < #:key cx))))
   (define painted (for/fold ([out (empty-grid n n 0)]) ([cells ordered] [i (in-naturals)])
     (recolor-cells out cells (at key (quotient i k) (remainder i k)))))
   ;; The new stage reads the assembled neighborhood, not the scattered pieces.
   (define intermediate painted)
   (define result (grid-from-fn n n (lambda (r c)
     (define colors (remove-duplicates (for/list ([d (cons (list 0 0) cardinal-deltas)]
       #:when (in-bounds? (+ r (first d)) (+ c (second d)) n n))
       (at intermediate (+ r (first d)) (+ c (second d))))))
     (if (>= (length colors) 3) 9 (at painted r c)))))
   result)))
