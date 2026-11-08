(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define comps (objects-multicolor g 0))
             (define singles (filter (lambda (o) (= (obj-size o) 1)) comps))
             (define sources
               (filter (lambda (o)
                         (and
                           (> (obj-size o) 1)
                           (> (length (unique (map (lambda (p) (at g (fst p) (snd p)))
                                                   (obj-cells o))))
                              1)))
                       comps))
             (define (contains-cell? cells p)
               (not (empty? (filter (lambda (q)
                                      (and (= (fst q) (fst p)) (= (snd q) (snd p))))
                                    cells))))
             (reduce (lambda (acc src)
                       (let* ((cells (obj-cells src))
                              (colors (unique (map (lambda (p) (at g (fst p) (snd p)))
                                                   cells))))
                         (reduce (lambda (acc2 anchor-color)
                                   (let ((anchors (filter (lambda (p)
                                                            (= (at g (fst p) (snd p))
                                                               anchor-color))
                                                          cells))
                                         (targets (filter (lambda (o)
                                                            (= (at g
                                                                   (fst (fst (obj-cells o)))
                                                                   (snd (fst (obj-cells o))))
                                                               anchor-color))
                                                          singles)))
                                     (if (!= (length anchors) 1)
                                         acc2
                                         (let ((anchor (fst anchors)))
                                           (reduce (lambda (a target-obj)
                                                     (let ((target (fst (obj-cells target-obj))))
                                                       (if (contains-cell? cells target)
                                                           a
                                                           (reduce (lambda (aa cell)
                                                                     (let* ((v (at g
                                                                                   (fst cell)
                                                                                   (snd cell)))
                                                                            (dr (- (fst cell)
                                                                                   (fst anchor)))
                                                                            (dc (- (snd cell)
                                                                                   (snd anchor)))
                                                                            (nr (+ (fst target)
                                                                                   dr))
                                                                            (nc (+ (snd target)
                                                                                   (if (!= anchor-color
                                                                                          2)
                                                                                       (- dc)
                                                                                       dc))))
                                                                       (if (and
                                                                             (not (and
                                                                                    (zero? dr)
                                                                                    (zero? dc)))
                                                                             (in-bounds? nr
                                                                                         nc
                                                                                         (rows g)
                                                                                         (cols g)))
                                                                           (set-cell aa
                                                                                     nr
                                                                                     nc
                                                                                     v)
                                                                           aa)))
                                                                   a
                                                                   cells))))
                                                   acc2
                                                   targets)))))
                                 acc
                                 (range 1 10))))
                     g
                     sources)))))