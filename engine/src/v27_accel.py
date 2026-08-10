"""Experimental V27 CPU acceleration layer; not a release profile."""

from __future__ import annotations

import concurrent.futures
import math
import threading
import time

import cv2
import numpy as np
from numba import set_num_threads

import pipeline_accel as accel


_ARRAY_EXECUTOR: concurrent.futures.ThreadPoolExecutor | None = None
_NUMBA_KERNEL_LOCK = threading.Lock()


def _row_ranges(height: int, workers: int) -> list[tuple[int, int]]:
    count = max(1, min(int(workers), int(height)))
    bounds = np.linspace(0, height, count + 1, dtype=np.int32)
    return [(int(bounds[index]), int(bounds[index + 1])) for index in range(count)]


def warm(module) -> None:
    """Compile/load all exact kernels before formal frame timing begins."""
    camera_lut = module.load_panasonic_raw_to_vgamut_lut()
    accel.camera_cube_trilinear(np.zeros((4, 4, 3), np.float32), camera_lut)
    if module._NEGATIVE_5279_NET_DENSITY_LUT is None:
        module._NEGATIVE_5279_NET_DENSITY_LUT = module.build_5279_net_density_lut()
    accel.density_cube_trilinear(
        np.zeros((4, 4, 3), np.float32),
        module._NEGATIVE_5279_NET_DENSITY_LUT,
        module.NEGATIVE_5279_MAX_RECORD_DENSITY,
    )
    if module._SPIRIT_NEUTRAL_SCALE_TABLE is None:
        module._SPIRIT_NEUTRAL_SCALE_TABLE = module.build_spirit_neutral_scale_table()
    axis, table = module._SPIRIT_NEUTRAL_SCALE_TABLE
    accel.factor_table_interp(np.zeros((4, 4), np.float32), axis, table)
    accel.factor_table_interp_float64(np.zeros((4, 4), np.float32), axis, table)
    accel.channel_table_interp(
        np.zeros((4, 4, 3), np.float32),
        module.GRANULARITY_LOG_EXPOSURE,
        module.GRANULARITY_SIGMA_D_RGB,
    )
    # Compile the signed print-output sampler against a tiny lattice.  The
    # production 193^3 lattice is still built lazily by the observer branch.
    accel.signed_density_cube_trilinear(
        np.zeros((4, 4, 3), np.float32),
        np.zeros((3, 3, 3, 3), np.float32),
        module.SENSITO_DMIN_RGB,
        -0.16,
        module.NEGATIVE_5279_MAX_RECORD_DENSITY,
    )
    accel.h61_density_cube_trilinear(
        np.zeros((4, 4, 3), np.float32),
        np.zeros((3, 3, 3, 3), np.float32),
        module.SENSITO_DMIN_RGB,
        -0.16,
        module.NEGATIVE_5279_MAX_RECORD_DENSITY,
    )
    accel.preserve_luma_and_compress_gamut(
        np.zeros((4, 4, 3), np.float32),
        np.zeros((4, 4), np.float32),
    )


