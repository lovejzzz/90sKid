"""Evidence-gated V35 acceleration candidates.

These kernels intentionally install after v27_accel. They preserve the V34
emulsion equations but may change the deterministic grain realization, so they
belong to Production validation rather than the bit-identical Archive path.
"""

from __future__ import annotations

import cv2
import numpy as np

import metal_binomial_bridge


SAMPLER_AUDIT: dict[str, object] = {}


def adapt_frame_linear_memory_reuse(
    module,
    projection: np.ndarray,
    scan: np.ndarray,
    crossover_sigma_at_2k: float,
    opponent_high_frequency_retention: float = 1.0,
    metal_blur: bool = False,
) -> np.ndarray:
    """V31 boundary with the same equations and fewer full-frame temporaries."""

    projection = np.asarray(projection, dtype=np.float32)
    scan = np.asarray(scan, dtype=np.float32)
    projection_lab = module.linear_rec709_to_oklab(projection)
    scan_lab = module.linear_rec709_to_oklab(scan)
    sigma = max(
        float(crossover_sigma_at_2k) * projection.shape[1] / 2048.0,
        0.05,
    )
    if metal_blur:
        import metal_gaussian_bridge

        projection_flight = metal_gaussian_bridge.submit_gaussian_async(
            projection_lab[..., 1:3], sigma, cv2.BORDER_REFLECT
        )
        scan_flight = metal_gaussian_bridge.submit_gaussian_async(
            scan_lab[..., 1:3], sigma, cv2.BORDER_REFLECT
        )
        projection_low_ab = projection_flight.wait()
        scan_low_ab = scan_flight.wait()
    else:
        projection_low_ab = cv2.GaussianBlur(
            projection_lab[..., 1:3],
            (0, 0),
            sigma,
            borderType=cv2.BORDER_REFLECT,
        )
        scan_low_ab = cv2.GaussianBlur(
            scan_lab[..., 1:3],
            (0, 0),
            sigma,
            borderType=cv2.BORDER_REFLECT,
        )
    # Match NumPy's original left-to-right evaluation before reusing buffers.
    np.subtract(
        projection_lab[..., 1:3],
        projection_low_ab,
        out=projection_lab[..., 1:3],
    )
    projection_lab[..., 1:3] *= float(opponent_high_frequency_retention)
    np.add(scan_low_ab, projection_lab[..., 1:3], out=projection_lab[..., 1:3])
    target_rgb = module.oklab_to_linear_rec709(projection_lab)
    weights = np.asarray([0.2126, 0.7152, 0.0722], dtype=np.float32)
    target_luma = np.einsum("...c,c->...", projection, weights).astype(
        np.float32
    )
    current_luma = np.einsum("...c,c->...", target_rgb, weights)
    target_rgb += (target_luma - current_luma)[..., None]
    target_rgb -= target_luma[..., None]
    scale = np.ones(target_luma.shape, dtype=np.float32)
    for channel in range(3):
        delta = target_rgb[..., channel]
        positive = np.where(
            delta > 1e-8,
            (1.0 - target_luma) / np.maximum(delta, 1e-8),
            np.inf,
        )
        negative = np.where(
            delta < -1e-8,
            target_luma / np.maximum(-delta, 1e-8),
            np.inf,
        )
        np.minimum(scale, positive, out=scale)
        np.minimum(scale, negative, out=scale)
    np.minimum(scale, 1.0, out=scale)
    target_rgb *= scale[..., None]
    target_rgb += target_luma[..., None]
    np.clip(target_rgb, 0.0, 1.0, out=target_rgb)
    return target_rgb.astype(np.float32, copy=False)


