"""5279 negative formation: exposure, H-D curves, DIR development and grain.

The model reproduces the research engine's V72 evidence-minimal record
formation and the V49 conservative common-density publication:

* three colour records with Kodak's published Status-M H-D curves
* fast / medium / slow finite silver-halide site populations per record
* development-inhibitor release (DIR) coupling between layers
* five dye-cloud size classes per population, sampled as seeded binomial
  developed fractions, integrated through the cloud kernel and optics
* normalisation of a uniform field to Kodak's 48 um RMS granularity curves
* the V49 boundary that keeps only the scalar density common to the records
* the processed-negative MTF with developer adjacency

Spatial parameters are defined in pixels at 5760 px across a 24.9 mm gate;
``native_scale`` converts them to the working raster and film gauge.
"""

from __future__ import annotations

import concurrent.futures
import functools
import math

import cv2
import numpy as np

from . import fast, priors
from .colour import REC709_TO_XYZ_D65, XYZ_D65_TO_REC709, luma, smoothstep

REFERENCE_PIXELS_PER_MM = 5760.0 / 24.9
_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="film5279-grain")


def native_scale_for(width: int, gate_width_mm: float, oversample: int = 1) -> float:
    """Ratio between the working pixel pitch and the 5760-px Super 35 reference."""
    return (width / float(gate_width_mm)) / REFERENCE_PIXELS_PER_MM * oversample


# ---------------------------------------------------------------------------
# Scene preparation
# ---------------------------------------------------------------------------


def separate_sensor_noise(scene_linear: np.ndarray, native_scale: float) -> np.ndarray:
    """Restrained edge-aware separation of electronic noise before the emulsion."""
    source = np.asarray(scene_linear, dtype=np.float32)
    if source.shape[0] < 4 or source.shape[1] < 4:
        return source.copy()
    y = np.einsum("...c,c->...", source, [0.2627, 0.6780, 0.0593]).astype(np.float32)
    luma_low = cv2.GaussianBlur(y, (0, 0), max(0.55 * native_scale, 0.10), borderType=cv2.BORDER_REFLECT)
    chroma = source - y[..., None]
    chroma_low = cv2.GaussianBlur(chroma, (0, 0), max(0.78 * native_scale, 0.10), borderType=cv2.BORDER_REFLECT)
    edge_source = cv2.GaussianBlur(y, (0, 0), max(0.70 * native_scale, 0.10), borderType=cv2.BORDER_REFLECT)
    gx = cv2.Sobel(edge_source, cv2.CV_32F, 1, 0, ksize=3, scale=0.125)
    gy = cv2.Sobel(edge_source, cv2.CV_32F, 0, 1, ksize=3, scale=0.125)
    relative_edge = np.sqrt(gx * gx + gy * gy) / (np.abs(luma_low) + 0.03)
    flat = 1.0 - smoothstep(0.025, 0.14, relative_edge)
    shadow = 1.0 - smoothstep(0.35, 1.25, np.maximum(luma_low, 0.0))
    signal = 0.65 + 0.35 * shadow
    luma_weight = priors.SENSOR_NOISE_LUMA_FLAT_REMOVAL * flat * signal
    chroma_weight = priors.SENSOR_NOISE_CHROMA_FLAT_REMOVAL * flat * signal
    treated_luma = y + luma_weight * (luma_low - y)
    treated_chroma = chroma + chroma_weight[..., None] * (chroma_low - chroma)
    return (treated_luma[..., None] + treated_chroma).astype(np.float32)


_BRADFORD = np.array([[0.8951, 0.2664, -0.1614], [-0.7502, 1.7135, 0.0367], [0.0389, -0.0685, 1.0296]])
_D50 = np.array([0.96422, 1.0, 0.82521])
_D65 = np.sum(np.asarray(priors.BT2020_TO_XYZ_D65, dtype=np.float64), axis=1)
_BRADFORD_D65_TO_D50 = np.linalg.inv(_BRADFORD) @ np.diag((_BRADFORD @ _D50) / (_BRADFORD @ _D65)) @ _BRADFORD
_BRADFORD_D50_TO_D65 = np.linalg.inv(_BRADFORD_D65_TO_D50)


