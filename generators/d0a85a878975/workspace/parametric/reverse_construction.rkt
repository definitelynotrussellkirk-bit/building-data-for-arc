(rule!
 ;; Solid squares are TALLY marks: each size s (2+) appears some number
 ;; of times, one color per size. Redraw the tally as corner-nested
 ;; glyphs: every glyph shows the sizes still active that round stacked
 ;; in one corner (smallest on top), emitted round-robin until all
 ;; counts run dry, each glyph followed by a blank spacer column. If
 ;; the smallest size outnumbers the runner-up, one of its tallies is
 ;; dropped (that square doubles as the size key).
 (lambda (g)
   (let ()
     (define bg (mode g -1))
     (define squares  ;; (size color) per solid square, size >= 2
       (filter (lambda (x) x)
               (map (lambda (o)
                      (and (>= (obj-h o) 2)
                           (= (obj-h o) (obj-w o))
                           (= (obj-size o) (* (obj-h o) (obj-w o)))
                           (list (obj-h o) (obj-color o))))
                    (objects g bg))))
     (define sizes (sort (remove-duplicates (map first squares)) <))
     (define (color-of s)
       (second (find (lambda (sq) (= (first sq) s)) squares)))
     (define counts
       (let ((raw (map (lambda (s)
                         (count-if (lambda (sq) (= (first sq) s))
                                   squares))
                       sizes)))
         (if (and (>= (length sizes) 2) (> (first raw) (second raw)))
             (cons (- (first raw) 1) (rest raw))
             raw)))
     (define construction-blocks  ;; input-derived active-size count layers
       (let loop ((pairs (zip-lists sizes counts)) (acc (list)))
         (if (null? pairs)
             acc
             (let ((m (min-list (map second pairs))))
               (loop (filter (lambda (p) (> (second p) 0))
                             (map (lambda (p) (list (first p)
                                                    (- (second p) m)))
                                  pairs))
                     (append acc (make-list m (map first pairs))))))))
     (define blocks (reverse construction-blocks))
     (define out-h (+ (max-list sizes) 1))
     (define (glyph-w blk) (+ 1 (max-list blk)))
     (let loop ((bs blocks) (col 0)
                (out (empty-grid out-h
                                 (apply + (map glyph-w blocks))
                                 bg)))
       (if (null? bs)
           out
           (loop (rest bs) (+ col (glyph-w (first bs)))
                 (for*/fold ((acc out))
                            ((r (range 0 out-h))
                             (c (range 0 (glyph-w (first bs)))))
                   (let ((cover (filter (lambda (s)
                                          (>= s (+ 1 (max r c))))
                                        (first bs))))
                     (if (null? cover)
                         acc
                         (set-cell acc r (+ col c)
                                   (color-of (min-list cover))))))))))))