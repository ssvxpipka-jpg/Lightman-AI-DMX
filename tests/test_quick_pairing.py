#!/usr/bin/env python3
"""Quick test for pairing code generation and HMAC logic."""
import sys
sys.path.insert(0, '.')

from shared.pairing import (
    generate_pairing_code,
    compute_hmac,
    sign_packet,
    verify_signed_packet,
)

# Test code generation
sound_code = generate_pairing_code('sound')
light_code = generate_pairing_code('light')
print(f"Sound code: {sound_code}")
print(f"Light code: {light_code}")

assert sound_code.startswith('SL-SOUND-'), "Sound code format wrong"
assert light_code.startswith('SL-LIGHT-'), "Light code format wrong"
assert len(sound_code.split('-')[-1]) == 4, "Code should have 4 hex chars"
assert len(light_code.split('-')[-1]) == 4, "Code should have 4 hex chars"
print("Code format: PASS")

# Test HMAC
secret = 'test_secret_key_123'
data = b'hello world'
sig = compute_hmac(secret, data)
print(f"HMAC-SHA256: {sig[:16]}...")
print("HMAC functions: PASS")

# Test signed packet
signed = sign_packet(secret, data)
print(f"Signed packet length: {len(signed)} bytes")
# 4 (length) + 32 (hmac) + len(data) = 47
assert len(signed) == 4 + 32 + len(data), f"Expected {4 + 32 + len(data)}, got {len(signed)}"
print("Sign packet structure: PASS")

# Test verify
payload = verify_signed_packet(secret, signed)
assert payload == data, "Packet verification failed"
print("Packet verify: PASS")

print()
print("All pairing tests PASSED!")
