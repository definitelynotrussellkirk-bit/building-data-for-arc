(rule!
 (let ()
   ;; Red line markers are mirror axes; a single red cell is a half-turn
   ;; center. Sources belong to their local 8-connected multicolor group,
   ;; NOT to all objects of the same color. Preserve all observed cells.
   (define turn-lines #f)
   (define bg (mode g -1))
   (define groups (objects-multicolor g bg))
   (for/fold ([out g]) ([obj groups])
     (define reds (filter (lambda (p) (= (at g (first p) (second p)) 2)) (obj-cells obj)))
     (define source (filter (lambda (p) (not (= (at g (first p) (second p)) 2))) (obj-cells obj)))
     (if (or (null? reds) (null? source)) out
         (let* ([box (bbox-of-cells reds)]
                [r0 (first box)] [c0 (second box)] [r1 (third box)] [c1 (fourth box)]
                [point (= (length reds) 1)]
                [horizontal (= r0 r1)]
                [center-r (+ r0 r1)] [center-c (+ c0 c1)])
           ;; A has recovered source cells and marker geometry/midpoint.
           ;; B consumes that geometry to place the newly copied source.
           (for/fold ([result out]) ([p source])
             (define r (first p))
             (define c (second p))
             (define rr (if (or turn-lines point horizontal) (- center-r r) r))
             (define cc (if (or turn-lines point (not horizontal)) (- center-c c) c))
             (if (and (in-bounds? rr cc h w) (= (at g rr cc) bg))
                 (set-cell result rr cc (at g r c)) result)))))))
