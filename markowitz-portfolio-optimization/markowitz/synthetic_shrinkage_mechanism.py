"""Independent synthetic mechanism study; true covariance is scoring-only.
SYNTHETIC DATA — NOT EMPIRICAL RESULTS.
"""
VERSION = '006-synthetic-shrinkage-mechanism-v1'
SEEDS = (7101,7102,7103,7104,7105)
RHOS = (0.,.35)
WINDOWS = (63,504)
TRAIN_POOL = 504
SHRINKAGE = .25
CAP = .35
ANNUAL_RF = .02
TIE_TOLERANCE = 1e-12
ORACLE_TOLERANCE = 1e-9
