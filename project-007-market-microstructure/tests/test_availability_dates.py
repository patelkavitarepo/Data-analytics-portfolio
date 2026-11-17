"""D015 timestamp-only freeze and no-source-price selection synthetic tests."""
from datetime import date,timedelta
import unittest
from research.freeze_availability_dates_once import select_dates,checksum,STOCKS
from microstructure.availability_alerts import freeze_calendar

def dates():
    start=date(2022,7,13)
    return [(start+timedelta(days=i)).isoformat() for i in range(90)
            if (start+timedelta(days=i)).weekday()<5][:41]

class TestAvailabilityDates(unittest.TestCase):
    def test_only_post_D014_first_40_common_dates(self):
        d=dates()
        inventory={s:{day:1023 for day in d} for s in STOCKS}
        parts,meta=select_dates(inventory)
        self.assertEqual(parts["warmup"],d[:20])
        self.assertEqual(parts["confirmation"],d[20:30])
        self.assertEqual(parts["sealed_final"],d[30:40])
        self.assertEqual(len(checksum(parts)),64)
        freeze_calendar(*(parts[k] for k in ("warmup","confirmation","sealed_final")))
    def test_no_stock_substitution_or_old_final_date(self):
        d=dates()
        inventory={s:{day:1 for day in d} for s in STOCKS[:2]}
        with self.assertRaises(ValueError):select_dates(inventory)
        inventory={s:{day:1 for day in d} for s in STOCKS}
        inventory[STOCKS[0]].pop(d[0])
        parts,_=select_dates(inventory)
        self.assertEqual(parts["warmup"][0],d[1])
        bad={k:list(v) for k,v in parts.items()}
        bad["warmup"][0]="2022-07-12"
        with self.assertRaises(ValueError):checksum(bad)

if __name__=="__main__":unittest.main()
