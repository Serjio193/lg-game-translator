"""Decode the deployed ARM32 legacy microsecond timestamp for telemetry only."""


def capture_age_ms(captured_ms, now_ms):
    if not isinstance(captured_ms, int) or captured_ms <= 0:
        return None, "unavailable"
    if captured_ms <= now_ms:
        age = now_ms-captured_ms
        if age <= 60000:
            return age, "monotonic_ms"
    # Deployed getticks_us(): signed ARM32 tv_sec * 1000000 expression,
    # sign-extended to uint64, then divided by 1000. Lost precision <1 ms.
    raw_us = captured_ms*1000
    low = raw_us % (1 << 32)
    now_us = now_ms*1000
    turn = round((now_us-low)/(1 << 32))
    restored_us = low+turn*(1 << 32)
    age = (now_us-restored_us)/1000
    if -.999 <= age <= 60000:
        return max(0, age), "legacy_arm32_wrap_recovered_lt_1ms"
    return None, "invalid_or_stale_capture_timestamp"
