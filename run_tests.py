import unittest


if __name__ == "__main__":
    loader = unittest.TestLoader()

    runner = unittest.TextTestRunner()

    runner.run(loader.discover("tests/"))