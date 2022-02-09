SKIP_API_TESTS = True
SKIP_IMAGE_TESTS = True

if __name__ == "__main__":
    import unittest

    loader = unittest.TestLoader()

    runner = unittest.TextTestRunner()

    runner.run(loader.discover("tests/"))
