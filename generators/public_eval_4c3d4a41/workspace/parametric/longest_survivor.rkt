(rule!
 ;; A separate gray comb enters the open left side of an upright gray vessel.
 ;; Align its baseline with the lowest side opening and its teeth with the lanes.
 ;; Each tooth pushes its gray-cap/colored stack upward by the minimum overlap;
 ;; cells pushed above the vessel's top aperture disappear. Erase the source comb.
 ;; Geometry, tooth heights, gaps and colors are read from this input, not stored.
 (lambda (g)
  (let ()
   (define gray (filter (lambda (o) (= (obj-color o) 5)) (objects g 0)))
   (define frame (pick-max gray (lambda (o) (- (fourth (obj-bbox o)) (second (obj-bbox o))))))
   (define fb (obj-bbox frame))
   (define top (first fb))
   (define left (second fb))
   (define bottom (third fb))
   (define comb (pick-max (filter (lambda (o) (< (fourth (obj-bbox o)) left)) gray) obj-size))
   (define cb (obj-bbox comb))
   (define openings (filter (lambda (r) (= (at g r left) 0)) (range (+ top 1) bottom)))
   (define base (apply max openings))
   (define capacity (- base top 1))
   (define count-lanes (+ 1 (quotient (- (fourth cb) (second cb)) 2)))
   ;; A lane record contains its destination column, tooth height and source stack.
   (define lanes
     (for/list ([i (range count-lanes)])
       (let* ([source-col (+ (second cb) (* 2 i))]
              [col (+ left 2 (* 2 i))]
              [tooth (- (count-if (lambda (p) (= (second p) source-col)) (obj-cells comb)) 1)]
              [stack (for/list ([r (range (+ top 1) base)] #:when (not (= (at g r col) 0)))
                       (list r (at g r col)))])
          (list col tooth stack))))
   (define cleared (recolor-cells g (obj-cells comb) 0))
   (define pushed
     (for/fold ([out cleared]) ([lane lanes])
       (let* ([col (first lane)] [tooth (second lane)] [stack (third lane)]
              [gap (- capacity (length stack))]
              [shift (max 0 (- tooth gap))]
              [empty (recolor-cells out (for/list ([r (range (+ top 1) base)]) (list r col)) 0)]
              [moved (for/fold ([a empty]) ([rv stack])
                       (let ([rr (- (first rv) shift)])
                         (if (> rr top) (set-cell a rr col (second rv)) a)))])
         (recolor-cells moved (for/list ([r (range (- base tooth) (+ base 1))]) (list r col)) 5))))
   (define intermediate
     (recolor-cells pushed
       (for/list ([c (range (+ left 2) (+ left 1 (* 2 count-lanes)))]) (list base c)) 5))
   ;; Stage B sees the surviving colors AFTER the geometric push and clipping.
   (define groups
     (for/list ([lane lanes])
       (for/list ([r (range (+ top 1) base)]
                  #:when (and (not (= (at intermediate r (first lane)) 0))
                              (not (= (at intermediate r (first lane)) 5))))
         (list r (first lane)))))
   (recolor-cells intermediate (pick-max groups length) 1))))
