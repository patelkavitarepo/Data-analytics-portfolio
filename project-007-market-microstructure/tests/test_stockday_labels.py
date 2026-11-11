import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from microstructure.stockday_labels import Quote, labels_from_quotes


TZ=timezone(timedelta(hours=8))

def q(symbol, day, minute, midpoint, stale=False, invalid=False):
    mid=Decimal(str(midpoint))
    bid=mid-Decimal("0.01")
    ask=mid+Decimal("0.01") if not invalid else bid
    return Quote(symbol,day,datetime.fromisoformat(day+"T09:30:00").replace(tzinfo=TZ)+timedelta(seconds=15 * minute),bid,ask,stale)

class Tests(unittest.TestCase):
    def test_exact_average_not_final_snapshot(self):
        x=[q("000001.SZ","2022-01-04",i,v) for i,v in enumerate((100,100,100,100.3))]
        got=labels_from_quotes(x,3)
        self.assertEqual(got[0].classification,2)  # mean 100.1, not 100.3
        self.assertEqual(got[0].target_indices,(1,2,3))

    def test_threshold_is_inclusive(self):
        x=[q("A","2022-01-04",0,100),q("A","2022-01-04",1,100.2)]
        self.assertEqual(labels_from_quotes(x,1)[0].classification,1)
        x[-1]=q("A","2022-01-04",1,99.8)
        self.assertEqual(labels_from_quotes(x,1)[0].classification,3)

    def test_cannot_cross_stock_or_day(self):
        x=[q("A","2022-01-04",0,100),
           q("B","2022-01-04",0,110),
           q("A","2022-01-05",0,150)]
        self.assertTrue(all(z.classification is None for z in labels_from_quotes(x,1)))

    def test_invalid_breaks_sequence(self):
        x=[q("A","2022-01-04",0,100),
           q("A","2022-01-04",1,100,stale=True),
           q("A","2022-01-04",2,100),
           q("A","2022-01-04",3,100)]
        r=labels_from_quotes(x,1)
        self.assertEqual([z.classification for z in r],[None,None,2,None])
        self.assertEqual(r[1].excluded,"invalid_or_stale_quote")

    def test_bad_values_and_unordered_rejected(self):
        x=[q("A","2022-01-04",2,100),q("A","2022-01-04",1,100)]
        with self.assertRaisesRegex(ValueError,"unsorted"):
            labels_from_quotes(x,1)
        for k in (-1,0,True,2.5):
            with self.subTest(k=k),self.assertRaises(ValueError):
                labels_from_quotes([],k)
        for t in (0,"NaN",1):
            with self.subTest(t=t),self.assertRaises(ValueError):
                labels_from_quotes([],1,t)

    def test_timestamp_day_must_match(self):
        x=q("A","2022-01-04",0,100)
        bad=Quote(x.symbol,"2022-01-05",x.available_at,x.bid,x.ask)
        with self.assertRaisesRegex(ValueError,"differ"):
            labels_from_quotes([bad],1)

    def test_gap_longer_than_declared_cadence_breaks_segment(self):
        rows = [q("A", "2022-01-04", 0, 100),
                q("A", "2022-01-04", 1, 100),
                q("A", "2022-01-04", 10, 102),
                q("A", "2022-01-04", 11, 102)]
        labels = labels_from_quotes(rows, 1, max_gap_seconds=30)
        self.assertEqual([x.classification for x in labels], [2, None, 2, None])
        self.assertEqual(labels[1].excluded, "incomplete_future")

    def test_large_window_exact_rolling_average(self):
        rows = [q("A", "2022-01-04", i, 100 + i * 0.03) for i in range(300)]
        lab = labels_from_quotes(rows, 5)
        self.assertEqual(len(lab), len(rows))
        self.assertEqual(sum(x.classification is not None for x in lab), 295)
        self.assertTrue(all(x.target_indices == tuple(range(i+1, i+6))
                            for i, x in enumerate(lab[:295])))
        self.assertTrue(all(x.classification is None for x in lab[-5:]))

    def test_short_segment_never_fabricates_label(self):
        z=labels_from_quotes([q("A","2022-01-04",0,100)],5)
        self.assertEqual(z[0].excluded,"incomplete_future")


if __name__=="__main__":
    unittest.main()
