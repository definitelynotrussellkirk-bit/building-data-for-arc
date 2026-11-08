(rule!
 ;; Infer the modal background, then discover SAME-COLOR eight-connected objects.
 ;; Measure each object's occupied area. Objects with another object of equal
 ;; area rise to the top; unique-area objects sink to the bottom. Colors, shapes,
 ;; and horizontal coordinates are preserved. Erase before painting, so old
 ;; locations never mask a translated object. Equal-size groups may exceed two.
 ;; Admitted generated scenes have disjoint destination footprints.
 (lambda (g)
  (let ()
    (define match-by 'occupied_area)
    (define connectivity 8)
    (define direction 'normal)
    (define exact-pairs #f)
    (define bg (mode g -1))
    (define components (if (= connectivity 8) (objects-8 g bg) (objects g bg)))
    (define (measure obj)
      (cond [(equal? match-by 'occupied_area) (obj-size obj)]
            [(equal? match-by 'bbox_area) (* (obj-h obj) (obj-w obj))]
            [(equal? match-by 'width) (obj-w obj)]
            [(equal? match-by 'height) (obj-h obj)]
            [(equal? match-by 'bbox_perimeter) (* 2 (+ (obj-h obj) (obj-w obj)))]
            [(equal? match-by 'color) (obj-color obj)]
            [else (error 'measure "unknown matching key")]))
    ;; Step A: input-derived measurements and their multiplicities.
    (define keys (map measure components))
    (define records
      (for/list ([obj components] [key keys])
        (list obj key (length (filter (lambda (x) (= x key)) keys)))))
    ;; Step B consumes those multiplicities to choose a per-object translation.
    (for/fold ([out (empty-grid (rows g) (cols g) bg)]) ([record records])
      (define obj (first record))
      (define repeated (if exact-pairs (= (third record) 2) (> (third record) 1)))
      (define top
        (cond [(equal? direction 'reverse) (not repeated)]
              [(equal? direction 'all_top) #t]
              [(equal? direction 'all_bottom) #f]
              [else repeated]))
      (define dr (if top (- (obj-r1 obj)) (- (rows g) 1 (obj-r2 obj))))
      (for/fold ([painted out]) ([p (obj-cells obj)])
        (set-cell painted (+ (first p) dr) (second p) (obj-color obj)))))))
