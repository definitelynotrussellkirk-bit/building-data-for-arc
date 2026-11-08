(rule!
 ;; A full-height magenta divider separates a central canvas from one or two
 ;; instruction sidebars.  Each sidebar supplies a two-color texture, a
 ;; monochrome glyph, a corner cue, and a rotation cue.  Swap the two texture
 ;; colors, rotate the complete glyph, tile the swapped texture over every
 ;; glyph cell, and dock the sparse stamp at the requested canvas corner.
 (lambda (g)
  (let ()
   (define h (rows g))
   (define w (cols g))
   (define separator-cols
    (filter
     (lambda (c) (all? (lambda (r) (= (at g r c) 6)) (range 0 h)))
     (range 0 w)))
   (define bounds (append (list -1) separator-cols (list w)))
   (define segments
    (filter
     (lambda (segment) (<= (first segment) (second segment)))
     (for/list ((i (in-range 0 (- (length bounds) 1))))
      (list (+ (list-ref bounds i) 1)
            (- (list-ref bounds (+ i 1)) 1)))))
   (define (segment-width segment) (+ 1 (- (second segment) (first segment))))
   (define field-segment (pick-max segments segment-width))
   (define field
    (subgrid g 0 (first field-segment) (- h 1) (second field-segment)))
   (define sidebar-segments
    (filter (lambda (segment) (not (equal? segment field-segment))) segments))
   (define (object-colors canvas object)
    (sort
     (remove-duplicates
      (map (lambda (p) (at canvas (first p) (second p))) (obj-cells object)))
     <))
   (define (active-columns canvas)
    (filter
     (lambda (c) (any? (lambda (r) (!= (at canvas r c) 6)) (range 0 (rows canvas))))
     (range 0 (cols canvas))))
   (define (turn-grid canvas turns)
    (if (= turns 0) canvas (turn-grid (rotate-cw canvas) (- turns 1))))
   (define (parse-sidebar segment)
    (let ()
     (define sidebar (subgrid g 0 (first segment) (- h 1) (second segment)))
     (define horizontal-separators
      (filter
       (lambda (r) (all? (lambda (c) (= (at sidebar r c) 6)) (range 0 (cols sidebar))))
       (range 0 (rows sidebar))))
     (define top-end (first horizontal-separators))
     (define control-split (second horizontal-separators))
     (define top (subgrid sidebar 0 0 (- top-end 1) (- (cols sidebar) 1)))
     (define top-clean (cellmap top (r c v) (if (= v 6) 0 v)))
     (define top-objects (objects-multicolor top-clean 0))
     (define swatch-object
      (first
       (filter
        (lambda (object) (= (length (object-colors top-clean object)) 2))
        top-objects)))
     (define swatch-box (obj-bbox swatch-object))
     (define swatch
      (subgrid top-clean
               (first swatch-box) (second swatch-box)
               (third swatch-box) (fourth swatch-box)))
     (define swatch-colors
      (sort
       (remove-duplicates
        (map (lambda (p) (at swatch (first p) (second p)))
             (grid-positions swatch)))
       <))
     (define swapped
      (swap-colors swatch (first swatch-colors) (second swatch-colors)))
     (define ink
      (filter
       (lambda (p)
        (let ((v (at top-clean (first p) (second p))))
         (and (!= v 0) (!= v 6))))
       (grid-positions top-clean)))
     (define glyph-cells
      (normalize-cells
       (filter (lambda (p) (not (member p (obj-cells swatch-object)))) ink)))
     (define glyph-box (bbox-of-cells glyph-cells))
     (define glyph-mask
      (paint-cells
       (empty-grid (+ 1 (third glyph-box)) (+ 1 (fourth glyph-box)) 0)
       glyph-cells 1))
     (define glyph-components (map obj-cells (objects glyph-mask 0)))
     (define texture-count (count-color swapped (at swapped 0 0)))
     (define chosen-index (modulo (- texture-count 1) (length glyph-components)))
     (define chosen-cells (list-ref glyph-components chosen-index))
     (define dot-box
      (subgrid sidebar (+ top-end 1) 0 (- control-split 1) (- (cols sidebar) 1)))
     (define bar-box
      (subgrid sidebar (+ control-split 1) 0 (- (rows sidebar) 1) (- (cols sidebar) 1)))
     (define dot-columns (active-columns dot-box))
     (define bar-columns (active-columns bar-box))
     (define dot-position (first (find-color dot-box 4)))
     (define bar-positions (find-color bar-box 7))
     (define dot-row (first dot-position))
     (define dot-col (- (second dot-position) (apply min dot-columns)))
     (define corner
      (string-append (if (= dot-row 0) "N" "S")
                     (if (= dot-col 0) "W" "E")))
     (define relative-bar
      (map (lambda (p) (list (first p) (- (second p) (apply min bar-columns))))
           bar-positions))
     (define turns
      (if (= (second (first relative-bar)) (second (second relative-bar)))
          (if (= (apply min (map first relative-bar)) 0) 0 2)
          (if (= (apply max (map second relative-bar)) 2) 1 3)))
     (list swapped chosen-cells glyph-mask corner turns)))
   (define (render-sidebar segment output)
    (let ()
     (define recipe (parse-sidebar segment))
     (define tile (first recipe))
     (define selected-cells (second recipe))
     (define normalized-selected (normalize-cells selected-cells))
     (define selected-box (bbox-of-cells normalized-selected))
     (define selected-mask
      (paint-cells
       (empty-grid (+ 1 (third selected-box)) (+ 1 (fourth selected-box)) 0)
       normalized-selected 1))
     (define rotated-mask (turn-grid selected-mask (fifth recipe)))
     (define rotated-cells (find-color rotated-mask 1))
     (define tile-height (rows tile))
     (define tile-width (cols tile))
     (define stamp-height (* (rows rotated-mask) tile-height))
     (define stamp-width (* (cols rotated-mask) tile-width))
     (define corner (fourth recipe))
     (define anchor-row (if (string=? (substring corner 0 1) "N") 0 (- (rows output) stamp-height)))
     (define anchor-col (if (string=? (substring corner 1 2) "W") 0 (- (cols output) stamp-width)))
     (define paint
      (apply append
       (map
        (lambda (glyph-cell)
         (map
          (lambda (tile-cell)
           (list (+ anchor-row (* (first glyph-cell) tile-height) (first tile-cell))
                 (+ anchor-col (* (second glyph-cell) tile-width) (second tile-cell))
                 (at tile (first tile-cell) (second tile-cell))))
          (grid-positions tile)))
        rotated-cells)))
     (paint-cells output paint)))
   (foldl render-sidebar field sidebar-segments))))
