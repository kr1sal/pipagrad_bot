from __future__ import annotations

import secrets


class SystemRandomizer:
    def int_between(self, low: int, high_inclusive: int) -> int:
        if high_inclusive < low:
            raise ValueError("high must be >= low")
        span = high_inclusive - low + 1
        return low + secrets.randbelow(span)
