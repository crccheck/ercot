import datetime
import unittest

import dataset

from scripts import scrape


class TestScraper(unittest.TestCase):
    def test_guess_type_works(self):
        should_be_float = scrape.FLOAT_KEYS[0]
        input = (
            ('a', '1'),
            ('b', '2'),
            (should_be_float, '2'),
        )
        output = dict(scrape.guess_type(input))
        self.assertEqual(type(output['a']), int)
        self.assertEqual(type(output[should_be_float]), float)

    def test_normalize_works(self):
        control = {
            'total_system_capacity': 38322,
            'actual_system_demand': 31579,
            'total_wind_output': 5973,
            'dc_e': 0,
            'dc_l': 100,
            'dc_n': 25,
            'dc_r': 151,
            'dc_s': 0,
            'current_frequency': 59.962,
            'instantaneous_time_error': -2.562,
            'timestamp': datetime.datetime(2012, 3, 29, 23, 9, 50),
        }
        with open('fixtures/test_download.html', 'r') as f:
            data = scrape.normalize_html(f)
            self.assertEqual(data, control)


class DBTestCase(unittest.TestCase):
    def setUp(self):
        super(DBTestCase, self).setUp()
        db = dataset.connect('sqlite:///:memory:')
        table = db['test']
        table.create_index(['timestamp'])
        self.table = table

    def tearDown(self):
        super(DBTestCase, self).tearDown()
        self.table.drop()

    def test_wont_duplicate_data(self):
        # TODO `upsert` is just manually copied, actually test a function
        with open('fixtures/test_download.html', 'r') as f:
            data = scrape.normalize_html(f)
            self.table.upsert(data, ['timestamp'])
            self.assertEqual(len(list(self.table.all())), 1)
            self.table.upsert(data, ['timestamp'])
            self.assertEqual(len(list(self.table.all())), 1)
