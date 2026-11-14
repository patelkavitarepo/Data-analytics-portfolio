"""D015 runner source-isolation and aggregate denominator synthetic checks."""
import unittest
from research.run_availability_alerts_once import pool,DATE_SHA
from research.freeze_availability_dates_once import load_manifest
from microstructure.availability_alerts import aggregate_states,matched_outcomes

class D015RunnerTests(unittest.TestCase):
    def test_committed_timestamp_manifest(self):
        x=load_manifest()
        self.assertEqual(x["date_list_sha256"],DATE_SHA)
        self.assertIs(x["price_or_label_columns_read"],False)
        self.assertEqual(x["dates"]["sealed_final"][0],"2022-08-24")
    def test_source_denominators_and_unknown_labels(self):
        statuses=("DATA_UNAVAILABLE_CURRENT","DATA_UNAVAILABLE_HISTORY",
                  "NO_SIGNAL","ALERT_UP","ALERT_DOWN")
        leaf={"state":aggregate_states(statuses),
              "outcome":matched_outcomes(statuses,(None,3,2,1,2))}
        p=pool([leaf])
        self.assertEqual(p["source_n"],5)
        self.assertEqual(sum(p["status_counts"].values()),5)
        self.assertEqual(p["all_source_alerts"],2)
        self.assertEqual(p["matched_n"],4)
        self.assertEqual(p["correct"],1)
        self.assertEqual(p["wrong"],1)
        self.assertEqual(p["hypothetical_4to1_units"],-3)
        self.assertEqual(p["zero_alert_reference_units"],0)

if __name__=="__main__":unittest.main()
