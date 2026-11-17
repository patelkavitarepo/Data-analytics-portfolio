"""Synthetic D018 timestamp-only calendar guards."""
import unittest
from datetime import date,timedelta
from research.freeze_fresh_replication_dates_once import select_dates,checksum,STOCKS

class FreshReplicationCalendarTests(unittest.TestCase):
    def test_after_sealed_final_and_partitioned(self):
        days=[(date(2023,1,6)+timedelta(days=i)).isoformat() for i in range(45)]
        dates,_=select_dates({s:{d:1 for d in days} for s in STOCKS})
        self.assertEqual(dates["warmup"][0],"2023-01-06")
        self.assertEqual(dates["confirmation"][0],days[20])
        self.assertEqual(dates["sealed_final"][-1],days[39])
        self.assertEqual(len(checksum(dates)),64)
    def test_fails_if_only_old_dates_exist(self):
        with self.assertRaises(ValueError):
            select_dates({s:{"2023-01-05":1} for s in STOCKS})
if __name__=="__main__":unittest.main()
