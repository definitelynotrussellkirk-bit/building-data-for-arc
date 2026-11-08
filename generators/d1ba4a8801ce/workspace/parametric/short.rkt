(rule!
 ;; A checkerboard background is disturbed by a FRAME (the most common
 ;; off-pattern color) and loose content blocks. Restore the
 ;; checkerboard, redraw the frame outline empty, and re-shelve the
 ;; blocks inside it: stacked along the frame's long axis with 1-cell
 ;; gaps (the group centered), each block centered on the cross axis.
 (lambda (g)
   (let ()
     (define bg-even (at g 0 0))
     (define bg-odd (at g 1 1))
     (define (expected r c)
       (if (and (= 1 (modulo r 2)) (= 1 (modulo c 2))) bg-odd bg-even))
     (define disruptions  ;; (r c v) cells breaking the checkerboard
       (fold-cells g (list)
                   (lambda (acc r c v)
                     (if (= v (expected r c))
                         acc
                         (append acc (list (list r c v)))))))
     (define (cells-of col)
       (filter (lambda (cell) (= (third cell) col)) disruptions))
     (define by-count  ;; disruption colors, most frequent first
       (sort-by (unique (map third disruptions))
                (lambda (col) (- 0 (length (cells-of col))))))
     (define frame-color (first by-count))
     (define fbb (bbox-of-cells (cells-of frame-color)))
     (define fr1 (first fbb)) (define fc1 (second fbb))
     (define fr2 (third fbb)) (define fc2 (fourth fbb))
     (define horizontal (< (- fc2 fc1) (- fr2 fr1)))
     (define contents  ;; (color r1 c1 h w) in shelf order
       (sort-by (map (lambda (col)
                       (let ((bb (bbox-of-cells (cells-of col))))
                         (list col (first bb) (second bb)
                               (+ 1 (- (third bb) (first bb)))
                               (+ 1 (- (fourth bb) (second bb))))))
                     (rest by-count))
                (lambda (c) (nth c (if horizontal 2 1)))))
     (define base  ;; clean board + hollow frame
       (paint-cells (erase-cells (grid-from-fn h w expected)
                                 (positions-in-rect (+ fr1 1) (+ fc1 1)
                                                    (- fr2 1) (- fc2 1))
                                 bg-even)
                    (filter (lambda (p) (or (= (first p) fr1)
                                            (= (first p) fr2)
                                            (= (second p) fc1)
                                            (= (second p) fc2)))
                            (positions-in-rect fr1 fc1 fr2 fc2))
                    frame-color))
     (define ir1 (+ fr1 1))
     (define ic1 (+ fc1 1))
     (define ih (- fr2 fr1 1))
     (define iw (- fc2 fc1 1))
     (define start  ;; centered group start along the long axis
       (+ (if horizontal ic1 ir1)
          (quotient (- (if horizontal iw ih)
                       (+ (apply + (map (lambda (c)
                                          (nth c (if horizontal 4 3)))
                                        contents))
                          (- (length contents) 1)))
                    2)))
     (let loop ((cs contents) (cur start) (grid base))
       (if (null? cs)
           grid
           (let* ((blk (first cs))
                  (bh (nth blk 3))
                  (bw (nth blk 4))
                  (r0 (if horizontal (+ ir1 (quotient (- ih bh) 2)) cur))
                  (c0 (if horizontal cur (+ ic1 (quotient (- iw bw) 2)))))
             (loop (rest cs)
                   (+ cur (if horizontal bw bh) 1)
                   (paint-cells grid
                                (positions-in-rect r0 c0 (+ r0 bh -1)
                                                   (+ c0 bw -1))
                                (first blk)))))))))