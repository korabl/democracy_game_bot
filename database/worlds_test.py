import unittest

from database.worlds import World


class MyTestCase(unittest.TestCase):
    def test_insert_world(self):
        world = World()
        world.save(1, "test description")
        self.assertEqual(True, True)  # add assertion here

    def test_get_world(self):
        world = World()
        result = world.get(1)
        print(result)
        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
