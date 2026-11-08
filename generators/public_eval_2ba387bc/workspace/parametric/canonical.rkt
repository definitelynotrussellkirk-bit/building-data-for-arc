(rule!
 ;; Separate hollow square frames from equally sized solid square blocks.
 ;; Order each class top-to-bottom, breaking equal top-row ties left-to-right.
 ;; Place frames in the left output column and solids in the right column.
 ;; Preserve exact block crops; fill missing trailing slots with background.
 (lambda (g)
  (let ()
   (define column-order #f)
   (define bg (mode g -1))
   (define blocks (objects g bg))
   (define size (obj-w (first blocks)))
   (define (before? a b)
    (if column-order
     (or (< (obj-c1 a) (obj-c1 b)) (and (= (obj-c1 a) (obj-c1 b)) (< (obj-r1 a) (obj-r1 b))))
     (or (< (obj-r1 a) (obj-r1 b)) (and (= (obj-r1 a) (obj-r1 b)) (< (obj-c1 a) (obj-c1 b))))))
   (define (ordered xs) (sort xs before?))
   ;; Step A: two ordered lists of classified, input-derived block crops.
   (define frames (ordered (filter (lambda (o) (not (solid-rect? o))) blocks)))
   (define solids (ordered (filter solid-rect? blocks)))
   (define buckets (list frames solids))
   ;; Step B: list lengths set output height; list membership and rank set slots.
   (define slots (max (length (first buckets)) (length (second buckets))))
   (for*/fold ((out (empty-grid (* size slots) (* size 2) bg)))
    ((i (range 0 slots)) (side (range 0 2)))
    (let ((bucket (nth buckets side)))
     (if (>= i (length bucket)) out
      (let ((block (nth bucket i)))
       (paste out (subgrid g (obj-r1 block) (obj-c1 block) (obj-r2 block) (obj-c2 block))
        (* i size) (* side size)))))))))
