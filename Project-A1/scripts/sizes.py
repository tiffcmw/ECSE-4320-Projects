"""Shared size sweeps."""


def chase_sizes(quick=False):
    """4 KB to 2 GB, 2 points per octave (1 per octave when quick), multiples of 128 B."""
    step = 1.0 if quick else 0.5
    out, k = [], 0.0
    while True:
        b = int(round(4096 * 2 ** k / 128)) * 128
        if b > 2 * 1024 ** 3:
            break
        out.append(b)
        k += step
    return sorted(set(out))


def bw_sizes(quick=False):
    """16 KB to 1 GB, 1 point per octave (every other octave when quick)."""
    sizes = [16384 * 2 ** k for k in range(0, 17)]
    return sizes[::2] if quick else sizes
