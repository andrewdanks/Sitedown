import unittest
from sitedown import *

class SitedownTest(unittest.TestCase):

    def setUp(self):
        self.SD = Sitedown('http://example.com')

    def tearDown(self):
        self.SD = None

    def test_is_same_site(self):

        cases = {
            'http://example.com' : True,
            'http://www.example.com' : True,
            'https://example.com' : True,
            'http://example2.com' : False,
            'http://example.net' : False,
            'http://blah.example.com' : False,
            'http://example.com/a/b' : True,
            'http://example.com/a/b/c.html' : True,
            '' : True,
            '/a/b' : True,
            'a/b' : True,
            '/a/b/c.html' : True,
            'a/b/c.html' : True,
            'a.html' : True,
            '/a.html' : True
        }

        self.assert_cases(cases, self.SD._is_same_site)

    def test_format_url(self):

        cases = {
            'http://example.com' : 'http://example.com',
            'http://www.example.com' : 'http://example.com',
            'http://hello.example.com' : 'http://hello.example.com',
            'http://example.com/hello/world' : 'http://example.com/hello/world',
            'http://example.com/hello/world/' : 'http://example.com/hello/world',
            'http://example.com/a/b/c.html' : 'http://example.com/a/b/c.html',
            'http://www.example.com/a/b/c.html' : 'http://example.com/a/b/c.html',
            '/hello/world' : 'http://example.com/hello/world',
            'hello/world' : 'http://example.com/hello/world',
            '' : 'http://example.com'
        }

        self.assert_cases(cases, self.SD._format_url)

    def test_format_path(self):

        cases = {
            '/path/to/somewhere' : '/path/to/somewhere/',
            '/path/to/somewhere/' : '/path/to/somewhere/',
            'path/to/somewhere/' : 'path/to/somewhere/',
            '/a' : '/a/',
            '/' : '/',
            '' : ''
        }

        self.assert_cases(cases, self.SD._format_path)

    def assert_cases(self, cases, fn):

        for inpt in cases:
            expected = cases[inpt]
            actual = fn(inpt)
            assert expected == actual, \
            'wanted ' + str(expected) + \
            ' but got ' + str(actual) + \
            ' for ' + fn.__name__ + '("' + str(inpt) + '")'

if __name__ == "__main__":
    unittest.main()