def input_chroma_residual(rec709_linear: np.ndarray, strength: float) -> np.ndarray:
    """V41 chart-informed chroma residual (neutral- and luminance-preserving)."""
    source = np.asarray(rec709_linear, dtype=np.float32)
    if strength == 0.0:
        return source
    xyz_d65 = np.einsum("...c,dc->...d", source, REC709_TO_XYZ_D65.astype(np.float32))
    xyz_d50 = np.einsum("...c,dc->...d", xyz_d65, _BRADFORD_D65_TO_D50.astype(np.float32))
    neutral = xyz_d50[..., 1:2] * _D50.astype(np.float32)
    chroma = xyz_d50 - neutral
    mapped = np.einsum("...c,cd->...d", chroma, priors.INPUT_CHROMA_RESIDUAL_D50)
    corrected = chroma + strength * (mapped - chroma)
    corrected[..., 1] = 0.0
    corrected_d65 = np.einsum("...c,dc->...d", neutral + corrected, _BRADFORD_D50_TO_D65.astype(np.float32))
    scale = xyz_d65[..., 1] / np.where(np.abs(corrected_d65[..., 1]) > 1e-8, corrected_d65[..., 1], 1e-8)
    corrected_d65 *= scale[..., None]
    return np.einsum("...c,dc->...d", corrected_d65, XYZ_D65_TO_REC709.astype(np.float32)).astype(np.float32)


def add_optical_scatter(film_rgb: np.ndarray, native_scale: float, strength: float = 1.0) -> np.ndarray:
    """Rem-jet-limited red halation and base light spread above diffuse white."""
    if strength <= 0.0:
        return np.asarray(film_rgb, dtype=np.float32)
    y = luma(np.clip(film_rgb, 0.0, None))
    source = smoothstep(0.90, 3.5, y)
    near = cv2.GaussianBlur(source, (0, 0), max(5.5 * native_scale, 0.1))
    far = cv2.GaussianBlur(source, (0, 0), max(18.0 * native_scale, 0.1))
    halo = (0.035 * near + 0.014 * far) * strength
    return (film_rgb + halo[..., None] * np.array([1.0, 0.22, 0.045], dtype=np.float32)).astype(np.float32)


def film_records(film_rgb: np.ndarray) -> np.ndarray:
    """Three record exposures; signed basis allowed when all records stay positive."""
    source = np.asarray(film_rgb, dtype=np.float32)
    records = np.einsum("...c,dc->...d", source, priors.FILM_RECORD_SENSITIVITY_RGB).astype(np.float32)
    clipped = np.einsum("...c,dc->...d", np.maximum(source, 0.0), priors.FILM_RECORD_SENSITIVITY_RGB).astype(np.float32)
    valid = np.all(records >= 0.0, axis=-1, keepdims=True)
    return np.maximum(np.where(valid, records, clipped), 0.0).astype(np.float32)


def log_exposure_from_records(records: np.ndarray) -> np.ndarray:
    return (np.log10(np.maximum(records, 1e-8)) - 1.0).astype(np.float32)


# ---------------------------------------------------------------------------
# Sensitometry and development
# ---------------------------------------------------------------------------


def hd_density(log_exposure: np.ndarray) -> np.ndarray:
    """Kodak's three published Status-M H-D curves (V72 identity record mix)."""
    out = np.empty_like(log_exposure, dtype=np.float32)
    for c in range(3):
        out[..., c] = np.interp(log_exposure[..., c], priors.SENSITO_LOG_EXPOSURE, priors.SENSITO_DENSITY_RGB[c]).astype(np.float32)
    return out


