(rule!
 ;; A separator lattice contains a majority normal tile and a minority special
 ;; tile. The special tile's one novel color encodes a small occupancy mask.
 ;; Find the unique translation of that mask on the macro tile grid containing
 ;; every observed special tile, then fill its missing positions with exact
 ;; special-tile copies. Separator thickness and palette are not hardcoded.
 ;; The fill-holes alternative first completes the macro copy, then fills its
 ;; four-connected enclosed background components. The fill-before ablation
 ;; measures those cavities on the incomplete arrangement instead.
 (lambda (g)
   (let ()
     (define completion-policy "complete")
     (define separator (at g 0 0))
     (define (row-line r) (for/and ((c (range w))) (= (at g r c) separator)))
     (define (col-line c) (for/and ((r (range h))) (= (at g r c) separator)))
     (define (row-end r) (if (and (< r h) (not (row-line r))) (row-end (+ r 1)) r))
     (define (col-end c) (if (and (< c w) (not (col-line c))) (col-end (+ c 1)) c))
     (define row-runs
       (for/list ((r (range h)) #:when (and (not (row-line r)) (or (= r 0) (row-line (- r 1)))))
         (range r (row-end r))))
     (define col-runs
       (for/list ((c (range w)) #:when (and (not (col-line c)) (or (= c 0) (col-line (- c 1)))))
         (range c (col-end c))))
     (define macro-h (length row-runs))
     (define macro-w (length col-runs))
     (define tile-h (length (first row-runs)))
     (define tile-w (length (first col-runs)))
     (define tiles
       (for*/list ((r (range macro-h)) (c (range macro-w)))
         (let ((rr (list-ref row-runs r)) (cc (list-ref col-runs c)))
           (list r c (subgrid g (first rr) (first cc) (last rr) (last cc))))))
     (define kinds (remove-duplicates (map third tiles)))
     (define normal
       (pick-max kinds (lambda (tile) (length (filter (lambda (p) (equal? (third p) tile)) tiles)))))
     (define special (first (filter (lambda (tile) (not (equal? tile normal))) kinds)))
     (define foreground
       (first (filter (lambda (v) (and (not (= v separator)) (not (member v (grid-colors normal)))))
                      (grid-colors special))))
     (define mask (find-color special foreground))
     (define observed (map (lambda (p) (list (first p) (second p)))
                           (filter (lambda (p) (equal? (third p) special)) tiles)))
     (define (shifted r c)
       (map (lambda (p) (list (+ r (first p)) (+ c (second p)))) mask))
     (define placements
       (for*/list ((r (range (+ 1 (- macro-h tile-h)))) (c (range (+ 1 (- macro-w tile-w))))
                   #:when (for/and ((p observed)) (member p (shifted r c))))
         (list r c)))
     (define anchor (first placements))
     (define target (shifted (first anchor) (second anchor)))
     (define (cavities occupied)
       (let* ((binary (grid-from-fn macro-h macro-w
                         (lambda (r c) (if (member (list r c) occupied) 1 0))))
              (inside (filter (lambda (o) (and (> (obj-r1 o) 0) (> (obj-c1 o) 0)
                                               (< (obj-r2 o) (- macro-h 1)) (< (obj-c2 o) (- macro-w 1))))
                              (objects binary 1))))
         (apply append (map obj-cells inside))))
     (define extra
       (cond ((equal? completion-policy "fill_holes") (cavities target))
             ((equal? completion-policy "fill_before") (cavities observed))
             (else '())))
     (for/fold ((out g)) ((p (remove-duplicates (append target extra))))
       (let ((rr (list-ref row-runs (first p))) (cc (list-ref col-runs (second p))))
         (for*/fold ((acc out)) ((r (range tile-h)) (c (range tile-w)))
           (set-cell acc (list-ref rr r) (list-ref cc c) (at special r c))))))))
