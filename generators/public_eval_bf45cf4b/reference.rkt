(rule!
 ;; The monochrome object is a stencil; the multicolor object is a tile.
 ;; Infer the background by frequency and segment all foreground with 8-neighbors.
 ;; Crop both roles tightly. An occupied stencil cell expands into one unchanged
 ;; tile, and an empty stencil cell expands into an equally sized background block.
 ;; The alternate family restricts the stencil to its largest 4-connected region,
 ;; breaking ties by reading order without shrinking the original stencil box.
 (lambda (g)
  (let ()
   (define selection "all")
   (define rival "")
   (define bg (mode g -1))
   (define groups (objects-multicolor g bg))
   (define (mono? o)
    (= (length (remove-duplicates
      (map (lambda (p) (at g (first p) (second p))) (obj-cells o)))) 1))
   (define mo (first (filter mono? groups)))
   (define to (first (filter (lambda (o) (not (mono? o))) groups)))
   (define mask (subgrid g (obj-r1 mo) (obj-c1 mo) (obj-r2 mo) (obj-c2 mo)))
   (define source-tile (subgrid g (obj-r1 to) (obj-c1 to) (obj-r2 to) (obj-c2 to)))
   (define regions (objects mask bg))
   (define effective (if (equal? rival "other_setting")
     (if (equal? selection "all") "largest" "all") selection))
   (define raw-active
    (cond
     [(equal? rival "first_component") (obj-cells (first regions))]
     [(equal? rival "last_component") (obj-cells (last regions))]
     [(equal? rival "smallest_component") (obj-cells (pick-min regions obj-size))]
     [(equal? effective "largest") (obj-cells (pick-max regions obj-size))]
     [else (filter (lambda (p) (not (= (at mask (first p) (second p)) bg))) (grid-positions mask))]))
   (define active
    (cond
     [(equal? rival "fill_stencil_box") (grid-positions mask)]
     [(equal? rival "flip_stencil")
      (map (lambda (p) (list (first p) (- (cols mask) 1 (second p)))) raw-active)]
     [else raw-active]))
   (define tile
    (cond
     [(equal? rival "transpose_tile") (transpose source-tile)]
     [(equal? rival "flip_tile") (flip-lr source-tile)]
     [(equal? rival "flat_tile")
      (empty-grid (rows source-tile) (cols source-tile) (first (grid-colors source-tile bg)))]
     [else source-tile]))
   (for/list ([r (in-range (* (rows mask) (rows tile)))])
    (for/list ([c (in-range (* (cols mask) (cols tile)))])
     (if (member (list (quotient r (rows tile)) (quotient c (cols tile))) active)
      (at tile (modulo r (rows tile)) (modulo c (cols tile))) bg))))))
