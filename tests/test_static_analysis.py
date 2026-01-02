"""Regression tests that lock down global constants required by contracts."""

from bot_neutro.api import STATS_MAX_SESSIONS
from bot_neutro.llm_tiers import TIER_FREEMIUM, TIER_ORDER, TIER_PREMIUM, TIERS
from bot_neutro.metrics_runtime import METRICS, InMemoryMetrics


def test_stats_max_sessions_constant_is_present() -> None:
    assert isinstance(STATS_MAX_SESSIONS, int)
    assert STATS_MAX_SESSIONS >= 0


def test_llm_tier_constants_are_preserved() -> None:
    assert TIER_FREEMIUM == "freemium"
    assert TIER_PREMIUM == "premium"
    assert TIERS == {TIER_FREEMIUM, TIER_PREMIUM}
    assert TIER_ORDER[TIER_FREEMIUM] < TIER_ORDER[TIER_PREMIUM]


def test_metrics_singleton_is_preserved() -> None:
    assert isinstance(METRICS, InMemoryMetrics)