def activation_probabilities(log_exposure: np.ndarray) -> np.ndarray:
    centres = (priors.SUBEMULSION_FAST_CENTRE_LOGE_RGB[:, None] + priors.SUBEMULSION_SPEED_OFFSETS_LOGE[None, :]).astype(np.float32)
    if fast.HAVE_NUMBA and log_exposure.size >= 3 * 4096:
        flat = np.ascontiguousarray(np.asarray(log_exposure, dtype=np.float32).reshape(-1, 3))
        return fast.activations(flat, np.ascontiguousarray(centres), np.ascontiguousarray(priors.SUBEMULSION_TRANSITION_WIDTH_RGB, dtype=np.float32)).reshape(log_exposure.shape + (3,))
    widths = priors.SUBEMULSION_TRANSITION_WIDTH_RGB[:, None]
    argument = np.clip((log_exposure[..., :, None] - centres) / widths, -16.0, 16.0)
    return (1.0 / (1.0 + np.exp(-argument))).astype(np.float32)


def granularity_sigma(log_exposure: np.ndarray) -> np.ndarray:
    out = np.empty_like(log_exposure, dtype=np.float32)
    for c in range(3):
        out[..., c] = np.interp(log_exposure[..., c], priors.GRANULARITY_LOG_EXPOSURE, priors.GRANULARITY_SIGMA_D_RGB[c]).astype(np.float32)
    return out


def _layer_capacity() -> np.ndarray:
    net_capacity = priors.SENSITO_DENSITY_RGB[:, -1] - priors.SENSITO_DMIN_RGB
    return (net_capacity[:, None] * priors.SUBEMULSION_CAPACITY_FRACTIONS[None, :]).astype(np.float32)


@functools.lru_cache(maxsize=1)
def _interimage_transport_tensor() -> np.ndarray:
    """T[d_rec, d_pop, s_rec, s_pop]: deterministic inter-record DIR transport."""
    t = np.zeros((3, 3, 3, 3), dtype=np.float32)
    for d_rec in range(3):
        for s_rec in range(3):
            record_transport = priors.DIR_INTERIMAGE_RECEIVER_CAUSER[d_rec, s_rec]
            if record_transport <= 0.0:
                continue
            for d_pop in range(3):
                for s_pop in range(3):
                    t[d_rec, d_pop, s_rec, s_pop] = (
                        priors.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH
                        * record_transport
                        * priors.DIR_POPULATION_TRANSPORT[d_pop, s_pop]
                        * priors.DIR_POPULATION_RELEASE_GAIN[s_pop]
                        * priors.DIR_POPULATION_RECEIVER_GAIN[d_pop]
                    )
    return t


def _transport(source: np.ndarray, gate: np.ndarray, scale: float) -> np.ndarray:
    """gate * scale * (T contracted with source) over the 3x3 population grid."""
    tensor = _interimage_transport_tensor()
    if fast.HAVE_NUMBA:
        shape = source.shape
        out = fast.transport_contract(
            np.ascontiguousarray(source.reshape(-1, 3, 3), dtype=np.float32),
            np.ascontiguousarray(tensor, dtype=np.float32),
            np.ascontiguousarray(np.broadcast_to(gate, shape).reshape(-1, 3, 3), dtype=np.float32),
            np.float32(scale),
        )
        return out.reshape(shape)
    return (scale * np.einsum("hwsp,drsp->hwdr", source, tensor) * gate).astype(np.float32)


