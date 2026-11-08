(rule!
 ;; A solid multicolor two-cell-thick table touches a canvas edge. Read each
 ;; color pair INWARD: the edge-facing color is the key, its inner neighbor the
 ;; value. A square 2x2 table uses a touched horizontal edge when one exists.
 ;; Find four-connected background regions not reaching the canvas border.
 ;; A monochromatic enclosing boundary selects its key; unmapped holes and
 ;; open background remain unchanged. Fill all cells of each mapped hole.
 ;; The native largest_per_color variant retains all maximum-area ties per key.
 (lambda (g)
  (let ()
    (define fill-scope 'all)
    (define size-measure 'area)
    (define legend-direction 'inward)
    (define connectivity 4)
    (define bg (mode g -1))
    (define (horizontal? obj)
      (and (= (obj-h obj) 2)
           (or (= (obj-r1 obj) 0) (= (obj-r2 obj) (- (rows g) 1)))))
    (define tables
      (filter
        (lambda (obj)
          (and (= (obj-size obj) (* (obj-h obj) (obj-w obj)))
               (> (length (remove-duplicates
                    (map (lambda (p) (at g (first p) (second p))) (obj-cells obj)))) 1)
               (or (horizontal? obj)
                   (and (= (obj-w obj) 2)
                        (or (= (obj-c1 obj) 0) (= (obj-c2 obj) (- (cols g) 1)))))))
        (objects-multicolor g bg)))
    (unless (= (length tables) 1) (error 'legend "one solid edge legend required"))
    (define table (first tables))
    (define horizontal (horizontal? table))
    (define source-first
      (let ([normal (if horizontal (= (obj-r1 table) 0) (= (obj-c1 table) 0))])
        (cond [(equal? legend-direction 'reverse) (not normal)]
              [(equal? legend-direction 'forward) #t]
              [(equal? legend-direction 'backward) #f]
              [else normal])))
    (define mapping
      (if horizontal
          (for/list ([c (in-range (obj-c1 table) (+ 1 (obj-c2 table)))])
            (if source-first (list (at g (obj-r1 table) c) (at g (obj-r2 table) c))
                             (list (at g (obj-r2 table) c) (at g (obj-r1 table) c))))
          (for/list ([r (in-range (obj-r1 table) (+ 1 (obj-r2 table)))])
            (if source-first (list (at g r (obj-c1 table)) (at g r (obj-c2 table)))
                             (list (at g r (obj-c2 table)) (at g r (obj-c1 table)))))))
    (define raw-regions
      (if (= connectivity 4) (find-0-regions g bg)
          (map obj-cells (objects-8
            (grid-from-fn (rows g) (cols g) (lambda (r c) (if (= (at g r c) bg) 1 0))) 0))))
    (define enclosed
      (filter (lambda (cells)
                (not (ormap (lambda (p)
                       (or (= (first p) 0) (= (first p) (- (rows g) 1))
                           (= (second p) 0) (= (second p) (- (cols g) 1)))) cells))) raw-regions))
    (define (boundary-colors cells)
      (remove-duplicates
        (apply append
          (for/list ([p cells])
            (for/list ([d cardinal-deltas]
                       #:when (let ([rr (+ (first p) (first d))] [cc (+ (second p) (second d))])
                                (and (in-bounds? rr cc (rows g) (cols g)) (not (= (at g rr cc) bg)))))
              (at g (+ (first p) (first d)) (+ (second p) (second d))))))))
    ;; A: discover each hole's exact cells, enclosing color and occupied area.
    (define records
      (filter (lambda (record) (not (null? record)))
        (for/list ([cells enclosed])
          (define colors (boundary-colors cells))
          (define box (bbox-of-cells cells))
          (if (= (length colors) 1)
              (list cells (first colors)
                    (if (equal? size-measure 'area) (length cells)
                        (* (+ 1 (- (third box) (first box))) (+ 1 (- (fourth box) (second box))))))
              '()))))
    ;; B consumes the region records, selects scope and looks up its fill color.
    (for/fold ([out g]) ([record records])
      (define key (second record))
      (define entry (find-first (lambda (p) (= (first p) key)) mapping))
      (define peers (filter (lambda (p) (= (second p) key)) records))
      (define selected
        (or (equal? fill-scope 'all)
            (= (third record) (apply max (map third peers)))))
      (if (and entry selected)
          (for/fold ([painted out]) ([p (first record)])
            (set-cell painted (first p) (second p) (second entry))) out)))))
