import unittest

from alerts import Alerts


class foo_alert(str): pass

class foo_bar_alert(foo_alert): pass

class foo_baz_alert(foo_alert): pass

class foo_baz_paf_alert(foo_baz_alert): pass


MSG = 'hello'


class TestAlerts(unittest.TestCase):

    def setUp(self):
        self.a = Alerts()
        self.r = []

    def test_simple(self):
        self.a.on(foo_bar_alert, self.r.append)
        self.a.on(foo_baz_alert, self.r.append)
        self.a.on(foo_baz_paf_alert, self.r.append)
        self.a.emit(foo_baz_alert(MSG))
        self.assertEqual(self.r.pop(), MSG)
        self.assertFalse(self.r)

    def test_hierarchy(self):
        self.a.on(foo_alert, self.r.append)
        self.a.emit(foo_alert(MSG))
        self.assertEqual(self.r.pop(), MSG)
        self.a.emit(foo_bar_alert(MSG))
        self.assertEqual(self.r.pop(), MSG)
        self.a.emit(foo_baz_alert(MSG))
        self.assertEqual(self.r.pop(), MSG)
        self.a.emit(foo_baz_paf_alert(MSG))
        self.assertEqual(self.r.pop(), MSG)
        self.assertFalse(self.r)

    def test_multiple_listeners(self):
        self.a.on(foo_alert, self.r.append)
        self.a.on(foo_alert, self.r.append)
        self.a.emit(foo_alert(MSG))
        self.assertEqual(self.r.pop(), MSG)
        self.assertEqual(self.r.pop(), MSG)
        self.assertFalse(self.r)


if __name__ == '__main__':
    unittest.main()
