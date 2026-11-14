"""Synthetic D019 source-date isolation tests (no price access)."""
import unittest
from research.freeze_stock_scarcity_dates_once import select_dates,checksum,STOCKS

class D019CalendarTests(unittest.TestCase):
    def test_first_forty_common_dates_after_sealed_boundary(self):
        from datetime import date,timedelta
        dates=[(date(2023,3,10)+timedelta(days=i)).isoformat() for i in range(55)]
        panel={s:{d:100 for d in dates} for s in STOCKS}
        selected,_=select_dates(panel)
        self.assertEqual(selected["warmup"][0],"2023-03-10")
        self.assertEqual(len(selected["warmup"]),20)
        self.assertEqual(len(selected["confirmation"]),10)
        self.assertEqual(len(selected["sealed_final"]),10)
        self.assertEqual(len(checksum(selected)),64)
    def test_reject_short_calendar(self):
        with self.assertRaises(ValueError):
            select_dates({s:{"2023-03-10":100} for s in STOCKS})
    def test_prior_dates_never_selected(self):
        dates=["2023-03-09"]+[( __import__("datetime").date(2023,3,10)+__import__("datetime").timedelta(days=i)).isoformat() for i in range(40)]
        selected,_=select_dates({s:{d:100 for d in dates} for s in STOCKS})
        self.assertNotIn("2023-03-09",sum(selected.values(),[]))
if __name__=="__main__":unittest.main()