def develop_record_density(log_exposure: np.ndarray, activations: np.ndarray, native_scale: float) -> np.ndarray:
    """Distribute H-D density over speed layers and add local DIR departures."""
    if fast.HAVE_NUMBA:
        return _develop_record_density_fast(log_exposure, activations, native_scale)
    base = hd_density(log_exposure)
    net = np.maximum(base - priors.SENSITO_DMIN_RGB, 0.0)
    weight = activations * priors.SUBEMULSION_CAPACITY_FRACTIONS[None, None, None, :]
    weight /= np.maximum(np.sum(weight, axis=-1, keepdims=True), 1e-8)
    layer = net[..., None] * weight
    capacity = _layer_capacity()
    release = 1.0 - np.exp(-1.45 * layer / np.maximum(capacity[None, None, ...], 1e-6))

    neutral_le = np.repeat(np.mean(log_exposure, axis=-1, keepdims=True), 3, axis=-1)
    neutral_net = np.maximum(hd_density(neutral_le) - priors.SENSITO_DMIN_RGB, 0.0)
    neutral_weight = activation_probabilities(neutral_le) * priors.SUBEMULSION_CAPACITY_FRACTIONS[None, None, None, :]
    neutral_weight /= np.maximum(np.sum(neutral_weight, axis=-1, keepdims=True), 1e-8)
    neutral_release = 1.0 - np.exp(-1.45 * (neutral_net[..., None] * neutral_weight) / np.maximum(capacity[None, None, ...], 1e-6))
    receiver = np.clip(4.0 * activations * (1.0 - activations), 0.0, 1.0)
    departure = release - neutral_release
    correction = _dir_correction(release, departure, receiver, capacity, native_scale)
    corrected = np.clip(layer + correction, 0.0, capacity[None, None, ...] * 1.08)
    return (np.sum(corrected, axis=-1) + priors.SENSITO_DMIN_RGB).astype(np.float32)


def _dir_correction(release, departure, receiver, capacity, native_scale):
    """Intralayer adjacency plus inter-record inhibitor transport (all spatial)."""
    diffused_departure = np.empty_like(departure)
    correction = np.zeros_like(departure, dtype=np.float32)
    for s_rec in range(3):
        for s_pop in range(3):
            sigma = max(float(priors.DIR_POPULATION_LATERAL_SIGMA_PX_5760[s_pop]) * native_scale, 0.20)
            intralayer = float(priors.DIR_DETERMINISTIC_INTRALAYER_STRENGTH_RGB[s_rec])
            if intralayer != 0.0:
                src = np.ascontiguousarray(release[..., s_rec, s_pop])
                diffused = cv2.GaussianBlur(src, (0, 0), sigma, borderType=cv2.BORDER_REFLECT)
                correction[..., s_rec, s_pop] += intralayer * capacity[s_rec, s_pop] * (src - diffused) * receiver[..., s_rec, s_pop]
            diffused_departure[..., s_rec, s_pop] = cv2.GaussianBlur(
                np.ascontiguousarray(departure[..., s_rec, s_pop]), (0, 0), sigma, borderType=cv2.BORDER_REFLECT
            )
    correction -= _transport(diffused_departure, capacity[None, None, ...] * receiver, 1.0)
    return correction


def _develop_record_density_fast(log_exposure: np.ndarray, activations: np.ndarray, native_scale: float) -> np.ndarray:
    shape = log_exposure.shape[:-1]
    flat_le = np.ascontiguousarray(log_exposure.reshape(-1, 3), dtype=np.float32)
    net = np.maximum(hd_density(flat_le) - priors.SENSITO_DMIN_RGB, 0.0).astype(np.float32)
    neutral_le = np.repeat(np.mean(flat_le, axis=-1, keepdims=True), 3, axis=-1).astype(np.float32)
    neutral_net = np.maximum(hd_density(neutral_le) - priors.SENSITO_DMIN_RGB, 0.0).astype(np.float32)
    act = np.ascontiguousarray(activations.reshape(-1, 3, 3), dtype=np.float32)
    neutral_act = activation_probabilities(neutral_le).reshape(-1, 3, 3)
    capacity = _layer_capacity()
    fractions = np.ascontiguousarray(priors.SUBEMULSION_CAPACITY_FRACTIONS, dtype=np.float32)
    layer, release, departure = fast.dir_pointwise(net, neutral_net, act, np.ascontiguousarray(neutral_act), fractions, np.ascontiguousarray(capacity))
    receiver = fast.receiver_marginal(act)
    correction = _dir_correction(release.reshape(shape + (3, 3)), departure.reshape(shape + (3, 3)), receiver.reshape(shape + (3, 3)), capacity, native_scale)
    developed = fast.dir_finish(layer, np.ascontiguousarray(correction.reshape(-1, 3, 3)), np.ascontiguousarray(capacity), np.ascontiguousarray(priors.SENSITO_DMIN_RGB, dtype=np.float32))
    return developed.reshape(shape + (3,))


