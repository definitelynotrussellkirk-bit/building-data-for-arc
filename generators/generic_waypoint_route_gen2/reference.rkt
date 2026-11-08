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
   (define objs (objects-multicolor panel bg))
   (define cursor (first (filter (lambda (o) (= (obj-size o) 2)) objs)))
   (define cells (obj-cells cursor))
   (define singles
    (map (lambda (o) (first (obj-cells o)))
         (filter (lambda (o) (= (obj-size o) 1)) objs)))
   (define head
    (first
     (filter
      (lambda (p)
       (> (count-if
           (lambda (q) (= (at panel (first q) (second q))
                          (at panel (first p) (second p))))
           singles)
          0))
      cells)))
   (define tail (first (filter (lambda (p) (not (equal? p head))) cells)))
   (define head-color (at panel (first head) (second head)))
   (define tail-color (at panel (first tail) (second tail)))
   (define dots
    (filter
     (lambda (p) (= (at panel (first p) (second p)) head-color))
     singles))
   (define traced
    (let loop ((pos head) (remaining dots) (last-delta (list 0 0)))
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
   (define dr (cond ((< (first delta) 0) -1)
                    ((> (first delta) 0) 1)
                    (else 0)))
   (define dc (cond ((< (second delta) 0) -1)
                    ((> (second delta) 0) 1)
                    (else 0)))
   (define r (first final))
   (define c (second final))
   (set-cell
    (set-cell (empty-grid h pw bg) r c head-color)
    (- r dr) (- c dc) tail-color))))