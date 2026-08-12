"""Named, auditable viewing policies for Cineon printing-density data."""

from __future__ import annotations

from enum import Enum

import numpy as np

from . import legacy


class CineonViewPolicy(str, Enum):
    """Single-input policies that consume only one RGB Cineon code image."""

    OPEN_MONITOR_V66 = "cineon_open_monitor_v66"
    BLURAY_POINTWISE_V66 = "cineon_bluray_pointwise_v66"


POLICY_CONTRACTS: dict[CineonViewPolicy, dict[str, object]] = {
    CineonViewPolicy.OPEN_MONITOR_V66: {
        "inputs": ["rgb_10bit_printing_density_code"],
        "output": "linear_rec709_display_light",
        "pure_function_of_dpx": True,
        "operations": [
            "code95_reference_black",
            "0.008D_soft_toe",
            "scene10_derived_high_anchor",
            "0.90_linear_peak",
            "unit_gamut_compression",
        ],
        "classification": "provisional_monitor_policy_not_5279_property",
    },
    CineonViewPolicy.BLURAY_POINTWISE_V66: {
        "inputs": ["rgb_10bit_printing_density_code"],
        "output": "linear_rec709_display_light",
        "pure_function_of_dpx": True,
        "operations": [
            "cineon_open_monitor_v66",
            "lower_scale_gamma_1.20_anchored_at_18_percent",
            "finish_fade_from_luma_0.12_to_0.30",
            "luminance_preserving_neutral_scale_calibration",
            "rec709_gamut_compression",
        ],
        "classification": "provisional_finish_policy_not_5279_property",
    },
}


LEGACY_MANAGED_SCAN_CONTRACT: dict[str, object] = {
    "name": "legacy_managed_bluray_v40_to_v66",
    "inputs": [
        "formed_rgb_10bit_printing_density_code",
        "hidden_deterministic_mean_scan",
    ],
    "pure_function_of_dpx": False,
    "additional_operations": [
        "mean_relative_luma_opponent_decomposition",
        "0.55px_at_2k_opponent_lowpass",
        "0.55_high_frequency_opponent_retention",
        "mean_luma_dependent_shadow_visibility",
    ],
    "classification": "historical_delivery_grain_management_not_view_transform",
}


LEGACY_MANAGED_PROJECTION_CONTRACT: dict[str, object] = {
    "name": "legacy_managed_projection_v40_to_v72",
    "inputs": [
        "formed_5279_record_density",
        "hidden_deterministic_mean_2383_projection",
        "matched_legacy_managed_scan",
    ],
    "pure_function_of_projected_print": False,
    "stochastic_observer": "archive_pointwise_signed_delta",
    "local_projection_grain_operations": [
        "mean_relative_rec709_luma_opponent_decomposition",
        "0.62px_at_2k_opponent_lowpass",
        "0.0_high_frequency_opponent_retention",
        "0.66_opponent_strength",
    ],
    "publication_operations": [
        "scan_referenced_low_frequency_oklab_opponent_colour",
        "0.72px_at_2k_colour_crossover",
        "0.0_projection_high_frequency_opponent_retention",
        "exact_projection_rec709_linear_luma",
    ],
    "classification": (
        "historical_managed_monitor_policy_not_measured_5279_or_2383_property"
    ),
    "evidence_boundary": (
        "Kodak's public granularity curves do not identify cross-record "
        "covariance or the final projected colour-grain NPS. V79 showed that "
        "removing this management reopens sparse primary-colour events in the "
        "current model; retention is therefore a defect-containment boundary, "
        "not evidence that real 5279 projection has these coefficients."
    ),
}


def render_cineon_view(
    cineon_code: np.ndarray,
    policy: CineonViewPolicy,
) -> np.ndarray:
    """Render one DPX code image through exactly one declared view policy."""
    selected = CineonViewPolicy(policy)
    e = legacy.model
    opened = e.render_cineon_open_display_from_code(cineon_code)
    if selected is CineonViewPolicy.OPEN_MONITOR_V66:
        return opened.astype(np.float32, copy=False)
    if selected is CineonViewPolicy.BLURAY_POINTWISE_V66:
        finished = e.finish_cineon_scan_for_bluray(opened)
        finished = e.compress_oklab_chroma_to_rec709(finished)
        if e.SPIRIT_NEUTRAL_SCALE_CALIBRATION_ENABLED:
            finished = e.neutralize_spirit_finished_gray_scale(finished)
        return np.clip(finished, 0.0, 1.0).astype(np.float32, copy=False)
    raise AssertionError(f"unhandled Cineon view policy: {selected}")
