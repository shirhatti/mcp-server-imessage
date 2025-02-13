import unittest
from collections import namedtuple

from mcp_server_imessage.SnowflakeComponents import SnowflakeDecoder


class TestSnowflakeDecoder(unittest.TestCase):
    def test_decode_snowflake_id(self):
        decoder = SnowflakeDecoder()
        TestCase = namedtuple("TestCase", ["snowflake_id", "timestamp_ms"])
        test_cases = [
            TestCase(760592585637712896, 1738899785633),
            TestCase(760506735602625664, 1738813935600),
        ]

        for test_case in test_cases:
            components = decoder.decode(test_case.snowflake_id)
            self.assertIsNotNone(components)
            self.assertEqual(components.timestamp_ms, test_case.timestamp_ms)
