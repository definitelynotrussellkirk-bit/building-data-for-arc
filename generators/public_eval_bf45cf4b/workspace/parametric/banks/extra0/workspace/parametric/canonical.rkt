(rule!
 ;; Infer the modal background. Of the two separated nonbackground objects,
 ;; the monochrome object is the macro mask and the multicolor object is a tile.
 ;; Crop both bounding boxes and substitute a whole tile for each marked mask
 ;; cell, leaving one tile-sized background block at each empty mask cell.
 ;; The alternate policy measures true four-connected background pockets AFTER
 ;; substitution and fills the unique largest enclosed one with the mask color.
 (lambda (g)
  (let ()
   (define output-policy "repeat")
   (define bg (mode g -1))
   (define pieces (objects-multicolor g bg))
   (define (colors o) (remove-duplicates (map (lambda (p) (at g (first p) (second p))) (obj-cells o))))
   (define mask-object (find-first (lambda (o) (= (length (colors o)) 1)) pieces))
   (define tile-object (find-first (lambda (o) (> (length (colors o)) 1)) pieces))
   (if (or (not mask-object) (not tile-object)) g
    (let ()
     (define mask (subgrid g (obj-r1 mask-object) (obj-c1 mask-object) (obj-r2 mask-object) (obj-c2 mask-object)))
     (define tile (subgrid g (obj-r1 tile-object) (obj-c1 tile-object) (obj-r2 tile-object) (obj-c2 tile-object)))
     (define ink (first (colors mask-object)))
     (define mh (rows mask))
     (define mw (cols mask))
     (define th (rows tile))
     (define tw (cols tile))
     (define mosaic
      (grid-from-fn (* mh th) (* mw tw)
       (lambda (r c)
        (if (= (at mask (quotient r th) (quotient c tw)) bg) bg
            (at tile (modulo r th) (modulo c tw))))))
     (define (inner regions height width)
      (filter (lambda (region)
        (for/and ((p region))
         (and (> (first p) 0) (< (first p) (- height 1))
              (> (second p) 0) (< (second p) (- width 1))))) regions))
     (define pockets (inner (find-0-regions mosaic bg) (* mh th) (* mw tw)))
     (define mask-holes (inner (find-0-regions mask bg) mh mw))
     (define selected
      (cond
       ((or (equal? output-policy "repeat") (null? pockets)) '())
       ((equal? output-policy "all_enclosed") (apply append pockets))
       ((equal? output-policy "smallest_enclosed") (pick-min pockets length))
       ((equal? output-policy "first_enclosed") (first pockets))
       ((equal? output-policy "last_enclosed") (last pockets))
       ((equal? output-policy "tile_holes")
        (apply append (filter (lambda (p) (= (length p) (length (find-color tile bg)))) pockets)))
       ((or (equal? output-policy "mask_area") (equal? output-policy "mask_area_last"))
        (if (null? mask-holes) '()
         (let* ((hole (pick-max (if (equal? output-policy "mask_area_last") (reverse mask-holes) mask-holes) length))
                (p (first hole))
                (target (list (* (first p) th) (* (second p) tw)))
                (region (find-first (lambda (q) (member target q)) pockets)))
          (if region region '()))))
       (else (pick-max pockets length))))
     (recolor-cells mosaic selected ink))))))
