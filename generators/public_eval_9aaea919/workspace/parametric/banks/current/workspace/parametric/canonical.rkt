(rule!
 ;; Bottom red bars identify donor stacks; one green bar identifies a receiver.
 ;; Count donor objects, rather than their pixels. Gray the donor objects, remove
 ;; the command bars and add their total count above the receiver stack. The
 ;; receiver's actual top shape, color and measured stacking pitch are preserved.
 ;; A: aligned stack counts and geometry. B: render that many shifted copies.
 (lambda (g)
  (let ()
   (define bg (mode g -1))
   (define objs (objects g bg))
   (define marker-y (apply max (map obj-r2 objs)))
   (define markers
    (filter (lambda (o) (and (= (obj-r1 o) marker-y) (= (obj-h o) 1)
                              (or (= (obj-color o) 2) (= (obj-color o) 3)))) objs))
   (define bodies (filter (lambda (o) (not (member o markers))) objs))
   (define donors (filter (lambda (o) (= (obj-color o) 2)) markers))
   (define receiver-mark (first (filter (lambda (o) (= (obj-color o) 3)) markers)))
   (define (stack m)
    (filter (lambda (o) (and (= (obj-c1 o) (obj-c1 m)) (= (obj-c2 o) (obj-c2 m)))) bodies))
   (define donor-counts (map (lambda (m) (length (stack m))) donors))
   (define amount (apply + donor-counts))
   (define receiver (stack receiver-mark))
   (define top (pick-min receiver obj-r1))
   (define bottom (pick-max receiver obj-r1))
   (define pitch (+ (obj-h bottom) (- marker-y (obj-r2 bottom) 1)))
   (define cleared
    (for/fold ((out g)) ((m markers)) (recolor-cells out (obj-cells m) bg)))
   (define grayed
    (for*/fold ((out cleared)) ((m donors) (o (stack m)))
     (recolor-cells out (obj-cells o) 5)))
   (for/fold ((out grayed)) ((k (range 1 (+ amount 1))))
    (recolor-cells out
     (map (lambda (p) (list (- (first p) (* k pitch)) (second p))) (obj-cells top))
     (obj-color top))))))