def apply_metal_binomial(
    module,
    *,
    mode: str = "inverse",
    asynchronous: bool = False,
    residual_convolution: bool = False,
    single_gaussian_after_disk: bool = False,
    domain_salt: int = 0,
    tile_workset_pixels: int | None = None,
    tile_in_flight: int = 2,
) -> None:
    """Replace finite-site sampling with a validated inverse-CDF Metal RNG.

    The implementation draws from a 24-bit open uniform and has been validated
    statistically over the production domain.  It is not described as
    mathematically exact or archive-bit-identical to NumPy's generator.
    """

    if mode not in ("inverse", "bernoulli"):
        raise ValueError(f"unsupported Metal binomial mode: {mode}")
    if not 0 <= int(domain_salt) <= 0xFFFFFFFF:
        raise ValueError("Philox domain salt must fit uint32")
    domain_salt = int(domain_salt)
    if tile_workset_pixels is not None and int(tile_workset_pixels) < 1:
        raise ValueError("tile workset must be positive when enabled")
    if tile_in_flight < 1:
        raise ValueError("tile in-flight count must be positive")
    if residual_convolution and single_gaussian_after_disk:
        raise ValueError("choose only one convolution reassociation candidate")

    SAMPLER_AUDIT.clear()
    SAMPLER_AUDIT.update(
        {
            "mode": mode,
            "seed_contract": (
                "30000000 + frame*10000 + channel*1000 + "
                "population*100 + size_class"
            ),
            "domain_salt_uint32": domain_salt,
            "tile_workset_pixels": (
                None
                if tile_workset_pixels is None
                else int(tile_workset_pixels)
            ),
            "tile_in_flight": int(tile_in_flight),
            "total_calls": 0,
            "duplicate_identity_count": 0,
            "frame_call_counts": {},
            "minimum_seed": None,
            "maximum_seed": None,
            "minimum_trials": None,
            "maximum_trials": None,
            "current_frame": None,
            "current_identities": set(),
        }
    )

    def metal_binomial_deviation(
        activation_probability: np.ndarray,
        rng: np.random.Generator,
        radius: float,
        optical_sigma: float,
        site_count: int,
        subpixel_offset: tuple[float, float] = (0.0, 0.0),
        sample_seed: int | None = None,
    ) -> np.ndarray:
        del rng
        if sample_seed is None:
            raise ValueError("V35 Metal sampler requires an explicit seed")
        relative_seed = int(sample_seed) - 30_000_000
        frame_identity, suffix = divmod(relative_seed, 10_000)
        channel_identity, suffix = divmod(suffix, 1_000)
        population_identity, size_class_identity = divmod(suffix, 100)
        identity = (
            frame_identity,
            channel_identity,
            population_identity,
            size_class_identity,
        )
        if (
            frame_identity < 0
            or channel_identity not in range(3)
            or population_identity not in range(3)
            or size_class_identity not in range(5)
        ):
            raise ValueError(f"invalid V35 finite-site identity seed: {sample_seed}")
        if SAMPLER_AUDIT["current_frame"] != frame_identity:
            SAMPLER_AUDIT["current_frame"] = frame_identity
            SAMPLER_AUDIT["current_identities"] = set()
        current_identities = SAMPLER_AUDIT["current_identities"]
        if identity in current_identities:
            SAMPLER_AUDIT["duplicate_identity_count"] += 1
            raise ValueError(f"duplicate V35 finite-site identity: {identity}")
        current_identities.add(identity)
        frame_counts = SAMPLER_AUDIT["frame_call_counts"]
        frame_counts[frame_identity] = frame_counts.get(frame_identity, 0) + 1
        SAMPLER_AUDIT["total_calls"] += 1
        for key, value in (
            ("minimum_seed", int(sample_seed)),
            ("minimum_trials", int(site_count)),
        ):
            if SAMPLER_AUDIT[key] is None or value < SAMPLER_AUDIT[key]:
                SAMPLER_AUDIT[key] = value
        for key, value in (
            ("maximum_seed", int(sample_seed)),
            ("maximum_trials", int(site_count)),
        ):
            if SAMPLER_AUDIT[key] is None or value > SAMPLER_AUDIT[key]:
                SAMPLER_AUDIT[key] = value
        if tile_workset_pixels is not None:
            probability = metal_binomial_bridge.aligned_empty(
                activation_probability.shape
            )
            np.copyto(probability, activation_probability)
        else:
            probability = np.ascontiguousarray(
                activation_probability, dtype=np.float32
            )
        effective_seed = (domain_salt << 32) | (int(sample_seed) & 0xFFFFFFFF)
        kernel = module.disk_kernel(radius)
        kernel /= float(kernel.sum())
        flight = None
        if tile_workset_pixels is not None:
            flight = metal_binomial_bridge.submit_tiled(
                probability,
                site_count,
                effective_seed,
                workset_pixels=int(tile_workset_pixels),
                in_flight=int(tile_in_flight),
                mode=mode,
            )
        elif asynchronous:
            flight = metal_binomial_bridge.submit(
                probability, site_count, effective_seed, mode=mode
            )
        else:
            developed_fraction = metal_binomial_bridge.sample(
                probability, site_count, effective_seed, mode=mode
            )
        expected = cv2.filter2D(
            probability, -1, kernel, borderType=cv2.BORDER_REFLECT
        )
        if flight is not None:
            developed_fraction = flight.wait()
        developed_fraction /= float(site_count)
        if (
            getattr(module, "_WAVEFRONT_INPLACE_OPTICAL_BUFFERS", False)
            and not residual_convolution
            and not single_gaussian_after_disk
        ):
            import wavefront_tile_lab_v002

            return wavefront_tile_lab_v002.optical_deviation_inplace(
                developed_fraction,
                expected,
                kernel,
                max(optical_sigma, 0.05),
                subpixel_offset,
            )
        if residual_convolution:
            # Both spatial operators are linear and use the same border rule:
            # L(sample) - L(expected) == L(sample - expected).  Reassociating
            # changes float32 rounding order, so this remains evidence-gated.
            np.subtract(developed_fraction, probability, out=developed_fraction)
            deviation = cv2.filter2D(
                developed_fraction, -1, kernel, borderType=cv2.BORDER_REFLECT
            )
            deviation = cv2.GaussianBlur(
                deviation,
                (0, 0),
                max(optical_sigma, 0.05),
                borderType=cv2.BORDER_REFLECT,
            ).astype(np.float32, copy=False)
            offset_x, offset_y = subpixel_offset
            if abs(offset_x) > 1e-6 or abs(offset_y) > 1e-6:
                transform = np.array(
                    [[1.0, 0.0, offset_x], [0.0, 1.0, offset_y]],
                    dtype=np.float32,
                )
                deviation = cv2.warpAffine(
                    deviation,
                    transform,
                    (deviation.shape[1], deviation.shape[0]),
                    flags=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_REFLECT,
                )
            return deviation
        sampled = cv2.filter2D(
            developed_fraction, -1, kernel, borderType=cv2.BORDER_REFLECT
        )
        if single_gaussian_after_disk:
            np.subtract(sampled, expected, out=sampled)
            deviation = cv2.GaussianBlur(
                sampled,
                (0, 0),
                max(optical_sigma, 0.05),
                borderType=cv2.BORDER_REFLECT,
            ).astype(np.float32, copy=False)
            offset_x, offset_y = subpixel_offset
            if abs(offset_x) > 1e-6 or abs(offset_y) > 1e-6:
                transform = np.array(
                    [[1.0, 0.0, offset_x], [0.0, 1.0, offset_y]],
                    dtype=np.float32,
                )
                deviation = cv2.warpAffine(
                    deviation,
                    transform,
                    (deviation.shape[1], deviation.shape[0]),
                    flags=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_REFLECT,
                )
            return deviation
        sigma = max(optical_sigma, 0.05)
        sampled = cv2.GaussianBlur(
            sampled, (0, 0), sigma, borderType=cv2.BORDER_REFLECT
        )
        expected = cv2.GaussianBlur(
            expected, (0, 0), sigma, borderType=cv2.BORDER_REFLECT
        )
        deviation = (sampled - expected).astype(np.float32, copy=False)
        offset_x, offset_y = subpixel_offset
        if abs(offset_x) > 1e-6 or abs(offset_y) > 1e-6:
            transform = np.array(
                [[1.0, 0.0, offset_x], [0.0, 1.0, offset_y]],
                dtype=np.float32,
            )
            deviation = cv2.warpAffine(
                deviation,
                transform,
                (deviation.shape[1], deviation.shape[0]),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REFLECT,
            )
        return deviation

    module.binomial_dye_cloud_deviation = metal_binomial_deviation


def sampler_audit_snapshot(expected_calls_per_frame: int = 45) -> dict[str, object]:
    """Return a JSON-safe identity audit and fail on incomplete formations."""

    frame_counts = dict(SAMPLER_AUDIT.get("frame_call_counts", {}))
    incomplete = {
        int(frame): int(count)
        for frame, count in frame_counts.items()
        if int(count) != expected_calls_per_frame
    }
    if incomplete:
        raise RuntimeError(f"incomplete V35 finite-site sampler frames: {incomplete}")
    return {
        key: value
        for key, value in SAMPLER_AUDIT.items()
        if key not in ("current_identities", "current_frame", "frame_call_counts")
    } | {
        "frames_audited": len(frame_counts),
        "calls_per_frame": expected_calls_per_frame,
        "frame_call_counts": {
            str(frame): int(count) for frame, count in frame_counts.items()
        },
    }


def warm_metal_binomial(mode: str = "inverse") -> None:
    probability = np.linspace(0.0, 1.0, 4096, dtype=np.float32).reshape(64, 64)
    metal_binomial_bridge.sample(probability, 17, 35_5279, mode=mode)
