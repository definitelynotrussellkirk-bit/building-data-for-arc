(rule!
 ;; Recover two multicolor motifs, including integer-scaled copies. The
 ;; greatest common translated color mask supplies an internal anchor.
 ;; Exchange whole motifs while preserving each recipient's anchor and scale.
 ;; Background is the most frequent color, including zero. Components are
 ;; eight-connected; normalized motif shapes, colors and offsets are inferred
 ;; from this input. Admitted instances have exactly two motifs and disjoint,
 ;; in-bounds replacement footprints. No stored examples or answers are used.
 (lambda (g)
  (let ()
    (define replacement 'swap)
    (define align-bbox #f)
    (define preserve-scale #t)
    (define bg (mode g -1))
    (define components (objects-multicolor g bg))
    (define (component-grid object)
      (grid-from-fn (obj-h object) (obj-w object)
        (lambda (r c)
          (define rr (+ r (obj-r1 object)))
          (define cc (+ c (obj-c1 object)))
          (if (member (list rr cc) (obj-cells object)) (at g rr cc) bg))))
    (define (block-scale image)
      (first
        (filter
          (lambda (s)
            (and (= (modulo (rows image) s) 0) (= (modulo (cols image) s) 0)
                 (for*/and ([r (in-range (rows image))] [c (in-range (cols image))])
                   (= (at image r c)
                      (at image (- r (modulo r s)) (- c (modulo c s)))))))
          (reverse (range 1 (+ 1 (min (rows image) (cols image))))))))
    ;; Each record contains the original component, its scale and primitive grid.
    (define records
      (for/list ([object components])
        (define image (component-grid object))
        (define scale (block-scale image))
        (list object scale
          (grid-from-fn (quotient (rows image) scale) (quotient (cols image) scale)
            (lambda (r c) (at image (* r scale) (* c scale)))))))
    (define templates (remove-duplicates (map third records)))
    (unless (= (length templates) 2)
      (error 'motifs "exactly two primitive motifs are required"))
    (define (color-cells image color)
      (for*/list ([r (in-range (rows image))] [c (in-range (cols image))]
                  #:when (= (at image r c) color))
        (list r c)))
    (define (origin cells)
      (list (apply min (map first cells)) (apply min (map second cells))))
    (define (signature image color)
      (define cells (color-cells image color))
      (if (null? cells) '()
          (let ([start (origin cells)])
            (map (lambda (p) (list (- (first p) (first start))
                                  (- (second p) (second start)))) cells))))
    (define anchors
      (filter
        (lambda (color)
          (and (not (= color bg)) (not (null? (color-cells (first templates) color)))
               (equal? (signature (first templates) color)
                       (signature (second templates) color))))
        (range 10)))
    (when (null? anchors) (error 'motifs "no congruent shared color anchor"))
    (define anchor-color
      (first (sort anchors
        (lambda (a b)
          (define na (length (color-cells (first templates) a)))
          (define nb (length (color-cells (first templates) b)))
          (or (> na nb) (and (= na nb) (< a b)))))))
    (define (anchor image) (origin (color-cells image anchor-color)))
    (define (frequency template)
      (length (filter (lambda (record) (equal? (third record) template)) records)))
    (when (and (equal? replacement 'minority)
               (= (frequency (first templates)) (frequency (second templates))))
      (error 'motifs "minority replacement requires unequal instance counts"))
    (define (donor record)
      (cond [(equal? replacement 'swap)
             (first (filter (lambda (template) (not (equal? template (third record)))) templates))]
            [(equal? replacement 'minority) (pick-min templates frequency)]
            [(equal? replacement 'majority) (pick-max templates frequency)]
            [(equal? replacement 'first) (first templates)]
            [(equal? replacement 'last) (second templates)]
            [else (error 'motifs "unknown replacement policy")]))
    ;; Step B consumes the input-derived motif identity, anchor and scale.
    (define painted-cells
      (apply append
        (for/list ([record records])
          (define object (first record))
          (define scale (if preserve-scale (second record) 1))
          (define source-anchor (anchor (third record)))
          (define target (donor record))
          (define target-anchor (anchor target))
          (define row (+ (obj-r1 object)
                         (if align-bbox 0 (* scale (- (first source-anchor) (first target-anchor))))))
          (define col (+ (obj-c1 object)
                         (if align-bbox 0 (* scale (- (second source-anchor) (second target-anchor))))))
          (for*/list ([r (in-range (rows target))] [c (in-range (cols target))]
                      #:when (not (= (at target r c) bg))
                      [dr (in-range scale)] [dc (in-range scale)])
            (list (+ row (* r scale) dr) (+ col (* c scale) dc) (at target r c))))))
    ;; The canvas fixes the output extent. Samplers admit only nonoverlapping,
    ;; in-bounds motif footprints; projection here is also total for ablations.
    (grid-from-fn (rows g) (cols g)
      (lambda (r c)
        (define hit (find-first (lambda (p) (and (= (first p) r) (= (second p) c))) painted-cells))
        (if hit (third hit) bg))))))
