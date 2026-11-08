(rule!
 ;; Bottom red bars donate the number of repeated objects in their columns.
 ;; Gray donor objects and erase bottom instructions. Broadcast copies each
 ;; receiver's own motif, using its lower gap as the vertical inter-unit gap.
 ;; In balanced mode spend one unit on the current shortest receiver each step;
 ;; equal-height receivers are ordered left-to-right. Object colors are not roles.
 (lambda (g)
  (let ()
   (define balanced? #t)
   (define bg (mode g -1))
   (define body (filter (lambda (o) (< (obj-r2 o) (- h 1))) (objects g bg)))
   (define lefts (sort (remove-duplicates (map obj-c1 body)) <))
   (define (parts c) (sort (filter (lambda (o) (= (obj-c1 o) c)) body)
                            (lambda (a b) (< (obj-r1 a) (obj-r1 b)))))
   (define (tag c) (at g (- h 1) c))
   (define donors (filter (lambda (c) (= (tag c) 2)) lefts))
   (define receivers (filter (lambda (c) (= (tag c) 3)) lefts))
   (define total (for/sum ((c donors)) (length (parts c))))
   (define initial (map (lambda (c) (length (parts c))) receivers))
   (define final
    (if balanced?
     (let loop ((remaining total) (heights initial))
      (if (= remaining 0) heights
       (let* ((lowest (apply min heights))
              (selected (for/first ((j (range (length heights))) #:when (= (list-ref heights j) lowest)) j)))
        (loop (- remaining 1)
          (for/list ((v heights) (j (range (length heights)))) (if (= j selected) (+ v 1) v))))))
     (map (lambda (v) (+ v total)) initial)))
   (define cleared
    (for/fold ((out g)) ((c (range w)))
     (if (member (at g (- h 1) c) '(2 3)) (set-cell out (- h 1) c bg) out)))
   (define grayed
    (for*/fold ((out cleared)) ((c donors) (o (parts c)) (p (obj-cells o)))
     (set-cell out (first p) (second p) 5)))
   (for/fold ((out grayed)) ((c receivers) (before initial) (after final))
    (let* ((ls (parts c)) (top (first ls)) (bottom (last ls))
           (gap (- h 2 (obj-r2 bottom))) (pitch (+ (obj-h bottom) gap)))
     (for*/fold ((acc out)) ((j (range 1 (+ 1 (- after before)))) (p (obj-cells top)))
      (set-cell acc (- (first p) (* j pitch)) (second p) (obj-color top))))))))
