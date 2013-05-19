import unittest

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


    @unittest.skip("TODO")
    def test_normalize_works(self):
        # TODO, grab a file and run it through scrape.normalize_html
        pass
