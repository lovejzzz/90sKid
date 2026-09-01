"""Numba kernels for the hot loops (all optional; NumPy fallbacks exist).

* trilinear lattice sampling
* speed-layer activation probabilities
* the 9x9 population transport contraction used by deterministic and
  stochastic DIR coupling
* a counter-based, thread-safe finite-site sampler ("philox_numba"): every
  pixel draws from its own SplitMix64 stream keyed by (seed, class, pixel),
  so the realization is independent of thread count and chunking.
"""

from __future__ import annotations

import numpy as np

try:
    import numba

    HAVE_NUMBA = True
except Exception:  # pragma: no cover
    HAVE_NUMBA = False


if HAVE_NUMBA:

    @numba.njit(parallel=True, cache=True, fastmath=False)
    def trilinear_sample(lut, index):
        """lut: (S,S,S,3) float32; index: (N,3) float32 fractional indices in [0,S-1)."""
        n = index.shape[0]
        size = lut.shape[0]
        out = np.empty((n, 3), dtype=np.float32)
        for i in numba.prange(n):
            fa = index[i, 0]
            fb = index[i, 1]
            fc = index[i, 2]
            a0 = int(fa)
            b0 = int(fb)
            c0 = int(fc)
            if a0 >= size - 1:
                a0 = size - 2
            if b0 >= size - 1:
                b0 = size - 2
            if c0 >= size - 1:
                c0 = size - 2
            ta = fa - a0
            tb = fb - b0
            tc = fc - c0
            a1 = a0 + 1
            b1 = b0 + 1
            c1 = c0 + 1
            for k in range(3):
                x00 = lut[a0, b0, c0, k] * (1.0 - ta) + lut[a1, b0, c0, k] * ta
                x01 = lut[a0, b0, c1, k] * (1.0 - ta) + lut[a1, b0, c1, k] * ta
                x10 = lut[a0, b1, c0, k] * (1.0 - ta) + lut[a1, b1, c0, k] * ta
                x11 = lut[a0, b1, c1, k] * (1.0 - ta) + lut[a1, b1, c1, k] * ta
                out[i, k] = (x00 * (1.0 - tc) + x01 * tc) * (1.0 - tb) + (x10 * (1.0 - tc) + x11 * tc) * tb
        return out

    @numba.njit(parallel=True, cache=True)
    def activations(log_exposure, centres, widths):
        """log_exposure (N,3) -> (N,3,3) sigmoid speed-layer activation."""
        n = log_exposure.shape[0]
        out = np.empty((n, 3, 3), dtype=np.float32)
        for i in numba.prange(n):
            for c in range(3):
                for p in range(3):
                    a = (log_exposure[i, c] - centres[c, p]) / widths[c]
                    if a > 16.0:
                        a = 16.0
                    elif a < -16.0:
                        a = -16.0
                    out[i, c, p] = np.float32(1.0 / (1.0 + np.exp(-a)))
        return out

    @numba.njit(parallel=True, cache=True)
    def transport_contract(source, tensor, gate, scale):
        """out[i,d,q] = scale * gate[i,d,q] * sum_{s,p} tensor[d,q,s,p] * source[i,s,p]."""
        n = source.shape[0]
        out = np.empty((n, 3, 3), dtype=np.float32)
        for i in numba.prange(n):
            for d in range(3):
                for q in range(3):
                    acc = 0.0
                    for s in range(3):
                        for p in range(3):
                            t = tensor[d, q, s, p]
                            if t != 0.0:
                                acc += t * source[i, s, p]
                    out[i, d, q] = np.float32(scale * gate[i, d, q] * acc)
        return out

    @numba.njit(cache=True, inline="always")
    def _splitmix(state):
        state = (state + np.uint64(0x9E3779B97F4A7C15)) & np.uint64(0xFFFFFFFFFFFFFFFF)
        z = state
        z = ((z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)) & np.uint64(0xFFFFFFFFFFFFFFFF)
        z = ((z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)) & np.uint64(0xFFFFFFFFFFFFFFFF)
        z = z ^ (z >> np.uint64(31))
        return state, z

    @numba.njit(cache=True, inline="always")
    def _uniform(state):
        state, z = _splitmix(state)
        return state, (np.float64(z >> np.uint64(11)) + 0.5) * (1.0 / 9007199254740992.0)

    @numba.njit(parallel=True, cache=True)
    def counter_binomial(probability, n, key):
        """Finite-site developed counts, one independent stream per pixel.

        Exact inversion when n*min(p,1-p) is small; otherwise the normal
        approximation of the same binomial law (n up to a few thousand sites
        per pixel makes the skewness negligible), rounded to an integer count
        and bounded by the site population.
        """
        h, w = probability.shape
        out = np.empty((h, w), dtype=np.float32)
        base = (np.uint64(key) * np.uint64(0xD1B54A32D192ED03)) & np.uint64(0xFFFFFFFFFFFFFFFF)
        nn = float(n)
        for y in numba.prange(h):
            for x in range(w):
                p = probability[y, x]
                if p <= 0.0:
                    out[y, x] = 0.0
                    continue
                if p >= 1.0:
                    out[y, x] = nn
                    continue
                state = (base ^ (np.uint64(y * w + x) * np.uint64(0x9E3779B97F4A7C15))) & np.uint64(0xFFFFFFFFFFFFFFFF)
                state, u = _uniform(state)
                mirror = p > 0.5
                q = 1.0 - p if mirror else p
                mean_small = nn * q
                if mean_small * (1.0 - q) >= 30.0:
                    # Box-Muller normal approximation of Binomial(n, p)
                    state, u2 = _uniform(state)
                    g = np.sqrt(-2.0 * np.log(u)) * np.cos(6.283185307179586 * u2)
                    value = np.floor(nn * p + g * np.sqrt(nn * p * (1.0 - p)) + 0.5)
                else:
                    # inversion on the smaller tail
                    prob = (1.0 - q) ** nn
                    cdf = prob
                    k = 0.0
                    while u > cdf and k < nn:
                        prob *= (nn - k) / (k + 1.0) * q / (1.0 - q)
                        k += 1.0
                        cdf += prob
                    value = nn - k if mirror else k
                if value < 0.0:
                    value = 0.0
                elif value > nn:
                    value = nn
                out[y, x] = np.float32(value)
        return out

    @numba.njit(parallel=True, cache=True)
    def status_m_index(density, maximum, inv_power, top):
        """Fractional lattice index for a power-spaced axis (N,3)."""
        n = density.shape[0]
        out = np.empty((n, 3), dtype=np.float32)
        for i in numba.prange(n):
            for k in range(3):
                u = density[i, k] / maximum
                if u < 0.0:
                    u = 0.0
                elif u > 1.0:
                    u = 1.0
                if inv_power != 1.0:
                    u = u**inv_power
                v = u * top
                if v > top - 1e-5:
                    v = top - 1e-5
                out[i, k] = np.float32(v)
        return out