def apply(
    module,
    numba_threads: int = 12,
    array_workers: int = 1,
    exact_only: bool = False,
    enable_record_density: bool = True,
    enable_matrix: bool = True,
) -> None:
    """Install fused kernels while retaining reference fallbacks for tiny arrays."""
    global _ARRAY_EXECUTOR
    import apply_v31_normal_process_adapter as normal_adapter
    set_num_threads(numba_threads)
    array_workers = max(1, int(array_workers))
    if array_workers > 1 and _ARRAY_EXECUTOR is None:
        _ARRAY_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
            max_workers=array_workers,
            thread_name_prefix="v27-array",
        )
    stochastic_profile = getattr(module, "_V27_STOCHASTIC_PROFILE", None)
    mean_profile = getattr(module, "_V27_MEAN_PROFILE", None)
    module._V27_VARIANCE_MEMORY_REUSE = True
    module._V27_RECORD_MIX_MEMORY_REUSE = True
    module._V27_PROBABILITY_POPULATION_CACHE = True
    stochastic_profile_lock = (
        threading.Lock() if stochastic_profile is not None else None
    )
    mean_profile_lock = threading.Lock() if mean_profile is not None else None

    def run_numba_kernel(function, *arguments):
        """Serialize Numba workqueue launches while other branch work overlaps.

        Numba's macOS workqueue backend is internally parallel but does not
        permit two outside Python threads to launch kernels concurrently. This
        lock is the explicit CPU-kernel queue in the heterogeneous scheduler;
        OpenCV, NumPy and Metal work on either observer remain free to overlap.
        """
        with _NUMBA_KERNEL_LOCK:
            return function(*arguments)

    def profile_stochastic(name: str, started: float) -> None:
        if stochastic_profile is None:
            return
        elapsed = time.perf_counter() - started
        assert stochastic_profile_lock is not None
        with stochastic_profile_lock:
            entry = stochastic_profile.setdefault(
                name, {"calls": 0, "summed_task_seconds": 0.0}
            )
            entry["calls"] = int(entry["calls"]) + 1
            entry["summed_task_seconds"] = (
                float(entry["summed_task_seconds"]) + elapsed
            )

    def profile_mean(name: str, started: float) -> None:
        if mean_profile is None:
            return
        elapsed = time.perf_counter() - started
        assert mean_profile_lock is not None
        with mean_profile_lock:
            entry = mean_profile.setdefault(
                name, {"calls": 0, "summed_task_seconds": 0.0}
            )
            entry["calls"] = int(entry["calls"]) + 1
            entry["summed_task_seconds"] = (
                float(entry["summed_task_seconds"]) + elapsed
            )
    if not hasattr(module, "_V27_REFERENCE_APPLY_RGB_CUBE_LUT"):
        module._V27_REFERENCE_APPLY_RGB_CUBE_LUT = module.apply_rgb_cube_lut
        module._V27_REFERENCE_RECORD_DENSITIES_FROM_LOG_EXPOSURE = (
            module.record_densities_from_log_exposure
        )
        module._V27_REFERENCE_APPLY_5279_NET_DENSITY_LUT = (
            module.apply_5279_net_density_lut
        )
        module._V27_REFERENCE_VGAMUT_TO_BALANCED_FILM_RGB = (
            module.vgamut_to_balanced_film_rgb
        )
        module._V27_REFERENCE_FILM_RECORDS_FROM_RGB = module.film_records_from_rgb
        module._V27_REFERENCE_NEUTRALIZE_SPIRIT_FINISHED_GRAY_SCALE = (
            module.neutralize_spirit_finished_gray_scale
        )
        module._V27_REFERENCE_COMPRESS_UNIT_GAMUT = module.compress_unit_gamut
        module._V27_REFERENCE_COMPRESS_OKLAB_CHROMA_TO_REC709 = (
            module.compress_oklab_chroma_to_rec709
        )
        module._V27_REFERENCE_SUBEMULSION_ACTIVATION_PROBABILITIES = (
            module.subemulsion_activation_probabilities
        )
        module._V27_REFERENCE_PUBLISHED_5279_GRANULARITY_SIGMA = (
            module.published_5279_granularity_sigma
        )
        module._V27_REFERENCE_DEVELOP_5279_FROM_LOG_EXPOSURE = (
            module.develop_5279_record_density_from_log_exposure
        )
        module._V27_REFERENCE_COUPLE_5279_POPULATION_DEVIATIONS = (
            module.couple_5279_population_deviations
        )
        module._V27_REFERENCE_BINOMIAL_DYE_CLOUD_DEVIATION = (
            module.binomial_dye_cloud_deviation
        )
        module._V27_REFERENCE_SCANNER_DENSITY_FROM_TOTAL_RECORD_DENSITY = (
            module.scanner_density_from_total_record_density
        )
        module._V27_REFERENCE_RENDER_CINEON_SCAN_MASTER_FROM_SCANNER_DENSITY = (
            module.render_cineon_scan_master_from_scanner_density
        )
        module._V27_REFERENCE_FINISH_CINEON_SCAN_FOR_BLURAY = (
            module.finish_cineon_scan_for_bluray
        )
        module._V27_REFERENCE_FINISH_BLURAY_GRAIN_DELTA = (
            module.finish_bluray_grain_delta
        )
        module._V27_REFERENCE_ADD_5279_OPTICAL_SCATTER = (
            module.add_5279_optical_scatter
        )
        module._V27_REFERENCE_SAMPLE_RECORD_DENSITY_DELTA_LUT = (
            module.sample_record_density_delta_lut
        )
        module._V27_REFERENCE_APPLY_2383_H61_COLOUR_DELTA_LUT = (
            module.apply_2383_h61_colour_delta_lut
        )
        module._V27_REFERENCE_APPLY_2383_PROJECTION_LUT = (
            module.apply_2383_projection_lut
        )
        module._V27_REFERENCE_APPLY_5279_TO_2383_PRINTER_DENSITY_LUT = (
            module.apply_5279_to_2383_printer_density_lut
        )
        module._V27_REFERENCE_RAW_PRINT_2383_DENSITY_FROM_NEGATIVE = (
            module._raw_print_2383_density_from_negative
        )
        module._V27_REFERENCE_PRINT_2383_DENSITY_FROM_NEGATIVE = (
            module.print_2383_density_from_negative
        )
        module._V27_REFERENCE_V31_PRESERVE_LUMA_AND_COMPRESS_GAMUT = (
            normal_adapter.preserve_luma_and_compress_gamut
        )
        module._V27_REFERENCE_APPLY_2383_MONITOR_NEUTRAL_CURVE = (
            module.apply_2383_monitor_neutral_curve
        )
        module._V27_REFERENCE_NEUTRALIZE_2383_PROJECTED_GRAY_SCALE = (
            module.neutralize_2383_projected_gray_scale
        )
        module._V27_REFERENCE_REMOVE_TONAL_GRAIN_BIAS = (
            module.remove_tonal_grain_bias
        )
        module._V27_REFERENCE_MATCH_2383_PROJECTION_TO_REC709_MONITOR = (
            module.match_2383_projection_to_rec709_monitor
        )

    reference_cube = module._V27_REFERENCE_APPLY_RGB_CUBE_LUT
    reference_record_density = (
        module._V27_REFERENCE_RECORD_DENSITIES_FROM_LOG_EXPOSURE
    )
    reference_density_cube = module._V27_REFERENCE_APPLY_5279_NET_DENSITY_LUT
    reference_vgamut = module._V27_REFERENCE_VGAMUT_TO_BALANCED_FILM_RGB
    reference_records = module._V27_REFERENCE_FILM_RECORDS_FROM_RGB
    reference_neutralize = (
        module._V27_REFERENCE_NEUTRALIZE_SPIRIT_FINISHED_GRAY_SCALE
    )
    reference_compress_oklab = (
        module._V27_REFERENCE_COMPRESS_OKLAB_CHROMA_TO_REC709
    )
    reference_scanner_density = (
        module._V27_REFERENCE_SCANNER_DENSITY_FROM_TOTAL_RECORD_DENSITY
    )
    reference_render_cineon = (
        module._V27_REFERENCE_RENDER_CINEON_SCAN_MASTER_FROM_SCANNER_DENSITY
    )
    reference_finish_cineon = (
        module._V27_REFERENCE_FINISH_CINEON_SCAN_FOR_BLURAY
    )
    reference_finish_bluray_grain = (
        module._V27_REFERENCE_FINISH_BLURAY_GRAIN_DELTA
    )
    reference_optical_scatter = module._V27_REFERENCE_ADD_5279_OPTICAL_SCATTER
    reference_print_output_cube = (
        module._V27_REFERENCE_SAMPLE_RECORD_DENSITY_DELTA_LUT
    )
    reference_h61_cube = (
        module._V27_REFERENCE_APPLY_2383_H61_COLOUR_DELTA_LUT
    )
    reference_projection_cube = module._V27_REFERENCE_APPLY_2383_PROJECTION_LUT
    reference_printer_density_cube = (
        module._V27_REFERENCE_APPLY_5279_TO_2383_PRINTER_DENSITY_LUT
    )
    reference_raw_print_density = (
        module._V27_REFERENCE_RAW_PRINT_2383_DENSITY_FROM_NEGATIVE
    )
    reference_print_density = (
        module._V27_REFERENCE_PRINT_2383_DENSITY_FROM_NEGATIVE
    )
    reference_v31_gamut = (
        module._V27_REFERENCE_V31_PRESERVE_LUMA_AND_COMPRESS_GAMUT
    )
    reference_monitor_neutral = (
        module._V27_REFERENCE_APPLY_2383_MONITOR_NEUTRAL_CURVE
    )
    reference_projected_gray = (
        module._V27_REFERENCE_NEUTRALIZE_2383_PROJECTED_GRAY_SCALE
    )
    reference_remove_grain_bias = module._V27_REFERENCE_REMOVE_TONAL_GRAIN_BIAS
    reference_match_projection = (
        module._V27_REFERENCE_MATCH_2383_PROJECTION_TO_REC709_MONITOR
    )

    def camera_cube(rgb: np.ndarray, lut: np.ndarray, rows_per_stripe: int = 96):
        source = np.asarray(rgb, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_cube(source, lut, rows_per_stripe)
        return run_numba_kernel(accel.camera_cube_trilinear, source, lut)

    def record_density(log_exposure: np.ndarray) -> np.ndarray:
        source = np.asarray(log_exposure, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_record_density(source)
        return run_numba_kernel(
            accel.record_density_mix_fused,
            source,
            module.SENSITO_LOG_EXPOSURE,
            module.SENSITO_DENSITY_RGB,
            module.SUBEMULSION_FAST_CENTRE_LOGE_RGB,
            module.SUBEMULSION_SPEED_OFFSETS_LOGE,
            module.SUBEMULSION_TRANSITION_WIDTH_RGB,
            module.SUBEMULSION_CAPACITY_FRACTIONS,
            module.SUBEMULSION_DYE_RECORD_MIX,
        )

    def record_density_exact_core(source: np.ndarray) -> np.ndarray:
        densities = np.empty_like(source, dtype=np.float32)
        for channel in range(3):
            densities[..., channel] = np.interp(
                source[..., channel],
                module.SENSITO_LOG_EXPOSURE,
                module.SENSITO_DENSITY_RGB[channel],
            ).astype(np.float32)
        neutral_log_exposure = np.mean(source, axis=-1, keepdims=True)
        neutral_density = np.empty_like(densities, dtype=np.float32)
        for channel in range(3):
            neutral_density[..., channel] = np.interp(
                neutral_log_exposure[..., 0],
                module.SENSITO_LOG_EXPOSURE,
                module.SENSITO_DENSITY_RGB[channel],
            ).astype(np.float32)
        centres = (
            module.SUBEMULSION_FAST_CENTRE_LOGE_RGB[:, None]
            + module.SUBEMULSION_SPEED_OFFSETS_LOGE[None, :]
        )
        widths = module.SUBEMULSION_TRANSITION_WIDTH_RGB[:, None]
        activations = (source[..., :, None] - centres) / widths
        np.clip(activations, -16.0, 16.0, out=activations)
        np.negative(activations, out=activations)
        np.exp(activations, out=activations)
        np.add(activations, 1.0, out=activations)
        np.reciprocal(activations, out=activations)
        marginal = np.subtract(1.0, activations)
        np.multiply(activations, marginal, out=marginal)
        np.multiply(
            marginal, module.SUBEMULSION_CAPACITY_FRACTIONS, out=marginal
        )
        np.divide(marginal, widths, out=marginal)
        denominator = np.sum(marginal, axis=-1, keepdims=True)
        np.maximum(denominator, 1e-8, out=denominator)
        np.divide(marginal, denominator, out=marginal)
        effective_mix = np.einsum(
            "...sp,pds->...ds", marginal, module.SUBEMULSION_DYE_RECORD_MIX
        )
        chromatic_departure = densities - neutral_density
        mixed_departure = np.einsum(
            "...s,...ds->...d", chromatic_departure, effective_mix
        )
        return (neutral_density + mixed_departure).astype(np.float32)

    def record_density_exact_inplace(log_exposure: np.ndarray) -> np.ndarray:
        source = np.asarray(log_exposure, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_record_density(source)
        if array_workers == 1 or source.shape[0] < array_workers * 8:
            return record_density_exact_core(source)
        result = np.empty_like(source, dtype=np.float32)
        ranges = _row_ranges(source.shape[0], array_workers)

        def process_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            result[row0:row1] = record_density_exact_core(source[row0:row1])

        assert _ARRAY_EXECUTOR is not None
        list(_ARRAY_EXECUTOR.map(process_rows, ranges))
        return result

    def neutral_record_density_exact(neutral_log: np.ndarray) -> np.ndarray:
        """Evaluate only the published neutral H-D curves.

        The caller supplies a scalar field obtained by averaging the three
        records. Repeating it across records makes chromatic departure exactly
        zero, so the full crossover-mixing branch returns these three
        interpolations bit-for-bit while allocating much more intermediate
        state.
        """
        neutral = np.asarray(neutral_log, dtype=np.float32)
        result = np.empty(neutral.shape + (3,), dtype=np.float32)

        def process_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            source_rows = neutral[row0:row1]
            for channel in range(3):
                result[row0:row1, :, channel] = np.interp(
                    source_rows,
                    module.SENSITO_LOG_EXPOSURE,
                    module.SENSITO_DENSITY_RGB[channel],
                ).astype(np.float32)

        if array_workers == 1 or neutral.shape[0] < array_workers * 8:
            process_rows((0, neutral.shape[0]))
        else:
            assert _ARRAY_EXECUTOR is not None
            list(
                _ARRAY_EXECUTOR.map(
                    process_rows, _row_ranges(neutral.shape[0], array_workers)
                )
            )
        return result

    def record_density_semifused(log_exposure: np.ndarray) -> np.ndarray:
        source = np.asarray(log_exposure, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_record_density(source)
        densities = np.empty_like(source, dtype=np.float32)
        for channel in range(3):
            densities[..., channel] = np.interp(
                source[..., channel],
                module.SENSITO_LOG_EXPOSURE,
                module.SENSITO_DENSITY_RGB[channel],
            ).astype(np.float32)
        neutral_log_exposure = np.mean(source, axis=-1, keepdims=True)
        neutral_density = np.empty_like(densities, dtype=np.float32)
        for channel in range(3):
            neutral_density[..., channel] = np.interp(
                neutral_log_exposure[..., 0],
                module.SENSITO_LOG_EXPOSURE,
                module.SENSITO_DENSITY_RGB[channel],
            ).astype(np.float32)
        centres = (
            module.SUBEMULSION_FAST_CENTRE_LOGE_RGB[:, None]
            + module.SUBEMULSION_SPEED_OFFSETS_LOGE[None, :]
        )
        widths = module.SUBEMULSION_TRANSITION_WIDTH_RGB[:, None]
        argument = (source[..., :, None] - centres) / widths
        argument = np.clip(argument, -16.0, 16.0)
        activations = (1.0 / (1.0 + np.exp(-argument))).astype(np.float32)
        marginal = (
            activations
            * (1.0 - activations)
            * module.SUBEMULSION_CAPACITY_FRACTIONS
            / widths
        )
        marginal /= np.maximum(np.sum(marginal, axis=-1, keepdims=True), 1e-8)
        return run_numba_kernel(
            accel.mix_record_departure,
            densities,
            neutral_density,
            marginal,
            module.SUBEMULSION_DYE_RECORD_MIX,
        )

    def density_cube(net_record_density: np.ndarray) -> np.ndarray:
        source = np.asarray(net_record_density, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_density_cube(source)
        if module._NEGATIVE_5279_NET_DENSITY_LUT is None:
            module._NEGATIVE_5279_NET_DENSITY_LUT = (
                module.build_5279_net_density_lut()
            )
        return run_numba_kernel(
            accel.density_cube_trilinear,
            source,
            module._NEGATIVE_5279_NET_DENSITY_LUT,
            module.NEGATIVE_5279_MAX_RECORD_DENSITY,
        )

    def print_output_cube(
        total_density: np.ndarray,
        lut: np.ndarray,
        rows_per_stripe: int = 96,
    ) -> np.ndarray:
        source = np.asarray(total_density, dtype=np.float32)
        lattice = np.asarray(lut, dtype=np.float32)
        if (
            source.ndim != 3
            or source.shape[-1] != 3
            or lattice.ndim != 4
            or lattice.shape[-1] != 3
        ):
            return reference_print_output_cube(source, lattice, rows_per_stripe)
        return run_numba_kernel(
            accel.signed_density_cube_trilinear,
            source,
            lattice,
            module.SENSITO_DMIN_RGB,
            -0.16,
            module.NEGATIVE_5279_MAX_RECORD_DENSITY,
        )

    def h61_colour_delta_cube(
        total_density: np.ndarray,
        include_reference_flare: bool,
    ) -> np.ndarray:
        source = np.asarray(total_density, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_h61_cube(source, include_reference_flare)
        if include_reference_flare not in module._PRINT_2383_H61_COLOUR_DELTA_LUTS:
            module._PRINT_2383_H61_COLOUR_DELTA_LUTS[include_reference_flare] = (
                module.build_2383_h61_colour_delta_lut(include_reference_flare)
            )
        return run_numba_kernel(
            accel.h61_density_cube_trilinear,
            source,
            module._PRINT_2383_H61_COLOUR_DELTA_LUTS[include_reference_flare],
            module.SENSITO_DMIN_RGB,
            -0.16,
            module.NEGATIVE_5279_MAX_RECORD_DENSITY,
        )

    def projection_density_cube(
        print_density_rgb: np.ndarray,
        rows_per_stripe: int = 96,
    ) -> np.ndarray:
        source = np.asarray(print_density_rgb, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_projection_cube(source, rows_per_stripe)
        if module._PRINT_2383_PROJECTION_LUT is None:
            module._PRINT_2383_PROJECTION_LUT = module.build_2383_projection_lut()
        return run_numba_kernel(
            accel.density_cube_trilinear,
            source,
            module._PRINT_2383_PROJECTION_LUT,
            module.PRINT_2383_DMAX,
        )

    def printer_density_cube(net_record_density: np.ndarray) -> np.ndarray:
        source = np.asarray(net_record_density, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_printer_density_cube(source)
        if module._NEGATIVE_5279_TO_2383_PRINTER_DENSITY_LUT is None:
            module._NEGATIVE_5279_TO_2383_PRINTER_DENSITY_LUT = (
                module.build_5279_to_2383_printer_density_lut()
            )
        return run_numba_kernel(
            accel.density_cube_trilinear,
            source,
            module._NEGATIVE_5279_TO_2383_PRINTER_DENSITY_LUT,
            module.NEGATIVE_5279_MAX_RECORD_DENSITY,
        )

    def raw_print_density_fast(negative_density_rgb: np.ndarray) -> np.ndarray:
        source = np.asarray(negative_density_rgb, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_raw_print_density(source)
        neutral_negative = module.negative_total_printer_density(
            np.array([0.18, 0.18, 0.18], dtype=np.float32)
        )
        aim_log_exposure = np.array(
            [
                module._inverse_2383_density(
                    channel,
                    float(module.PRINT_2383_LAD_STATUS_A_AIM_RGB[channel]),
                )
                for channel in range(3)
            ],
            dtype=np.float32,
        )
        printer_log_light = neutral_negative + aim_log_exposure
        captured_log_exposure = printer_log_light - source
        print_log_exposure = (
            aim_log_exposure
            + np.einsum(
                "...c,dc->...d",
                captured_log_exposure - aim_log_exposure,
                module.PRINT_2383_INTERIMAGE_MATRIX,
            )
        ).astype(np.float32)
        return run_numba_kernel(
            accel.channel_table_interp,
            print_log_exposure,
            module.PRINT_2383_LOG_EXPOSURE,
            module.PRINT_2383_DENSITY_RGB,
        )

    def print_density_fast(negative_density_rgb: np.ndarray) -> np.ndarray:
        source = np.asarray(negative_density_rgb, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_print_density(source)
        if module._PRINT_2383_NEUTRAL_SHAPERS is None:
            module._PRINT_2383_NEUTRAL_SHAPERS = (
                module._build_2383_neutral_shapers()
            )
        raw = module._raw_print_2383_density_from_negative(source)
        x_tables, y_tables = module._PRINT_2383_NEUTRAL_SHAPERS
        calibrated = np.empty_like(raw)

        def interpolate_channel(channel: int) -> None:
            calibrated[..., channel] = np.interp(
                raw[..., channel], x_tables[channel], y_tables[channel]
            ).astype(np.float32)

        if array_workers == 1:
            for channel in range(3):
                interpolate_channel(channel)
        else:
            assert _ARRAY_EXECUTOR is not None
            list(_ARRAY_EXECUTOR.map(interpolate_channel, range(3)))
        return calibrated

    def v31_gamut_fast(rgb: np.ndarray, target_luma: np.ndarray) -> np.ndarray:
        source = np.asarray(rgb, dtype=np.float32)
        target = np.asarray(target_luma, dtype=np.float32)
        if (
            source.ndim != 3
            or source.shape[-1] != 3
            or target.shape != source.shape[:2]
        ):
            return reference_v31_gamut(source, target)
        return run_numba_kernel(
            accel.preserve_luma_and_compress_gamut, source, target
        )

    def monitor_neutral_curve_fast(physical: np.ndarray) -> np.ndarray:
        source = np.asarray(physical, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_monitor_neutral(source)
        if module._PRINT_2383_MONITOR_NEUTRAL_CURVE is None:
            module._PRINT_2383_MONITOR_NEUTRAL_CURVE = (
                module.build_2383_monitor_neutral_curve()
            )
        axis, table = module._PRINT_2383_MONITOR_NEUTRAL_CURVE
        return run_numba_kernel(
            accel.channel_table_interp,
            source, axis, np.repeat(table[None, :], 3, axis=0)
        )

    def projected_gray_fast(projected: np.ndarray) -> np.ndarray:
        source = np.asarray(projected, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_projected_gray(source)
        if module._PRINT_2383_VIEW_NEUTRAL_TABLE is None:
            # Let the historical path construct its self-referential neutral
            # table once. Every subsequent native stripe uses the fused tail.
            return reference_projected_gray(source)
        luma_axis, factor_table = module._PRINT_2383_VIEW_NEUTRAL_TABLE
        luma = np.einsum(
            "...c,c->...",
            np.maximum(source, 0.0),
            [0.2126, 0.7152, 0.0722],
        )
        factors = run_numba_kernel(
            accel.factor_table_interp_float64,
            luma, luma_axis, factor_table
        )
        return np.maximum(source * factors, 0.0).astype(np.float32)

    def remove_grain_bias_parallel(
        mean_display: np.ndarray,
        grain_delta: np.ndarray,
        bins: int = 96,
    ) -> np.ndarray:
        mean = np.asarray(mean_display)
        delta = np.asarray(grain_delta)
        if (
            mean.ndim != 3
            or mean.shape[-1] != 3
            or delta.shape != mean.shape
        ):
            return reference_remove_grain_bias(mean, delta, bins)
        corrected = np.asarray(delta, dtype=np.float32).copy()

        def process_channel(channel: int) -> None:
            level = np.clip(mean[..., channel], 0.0, 1.0)
            index = np.minimum(
                np.floor(np.sqrt(level) * bins).astype(np.int16), bins - 1
            )
            flat_index = index.ravel()
            counts = np.bincount(
                flat_index, minlength=bins
            ).astype(np.float64)
            sums = np.bincount(
                flat_index,
                weights=corrected[..., channel].ravel(),
                minlength=bins,
            )
            valid = counts >= 256
            if not np.any(valid):
                return
            table = np.zeros(bins, dtype=np.float64)
            table[valid] = sums[valid] / counts[valid]
            valid_x = np.flatnonzero(valid)
            table = np.interp(np.arange(bins), valid_x, table[valid_x])
            table = np.convolve(table, [0.25, 0.50, 0.25], mode="same")
            table[0] = 0.75 * table[0] + 0.25 * table[1]
            table[-1] = 0.75 * table[-1] + 0.25 * table[-2]
            corrected[..., channel] -= table[index].astype(np.float32)

        if array_workers == 1:
            for channel in range(3):
                process_channel(channel)
        else:
            assert _ARRAY_EXECUTOR is not None
            list(_ARRAY_EXECUTOR.map(process_channel, range(3)))
        return corrected

    def match_projection_zero_physical_authority(
        physical_projection: np.ndarray,
        scan_reference: np.ndarray,
        scan_metrics: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None,
    ) -> np.ndarray:
        physical = np.asarray(physical_projection, dtype=np.float32)
        scan = np.asarray(scan_reference, dtype=np.float32)
        if (
            physical.ndim != 3
            or physical.shape[-1] != 3
            or scan.shape != physical.shape
            or module.PRINT_MONITOR_PHYSICAL_HUE_WEIGHT != 0.0
            or module.PRINT_MONITOR_PHYSICAL_SATURATION_WEIGHT != 0.0
        ):
            return reference_match_projection(
                physical, scan, scan_metrics=scan_metrics
            )

        # V31 withdrew unmeasured physical hue and saturation authority. The
        # historical general expression still evaluated every physical OKLab,
        # norm and smoothstep before multiplying those branches by exact zero.
        # Preserve the surviving scan-reference arithmetic and its operation
        # order without evaluating a colour contribution that cannot exist.
        if scan_metrics is None:
            reference_lab, _target_luma, _scan_relative_chroma = (
                module.projection_monitor_scan_metrics(scan)
            )
        else:
            reference_lab, _target_luma, _scan_relative_chroma = scan_metrics
        lightness = reference_lab[..., 0]
        reference_ab = reference_lab[..., 1:3]
        reference_chroma = np.linalg.norm(reference_ab, axis=-1)
        reference_direction = reference_ab / np.maximum(
            reference_chroma[..., None], 1e-6
        )
        direction = reference_direction.copy()
        direction /= np.maximum(
            np.linalg.norm(direction, axis=-1)[..., None], 1e-6
        )
        reference_saturation = reference_chroma / np.maximum(
            reference_lab[..., 0], 0.025
        )
        # The lower bound is <= the non-negative reference value and the upper
        # bound is >= it, so this historical self-clip is exactly an identity.
        saturation = reference_saturation
        if module.PRINT_MONITOR_CHROMA_ADAPTATION == "absolute_chroma":
            target_chroma = reference_chroma
        elif module.PRINT_MONITOR_CHROMA_ADAPTATION == "relative_saturation":
            target_chroma = saturation * lightness
        else:
            return reference_match_projection(physical, scan)
        matched_lab = reference_lab.copy()
        matched_lab[..., 0] = lightness
        matched_lab[..., 1:3] = direction * target_chroma[..., None]
        return module.compress_oklab_chroma_to_rec709(
            module.oklab_to_linear_rec709(matched_lab)
        ).astype(np.float32)

    vgamut_to_rec709 = np.asarray(
        module.XYZ_D65_TO_REC709 @ module.VGAMUT_TO_XYZ_D65,
        dtype=np.float32,
    )
    record_matrix = np.asarray(module.FILM_RECORD_SENSITIVITY_RGB, dtype=np.float32)

    def vgamut_to_film(vgamut: np.ndarray) -> np.ndarray:
        source = np.asarray(vgamut, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_vgamut(source)
        return np.clip(cv2.transform(source, vgamut_to_rec709), 0.0, None).astype(
            np.float32
        )

    def film_records(film_rgb: np.ndarray) -> np.ndarray:
        source = np.asarray(film_rgb, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_records(source)
        return cv2.transform(source, record_matrix).astype(np.float32)

    def neutralize_spirit(display_linear: np.ndarray) -> np.ndarray:
        source = np.clip(np.asarray(display_linear, dtype=np.float32), 0.0, 1.0)
        if not module.SPIRIT_NEUTRAL_SCALE_CALIBRATION_ENABLED:
            return source
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_neutralize(source)
        if module._SPIRIT_NEUTRAL_SCALE_TABLE is None:
            module._SPIRIT_NEUTRAL_SCALE_TABLE = module.build_spirit_neutral_scale_table()
        luma_weights = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        source_luma = np.empty(source.shape[:2], dtype=np.float32)

        def measure_source_luma(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            source_luma[row0:row1] = np.einsum(
                "...c,c->...", source[row0:row1], luma_weights
            )

        ranges = _row_ranges(source.shape[0], array_workers)
        if array_workers == 1 or source.shape[0] < array_workers * 8:
            measure_source_luma((0, source.shape[0]))
        else:
            assert _ARRAY_EXECUTOR is not None
            list(_ARRAY_EXECUTOR.map(measure_source_luma, ranges))
        luma_axis, factor_table = module._SPIRIT_NEUTRAL_SCALE_TABLE
        factors = run_numba_kernel(
            accel.factor_table_interp, source_luma, luma_axis, factor_table
        )
        corrected = source * factors
        def correct_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            corrected_rows = corrected[row0:row1]
            corrected_luma = np.einsum(
                "...c,c->...", corrected_rows, luma_weights
            )
            corrected_rows *= (
                source_luma[row0:row1] / np.maximum(corrected_luma, 1e-8)
            )[..., None]
            corrected[row0:row1] = np.where(
                (source_luma[row0:row1] > 0.0)[..., None],
                corrected_rows,
                0.0,
            )

        if array_workers == 1 or source.shape[0] < array_workers * 8:
            correct_rows((0, source.shape[0]))
        else:
            assert _ARRAY_EXECUTOR is not None
            list(_ARRAY_EXECUTOR.map(correct_rows, ranges))
        return module.compress_unit_gamut(corrected).astype(np.float32)

    def compress_unit_gamut_core(source: np.ndarray) -> np.ndarray:
        luma = np.einsum("...c,c->...", source, [0.2126, 0.7152, 0.0722])
        np.clip(luma, 0.0, 1.0, out=luma)
        chroma = source - luma[..., None]
        upper_excursion = np.max(chroma, axis=-1)
        lower_excursion = -np.min(chroma, axis=-1)
        upper_scale = np.ones_like(luma)
        np.divide(
            1.0 - luma,
            np.maximum(upper_excursion, 1e-6),
            out=upper_scale,
            where=upper_excursion > 1e-6,
        )
        lower_scale = np.ones_like(luma)
        np.divide(
            luma,
            np.maximum(lower_excursion, 1e-6),
            out=lower_scale,
            where=lower_excursion > 1e-6,
        )
        scale = np.minimum(1.0, np.minimum(upper_scale, lower_scale))
        result = luma[..., None] + chroma * scale[..., None]
        np.clip(result, 0.0, 1.0, out=result)
        return result

    def compress_unit_gamut_inplace(rgb: np.ndarray) -> np.ndarray:
        source = np.asarray(rgb, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return module._V27_REFERENCE_COMPRESS_UNIT_GAMUT(source)
        if array_workers == 1 or source.shape[0] < array_workers * 8:
            return compress_unit_gamut_core(source)
        result = np.empty_like(source, dtype=np.float32)
        ranges = _row_ranges(source.shape[0], array_workers)

        def process_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            result[row0:row1] = compress_unit_gamut_core(source[row0:row1])

        assert _ARRAY_EXECUTOR is not None
        list(_ARRAY_EXECUTOR.map(process_rows, ranges))
        return result

    def compress_oklab_parallel(
        rgb: np.ndarray,
        lower_bound: float = 0.0,
    ) -> np.ndarray:
        source = np.asarray(rgb, dtype=np.float32)
        if (
            array_workers == 1
            or source.ndim != 3
            or source.shape[-1] != 3
            or source.shape[0] < array_workers * 8
        ):
            return reference_compress_oklab(source, lower_bound)
        result = np.empty_like(source, dtype=np.float32)
        ranges = _row_ranges(source.shape[0], array_workers)

        def process_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            result[row0:row1] = reference_compress_oklab(
                source[row0:row1], lower_bound
            )

        assert _ARRAY_EXECUTOR is not None
        list(_ARRAY_EXECUTOR.map(process_rows, ranges))
        return result

    def scanner_density_parallel(total_density: np.ndarray) -> np.ndarray:
        """Preserve the scanner model while parallelizing its pointwise tail."""
        source = np.asarray(total_density)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_scanner_density(source)
        signed_net_density = source - module.SENSITO_DMIN_RGB
        positive_net_density = np.maximum(signed_net_density, 0.0)
        optical_density = module.apply_5279_net_density_lut(positive_net_density)
        result = np.empty_like(optical_density, dtype=np.float32)

        def process_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            positive_rows = positive_net_density[row0:row1]
            optical_rows = optical_density[row0:row1]
            signed_rows = signed_net_density[row0:row1]
            mean_positive_density = np.mean(positive_rows, axis=-1)
            shoulder = module.smoothstep(
                float(module.SPIRIT_PRIMARY_CORRECTION_SHOULDER_DENSITY[0]),
                float(module.SPIRIT_PRIMARY_CORRECTION_SHOULDER_DENSITY[1]),
                mean_positive_density,
            )
            correction_strength = (
                module.SPIRIT_PRIMARY_CORRECTION_STRENGTH
                - module.SPIRIT_PRIMARY_CORRECTION_SHOULDER_RELEASE * shoulder
            )
            result[row0:row1] = (
                optical_rows
                + correction_strength[..., None]
                * (signed_rows - optical_rows)
            ).astype(np.float32)

        if array_workers == 1 or source.shape[0] < array_workers * 8:
            process_rows((0, source.shape[0]))
        else:
            assert _ARRAY_EXECUTOR is not None
            list(
                _ARRAY_EXECUTOR.map(
                    process_rows, _row_ranges(source.shape[0], array_workers)
                )
            )
        return result

    def render_cineon_parallel(scanner_density: np.ndarray) -> np.ndarray:
        """Run the exact Cineon density/code curve in independent row stripes."""
        source = np.asarray(scanner_density)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_render_cineon(source)
        mapped = np.empty_like(source, dtype=np.float32)

        def process_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            source_rows = source[row0:row1]
            cineon_mid_density = 0.700
            gain = cineon_mid_density / np.maximum(
                module.NEUTRAL_MID_SCANNER_DENSITY, 1e-6
            )
            matched_density = source_rows * gain
            cineon_code = np.clip(
                np.rint(95.0 + matched_density / 0.002), 0.0, 1023.0
            )
            decoded_density = (cineon_code - 95.0) * 0.002
            toe_width_density = 0.008
            decoded_density = 0.5 * (
                decoded_density
                + np.sqrt(
                    decoded_density * decoded_density + toe_width_density**2
                )
            )
            high_density = module.NEUTRAL_HIGH_SCANNER_DENSITY * gain
            high_density_toe = 0.5 * (
                high_density
                + np.sqrt(high_density * high_density + toe_width_density**2)
            )
            mid_density_toe = 0.5 * (
                cineon_mid_density
                + math.sqrt(cineon_mid_density**2 + toe_width_density**2)
            )
            unit_density = decoded_density / np.maximum(high_density_toe, 1e-6)
            neutral_mid_unit = mid_density_toe / np.maximum(
                high_density_toe, 1e-6
            )
            peak = np.array([0.90, 0.90, 0.90], dtype=np.float32)
            power = np.log(0.18 / peak) / np.log(
                np.maximum(neutral_mid_unit, 1e-5)
            )
            mapped[row0:row1] = peak * np.power(
                np.clip(unit_density, 0.0, 1.25), power
            )

        if array_workers == 1 or source.shape[0] < array_workers * 8:
            process_rows((0, source.shape[0]))
        else:
            assert _ARRAY_EXECUTOR is not None
            list(
                _ARRAY_EXECUTOR.map(
                    process_rows, _row_ranges(source.shape[0], array_workers)
                )
            )
        return module.compress_unit_gamut(mapped).astype(np.float32)

    def finish_cineon_parallel(scan_linear: np.ndarray) -> np.ndarray:
        """Parallelize the exact pointwise Blu-ray finish before gamut fitting."""
        source = np.asarray(scan_linear)
        if source.ndim != 3 or source.shape[-1] != 3:
            return reference_finish_cineon(source)
        finished = np.empty_like(source, dtype=np.float32)

        def process_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            rgb = np.maximum(
                np.asarray(source[row0:row1], dtype=np.float32), 0.0
            )
            luma = np.einsum("...c,c->...", rgb, [0.2126, 0.7152, 0.0722])
            lower = 0.18 * np.power(
                np.maximum(luma, 0.0) / 0.18, 1.20
            )
            lower = np.where(luma > 0.0, lower, 0.0)
            blend = module.smoothstep(0.12, 0.30, luma)
            target_luma = lower * (1.0 - blend) + luma * blend
            scale = target_luma / np.maximum(luma, 1e-8)
            finished[row0:row1] = rgb * scale[..., None]

        if array_workers == 1 or source.shape[0] < array_workers * 8:
            process_rows((0, source.shape[0]))
        else:
            assert _ARRAY_EXECUTOR is not None
            list(
                _ARRAY_EXECUTOR.map(
                    process_rows, _row_ranges(source.shape[0], array_workers)
                )
            )
        return module.compress_oklab_chroma_to_rec709(finished)

    def finish_bluray_grain_parallel(
        mean_linear: np.ndarray,
        grain_delta: np.ndarray,
    ) -> np.ndarray:
        """Keep the global chroma blur intact and parallelize only pointwise work."""
        mean_source = np.asarray(mean_linear)
        delta_source = np.asarray(grain_delta)
        if (
            mean_source.ndim != 3
            or delta_source.ndim != 3
            or mean_source.shape[-1] != 3
            or delta_source.shape != mean_source.shape
        ):
            return reference_finish_bluray_grain(mean_source, delta_source)
        # The reference's Python luma coefficients promote these intermediates
        # to float64. Keep that dtype: narrowing here changes the final float32
        # rounding even though the numerical error is tiny.
        luma_delta = np.empty(delta_source.shape[:2], dtype=np.float64)
        opponent = np.empty(delta_source.shape, dtype=np.float64)
        ranges = _row_ranges(delta_source.shape[0], array_workers)

        def split_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            luma_rows = np.einsum(
                "...c,c->...",
                delta_source[row0:row1],
                [0.2126, 0.7152, 0.0722],
            )
            luma_delta[row0:row1] = luma_rows
            opponent[row0:row1] = (
                delta_source[row0:row1] - luma_rows[..., None]
            )

        if array_workers == 1 or delta_source.shape[0] < array_workers * 8:
            split_rows((0, delta_source.shape[0]))
        else:
            assert _ARRAY_EXECUTOR is not None
            list(_ARRAY_EXECUTOR.map(split_rows, ranges))
        native_2k_scale = mean_source.shape[1] / 2048.0
        sigma = max(
            module.BLURAY_CHROMA_GRAIN_SIGMA_AT_2K * native_2k_scale,
            0.05,
        )
        opponent_low = cv2.GaussianBlur(
            opponent, (0, 0), sigma, borderType=cv2.BORDER_REFLECT
        )
        managed = np.empty_like(delta_source, dtype=np.float32)

        def finish_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            opponent_rows = (
                opponent_low[row0:row1]
                + module.BLURAY_CHROMA_GRAIN_HIGH_FREQUENCY_RETENTION
                * (opponent[row0:row1] - opponent_low[row0:row1])
            )
            if module.BLURAY_CHROMA_GRAIN_OPPONENT_STRENGTH != 1.0:
                opponent_rows *= module.BLURAY_CHROMA_GRAIN_OPPONENT_STRENGTH
            mean_luma = np.einsum(
                "...c,c->...",
                np.maximum(mean_source[row0:row1], 0.0),
                [0.2126, 0.7152, 0.0722],
            )
            shadow_visibility = module.smoothstep(0.0012, 0.018, mean_luma)
            managed[row0:row1] = (
                luma_delta[row0:row1, ..., None] + opponent_rows
            ) * shadow_visibility[..., None]

        if array_workers == 1 or delta_source.shape[0] < array_workers * 8:
            finish_rows((0, delta_source.shape[0]))
        else:
            assert _ARRAY_EXECUTOR is not None
            list(_ARRAY_EXECUTOR.map(finish_rows, ranges))
        return managed.astype(np.float32, copy=False)

    def optical_scatter_parallel(rec709: np.ndarray) -> np.ndarray:
        """Parallelize scatter source/composite while preserving both blurs."""
        rgb = np.asarray(rec709)
        if rgb.ndim != 3 or rgb.shape[-1] != 3:
            return reference_optical_scatter(rgb)
        # As in the reference, Python scalar coefficients promote the halo and
        # returned composite to float64.
        source = np.empty(rgb.shape[:2], dtype=np.float64)
        result = np.empty(rgb.shape, dtype=np.float64)
        ranges = _row_ranges(rgb.shape[0], array_workers)

        def source_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            luma = np.einsum(
                "...c,c->...",
                np.clip(rgb[row0:row1], 0.0, None),
                [0.2126, 0.7152, 0.0722],
            )
            source[row0:row1] = module.smoothstep(0.90, 3.5, luma)

        if array_workers == 1 or rgb.shape[0] < array_workers * 8:
            source_rows((0, rgb.shape[0]))
        else:
            assert _ARRAY_EXECUTOR is not None
            list(_ARRAY_EXECUTOR.map(source_rows, ranges))
        native_scale = rgb.shape[1] / 5760.0
        near = cv2.GaussianBlur(source, (0, 0), max(5.5 * native_scale, 0.1))
        far = cv2.GaussianBlur(source, (0, 0), max(18.0 * native_scale, 0.1))
        halo = 0.035 * near + 0.014 * far
        scatter_colour = np.array([1.0, 0.22, 0.045], dtype=np.float32)

        def composite_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            result[row0:row1] = (
                rgb[row0:row1]
                + halo[row0:row1, ..., None] * scatter_colour
            )

        if array_workers == 1 or rgb.shape[0] < array_workers * 8:
            composite_rows((0, rgb.shape[0]))
        else:
            assert _ARRAY_EXECUTOR is not None
            list(_ARRAY_EXECUTOR.map(composite_rows, ranges))
        return result

    def activation_probabilities_core(source: np.ndarray) -> np.ndarray:
        centres = (
            module.SUBEMULSION_FAST_CENTRE_LOGE_RGB[:, None]
            + module.SUBEMULSION_SPEED_OFFSETS_LOGE[None, :]
        )
        widths = module.SUBEMULSION_TRANSITION_WIDTH_RGB[:, None]
        argument = (source[..., :, None] - centres) / widths
        np.clip(argument, -16.0, 16.0, out=argument)
        np.negative(argument, out=argument)
        np.exp(argument, out=argument)
        np.add(argument, 1.0, out=argument)
        np.reciprocal(argument, out=argument)
        return argument

    def activation_probabilities_inplace(log_exposure: np.ndarray) -> np.ndarray:
        source = np.asarray(log_exposure, dtype=np.float32)
        if array_workers == 1 or source.ndim != 3 or source.shape[0] < array_workers * 8:
            return activation_probabilities_core(source)
        result = np.empty(source.shape + (3,), dtype=np.float32)
        ranges = _row_ranges(source.shape[0], array_workers)

        def process_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            result[row0:row1] = activation_probabilities_core(source[row0:row1])

        assert _ARRAY_EXECUTOR is not None
        list(_ARRAY_EXECUTOR.map(process_rows, ranges))
        return result

    def neutral_activation_probabilities_exact(
        neutral_log: np.ndarray,
    ) -> np.ndarray:
        neutral = np.asarray(neutral_log, dtype=np.float32)
        centres = (
            module.SUBEMULSION_FAST_CENTRE_LOGE_RGB[:, None]
            + module.SUBEMULSION_SPEED_OFFSETS_LOGE[None, :]
        )
        widths = module.SUBEMULSION_TRANSITION_WIDTH_RGB[:, None]

        def evaluate(source: np.ndarray) -> np.ndarray:
            argument = (source[..., None, None] - centres) / widths
            np.clip(argument, -16.0, 16.0, out=argument)
            np.negative(argument, out=argument)
            np.exp(argument, out=argument)
            np.add(argument, 1.0, out=argument)
            np.reciprocal(argument, out=argument)
            return argument

        if array_workers == 1 or neutral.shape[0] < array_workers * 8:
            return evaluate(neutral)
        result = np.empty(neutral.shape + (3, 3), dtype=np.float32)

        def process_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            result[row0:row1] = evaluate(neutral[row0:row1])

        assert _ARRAY_EXECUTOR is not None
        list(
            _ARRAY_EXECUTOR.map(
                process_rows, _row_ranges(neutral.shape[0], array_workers)
            )
        )
        return result

    def distribute_layer_density_exact(
        activation_field: np.ndarray,
        net_density_field: np.ndarray,
    ) -> np.ndarray:
        result = np.empty_like(activation_field, dtype=np.float32)

        def process_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            target = result[row0:row1]
            np.multiply(
                activation_field[row0:row1],
                module.SUBEMULSION_CAPACITY_FRACTIONS,
                out=target,
            )
            denominator = np.sum(target, axis=-1, keepdims=True)
            np.maximum(denominator, 1e-8, out=denominator)
            np.divide(target, denominator, out=target)
            np.multiply(
                target,
                net_density_field[row0:row1, ..., None],
                out=target,
            )

        if array_workers == 1 or result.shape[0] < array_workers * 8:
            process_rows((0, result.shape[0]))
        else:
            assert _ARRAY_EXECUTOR is not None
            list(
                _ARRAY_EXECUTOR.map(
                    process_rows, _row_ranges(result.shape[0], array_workers)
                )
            )
        return result

    def release_field_exact(
        density_field: np.ndarray,
        layer_capacity: np.ndarray,
    ) -> np.ndarray:
        result = np.empty_like(density_field, dtype=np.float32)
        safe_capacity = np.maximum(layer_capacity, 1e-6)

        def process_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            target = result[row0:row1]
            np.multiply(density_field[row0:row1], -1.45, out=target)
            np.divide(target, safe_capacity, out=target)
            np.exp(target, out=target)
            np.subtract(1.0, target, out=target)

        if array_workers == 1 or result.shape[0] < array_workers * 8:
            process_rows((0, result.shape[0]))
        else:
            assert _ARRAY_EXECUTOR is not None
            list(
                _ARRAY_EXECUTOR.map(
                    process_rows, _row_ranges(result.shape[0], array_workers)
                )
            )
        return result

    def finalize_layer_density_exact(
        layer_density: np.ndarray,
        correction: np.ndarray,
        layer_capacity: np.ndarray,
    ) -> np.ndarray:
        developed = np.empty(layer_density.shape[:3], dtype=np.float32)
        upper = layer_capacity[None, None, ...] * 1.08

        def process_rows(bounds: tuple[int, int]) -> None:
            row0, row1 = bounds
            target = layer_density[row0:row1]
            np.add(target, correction[row0:row1], out=target)
            np.clip(target, 0.0, upper, out=target)
            developed[row0:row1] = np.sum(target, axis=-1)
            np.add(
                developed[row0:row1],
                module.SENSITO_DMIN_RGB,
                out=developed[row0:row1],
            )

        if array_workers == 1 or layer_density.shape[0] < array_workers * 8:
            process_rows((0, layer_density.shape[0]))
        else:
            assert _ARRAY_EXECUTOR is not None
            list(
                _ARRAY_EXECUTOR.map(
                    process_rows,
                    _row_ranges(layer_density.shape[0], array_workers),
                )
            )
        return developed

    def granularity_sigma_fast(log_exposure: np.ndarray) -> np.ndarray:
        source = np.asarray(log_exposure, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return module._V27_REFERENCE_PUBLISHED_5279_GRANULARITY_SIGMA(source)
        return run_numba_kernel(
            accel.channel_table_interp,
            source,
            module.GRANULARITY_LOG_EXPOSURE,
            module.GRANULARITY_SIGMA_D_RGB,
        )

    def develop_density_memory_reuse(log_exposure: np.ndarray) -> np.ndarray:
        source = np.asarray(log_exposure, dtype=np.float32)
        if source.ndim != 3 or source.shape[-1] != 3:
            return module._V27_REFERENCE_DEVELOP_5279_FROM_LOG_EXPOSURE(source)

        mean_total_started = time.perf_counter()
        record_started = time.perf_counter()
        net_density = module.record_densities_from_log_exposure(source)
        profile_mean("record_density", record_started)
        net_clamp_started = time.perf_counter()
        np.subtract(net_density, module.SENSITO_DMIN_RGB, out=net_density)
        np.maximum(net_density, 0.0, out=net_density)
        profile_mean("net_density_clamp", net_clamp_started)
        activation_started = time.perf_counter()
        activations = module.subemulsion_activation_probabilities(source)
        profile_mean("activation_probabilities", activation_started)
        layer_distribution_started = time.perf_counter()
        layer_density = distribute_layer_density_exact(
            activations, net_density
        )
        profile_mean("layer_density_distribution", layer_distribution_started)

        release_started = time.perf_counter()
        net_capacity = module.SENSITO_DENSITY_RGB[:, -1] - module.SENSITO_DMIN_RGB
        layer_capacity = (
            net_capacity[:, None]
            * module.SUBEMULSION_CAPACITY_FRACTIONS[None, :]
        )
        release = release_field_exact(layer_density, layer_capacity)
        profile_mean("release_field", release_started)

        neutral_record_started = time.perf_counter()
        neutral_scalar = np.mean(source, axis=-1)
        neutral_net = neutral_record_density_exact(neutral_scalar)
        profile_mean("neutral_record_density", neutral_record_started)
        np.subtract(neutral_net, module.SENSITO_DMIN_RGB, out=neutral_net)
        np.maximum(neutral_net, 0.0, out=neutral_net)
        neutral_activation_started = time.perf_counter()
        neutral_release = neutral_activation_probabilities_exact(
            neutral_scalar
        )
        profile_mean("neutral_activation_probabilities", neutral_activation_started)
        neutral_release_started = time.perf_counter()
        neutral_release = distribute_layer_density_exact(
            neutral_release, neutral_net
        )
        neutral_release = release_field_exact(
            neutral_release, layer_capacity
        )
        profile_mean("neutral_release_field", neutral_release_started)

        dir_setup_started = time.perf_counter()
        native_scale = source.shape[1] / 5760.0
        receiver_marginal = np.subtract(1.0, activations)
        np.multiply(receiver_marginal, activations, out=receiver_marginal)
        np.multiply(receiver_marginal, 4.0, out=receiver_marginal)
        np.clip(receiver_marginal, 0.0, 1.0, out=receiver_marginal)
        del activations
        correction = np.zeros_like(layer_density, dtype=np.float32)
        np.subtract(release, neutral_release, out=neutral_release)
        release_departure = neutral_release
        profile_mean("dir_setup", dir_setup_started)

        mean_dir_batch = getattr(module, "_WAVEFRONT_MEAN_DIR_BATCH", None)
        if mean_dir_batch is not None:
            mean_dir_started = time.perf_counter()
            correction = mean_dir_batch(
                release_departure,
                receiver_marginal,
                layer_capacity,
                native_scale,
            )
            profile_mean("dir_wavefront_batch", mean_dir_started)
        else:
            for source_record in range(3):
                for source_population in range(3):
                    sigma = max(
                        float(
                            module.DIR_POPULATION_LATERAL_SIGMA_PX_5760[
                                source_population
                            ]
                        )
                        * native_scale,
                        0.20,
                    )
                    deterministic_intralayer = float(
                        module.DIR_DETERMINISTIC_INTRALAYER_STRENGTH_RGB[
                            source_record
                        ]
                    )
                    if deterministic_intralayer != 0.0:
                        source_release = release[
                            ..., source_record, source_population
                        ]
                        release_gaussian_started = time.perf_counter()
                        diffused_release = cv2.GaussianBlur(
                            source_release,
                            (0, 0),
                            sigma,
                            borderType=cv2.BORDER_REFLECT,
                        )
                        profile_mean(
                            "dir_release_gaussian", release_gaussian_started
                        )
                        intralayer_started = time.perf_counter()
                        correction[..., source_record, source_population] += (
                            deterministic_intralayer
                            * layer_capacity[source_record, source_population]
                            * (source_release - diffused_release)
                            * receiver_marginal[
                                ..., source_record, source_population
                            ]
                        )
                        profile_mean("dir_intralayer_update", intralayer_started)

                    departure_gaussian_started = time.perf_counter()
                    diffused_departure = cv2.GaussianBlur(
                        release_departure[..., source_record, source_population],
                        (0, 0),
                        sigma,
                        borderType=cv2.BORDER_REFLECT,
                    )
                    profile_mean("dir_departure_gaussian", departure_gaussian_started)
                    updates: list[tuple[int, int, float]] = []
                    for destination_record in range(3):
                        record_transport = module.DIR_INTERIMAGE_RECEIVER_CAUSER[
                            destination_record, source_record
                        ]
                        if record_transport <= 0.0:
                            continue
                        for destination_population in range(3):
                            transport = (
                                module.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH
                                * record_transport
                                * module.DIR_POPULATION_TRANSPORT[
                                    destination_population, source_population
                                ]
                                * module.DIR_POPULATION_RELEASE_GAIN[source_population]
                                * module.DIR_POPULATION_RECEIVER_GAIN[
                                    destination_population
                                ]
                            )
                            updates.append(
                                (
                                    destination_record,
                                    destination_population,
                                    transport
                                    * layer_capacity[
                                        destination_record, destination_population
                                    ],
                                )
                            )

                    def apply_update(update: tuple[int, int, float]) -> None:
                        destination_record, destination_population, scale = update
                        correction[
                            ..., destination_record, destination_population
                        ] -= (
                            scale
                            * receiver_marginal[
                                ..., destination_record, destination_population
                            ]
                            * diffused_departure
                        )

                    if array_workers > 1 and len(updates) > 1:
                        interlayer_started = time.perf_counter()
                        assert _ARRAY_EXECUTOR is not None
                        list(_ARRAY_EXECUTOR.map(apply_update, updates))
                        profile_mean("dir_interlayer_updates", interlayer_started)
                    else:
                        interlayer_started = time.perf_counter()
                        for update in updates:
                            apply_update(update)
                        profile_mean("dir_interlayer_updates", interlayer_started)

        finalize_started = time.perf_counter()
        developed = finalize_layer_density_exact(
            layer_density, correction, layer_capacity
        )
        profile_mean("finalize_density", finalize_started)
        profile_mean("mean_negative_total", mean_total_started)
        return developed.astype(np.float32, copy=False)

    def couple_population_deviations_parallel(
        layer_deviation: np.ndarray,
        activations: np.ndarray,
        work_scale: float,
    ) -> np.ndarray:
        coupling_started = time.perf_counter()
        marginal_tile_pixels = getattr(
            module, "_WAVEFRONT_INPLACE_MARGINAL_TILE_PIXELS", None
        )
        if marginal_tile_pixels is None:
            copy_started = time.perf_counter()
            coupled = np.asarray(layer_deviation, dtype=np.float32).copy()
            profile_stochastic("coupling_initial_copy", copy_started)
            marginal_started = time.perf_counter()
            marginal = np.clip(
                4.0 * activations * (1.0 - activations), 0.0, 1.0
            )
            profile_stochastic("coupling_marginal", marginal_started)
        else:
            import wavefront_tile_lab_v001

            marginal_started = time.perf_counter()
            marginal = wavefront_tile_lab_v001.activation_marginal_inplace(
                activations,
                tile_pixels=int(marginal_tile_pixels),
            )
            profile_stochastic("coupling_marginal", marginal_started)
            # Contract the activation lifetime before allocating the coupled
            # output; the accepted default retains its historical order above.
            copy_started = time.perf_counter()
            coupled = np.asarray(layer_deviation, dtype=np.float32).copy()
            profile_stochastic("coupling_initial_copy", copy_started)
        for source_record in range(3):
            for source_population in range(3):
                source = layer_deviation[..., source_record, source_population]
                sigma = max(
                    float(
                        module.DIR_POPULATION_LATERAL_SIGMA_PX_5760[
                            source_population
                        ]
                    )
                    * work_scale,
                    0.20,
                )
                gaussian_started = time.perf_counter()
                diffused = cv2.GaussianBlur(
                    source, (0, 0), sigma, borderType=cv2.BORDER_REFLECT
                )
                profile_stochastic("coupling_gaussian", gaussian_started)
                intralayer_started = time.perf_counter()
                coupled[..., source_record, source_population] += (
                    module.DIR_STOCHASTIC_COUPLING_SCALE
                    * module.DIR_DEVELOPMENT_INTRALAYER_STRENGTH_RGB[source_record]
                    * (source - diffused)
                    * marginal[..., source_record, source_population]
                )
                profile_stochastic("coupling_intralayer_update", intralayer_started)
                updates: list[tuple[int, int, float]] = []
                for destination_record in range(3):
                    record_transport = module.DIR_INTERIMAGE_RECEIVER_CAUSER[
                        destination_record, source_record
                    ]
                    if record_transport <= 0.0:
                        continue
                    for destination_population in range(3):
                        transport = (
                            module.DIR_STOCHASTIC_COUPLING_SCALE
                            * module.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH
                            * record_transport
                            * module.DIR_POPULATION_TRANSPORT[
                                destination_population, source_population
                            ]
                            * module.DIR_POPULATION_RELEASE_GAIN[source_population]
                            * module.DIR_POPULATION_RECEIVER_GAIN[
                                destination_population
                            ]
                        )
                        updates.append(
                            (destination_record, destination_population, transport)
                        )

                def apply_update(update: tuple[int, int, float]) -> None:
                    destination_record, destination_population, transport = update
                    coupled[..., destination_record, destination_population] -= (
                        transport
                        * diffused
                        * marginal[
                            ..., destination_record, destination_population
                        ]
                    )

                if array_workers > 1 and len(updates) > 1:
                    interlayer_started = time.perf_counter()
                    assert _ARRAY_EXECUTOR is not None
                    list(_ARRAY_EXECUTOR.map(apply_update, updates))
                    profile_stochastic(
                        "coupling_interlayer_updates", interlayer_started
                    )
                else:
                    interlayer_started = time.perf_counter()
                    for update in updates:
                        apply_update(update)
                    profile_stochastic(
                        "coupling_interlayer_updates", interlayer_started
                    )
        profile_stochastic("coupling_total", coupling_started)
        return coupled.astype(np.float32, copy=False)

    def binomial_deviation_single_copy(
        activation_probability: np.ndarray,
        rng: np.random.Generator,
        radius: float,
        optical_sigma: float,
        site_count: int,
        subpixel_offset: tuple[float, float] = (0.0, 0.0),
        sample_seed: int | None = None,
    ) -> np.ndarray:
        # V27 callers pass the float32 output of a sigmoid, so every value is
        # already in [0, 1]. np.clip(...).astype(float32) made two full-frame
        # copies for each of 45 classes; one contiguous copy is sufficient and
        # feeds the random generator the identical probability bit pattern.
        probability_started = time.perf_counter()
        probability = np.ascontiguousarray(
            activation_probability, dtype=np.float32
        )
        profile_stochastic("probability_contiguous_copy", probability_started)
        random_started = time.perf_counter()
        if module.BINOMIAL_SAMPLER_MODE == "striped_v25":
            if sample_seed is None:
                raise ValueError("striped V25 sampler requires an explicit seed")
            developed_fraction = module._striped_binomial_sample(
                probability, site_count, sample_seed
            )
        else:
            developed_fraction = rng.binomial(site_count, probability).astype(
                np.float32
            )
        profile_stochastic("binomial_sampling", random_started)
        normalize_started = time.perf_counter()
        developed_fraction /= float(site_count)
        profile_stochastic("sample_normalize", normalize_started)

        kernel_started = time.perf_counter()
        kernel = module.disk_kernel(radius)
        kernel /= float(kernel.sum())
        profile_stochastic("disk_kernel_build", kernel_started)
        sampled_filter_started = time.perf_counter()
        sampled = cv2.filter2D(
            developed_fraction, -1, kernel, borderType=cv2.BORDER_REFLECT
        )
        profile_stochastic("disk_filter_sampled", sampled_filter_started)
        expected_filter_started = time.perf_counter()
        expected = cv2.filter2D(
            probability, -1, kernel, borderType=cv2.BORDER_REFLECT
        )
        profile_stochastic("disk_filter_expected", expected_filter_started)
        sigma = max(optical_sigma, 0.05)
        sampled_gaussian_started = time.perf_counter()
        sampled = cv2.GaussianBlur(
            sampled, (0, 0), sigma, borderType=cv2.BORDER_REFLECT
        )
        profile_stochastic("dye_gaussian_sampled", sampled_gaussian_started)
        expected_gaussian_started = time.perf_counter()
        expected = cv2.GaussianBlur(
            expected, (0, 0), sigma, borderType=cv2.BORDER_REFLECT
        )
        profile_stochastic("dye_gaussian_expected", expected_gaussian_started)
        subtract_started = time.perf_counter()
        deviation = (sampled - expected).astype(np.float32, copy=False)
        profile_stochastic("sample_expected_subtract", subtract_started)
        offset_x, offset_y = subpixel_offset
        if abs(offset_x) > 1e-6 or abs(offset_y) > 1e-6:
            transform = np.array(
                [[1.0, 0.0, offset_x], [0.0, 1.0, offset_y]],
                dtype=np.float32,
            )
            warp_started = time.perf_counter()
            deviation = cv2.warpAffine(
                deviation,
                transform,
                (deviation.shape[1], deviation.shape[0]),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REFLECT,
            )
            profile_stochastic("subpixel_warp", warp_started)
        return deviation

    module.apply_rgb_cube_lut = camera_cube
    module.apply_5279_net_density_lut = density_cube
    module.sample_record_density_delta_lut = print_output_cube
    module.apply_2383_h61_colour_delta_lut = h61_colour_delta_cube
    module.apply_2383_projection_lut = projection_density_cube
    module.apply_5279_to_2383_printer_density_lut = printer_density_cube
    module._raw_print_2383_density_from_negative = raw_print_density_fast
    module.print_2383_density_from_negative = print_density_fast
    normal_adapter.preserve_luma_and_compress_gamut = v31_gamut_fast
    module.apply_2383_monitor_neutral_curve = monitor_neutral_curve_fast
    module.neutralize_2383_projected_gray_scale = projected_gray_fast
    module.remove_tonal_grain_bias = remove_grain_bias_parallel
    module.match_2383_projection_to_rec709_monitor = (
        match_projection_zero_physical_authority
    )
    module.compress_unit_gamut = compress_unit_gamut_inplace
    module.compress_oklab_chroma_to_rec709 = compress_oklab_parallel
    module.neutralize_spirit_finished_gray_scale = neutralize_spirit
    module.scanner_density_from_total_record_density = scanner_density_parallel
    module.render_cineon_scan_master_from_scanner_density = render_cineon_parallel
    module.finish_cineon_scan_for_bluray = finish_cineon_parallel
    module.finish_bluray_grain_delta = finish_bluray_grain_parallel
    module.add_5279_optical_scatter = optical_scatter_parallel
    module.record_densities_from_log_exposure = record_density_exact_inplace
    module.subemulsion_activation_probabilities = activation_probabilities_inplace
    module.published_5279_granularity_sigma = granularity_sigma_fast
    module.develop_5279_record_density_from_log_exposure = (
        develop_density_memory_reuse
    )
    module.couple_5279_population_deviations = couple_population_deviations_parallel
    module.binomial_dye_cloud_deviation = binomial_deviation_single_copy
    if not exact_only and enable_record_density:
        module.record_densities_from_log_exposure = (
            record_density_semifused
            if enable_record_density == "semi"
            else record_density
        )
    if not exact_only and enable_matrix:
        module.vgamut_to_balanced_film_rgb = vgamut_to_film
        module.film_records_from_rgb = film_records
