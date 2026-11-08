(rule!
;; A square grid has sparse colored source cells on a zero background.
;; Copy each source across the main diagonal and keep the original.
;; Inputs exclude occupied reflected targets, so colors never conflict.
 (lambda (g) (overlay g (transpose g))))