# ---------------------------------------------------------------------------
# Finite-site grain
# ---------------------------------------------------------------------------


def disk_kernel(radius: float) -> np.ndarray:
    extent = max(1, int(math.ceil(radius)))
    yy, xx = np.mgrid[-extent : extent + 1, -extent : extent + 1]
    kernel = ((xx * xx + yy * yy) <= radius * radius).astype(np.float32)
    kernel[extent, extent] = 1.0
    return kernel


@functools.lru_cache(maxsize=512)
def filtered_kernel_power(radius: float, optical_sigma: float, aperture_radius: float) -> float:
    """Noise-power gain through dye cloud, optics and Kodak's 48 um aperture."""
    extent = int(math.ceil(radius + 4.0 * optical_sigma + aperture_radius)) + 4
    size = 2 * extent + 1
    impulse = np.zeros((size, size), dtype=np.float32)
    impulse[extent, extent] = 1.0
    cloud = disk_kernel(radius)
    cloud /= float(cloud.sum())
    response = cv2.filter2D(impulse, -1, cloud, borderType=cv2.BORDER_CONSTANT)
    response = cv2.GaussianBlur(response, (0, 0), max(optical_sigma, 0.05), borderType=cv2.BORDER_CONSTANT)
    aperture = disk_kernel(aperture_radius)
    aperture /= float(aperture.sum())
    response = cv2.filter2D(response, -1, aperture, borderType=cv2.BORDER_CONSTANT)
    return float(np.sum(np.square(response)))


def striped_binomial(probability: np.ndarray, site_count: int, sample_seed: int, user_seed: int, stripes: int = 8) -> np.ndarray:
    """Seeded row-striped binomial developed counts (identical layout to V25)."""
    height = probability.shape[0]
    stripes = min(stripes, height)
    bounds = np.linspace(0, height, stripes + 1, dtype=np.int32)
    out = np.empty(probability.shape, dtype=np.float32)
    for index in range(stripes):
        r0, r1 = int(bounds[index]), int(bounds[index + 1])
        entropy = [int(sample_seed), int(index)] if user_seed == 0 else [int(user_seed), int(sample_seed), int(index)]
        rng = np.random.default_rng(np.random.SeedSequence(entropy))
        out[r0:r1] = rng.binomial(site_count, probability[r0:r1]).astype(np.float32)
    return out


def class_deviation(probability: np.ndarray, radius: float, optical_sigma: float, site_count: int, sample_seed: int, user_seed: int, sampler: str = "fast") -> np.ndarray:
    if sampler == "fast" and fast.HAVE_NUMBA:
        key = (int(user_seed) * 0x100000001B3 + int(sample_seed)) & 0xFFFFFFFFFFFFFFFF
        developed = fast.counter_binomial(np.ascontiguousarray(probability, dtype=np.float32), int(site_count), np.uint64(key)) / float(site_count)
    else:
        developed = striped_binomial(probability, site_count, sample_seed, user_seed) / float(site_count)
    kernel = disk_kernel(radius)
    kernel /= float(kernel.sum())
    sampled = cv2.filter2D(developed, -1, kernel, borderType=cv2.BORDER_REFLECT)
    expected = cv2.filter2D(probability, -1, kernel, borderType=cv2.BORDER_REFLECT)
    sigma = max(optical_sigma, 0.05)
    sampled = cv2.GaussianBlur(sampled, (0, 0), sigma, borderType=cv2.BORDER_REFLECT)
    expected = cv2.GaussianBlur(expected, (0, 0), sigma, borderType=cv2.BORDER_REFLECT)
    return (sampled - expected).astype(np.float32)


