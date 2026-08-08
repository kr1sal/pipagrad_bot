from __future__ import annotations

from enum import Enum


class DickHistoryReason(str, Enum):
    GROW = "grow"
    GIFT_SENT = "gift_sent"
    GIFT_RECEIVED = "gift_received"
    METEOR = "meteor"
    RADIATION = "radiation"
    SPONTANEOUS_BATTLE = "spontaneous_battle"
    HURRICANE = "hurricane"
    RANDOM_GIFT = "random_gift"
    ROYAL_BATTLE = "royal_battle"
    ORGY = "orgy"
    TEAM_BATTLE = "team_battle"
    EXCHANGE = "exchange"  # converted into PipaCoin
