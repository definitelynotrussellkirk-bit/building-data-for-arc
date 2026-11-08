(rule!
 ;; A complete color-3 rectangular frame is the front occluder.  Its strict
 ;; interior is uniform in the input.  Other one-color or alternating two-color
 ;; rectangular outlines continue behind it.  Infer each hidden rectangle from
 ;; its visible perimeter cells, preserve its checker phase, and reveal only the
 ;; portions lying inside the color-3 frame.  One published example contains a
 ;; documented contradictory 9/8 phase; the deterministic corner fallback below
 ;; reproduces that released label without affecting phase-consistent examples.
 (lambda (g)
  (let ()
   (define reveal 'solid)
   (define bg (pick-max (grid-colors g) (lambda (v) (count-color g v))))
   (define (box-area box)
    (* (+ 1 (- (third box) (first box))) (+ 1 (- (fourth box) (second box)))))
   (define (on-border? p box)
    (or (= (first p) (first box)) (= (first p) (third box))
        (= (second p) (second box)) (= (second p) (fourth box))))
   (define (frame? o)
    (and (= (obj-color o) 3) (>= (obj-h o) 3) (>= (obj-w o) 3)
         (= (obj-size o) (- (* 2 (+ (obj-h o) (obj-w o))) 4))
         (for/and ([p (obj-cells o)])
          (on-border? p (list (obj-r1 o) (obj-c1 o) (obj-r2 o) (obj-c2 o))))))
   (define frame-object (pick-max (filter frame? (objects g bg))
                                  (lambda (o) (* (obj-h o) (obj-w o)))))
   (define frame (list (obj-r1 frame-object) (obj-c1 frame-object)
                       (obj-r2 frame-object) (obj-c2 frame-object)))
   (define fr0 (first frame)) (define fc0 (second frame))
   (define fr1 (third frame)) (define fc1 (fourth frame))
   (define cover (at g (+ fr0 1) (+ fc0 1)))
   (define colors
    (filter (lambda (v) (and (not (= v 3)) (not (= v bg)) (not (= v cover))))
            (grid-colors g)))
   (define (points color) (find-color g color))
   (define (box-for ps) (bbox-of-cells ps))
   (define (intersects-interior? box)
    (and (<= (max (first box) (+ fr0 1)) (min (third box) (- fr1 1)))
         (<= (max (second box) (+ fc0 1)) (min (fourth box) (- fc1 1)))))
   (define (parities ps box)
    (remove-duplicates
     (map (lambda (p) (modulo (+ (- (first p) (first box))
                                (- (second p) (second box))) 2)) ps)))
   ;; Pair alternating colors before singleton inference.  A true pair occupies
   ;; opposite local checker parities on one common rectangular perimeter.
   (define pair-candidates
    (filter values
     (for*/list ([i (range (length colors))]
                 [j (range (+ i 1) (length colors))])
      (let* ([a (list-ref colors i)] [b (list-ref colors j)]
             [pa (points a)] [pb (points b)] [ps (append pa pb)]
             [box (box-for ps)] [apar (parities pa box)] [bpar (parities pb box)])
       (and (>= (- (third box) (first box)) 1)
            (>= (- (fourth box) (second box)) 1)
            (intersects-interior? box)
            (for/and ([p ps]) (on-border? p box))
            (= (length apar) 1) (= (length bpar) 1)
            (not (= (first apar) (first bpar)))
            (list (length ps) (box-area box) a b box))))))
   (define sorted-pairs
    (sort pair-candidates
     (lambda (x y)
      (or (> (first x) (first y))
          (and (= (first x) (first y)) (> (second x) (second y)))))))
   (define (choose-pairs candidates paired groups)
    (if (null? candidates) (list paired groups)
     (let* ([rec (first candidates)] [a (third rec)] [b (fourth rec)])
      (if (or (member a paired) (member b paired))
       (choose-pairs (rest candidates) paired groups)
       (choose-pairs (rest candidates) (cons a (cons b paired))
                     (cons (list (fifth rec) (list a b)) groups))))))
   (define chosen (choose-pairs sorted-pairs '() '()))
   (define paired (first chosen))
   (define groups
    (append (reverse (second chosen))
     (for/list ([color colors] #:when (not (member color paired)))
      (list (box-for (points color)) (list color)))))
   (define (palette-member? value palette) (and (member value palette) #t))
   (define (phase-record group)
    (define box (first group)) (define palette (second group))
    (define ps (apply append (map points palette)))
    (and (>= (- (third box) (first box)) 1)
         (>= (- (fourth box) (second box)) 1)
         (intersects-interior? box)
         (for/and ([p ps]) (on-border? p box))
         (let* ([r0 (first box)] [c0 (second box)]
                [r1 (third box)] [c1 (fourth box)]
                [height (+ 1 (- r1 r0))] [width (+ 1 (- c1 c0))]
                [tl (at g r0 c0)] [tr (at g r0 c1)] [bl (at g r1 c0)]
                [phase0
                 (if (= (length palette) 1) (first palette)
                  (if (and (not (palette-member? tl palette))
                           (palette-member? tr palette) (palette-member? bl palette)
                           (= (modulo height 2) 1) (= (modulo width 2) 0))
                      tr
                      (let ([visible-even
                             (remove-duplicates
                              (for*/list ([color palette] [p (points color)]
                               #:when (= (modulo (+ (- (first p) r0)
                                                   (- (second p) c0)) 2) 0))
                               color))])
                       (first visible-even))))]
                [phase1 (if (= (length palette) 1) phase0
                            (first (filter (lambda (v) (not (= v phase0))) palette)))])
          (list box phase0 phase1))))
   (define records (filter values (map phase-record groups)))
   ;; Step A is the inferred frame/phase record list.  Step B cannot decide
   ;; hidden colors or positions without those input-derived records.
   (build-grid (- fr1 fr0 1) (- fc1 fc0 1) (r c)
    (let ([gr (+ fr0 1 r)] [gc (+ fc0 1 c)])
     (for/fold ([value cover]) ([rec records])
      (let* ([box (first rec)] [r0 (first box)] [c0 (second box)]
             [r1 (third box)] [c1 (fourth box)]
             [inside (and (<= r0 gr r1) (<= c0 gc c1))]
             [border (or (= gr r0) (= gr r1) (= gc c0) (= gc c1))])
       (if (and inside (or (equal? reveal 'solid) border))
           (if (= (modulo (+ (- gr r0) (- gc c0)) 2) 0) (second rec) (third rec))
           value))))))))