def _class_plan(population: int, total_sites: int, size_classes: int) -> list[tuple[float, float, float, int]]:
    """(weight, radius factor, optical factor, sites) for the requested class count."""
    fractions = np.asarray(priors.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION[population], dtype=np.float64)
    radius_factors = np.asarray(priors.GRAIN_SIZE_CLASS_RADIUS_FACTORS, dtype=np.float64)
    optical_factors = np.asarray(priors.GRAIN_SIZE_CLASS_OPTICAL_FACTORS, dtype=np.float64)
    if size_classes >= 5:
        groups = [[0], [1], [2], [3], [4]]
    elif size_classes == 3:
        groups = [[0, 1], [2], [3, 4]]
    else:
        groups = [[0, 1, 2, 3, 4]]
    plan = []
    raw_counts = []
    for group in groups:
        weight = float(np.sum(fractions[group]))
        radius = float(np.sum(fractions[group] * radius_factors[group]) / weight)
        optical = float(np.sum(fractions[group] * optical_factors[group]) / weight)
        plan.append((weight, radius, optical))
        raw_counts.append(weight * total_sites)
    counts = np.maximum(np.floor(raw_counts).astype(np.int32), 1)
    while int(counts.sum()) < total_sites:
        counts[int(np.argmax(np.asarray(raw_counts) - counts))] += 1
    while int(counts.sum()) > total_sites:
        removable = np.where(counts > 1, counts, 0)
        counts[int(np.argmax(removable))] -= 1
    return [(w, r, o, int(n)) for (w, r, o), n in zip(plan, counts)]


def couple_population_deviations(layer_deviation: np.ndarray, activations: np.ndarray, work_scale: float) -> np.ndarray:
    """Sampled site development releases spatially mobile inhibitor (zero mean)."""
    coupled = np.asarray(layer_deviation, dtype=np.float32).copy()
    marginal = (
        fast.receiver_marginal(np.ascontiguousarray(activations.reshape(-1, 3, 3), dtype=np.float32)).reshape(activations.shape)
        if fast.HAVE_NUMBA
        else np.clip(4.0 * activations * (1.0 - activations), 0.0, 1.0)
    )
    diffused_all = np.empty_like(coupled)
    for s_rec in range(3):
        for s_pop in range(3):
            source = np.ascontiguousarray(layer_deviation[..., s_rec, s_pop])
            sigma = max(float(priors.DIR_POPULATION_LATERAL_SIGMA_PX_5760[s_pop]) * work_scale, 0.20)
            diffused = cv2.GaussianBlur(source, (0, 0), sigma, borderType=cv2.BORDER_REFLECT)
            diffused_all[..., s_rec, s_pop] = diffused
            coupled[..., s_rec, s_pop] += (
                priors.DIR_STOCHASTIC_COUPLING_SCALE
                * priors.DIR_DEVELOPMENT_INTRALAYER_STRENGTH_RGB[s_rec]
                * (source - diffused)
                * marginal[..., s_rec, s_pop]
            )
    coupled -= _transport(diffused_all, marginal, float(priors.DIR_STOCHASTIC_COUPLING_SCALE))
    return coupled.astype(np.float32)


