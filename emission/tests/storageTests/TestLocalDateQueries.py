# Standard imports
import unittest
import arrow
import logging
import uuid

# Our imports
import emission.core.get_database as edb
import emission.core.wrapper.motionactivity as ecwm
import emission.core.wrapper.localdate as ecwl
import emission.core.wrapper.entry as ecwe

import emission.storage.timeseries.abstract_timeseries as esta
import emission.storage.decorations.local_date_queries as esdl
import emission.storage.timeseries.format_hacks.move_filter_field as estfm

# Test imports
import emission.tests.common as etc

class TestLocalDateQueries(unittest.TestCase):
    def setUp(self):
        etc.setupRealExample(self, "emission/tests/data/real_examples/shankari_2015-aug-27")
        estfm.move_all_filters_to_data()

    def tearDown(self):
        self.clearRelatedDb()

    def clearRelatedDb(self):
        edb.get_timeseries_db().remove({'user_id': self.testUUID})
        edb.get_analysis_timeseries_db().remove({'user_id': self.testUUID})

    def testLocalDateReadWrite(self):
        ts = esta.TimeSeries.get_time_series(self.testUUID)
        start_ts = arrow.now().timestamp
        ma_ts = 1460586729
        local_dt = esdl.get_local_date(ma_ts, "America/Los_Angeles")
        fmt_time = arrow.get(ma_ts).to("America/Los_Angeles").isoformat()
        ma = ecwm.Motionactivity({
            "ts": 1460586729,
            "local_dt": local_dt,
            "fmt_time": fmt_time
        })
        ma_entry = ecwe.Entry.create_entry(self.testUUID, "background/motion_activity",
            ma)
        ts.insert(ma_entry)
        ret_entry = ecwe.Entry(ts.get_entry_at_ts("background/motion_activity", "data.ts", 1460586729))

        self.assertGreaterEqual(ret_entry.metadata.write_ts, start_ts)
        metadata_dt = arrow.get(ret_entry.metadata.write_ts).to(ret_entry.metadata.time_zone).datetime
        self.assertEqual(metadata_dt.hour, ret_entry.metadata.write_local_dt.hour)
        self.assertEqual(metadata_dt.minute, ret_entry.metadata.write_local_dt.minute)
        self.assertEqual(metadata_dt.weekday(), ret_entry.metadata.write_local_dt.weekday)

        self.assertEqual(ret_entry.data.local_dt.hour, 15)
        self.assertEqual(ret_entry.data.local_dt.month, 4)
        self.assertEqual(ret_entry.data.local_dt.weekday, 2)
        self.assertEqual(ret_entry.data.fmt_time, "2016-04-13T15:32:09-07:00")

    def testLocalRangeQuery(self):
        """
        Search for all entries between 8:18 and 8:20 local time, both inclusive
        """
        start_local_dt = ecwl.LocalDate({'year': 2015, 'month': 8, 'hour': 8, 'minute': 18})
        end_local_dt = ecwl.LocalDate({'year': 2015, 'month': 8, 'hour': 8, 'minute': 20})
        final_query = {"user_id": self.testUUID}
        final_query.update(esdl.get_range_query("data.local_dt", start_local_dt, end_local_dt))
        entries = edb.get_timeseries_db().find(final_query)
        self.assertEquals(15, entries.count())

    def testLocalMatchingQuery(self):
        """
        Search for all entries that occur at minute = 8 from any hour
        """
        start_local_dt = ecwl.LocalDate({'minute': 8})
        end_local_dt = ecwl.LocalDate({'minute': 8})
        final_query = {"user_id": self.testUUID}
        final_query.update(esdl.get_range_query("data.local_dt", start_local_dt, end_local_dt))
        entries_docs = edb.get_timeseries_db().find(final_query).sort("metadata.write_ts")
        self.assertEquals(20, entries_docs.count())
        entries = [ecwe.Entry(doc) for doc in entries_docs]
        logging.debug("entries bookends are %s and %s" % (entries[0], entries[-1]))
        first_entry = entries[0]
        self.assertEquals(first_entry.data.local_dt.hour, 9)
        last_entry = entries[19]
        self.assertEquals(last_entry.data.local_dt.hour, 17)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()