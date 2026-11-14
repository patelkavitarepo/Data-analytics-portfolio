"""Differential synthetic oracle for prospective-label chronology and masking.

The oracle independently searches every future candidate per origin (O(n^2)),
unlike the production two-pointer scan. Only seeded synthetic snapshots are used.
"""
import random
import unittest
from datetime import date, timedelta
from decimal import Decimal

from microstructure.chronology import Snapshot, label_after_elapsed_time


def slow_oracle(rows, horizon):
    labels = []
    for i, origin in enumerate(rows):
        if origin.state != "active" or any(
            type(v) is not int for v in (
                origin.bid_price, origin.ask_price, origin.bid_size, origin.ask_size
            )
        ) or not (
            origin.bid_price > 0
            and origin.ask_price > origin.bid_price
            and origin.bid_size > 0
            and origin.ask_size > 0
        ):
            labels.append((None, None))
            continue
        origin_mid = origin.ask_price + origin.bid_price
        target = None
        for j in range(i + 1, len(rows)):
            future = rows[j]
            if future.session != origin.session:
                break
            if future.state != "active" or any(
                type(v) is not int for v in (
                    future.bid_price, future.ask_price, future.bid_size, future.ask_size
                )
            ) or not (
                future.bid_price > 0
                and future.ask_price > future.bid_price
                and future.bid_size > 0
                and future.ask_size > 0
            ):
                break
            if future.time <= origin.time:
                continue
            if future.time - origin.time >= horizon:
                target = j
                break
        if target is None:
            labels.append((None, None))
        else:
            end_mid = rows[target].bid_price + rows[target].ask_price
            labels.append((target, (end_mid > origin_mid) - (end_mid < origin_mid)))
    return labels


class OracleTests(unittest.TestCase):
    def test_seeded_variable_density_and_interruptions(self):
        rng = random.Random(7007)
        sessions = [(date(2026, 1, 2) + timedelta(days=d)).isoformat() for d in range(4)]
        rows = []
        for session in sessions:
            timestamp = Decimal(34000)
            for i in range(140):
                timestamp += Decimal(rng.choice(["0", "0", "0.125", "0.25", "1", "4"]))
                state = rng.choices(["active", "halt", "unusable"], weights=[90, 4, 6])[0]
                bid = 1000000 + 50 * rng.randrange(-3, 4)
                ask = bid + 100
                if i % 29 == 0:
                    ask = bid  # invalid quote becomes segment boundary
                rows.append(
                    Snapshot(
                        session, timestamp, state, bid, ask,
                        rng.choice([0, 10, 50, 200]),
                        rng.choice([0, 10, 50, 200]),
                    )
                )
        for h in [Decimal("0.125"), Decimal("0.5"), Decimal("2"), Decimal("10")]:
            with self.subTest(horizon=str(h)):
                expected = slow_oracle(rows, h)
                observed = label_after_elapsed_time(rows, h)
                self.assertEqual(
                    [(x.target_index, x.direction) for x in observed], expected
                )
                self.assertEqual(len(observed), len(rows))
                for i, label in enumerate(observed):
                    self.assertEqual(label.origin_index, i)
                    self.assertEqual(label.session, rows[i].session)
                    if label.target_index is not None:
                        self.assertGreater(label.target_time, label.origin_time)
                        self.assertGreaterEqual(
                            label.target_time - label.origin_time, h
                        )
                        self.assertEqual(
                            rows[label.target_index].session, rows[i].session
                        )
                        self.assertIsNone(label.reason)

    def test_no_future_influence_on_origin_features(self):
        rows = [
            Snapshot("2026-01-02", Decimal(i), "active",
                     1000000 + 10 * i, 1000100 + 10 * i,
                     20 + i, 100 - i)
            for i in range(40)
        ]
        standard = label_after_elapsed_time(rows, Decimal(3))
        altered = list(rows)
        for i in range(20, len(altered)):
            future = altered[i]
            altered[i] = Snapshot(
                future.session, future.time, future.state,
                future.bid_price + 10000, future.ask_price + 10000,
                1000, 1,
            )
        changed = label_after_elapsed_time(altered, Decimal(3))
        for index in range(20):
            self.assertEqual(
                standard[index].origin_imbalance,
                changed[index].origin_imbalance,
            )
            self.assertEqual(standard[index].origin_time, changed[index].origin_time)

    def test_zero_change_class_is_preserved_in_repeated_quotes(self):
        rows = [
            Snapshot("2026-01-02", Decimal(i), "active", 1000000, 1000100, 50, 50)
            for i in range(4)
        ]
        labels = label_after_elapsed_time(rows, 1)
        self.assertEqual([x.direction for x in labels], [0, 0, 0, None])

    def test_no_labels_on_or_through_invalid_quotes(self):
        rows = [
            Snapshot("2026-01-02", Decimal(0), "active", 1000000, 1000100, 50, 50),
            Snapshot("2026-01-02", Decimal(1), "active", 1000100, 1000100, 50, 50),
            Snapshot("2026-01-02", Decimal(2), "active", 1000200, 1000300, 50, 50),
            Snapshot("2026-01-02", Decimal(3), "active", 1000200, 1000300, 50, 50),
        ]
        labels = label_after_elapsed_time(rows, 1)
        self.assertIsNone(labels[0].direction)
        self.assertEqual(labels[0].reason, "interrupted_before_horizon")
        self.assertEqual(labels[1].reason, "unusable_origin")
        self.assertEqual(labels[2].direction, 0)


if __name__ == "__main__":
    unittest.main()