def form_grain_deviation(
    log_exposure: np.ndarray,
    activations: np.ndarray,
    frame_index: int,
    work_scale: float,
    pixels_per_mm: float,
    grain_scale: float,
    size_classes: int,
    user_seed: int,
    oversample: int,
    sampler: str = "fast",
) -> np.ndarray:
    """Return the calibrated stochastic record-density deviation (zero mean)."""
    aperture_radius = 0.5 * priors.KODAK_GRANULARITY_APERTURE_DIAMETER_UM * 1e-3 * pixels_per_mm * oversample
    radii = priors.SUBEMULSION_CLOUD_RADIUS_PX_5760_RGB * work_scale * grain_scale * priors.NEGATIVE_GRAIN_CORRELATION_SCALE
    optical = priors.SUBEMULSION_OPTICAL_SIGMA_PX_5760_RGB * work_scale
    site_counts = np.maximum(1, np.rint(priors.SUBEMULSION_SITE_COUNT_PX_5760_RGB / max(work_scale * work_scale, 1e-6)).astype(np.int32))
    capacity = _layer_capacity()
    target_sigma = granularity_sigma(log_exposure)
    shape = log_exposure.shape[:2]
    layer_deviation = np.zeros(shape + (3, 3), dtype=np.float32)
    predicted_variance = np.zeros(shape + (3,), dtype=np.float32)

    def population_task(channel: int, population: int):
        probability = np.ascontiguousarray(activations[..., channel, population], dtype=np.float32)
        total_sites = int(site_counts[channel, population])
        deviation = np.zeros(shape, dtype=np.float32)
        kernel_power = 0.0
        for size_class, (weight, radius_factor, optical_factor, sites) in enumerate(_class_plan(population, total_sites, size_classes)):
            radius = float(radii[channel, population] * radius_factor)
            sigma = float(optical[channel, population] * optical_factor)
            seed = 30_000_000 + int(frame_index) * 10_000 + channel * 1_000 + population * 100 + size_class
            deviation += weight * class_deviation(probability, radius, sigma, sites, seed, user_seed, sampler)
            kernel_power += weight * weight * filtered_kernel_power(round(radius, 6), round(sigma, 6), round(aperture_radius, 6)) / float(sites)
        cap = float(capacity[channel, population])
        variance = cap * cap * probability * (1.0 - probability) * kernel_power
        return channel, population, deviation, variance

    if sampler == "fast" and fast.HAVE_NUMBA:
        # The counter-based sampler is already multi-threaded; Numba's default
        # threading layer must not be entered from several Python threads.
        results = [population_task(c, p) for c in range(3) for p in range(3)]
    else:
        results = [f.result() for f in [_EXECUTOR.submit(population_task, c, p) for c in range(3) for p in range(3)]]
    for channel, population, deviation, variance in results:
        layer_deviation[..., channel, population] = deviation
        predicted_variance[..., channel] += variance

    coupled = couple_population_deviations(layer_deviation, activations, work_scale)
    combined = np.zeros(shape + (3,), dtype=np.float32)
    for c in range(3):
        for p in range(3):
            combined[..., c] += float(capacity[c, p]) * coupled[..., c, p]
    calibration = target_sigma / np.sqrt(np.maximum(predicted_variance, 1e-12))
    return (combined * calibration).astype(np.float32)


