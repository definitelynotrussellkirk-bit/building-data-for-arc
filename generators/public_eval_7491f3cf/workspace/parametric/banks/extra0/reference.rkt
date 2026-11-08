(rule!
 ;; Four framed panels: divider and isolated marker, two source patterns, blank.
 ;; Separate the long 8-connected divider from its singleton marker. Four-neighbor
 ;; reachability locates the marked region. Source one supplies that region and
 ;; source two supplies the other. Both can paint the divider; first-source ink
 ;; wins overlap, but its background never erases second-source ink. Keep framing.
 (lambda (g)
  (let ()
   (define marker-first #t)
   (define frame (at g 0 0))
   (define active-rows (filter (lambda (r) (not (and (row-uniform? g r) (= (at g r 0) frame)))) (range (rows g))))
   (define top (first active-rows))
   (define bottom (last active-rows))
   (define separators (filter (lambda (c) (and (col-uniform? g c) (= (at g 0 c) frame))) (range (cols g))))
   (define starts (filter (lambda (c) (and (not (member c separators)) (or (= c 0) (member (- c 1) separators)))) (range (cols g))))
   (define width (- (find-first (lambda (c) (> c (first starts))) separators) (first starts)))
   (define height (+ 1 (- bottom top)))
   (define (panel n) (subgrid g top (list-ref starts n) bottom (+ (list-ref starts n) width -1)))
   (define selector (panel 0))
   (define source-a (panel 1))
   (define source-b (panel 2))
   (define bg (at (panel 3) 0 0))
   (define pieces (objects-8 selector bg))
   (define barrier (obj-cells (pick-max pieces obj-size)))
   (define marker (first (obj-cells (pick-min pieces obj-size))))
   (define region (connected-region selector (first marker) (second marker)
                    (lambda (r c v) (not (member (list r c) barrier))) 4))
   (define (selected? p) (if marker-first (member p region) (and (not (member p region)) (not (member p barrier)))))
   (define result
    (build-grid height width (r c)
     (let* ((p (list r c)) (on (member p barrier))
            (x (if (or on (selected? p)) (at source-a r c) bg))
            (y (if (or on (and (not on) (not (selected? p)))) (at source-b r c) bg)))
      (if (not (= x bg)) x y))))
   (paste g result top (fourth starts)))))
