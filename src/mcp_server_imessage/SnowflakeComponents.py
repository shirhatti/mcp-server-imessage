from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class SnowflakeComponents:
    """Contains the decoded components of a Snowflake ID."""

    timestamp_ms: int
    sequence: int
    worker_id: int
    process_id: int
    raw_timestamp: int
    datetime_utc: datetime


class SnowflakeDecoder:
    """Decoder for Snowflake IDs using 2^22 nanosecond timestamp precision."""

    # Epoch (January 1, 2001 00:00:00.000 UTC)
    EPOCH = int(datetime(2001, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)

    # Each timestamp unit represents 2^22 nanoseconds
    NANOS_PER_UNIT = 1 << 22  # 2^22 nanoseconds
    NANOS_PER_MS = 1_000_000  # 10^6 nanoseconds

    # Bit lengths
    TIMESTAMP_BITS = 42
    WORKER_BITS = 10
    PROCESS_BITS = 5
    SEQUENCE_BITS = 7

    # Bit masks
    TIMESTAMP_MASK = (1 << TIMESTAMP_BITS) - 1
    WORKER_MASK = (1 << WORKER_BITS) - 1
    PROCESS_MASK = (1 << PROCESS_BITS) - 1
    SEQUENCE_MASK = (1 << SEQUENCE_BITS) - 1

    @classmethod
    def decode(cls, snowflake_id: int | str) -> SnowflakeComponents:
        """
        Decode a Snowflake ID into its component parts.

        Args:
            snowflake_id: The Snowflake ID to decode (can be int or string)

        Returns:
            SnowflakeComponents object containing the decoded parts
        """
        # Convert string to int if necessary
        snowflake = int(snowflake_id)

        # Extract components using bit operations
        raw_timestamp = (snowflake >> (cls.WORKER_BITS + cls.PROCESS_BITS + cls.SEQUENCE_BITS)) & cls.TIMESTAMP_MASK
        worker_id = (snowflake >> (cls.PROCESS_BITS + cls.SEQUENCE_BITS)) & cls.WORKER_MASK
        process_id = (snowflake >> cls.SEQUENCE_BITS) & cls.PROCESS_MASK
        sequence = snowflake & cls.SEQUENCE_MASK

        # Convert to milliseconds using exact nanosecond math
        ms_since_epoch = (raw_timestamp * cls.NANOS_PER_UNIT) // cls.NANOS_PER_MS
        timestamp_ms = cls.EPOCH + ms_since_epoch

        # Convert to datetime objects
        dt_utc = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)

        return SnowflakeComponents(
            timestamp_ms=timestamp_ms,
            sequence=sequence,
            worker_id=worker_id,
            process_id=process_id,
            raw_timestamp=raw_timestamp,
            datetime_utc=dt_utc,
        )
