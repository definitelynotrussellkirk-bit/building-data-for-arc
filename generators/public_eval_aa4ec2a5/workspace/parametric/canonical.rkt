(rule!
 (let* ((hole-connectivity 4)
        (bg (mode g -1))
        (pieces (objects g bg))
        (cavities
          (lambda (cells)
            (let* ((box (bbox-of-cells cells))
                   (r0 (first box)) (c0 (second box))
                   (h (+ 1 (- (third box) r0))) (w (+ 1 (- (fourth box) c0)))
                   (mask (grid-from-fn h w
                           (lambda (r c) (if (member? (list (+ r r0) (+ c c0)) cells) 1 0))))
                   (regions ((if (= hole-connectivity 4) objects objects-8) mask 1))
                   (closed (filter
                             (lambda (o)
                               (andmap (lambda (p) (and (< 0 (first p) (- h 1))
                                                       (< 0 (second p) (- w 1))))
                                       (obj-cells o))) regions)))
              (map (lambda (p) (list (+ r0 (first p)) (+ c0 (second p))))
                   (apply append (map obj-cells closed))))))
        (classified (map (lambda (o) (let ((cells (obj-cells o)))
                                      (list cells (cavities cells)))) pieces))
        (holes (apply append (map second classified)))
        (holed-cells (apply append (map first
                        (filter (lambda (record) (not (empty? (second record)))) classified))))
        (support (append (apply append (map first classified)) holes))
        (rim (remove-duplicates
               (apply append
                 (map (lambda (p)
                        (for*/list ((dr (in-range -1 2)) (dc (in-range -1 2)))
                          (list (+ (first p) dr) (+ (second p) dc)))) support)))))
   (grid-from-fn (rows g) (cols g)
     (lambda (r c)
       (let ((p (list r c)))
         (cond ((member? p holes) 6)
               ((member? p holed-cells) 8)
               ((not (= (at g r c) bg)) (at g r c))
               ((member? p rim) 2)
               (else bg)))))))
