(rule!
 (lambda (g)
  (let ()
   (define h (rows g))
   (define w (cols g))
   (define bg (mode g -1))
   (define sep-cols
    (filter
     (lambda (c)
      (and (!= (at g 0 c) bg)
           (all? (lambda (r) (= (at g r c) (at g 0 c))) (range 0 h))))
     (range 0 w)))
   (define start (+ 1 (apply max sep-cols)))
   (define panel (subgrid g 0 start (- h 1) (- w 1)))
   (define pw (cols panel))
   (define objs (objects-8 panel bg))
   (define cursor (first (filter (lambda (o) (> (obj-size o) 1)) objs)))
   (define cells (obj-cells cursor))
   (define bb (obj-bbox cursor))
   (define bh (+ 1 (- (third bb) (first bb))))
   (define bw (+ 1 (- (fourth bb) (second bb))))
   (define tip
    (if (> bw bh)
        (first
         (filter
          (lambda (p)
           (= 1 (count-if (lambda (q) (= (first q) (first p))) cells)))
          cells))
        (first
         (filter
          (lambda (p)
           (= 1 (count-if (lambda (q) (= (second q) (second p))) cells)))
          cells))))
   (define dots
    (map (lambda (o) (first (obj-cells o)))
         (filter (lambda (o) (= (obj-size o) 1)) objs)))
   (define traced
    (let loop ((pos tip) (remaining dots) (last-delta (list 0 0)))
     (if (empty? remaining)
         (list pos last-delta)
         (let* ((aligned
                 (filter
                  (lambda (q)
                   (or (= (first q) (first pos))
                       (= (second q) (second pos))))
                  remaining))
                (next (first aligned))
                (delta (list (- (first next) (first pos))
                             (- (second next) (second pos)))))
          (loop next
                (filter (lambda (q) (not (equal? q next))) remaining)
                delta)))))
   (define final (first traced))
   (define delta (second traced))
   (define r (first final))
   (define c (second final))
   (define arrow
    (cond ((< (first delta) 0)
           (list (list r c) (list (+ r 1) (- c 1)) (list (+ r 1) (+ c 1))))
          ((> (first delta) 0)
           (list (list r c) (list (- r 1) (- c 1)) (list (- r 1) (+ c 1))))
          ((< (second delta) 0)
           (list (list r c) (list (- r 1) (+ c 1)) (list (+ r 1) (+ c 1))))
          (else
           (list (list r c) (list (- r 1) (- c 1)) (list (+ r 1) (- c 1))))))
   (paint-cells (empty-grid h pw bg) arrow (obj-color cursor)))))