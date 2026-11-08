# 0de1e91bfb95

0-bg grid (h~7-10, w~9-12) with: (a) ONE COLOR-2 SEED at (sr, 1) — left edge interior row sr ∈ [2, h-3]; (b) ONE MIRROR at (sr, mirror_c) with mirror_c ∈ [sr+3, w-3] — color either 6 (UP-FROM-RIGHT reflector) or 7 (DOWN-FROM-RIGHT reflector); (c) ONE COLOR-5 WALL at (wall_r, mirror_c) placed in the column the beam will enter after deflection. Rule (LASER BEAM FROM 2-SEED, DEFLECTED BY 6/7 MIRRORS, STOPPED BY 5-WALL): from the 2-seed at (sr, 1), cast a beam to the RIGHT. PAINT every 0-cell along the beam's path with COLOR 8. When the beam hits a 6-mirror: turn LEFT-OF-INCOMING (right → up). When it hits a 7-mirror: turn RIGHT-OF-INCOMING (right → down). When it hits a 5-WALL or grid edge, the beam STOPS. Net: a cyan-painted trajectory traces through the optical system from the seed.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
