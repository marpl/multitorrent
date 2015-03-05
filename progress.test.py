import unittest

from progress import Progress


class TestProgress(unittest.TestCase):

    def setUp(self):
        self.p = Progress(100)
        self.assertTrue(self.p.add(40, 20))
        self.assertEqual(self.p.have, [(40, 60)])
        self.assertFalse(self.p.is_complete)

    def test_already_have(self):
        self.assertFalse(self.p.add(45, 10))
        self.assertEqual(self.p.have, [(40, 60)])
        self.assertFalse(self.p.is_complete)

    def test_join_left(self):
        self.assertTrue(self.p.add(30, 10))
        self.assertEqual(self.p.have, [(30, 60)])
        self.assertFalse(self.p.is_complete)

    def test_overlap_left(self):
        self.assertTrue(self.p.add(30, 20))
        self.assertFalse(self.p.is_complete)
        self.assertEqual(self.p.have, [(30, 60)])

    def test_join_right(self):
        self.assertTrue(self.p.add(60, 10))
        self.assertEqual(self.p.have, [(40, 70)])
        self.assertFalse(self.p.is_complete)

    def test_overlap_right(self):
        self.assertTrue(self.p.add(50, 20))
        self.assertEqual(self.p.have, [(40, 70)])
        self.assertFalse(self.p.is_complete)

    def test_overlap_both(self):
        self.assertTrue(self.p.add(10, 80))
        self.assertEqual(self.p.have, [(10, 90)])
        self.assertFalse(self.p.is_complete)

    def test_join_both(self):
        self.assertTrue(self.p.add(0, 20))
        self.assertTrue(self.p.add(20, 20))
        self.assertTrue(self.p.add(80, 20))
        self.assertTrue(self.p.add(60, 20))
        self.assertEqual(self.p.have, [(0, 100)])
        self.assertTrue(self.p.is_complete)

    def test_add_all(self):
        self.assertTrue(self.p.add(0, 100))
        self.assertTrue(self.p.is_complete)


if __name__ == '__main__':
    unittest.main()
