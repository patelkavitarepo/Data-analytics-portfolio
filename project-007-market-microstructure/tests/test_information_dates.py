"""D016 source-only timestamp freezer synthetic checks."""
import unittest
from research.freeze_information_dates_once import select_dates,checksum,STOCKS

class InformationDatesTests(unittest.TestCase):
    def test_first_40_common_dates_strictly_after_previous_final(self):
        from datetime import date,timedelta
        dates=[(date(2022,9,7)+timedelta(days=i)).isoformat() for i in range(44)]
        inventory={s:{d:1023 for d in dates} for s in STOCKS}
        result,_=select_dates(inventory)
        self.assertEqual(result["warmup"][0],"2022-09-07")
        self.assertEqual(result["sealed_final"][-1],dates[39])
        self.assertEqual(len(result["confirmation"]),10)
        self.assertEqual(len(checksum(result)),64)
    def test_insufficient_common_dates_fails_closed(self):
        inventory={s:{"2022-09-07":1} for s in STOCKS}
        with self.assertRaises(ValueError):select_dates(inventory)
if __name__=="__main__":unittest.main()
