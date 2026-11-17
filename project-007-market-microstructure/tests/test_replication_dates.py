"""D017 prospective date selection: only timestamp inventory, no market prices."""
import unittest
from datetime import date,timedelta
from research.freeze_replication_dates_once import select_dates,checksum,STOCKS

class ReplicationCalendarTests(unittest.TestCase):
    def test_fresh_post_sealed_calendar(self):
        days=[(date(2022,11,10)+timedelta(days=i)).isoformat() for i in range(45)]
        inventory={stock:{d:100 for d in days} for stock in STOCKS}
        parts,_=select_dates(inventory)
        self.assertEqual(parts["warmup"][0],"2022-11-10")
        self.assertEqual(parts["confirmation"][0],days[20])
        self.assertEqual(parts["sealed_final"][-1],days[39])
        self.assertEqual(len(checksum(parts)),64)
    def test_insufficient_common_history_fails(self):
        with self.assertRaises(ValueError):
            select_dates({s:{"2022-11-10":1} for s in STOCKS})
if __name__=="__main__":unittest.main()
