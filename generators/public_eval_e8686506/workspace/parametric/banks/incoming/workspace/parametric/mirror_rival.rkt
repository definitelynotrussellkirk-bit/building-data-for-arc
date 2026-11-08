(rule!
 ;; The most frequent color is background. Monochromatic 8-connected objects
 ;; of maximum size jointly form the target skeleton, even across colors.
 ;; Crop their union and translate every other object into its missing cells.
 ;; Pieces keep their orientation and are each used exactly once.
 ;; Identical-color/shape copies are interchangeable; generated lessons have
 ;; one colored filling. Outside that domain, choose the first exact cover.
 (lambda (g)
  (let ()
   (define bg (mode g -1))
   (define obs (objects-8 g bg))
   (if (null? obs) g
    (let ()
     (define largest (apply max (map obj-size obs)))
     (define frames (filter (lambda (o) (= (obj-size o) largest)) obs))
     (define loose (filter (lambda (o) (not (= (obj-size o) largest))) obs))
     (define box (bbox-of-cells (apply append (map obj-cells frames))))
     (define r0 (first box))
     (define c0 (second box))
     (define nh (+ 1 (- (third box) r0)))
     (define nw (+ 1 (- (fourth box) c0)))
     (define walls (apply append
       (for/list ([o frames])
         (for/list ([p (obj-cells o)])
           (list (- (first p) r0) (- (second p) c0) (obj-color o))))))
     (define mask (map (lambda (p) (list (first p) (second p))) walls))
     (define target (paint-cells (build-grid nh nw (r c) bg) walls))
     (define pieces (for/list ([i (range (length loose))])
       (let ([o (list-ref loose i)])
         (list i (obj-color o) (sort (normalize-cells (obj-cells o)) cell<)))))
     (define empty (filter (lambda (p) (not (member p mask))) (grid-positions target)))
     (define (search rem free placed)
       (if (null? free)
           (if (null? rem) placed #f)
           (let ([q (first free)])
             (let try ([todo rem] [seen '()])
               (if (null? todo) #f
                   (let* ([piece (first todo)]
                          [key (list (second piece) (third piece))])
                     (if (member key seen)
                         (try (rest todo) seen)
                         (or
                           (for/or ([anchor (third piece)])
                             (let* ([dr (- (first q) (first anchor))]
                                    [dc (- (second q) (second anchor))]
                                    [cells (map (lambda (p) (list (+ (first p) dr) (+ (second p) dc))) (third piece))])
                               (and (andmap (lambda (p) (member p free)) cells)
                                    (search (filter (lambda (p) (not (= (first p) (first piece)))) rem)
                                      (filter (lambda (p) (not (member p cells))) free)
                                      (cons (list (first piece) (second piece) cells) placed)))))
                           (try (rest todo) (cons key seen))))))))))
     (define packed (and (= (length empty) (apply + (map (lambda (p) (length (third p))) pieces)))
                         (search pieces empty '())))
     (define complete (if packed
       (for/fold ([out target]) ([p packed]) (recolor-cells out (third p) (second p))) target))
     (flip-lr complete))))))
