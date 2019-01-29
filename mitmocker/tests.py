import unittest
from mitmocker import MitmMockServer
import os


def match(expression):
    return type('obj', (object,), { 'group' : lambda _=None:  expression })


class MitmMockServerTest(unittest.TestCase):

    srv = None

    def setUp(self):
        self.srv = MitmMockServer(os.path.dirname(os.path.realpath(__file__)))
        self.srv.log = lambda message: print('')
        self.srv.warn = lambda message: print(message)

    def test_match_empty(self):
        out = self.srv.match_func(match(''))
        self.assertEqual(out, None, 'Empty expression should return None.')

    def test_match_invalid(self):
        out = self.srv.match_func(match('$'))
        self.assertEqual(out, None, 'Bad expression should return None.')

    def test_match_variable(self):
        self.srv.testvar = 123.456
        out = self.srv.match_func(match('$testvar'))
        self.assertEqual(out, str(self.srv.testvar), 'Expression should be replaced with value.')

    def test_match_expression(self):
        self.srv.testvar = 123.456
        out = self.srv.match_func(match('math.ceil($testvar)'))
        self.assertEqual(out, str(124), 'Expression should be replaced and evaluated.')

    def test_match_assign_expression_to_variable(self):
        self.srv.testvar = 123.456
        out = self.srv.match_func(match('math.ceil($testvar)||othervar'))
        self.assertEqual(out, str(124), 'Expression should be replaced, evaluated and assigned to new variable.')

        new_out = self.srv.match_func(match('$othervar'))

        self.assertEqual(new_out, '124')


if __name__ == '__main__':
    unittest.main()