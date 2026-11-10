import hashlib


def base_window(seed: int) -> int:
    """Return deterministic per-seed coverage duration, not a secret challenge."""
    digest = hashlib.sha256(f"CFR18:stability-window-v1:{seed}".encode()).hexdigest()
    return 100 + (int(digest[:8], 16) % 41)


def required_window(seed: int, elapsed_seconds: int = 0) -> int:
    """Return the public, reproducible stability duration for this scenario."""
    base = base_window(seed)
    penalty = max(0, elapsed_seconds - 1800) // 60 * 2
    return min(300, base + penalty)
