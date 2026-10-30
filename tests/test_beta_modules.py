#!/usr/bin/env python3
"""Test i18n and blackout_guard modules."""
import sys
sys.path.insert(0, '.')

from shared.i18n import _, set_language, get_available_languages

# Test English
set_language('en')
assert _('Studio') == 'Studio'
assert _('Login') == 'Login'

# Test Russian
set_language('ru')
assert _('Studio') == 'Студио'
assert _('Login') == 'Вход'

# Unknown key fallback
assert _('NonExistentKey') == 'NonExistentKey'

# Available languages
langs = get_available_languages()
assert ('en', 'English') in langs
assert ('ru', 'Русский') in langs

print("i18n tests PASSED!")

set_language('en')

# ─── Blackout Guard Tests ───────────────────────────────────────────

from shared.blackout_guard import BlackoutGuard

print("\n--- BLACKOUT TESTS ---")

# Test 1: 0% rule applies to ALL modes (including follow_only)
print("\nTest 1: 0% rule in follow_only mode")
guard = BlackoutGuard('follow_only')
guard.set_level(0.0)
assert not guard.can_ai_adjust(), "follow_only: AI should not adjust at 0%"
assert guard.state.live_light_muted, "follow_only: Live Light MUST be muted at 0%"
assert guard.state.tracking_muted, "follow_only: Tracking MUST be muted at 0%"
assert guard.get_adjusted_level(1.0) == 0.0, "0% must clamp ALL output to 0"
print("  PASS: 0% in follow_only — AI holds 0%, Live Light/Tracking MUTED")

# Test 2: 0% rule in full_auto
print("\nTest 2: 0% rule in full_auto mode")
guard = BlackoutGuard('full_auto')
guard.set_level(0.0)
assert not guard.can_ai_adjust()
assert guard.state.live_light_muted
assert guard.state.tracking_muted
assert guard.get_adjusted_level(1.0) == 0.0
print("  PASS: 0% in full_auto — AI holds 0%, Live Light/Tracking MUTED")

# Test 3: 0% rule in assist
print("\nTest 3: 0% rule in assist mode")
guard = BlackoutGuard('assist')
guard.set_level(0.0)
assert not guard.can_ai_adjust()
assert guard.state.live_light_muted
assert guard.state.tracking_muted
print("  PASS: 0% in assist — AI holds 0%, Live Light/Tracking MUTED")

# Test 4: 1-5% — AI does NOT increase
print("\nTest 4: 1-5% rule")
guard = BlackoutGuard('assist')
guard.set_level(0.03)  # 3%
assert not guard.can_ai_adjust(), "AI should NOT increase at 3%"
print("  PASS: 1-5% — AI does NOT increase brightness")

# Test 5: >5% — AI works
print("\nTest 5: >5% rule")
guard = BlackoutGuard('full_auto')
guard.set_level(0.10)  # 10%
assert guard.can_ai_adjust()
print("  PASS: >5% — AI works within limits")

# Test 6: follow_only above 0% — AI disabled, tracking active
print("\nTest 6: follow_only above 0%")
guard = BlackoutGuard('follow_only')
guard.set_level(0.50)
assert not guard.can_ai_adjust(), "follow_only: AI should never control"
assert not guard.state.tracking_muted, "follow_only: tracking should NOT be muted above 0%"
print("  PASS: follow_only at 50% — AI disabled, tracking active")

# Test 7: SACRED RULE — get_adjusted_level returns 0 at blackout
print("\nTest 7: SACRED RULE — get_adjusted_level returns 0 at 0%")
for mode in ['full_auto', 'assist', 'follow_only']:
    guard = BlackoutGuard(mode)
    guard.set_level(0.0)
    assert guard.get_adjusted_level(1.0) == 0.0, f"Mode {mode}: 0% must return 0"
    assert guard.get_adjusted_level(0.5) == 0.0, f"Mode {mode}: 0% must clamp all"
print("  PASS: All modes return 0% at blackout level")

print("\n--- LIGHT ENGINE TESTS ---")

from shared.light_engine import LightEngine

# Test LightEngine in assist mode (above blackout level)
engine = LightEngine('assist')
engine.set_level(0.10)  # 10% — above blackout
result = engine.ai_request_level(0.8)
assert result == 0.8
print("  PASS: LightEngine assist at 10%: AI request passes")

# Test LightEngine at 0% — AI cannot increase (sacred rule)
engine = LightEngine('assist')
engine.set_level(0.0)
result = engine.ai_request_level(0.8)
assert result == 0.0, "0% must clamp AI request to 0"
print("  PASS: LightEngine assist at 0%: AI request clamped to 0")

# Test LightEngine 0% rule across ALL modes
for mode in ['full_auto', 'assist', 'follow_only']:
    engine = LightEngine(mode)
    engine.set_level(0.0)
    # AI request at 0% must return 0
    result = engine.ai_request_level(1.0)
    assert result == 0.0, f"Mode {mode}: 0% must return 0 for AI request"
    # Direct request at 0% must also return 0
    result = engine.direct_request_level(1.0)
    assert result == 0.0, f"Mode {mode}: 0% must return 0 for direct request"
print("  PASS: LightEngine 0% rule applies to ALL modes (AI and direct)")

# Test follow_only above 0% — AI disabled, direct control works
engine = LightEngine('follow_only')
engine.set_level(0.50)
ai_result = engine.ai_request_level(1.0)
direct_result = engine.direct_request_level(1.0)
assert ai_result == 0.5, f"follow_only: AI should not control, got {ai_result}"
assert direct_result == 1.0, f"follow_only: direct should work, got {direct_result}"
print("  PASS: follow_only at 50%: AI returns current, direct set to 1.0")

print("\nAll tests PASSED!")