if HAVE_NUMBA:

    @numba.njit(parallel=True, cache=True)
    def dir_pointwise(net, neutral_net, act, neutral_act, fractions, capacity):
        """Speed-layer densities and inhibitor release for actual and neutral exposure.

        net/neutral_net: (N,3) net density above D-min; act/neutral_act: (N,3,3).
        Returns layer (N,3,3), release (N,3,3), departure (N,3,3).
        """
        n = net.shape[0]
        layer = np.empty((n, 3, 3), dtype=np.float32)
        release = np.empty((n, 3, 3), dtype=np.float32)
        departure = np.empty((n, 3, 3), dtype=np.float32)
        for i in numba.prange(n):
            for c in range(3):
                total = 0.0
                ntotal = 0.0
                for p in range(3):
                    total += act[i, c, p] * fractions[p]
                    ntotal += neutral_act[i, c, p] * fractions[p]
                if total < 1e-8:
                    total = 1e-8
                if ntotal < 1e-8:
                    ntotal = 1e-8
                for p in range(3):
                    cap = capacity[c, p]
                    if cap < 1e-6:
                        cap = 1e-6
                    ld = net[i, c] * act[i, c, p] * fractions[p] / total
                    nd = neutral_net[i, c] * neutral_act[i, c, p] * fractions[p] / ntotal
                    r = 1.0 - np.exp(-1.45 * ld / cap)
                    nr = 1.0 - np.exp(-1.45 * nd / cap)
                    layer[i, c, p] = np.float32(ld)
                    release[i, c, p] = np.float32(r)
                    departure[i, c, p] = np.float32(r - nr)
        return layer, release, departure

    @numba.njit(parallel=True, cache=True)
    def dir_finish(layer, correction, capacity, dmin):
        """Clip corrected layers to 1.08 x capacity and sum with D-min -> (N,3)."""
        n = layer.shape[0]
        out = np.empty((n, 3), dtype=np.float32)
        for i in numba.prange(n):
            for c in range(3):
                acc = 0.0
                for p in range(3):
                    v = layer[i, c, p] + correction[i, c, p]
                    top = capacity[c, p] * 1.08
                    if v < 0.0:
                        v = 0.0
                    elif v > top:
                        v = top
                    acc += v
                out[i, c] = np.float32(acc + dmin[c])
        return out

    @numba.njit(parallel=True, cache=True)
    def receiver_marginal(act):
        n = act.shape[0]
        out = np.empty((n, 3, 3), dtype=np.float32)
        for i in numba.prange(n):
            for c in range(3):
                for p in range(3):
                    v = 4.0 * act[i, c, p] * (1.0 - act[i, c, p])
                    if v < 0.0:
                        v = 0.0
                    elif v > 1.0:
                        v = 1.0
                    out[i, c, p] = np.float32(v)
        return out