def common_density_projection(mean: np.ndarray, formed: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """V49: keep only the scalar density common to the three records."""
    sigma = np.maximum(np.asarray(sigma, dtype=np.float32), 1e-6)
    residual = np.asarray(formed, dtype=np.float32) - np.asarray(mean, dtype=np.float32)
    latent = np.sum(residual / sigma, axis=2, keepdims=True) / np.sqrt(3.0)
    return np.maximum(mean + latent * np.min(sigma, axis=2, keepdims=True), 0.0).astype(np.float32)


# ---------------------------------------------------------------------------
# Processed-negative MTF
# ---------------------------------------------------------------------------


def apply_negative_mtf(record_density: np.ndarray, native_scale: float, grain_scale: float) -> np.ndarray:
    scale = native_scale * grain_scale
    mid_sigma = priors.NEGATIVE_MTF_ADJACENCY_MID_SIGMA_PX_5760 * scale
    broad_sigma = priors.NEGATIVE_MTF_ADJACENCY_BROAD_SIGMA_PX_5760 * scale
    out = np.empty_like(record_density, dtype=np.float32)
    for c in range(3):
        src = np.ascontiguousarray(record_density[..., c], dtype=np.float32)
        core = cv2.GaussianBlur(src, (0, 0), max(priors.NEGATIVE_MTF_CORE_SIGMA_RGB[c] * scale, 0.05), borderType=cv2.BORDER_REFLECT)
        mid = cv2.GaussianBlur(src, (0, 0), max(mid_sigma, 0.05), borderType=cv2.BORDER_REFLECT)
        broad = cv2.GaussianBlur(src, (0, 0), max(broad_sigma, 0.05), borderType=cv2.BORDER_REFLECT)
        out[..., c] = core + priors.NEGATIVE_MTF_ADJACENCY_AMOUNT_RGB[c] * (mid - broad)
    return out


# ---------------------------------------------------------------------------
# Complete negative
# ---------------------------------------------------------------------------


class FormedNegative:
    __slots__ = ("mean", "formed", "log_exposure", "native_scale")

    def __init__(self, mean, formed, log_exposure, native_scale):
        self.mean = mean
        self.formed = formed
        self.log_exposure = log_exposure
        self.native_scale = native_scale


def form_negative(
    scene_rec709_linear: np.ndarray,
    frame_index: int,
    *,
    exposure_stops: float,
    gate_width_mm: float,
    halation: float,
    sensor_noise_separation: bool,
    chroma_residual: float,
    grain_scale: float,
    grain_amount: float,
    size_classes: int,
    grain_policy: str,
    oversample: int,
    seed: int,
    reference_width: int | None = None,
    sampler: str = "fast",
) -> FormedNegative:
    """Expose, develop and stochastically form one 5279 negative frame."""
    scene = np.asarray(scene_rec709_linear, dtype=np.float32)
    height, width = scene.shape[:2]
    geometry_width = int(reference_width or width)
    native_scale = native_scale_for(geometry_width, gate_width_mm)
    pixels_per_mm = geometry_width / float(gate_width_mm)
    prepared = separate_sensor_noise(scene, native_scale) if sensor_noise_separation else scene
    prepared = input_chroma_residual(prepared, chroma_residual)
    film_rgb = add_optical_scatter(prepared * (2.0**exposure_stops), native_scale, halation)
    records = film_records(film_rgb)
    log_exposure = log_exposure_from_records(records)

    if oversample > 1:
        work = np.stack(
            [cv2.resize(log_exposure[..., c], (width * oversample, height * oversample), interpolation=cv2.INTER_CUBIC) for c in range(3)],
            axis=2,
        ).astype(np.float32)
    else:
        work = log_exposure
    work_scale = native_scale * oversample
    activations = activation_probabilities(work)
    mean_work = develop_record_density(work, activations, work_scale)

    if grain_amount > 0.0:
        deviation = form_grain_deviation(work, activations, frame_index, work_scale, pixels_per_mm, grain_scale, size_classes, seed, oversample, sampler) * grain_amount
        formed_work = np.maximum(mean_work + deviation, 0.0)
        if grain_policy == "common":
            formed_work = common_density_projection(mean_work, formed_work, granularity_sigma(work))
    else:
        formed_work = mean_work

    if oversample > 1:
        mean = np.stack([cv2.resize(mean_work[..., c], (width, height), interpolation=cv2.INTER_AREA) for c in range(3)], axis=2)
        formed = np.stack([cv2.resize(formed_work[..., c], (width, height), interpolation=cv2.INTER_AREA) for c in range(3)], axis=2)
    else:
        mean, formed = mean_work, formed_work

    mean_mtf = apply_negative_mtf(mean, native_scale, grain_scale)
    formed_mtf = (mean_mtf + formed - mean).astype(np.float32)
    return FormedNegative(mean_mtf.astype(np.float32), formed_mtf, log_exposure, native_scale)
