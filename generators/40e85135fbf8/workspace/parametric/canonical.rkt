(rule!
 ;; Drop the header row+column; an interior cell lights with the shared
 ;; header color when its ROW header equals its COLUMN header (non-zero).
 (grid-from-fn (- h 1) (- w 1) (lambda (r c)
   (let ((left (at g (+ r 1) 0)) (top (at g 0 (+ c 1))))
     (if (and (!= left 0) (= left top)) left 0)))))