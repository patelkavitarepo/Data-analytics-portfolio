"""Dataset-free mathematical checks, not market results or a scoring system."""

import json
from fractions import Fraction


def verify():
    checked = 0
    for n in range(1, 31):
        for a_only in range(n + 1):
            for c_only in range(n - a_only + 1):
                for both in range(n - a_only - c_only + 1):
                    na, nc = a_only + both, c_only + both
                    if not na or not nc:
                        continue  # CVR undefined; not silently assigned zero.
                    p_a, p_c, p_11 = Fraction(na, n), Fraction(nc, n), Fraction(both, n)
                    cvr = Fraction(n * both, na * nc)
                    assert cvr == (Fraction(both, nc) / p_a)
                    assert cvr == (Fraction(both, na) / p_c)
                    assert cvr == p_11 / (p_a * p_c)
                    assert max(Fraction(0), p_a + p_c - 1) / (p_a * p_c) <= cvr
                    assert cvr <= 1 / max(p_a, p_c)
                    checked += 1
    assert checked == 45415

    n, na, nc, both = 50, 10, 5, 2
    direction = {
        "label": "synthetic illustration, NOT stock results",
        "N": n,
        "A_stress": na,
        "C_stress": nc,
        "both": both,
        "CVR": float(Fraction(n * both, na * nc)),
        "P_A_given_C": float(Fraction(both, nc)),
        "P_C_given_A": float(Fraction(both, na)),
    }
    assert direction["CVR"] == 2
    assert direction["P_A_given_C"] == 0.4
    assert direction["P_C_given_A"] == 0.2

    # Each severity stratum is exactly independent; the mixture is not.
    strata = [(1000, 100, 100, 10), (1000, 800, 800, 640)]
    within = [Fraction(k * b, a * c) for k, a, c, b in strata]
    assert within == [1, 1]
    n, na, nc, both = (sum(row[i] for row in strata) for i in range(4))
    expected_joint = sum(
        Fraction(k, n) * Fraction(a, k) * Fraction(c, k)
        for k, a, c, _ in strata
    )
    standardized = Fraction(both, n) / expected_joint
    assert standardized == 1
    return {
        "exhaustive_synthetic_tables_checked": checked,
        "symmetry_and_probability_bounds": "passed",
        "direction_example": direction,
        "mixture_example": {
            "label": "synthetic severity confounding, NOT stock results",
            "N": n,
            "A_stress": na,
            "C_stress": nc,
            "both": both,
            "within_stratum_CVR": [float(x) for x in within],
            "pooled_CVR": float(Fraction(n * both, na * nc)),
            "severity_standardized_joint_lift": float(standardized),
        },
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
