"""Executable gates for the accepted V37--V41 research conclusions."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .contracts import EngineConfig, EngineMode


class ResearchConformanceError(RuntimeError):
    """Raised when active code no longer represents the documented baseline."""


def _close(actual: float, expected: float, tolerance: float = 1e-9) -> bool:
    return math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tolerance)


def research_conformance(model: Any, profile: Any, config: EngineConfig) -> dict[str, Any]:
    """Report code-level ownership of the latest accepted research boundaries."""

    hypothesis = config.profile == "v43h"
    v48_integration = config.profile in {"v46", "v48", "v49", "v50", "v51", "v52", "v53", "v54", "v55", "v56", "v57", "v58", "v59", "v60", "v61", "v62", "v63", "v64", "v66", "v72"}
    v49_density_boundary = config.profile in {"v46", "v49", "v50", "v51", "v52", "v53", "v54", "v55", "v56", "v57", "v58", "v59", "v60", "v61", "v62", "v63", "v64", "v66", "v72"}
    v50_granularity_trace = config.profile in {"v46", "v50", "v51", "v52", "v53", "v54", "v55", "v56", "v57", "v58", "v59", "v60", "v61", "v62", "v63", "v64", "v66", "v72"}
    v51_spectral_trace = config.profile in {"v46", "v51", "v52", "v53", "v54", "v55", "v56", "v57", "v58", "v59", "v60", "v61", "v62", "v63", "v64", "v66", "v72"}
    v52_characteristic_trace = config.profile in {"v46", "v52", "v53", "v54", "v55", "v56", "v57", "v58", "v59", "v60", "v61", "v62", "v63", "v64", "v66", "v72"}
    v53_print_characteristic_trace = config.profile in {"v46", "v53", "v54", "v55", "v56", "v57", "v58", "v59", "v60", "v61", "v62", "v63", "v64", "v66", "v72"}
    v54_print_sensitivity_trace = config.profile in {"v46", "v54", "v55", "v56", "v57", "v58", "v59", "v60", "v61", "v62", "v63", "v64", "v66", "v72"}
    v55_print_dye_trace = config.profile in {"v46", "v55", "v56", "v57", "v58", "v59", "v60", "v61", "v62", "v63", "v64", "v66", "v72"}
    v56_physical_colour_authority = config.profile in {"v56", "v57"}
    v57_identity_interimage = config.profile == "v57"
    v58_integral_lad_coordinate = config.profile == "v58"
    v59_visual_neutral_base = config.profile == "v59"
    v60_dmin_registration = config.profile in {"v46", "v60", "v61", "v62", "v63", "v64", "v66", "v72"}
    v61_status_m_joint_inverse = config.profile in {"v46", "v61", "v62", "v63", "v64", "v66", "v72"}
    v62_interimage_and_lattice = config.profile in {"v46", "v62", "v63", "v64", "v66", "v72"}
    v63_neutral_trajectory = config.profile in {"v46", "v63", "v64", "v66", "v72"}
    v64_unshaped_print_density = config.profile in {"v46", "v64", "v66", "v72"}
    v66_cineon_printing_density = config.profile in {"v46", "v66", "v72"}
    observer_integrity = config.profile in {
        "v44", "v45", "v46", "v48", "v49", "v50", "v51", "v52", "v53", "v54", "v55", "v56", "v57", "v58", "v59", "v60", "v61", "v62", "v63", "v64", "v66", "v72"
    }
    official_observer = config.profile in {
        "v45", "v46", "v48", "v49", "v50", "v51", "v52", "v53", "v54", "v55", "v56", "v57", "v58", "v59", "v60", "v61", "v62", "v63", "v64", "v66", "v72"
    }
    release_class_by_profile = {
        "v44": "evidence_boundary_revision",
        "v45": "measured_observer_revision",
        "v48": "numerical_image_formation_correction",
        "v49": "microscopic_density_boundary_correction",
        "v50": "published_granularity_vector_trace_correction",
        "v51": "published_negative_spectral_vector_trace_correction",
        "v52": "published_characteristic_vector_trace_correction",
        "v53": "published_2383_characteristic_vector_trace_correction",
        "v54": "published_2383_sensitivity_vector_trace_correction",
        "v55": "published_2383_dye_vector_trace_correction",
        "v56": "evidence_enabled_observer_experiment",
        "v57": "unidentified_interimage_boundary_experiment",
        "v58": "evidence_corrected_2383_lad_coordinate",
        "v59": "published_2383_visual_neutral_vector_trace_correction",
        "v60": "evidence_reconciled_2383_dmin_coordinate",
        "v61": "evidence_corrected_5279_status_m_joint_inverse",
        "v62": "evidence_separated_2383_interimage_and_lattice",
        "v63": "evidence_corrected_projection_neutral_coordinate",
        "v64": "evidence_withdrawn_unmeasured_2383_density_shaper",
        "v66": "evidence_corrected_cineon_printing_density_coordinate",
        "v72": "evidence_minimal_identity_record_formation",
        "v46": "certified_spectral_inverse_and_endpoint_correction",
    }
    expected_release_class = release_class_by_profile.get(config.profile)

    checks = {
        # V37: independent sites, stable numerical integration operator.
        "v37_stable_balanced_phase": model.GRAIN_SUBPIXEL_PHASE_MODE
        == "stable_balanced",
        "v37_or_v48_site_integration_radius": _close(
            model.GRAIN_SUBPIXEL_PHASE_RADIUS_PX,
            0.0 if v48_integration else 0.38,
        ),
        "v37_phase_offset_30_degrees": _close(
            model.GRAIN_STABLE_PHASE_OFFSET_RADIANS, math.pi / 6.0
        ),
        # V40: retain processed-density RMS, remove unsupported print grain and
        # duplicate high-frequency opponent colour.
        "v40_post_process_granularity_boundary": model.GRAIN_CALIBRATION_DOMAIN
        == "post_coupling_residual",
        "v40_formed_density_observer_management": bool(
            model.FORMED_DENSITY_OBSERVER_GRAIN_MANAGEMENT
        ),
        "v40_or_v43h_explicit_2383_grain_boundary": model.PRINT_GRAIN_DOMAIN
        == ("hypothesis_common_density" if hypothesis else "none"),
        "v40_archive_pointwise_signed_grain_observer": (
            model.PROJECTION_GRAIN_DELTA_OBSERVER == "archive_pointwise"
        ),
        "v40_no_duplicate_hf_opponent_reinjection": _close(
            model.PROJECTION_CHROMA_GRAIN_HIGH_FREQUENCY_RETENTION, 0.0
        ),
        # V41: provisional chart-bounded chroma transport with a physical
        # record-positive boundary, never a global white-balance or grade.
        "v41_signed_basis_only_when_records_stay_positive": (
            not model.FILM_RGB_CLIP_BEFORE_RECORDS
            and model.FILM_RECORD_BOUNDARY_MODE == "record_positive_signed"
        ),
        "v41_chart_residual_enabled_at_one_eighth": (
            bool(model.INPUT_CHROMA_RESIDUAL_ENABLED)
            and _close(model.INPUT_CHROMA_RESIDUAL_STRENGTH, 0.125)
            and np.array_equal(
                np.asarray(model.INPUT_CHROMA_RESIDUAL_D50, dtype=np.float32),
                np.asarray(profile.INPUT_CHROMA_RESIDUAL_D50, dtype=np.float32),
            )
        ),
        "v30_to_v41_unidentified_d60_lattice_disabled": _close(
            model.PRINT_2383_D60_RELATIVE_CHROMA_STRENGTH, 0.0
        ),
        "baseline_controls_frozen": (
            config.research_baseline
            and _close(config.exposure_stops, 0.45)
            and _close(config.grain_scale, 1.0)
            and config.oversample == 1
            and config.grain_domain_salt == 0
        ),
    }
    if hypothesis:
        expected = profile.PROFILE
        checks.update(
            {
                "v43h_is_explicitly_not_a_measurement": (
                    expected.get("release_class") == "hypothesis_not_measurement"
                ),
                "v43h_kodak_48um_rms_authority_retained": (
                    model.GRAIN_CALIBRATION_DOMAIN == "post_coupling_residual"
                    and _close(model.NEGATIVE_GRAIN_CORRELATION_SCALE, 0.72)
                ),
                "v43h_spirit_quarter_step_isolated": (
                    np.array_equal(
                        np.asarray(model.SPIRIT_PERIOD_OBSERVER_CENTRES_NM),
                        np.asarray(profile.SPIRIT_PERIOD_OBSERVER_CENTRES_NM),
                    )
                    and np.array_equal(
                        np.asarray(model.SPIRIT_PERIOD_OBSERVER_SIGMAS_NM),
                        np.asarray(profile.SPIRIT_PERIOD_OBSERVER_SIGMAS_NM),
                    )
                ),
                "v43h_2383_common_mode_is_subordinate": (
                    _close(
                        model.PRINT_2383_HYPOTHESIS_COMMON_GRAIN_DENSITY_SCALE,
                        0.06,
                    )
                    and _close(model.PRINT_2383_HYPOTHESIS_SITE_COUNT, 900.0)
                ),
            }
        )
    if observer_integrity:
        expected = profile.PROFILE
        checks.update(
            {
                "v44_is_an_evidence_boundary_revision": (
                    expected.get("release_class") == expected_release_class
                ),
                "v44_retains_accepted_normal_process_colour_boundary": (
                    expected.get("projection_colour_policy")
                    == (
                        "physical_spectral_v56"
                        if v56_physical_colour_authority
                        else "scan_referenced_v31"
                    )
                ),
                "v44_review_integration_is_explicit": (
                    expected.get("review_sampling_policy")
                    == "linear_light_pixel_area_integration"
                ),
                "v44_withholds_unmeasured_2383_grain": (
                    model.PRINT_GRAIN_DOMAIN == "none"
                    and _close(
                        model.PRINT_2383_HYPOTHESIS_COMMON_GRAIN_DENSITY_SCALE,
                        0.0,
                    )
                ),
                "v44_retains_v42_negative_morphology": _close(
                    model.NEGATIVE_GRAIN_CORRELATION_SCALE, 0.76
                ),
                "v44_retains_v42_spirit_observer": (
                    np.array_equal(
                        np.asarray(model.SPIRIT_PERIOD_OBSERVER_CENTRES_NM),
                        np.asarray([620.0, 540.0, 470.0], dtype=np.float32),
                    )
                    and np.array_equal(
                        np.asarray(model.SPIRIT_PERIOD_OBSERVER_SIGMAS_NM),
                        np.asarray([52.0, 44.0, 38.0], dtype=np.float32),
                    )
                ),
            }
        )
    if official_observer:
        checks.update(
            {
                "active_release_class_matches_profile": (
                    profile.PROFILE.get("release_class") == expected_release_class
                ),
                "v45_uses_official_cie_1931_1nm_observer": (
                    model.PRINT_2383_CMF_MODE
                    == "cie_1931_2deg_official_1nm"
                ),
            }
        )
    if v48_integration:
        expected_sigma = np.sqrt(
            np.square(model.SUBEMULSION_OPTICAL_SIGMA_BASE_PX_5760_RGB)
            + 1.0 / 6.0
        ).astype(np.float32)
        checks.update(
            {
                "v48_removes_global_bilinear_phase": (
                    model.GRAIN_SITE_RASTERIZATION_MODE
                    == "isotropic_continuous_site_second_moment"
                    and _close(model.GRAIN_SUBPIXEL_PHASE_RADIUS_PX, 0.0)
                ),
                "v48_uses_geometric_second_moment_integration": np.array_equal(
                    np.asarray(
                        model.SUBEMULSION_OPTICAL_SIGMA_PX_5760_RGB,
                        dtype=np.float32,
                    ),
                    expected_sigma,
                ),
                "v48_plus_declares_local_density_boundary": (
                    model.GRAIN_LOCAL_DENSITY_BOUND_MODE
                    == (
                        "nonnegative_microscopic_density"
                        if v49_density_boundary
                        else "legacy_macro_dmax_plus_0_12"
                    )
                ),
            }
        )
    if v50_granularity_trace:
        checks.update(
            {
                "v50_uses_vector_traced_granularity_domain": np.array_equal(
                    np.asarray(model.GRANULARITY_LOG_EXPOSURE, dtype=np.float32),
                    np.asarray(profile.GRANULARITY_LOG_EXPOSURE, dtype=np.float32),
                ),
                "v50_uses_vector_traced_granularity_sigma": np.array_equal(
                    np.asarray(model.GRANULARITY_SIGMA_D_RGB, dtype=np.float32),
                    np.asarray(profile.GRANULARITY_SIGMA_D_RGB, dtype=np.float32),
                ),
                "v50_withholds_unplotted_plus_one_loge_sample": (
                    float(model.GRANULARITY_LOG_EXPOSURE[-1]) == 0.0
                ),
            }
        )
    if v51_spectral_trace:
        checks.update(
            {
                "v51_uses_vector_traced_net_dye_spectra": np.array_equal(
                    np.asarray(
                        model.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY,
                        dtype=np.float32,
                    ),
                    np.asarray(
                        profile.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY,
                        dtype=np.float32,
                    ),
                ),
                "v51_uses_vector_traced_minimum_density_spectrum": np.array_equal(
                    np.asarray(
                        model.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY,
                        dtype=np.float32,
                    ),
                    np.asarray(
                        profile.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY,
                        dtype=np.float32,
                    ),
                ),
            }
        )
    if v52_characteristic_trace:
        zero_index = int(np.flatnonzero(profile.SENSITO_LOG_EXPOSURE == 0.0)[0])
        archive_zero = int(
            np.flatnonzero(model.SENSITO_LOG_EXPOSURE_ARCHIVE == 0.0)[0]
        )
        archive_shoulder = np.asarray(
            model.SENSITO_DENSITY_RGB_ARCHIVE[:, archive_zero + 1 : archive_zero + 3]
            - model.SENSITO_DENSITY_RGB_ARCHIVE[:, archive_zero, None],
            dtype=np.float32,
        )
        active_shoulder = np.asarray(
            model.SENSITO_DENSITY_RGB[:, zero_index + 1 : zero_index + 3]
            - model.SENSITO_DENSITY_RGB[:, zero_index, None],
            dtype=np.float32,
        )
        checks.update(
            {
                "v52_uses_vector_traced_characteristic_domain": np.array_equal(
                    np.asarray(model.SENSITO_LOG_EXPOSURE, dtype=np.float32),
                    np.asarray(profile.SENSITO_LOG_EXPOSURE, dtype=np.float32),
                ),
                "v52_uses_vector_traced_characteristic_density": np.array_equal(
                    np.asarray(model.SENSITO_DENSITY_RGB, dtype=np.float32),
                    np.asarray(profile.SENSITO_DENSITY_RGB, dtype=np.float32),
                ),
                "v52_dmin_matches_first_traced_density": np.array_equal(
                    np.asarray(model.SENSITO_DMIN_RGB, dtype=np.float32),
                    np.asarray(profile.SENSITO_DENSITY_RGB[:, 0], dtype=np.float32),
                ),
                "v52_pretrace_dmin_hold_is_explicit": np.array_equal(
                    np.asarray(model.SENSITO_DENSITY_RGB[:, 0], dtype=np.float32),
                    np.asarray(model.SENSITO_DENSITY_RGB[:, 1], dtype=np.float32),
                ),
                "v52_inferred_shoulder_preserves_archive_increments": np.allclose(
                    active_shoulder, archive_shoulder, rtol=0.0, atol=3e-7
                ),
            }
        )
    if v53_print_characteristic_trace:
        print_density = np.asarray(model.PRINT_2383_DENSITY_RGB, dtype=np.float32)
        profile_print_density = np.asarray(
            profile.PRINT_2383_DENSITY_RGB, dtype=np.float32
        )
        checks.update(
            {
                "v53_uses_vector_traced_2383_characteristic_domain": np.array_equal(
                    np.asarray(model.PRINT_2383_LOG_EXPOSURE, dtype=np.float32),
                    np.asarray(profile.PRINT_2383_LOG_EXPOSURE, dtype=np.float32),
                ),
                "v53_uses_vector_traced_2383_characteristic_density": np.array_equal(
                    print_density, profile_print_density
                ),
                "v53_2383_dmin_is_one_consistent_source": np.array_equal(
                    np.asarray(model.PRINT_2383_STATUS_A_DMIN_RGB, dtype=np.float32),
                    print_density[:, 0],
                ),
                "v53_2383_curves_are_monotonic": bool(
                    np.all(np.diff(print_density, axis=1) >= 0.0)
                ),
                "v53_2383_dmax_covers_all_vector_endpoints": _close(
                    model.PRINT_2383_DMAX, float(np.max(print_density)), 1e-7
                ),
                "v53_2383_graph_border_holds_are_explicit": (
                    _close(model.PRINT_2383_LOG_EXPOSURE[0], -3.0)
                    and _close(model.PRINT_2383_LOG_EXPOSURE[-1], 3.0)
                    and np.array_equal(print_density[:, 0], print_density[:, 1])
                    and np.array_equal(print_density[:, -1], print_density[:, -2])
                ),
            }
        )
    if v54_print_sensitivity_trace:
        checks.update(
            {
                "v54_uses_vector_traced_2383_record_sensitivity": np.array_equal(
                    np.asarray(
                        model.PRINT_2383_LOG_SENSITIVITY_CMY, dtype=np.float32
                    ),
                    np.asarray(
                        profile.PRINT_2383_LOG_SENSITIVITY_CMY, dtype=np.float32
                    ),
                ),
                "v54_retains_unmodified_2383_dye_spectra": np.array_equal(
                    np.asarray(
                        model.PRINT_DYE_CMY_SPECTRAL_DENSITY, dtype=np.float32
                    ),
                    np.asarray(
                        (
                            profile.PRINT_DYE_CMY_SPECTRAL_DENSITY
                            if v55_print_dye_trace
                            else model.PRINT_DYE_CMY_SPECTRAL_DENSITY_ARCHIVE
                        ),
                        dtype=np.float32,
                    ),
                ),
                "v54_explicit_sensitivity_floor_is_bounded": bool(
                    np.min(model.PRINT_2383_LOG_SENSITIVITY_CMY) == -6.0
                    and np.max(model.PRINT_2383_LOG_SENSITIVITY_CMY) < 1.0
                ),
            }
        )
    if v55_print_dye_trace:
        dye = np.asarray(model.PRINT_DYE_CMY_SPECTRAL_DENSITY, dtype=np.float32)
        checks.update(
            {
                "v55_uses_vector_traced_2383_dye_spectra": np.array_equal(
                    dye,
                    np.asarray(
                        profile.PRINT_DYE_CMY_SPECTRAL_DENSITY, dtype=np.float32
                    ),
                ),
                "v55_retains_archive_xenon_spd": np.array_equal(
                    np.asarray(
                        model.KODAK_XENON_PROJECTOR_RELATIVE_SPD,
                        dtype=np.float32,
                    ),
                    np.asarray(
                        model.KODAK_XENON_PROJECTOR_RELATIVE_SPD_ARCHIVE,
                        dtype=np.float32,
                    ),
                ),
                "v55_dye_peaks_match_vector_graph_regions": np.array_equal(
                    np.argmax(dye, axis=0), np.asarray([14, 8, 3])
                ),
                "v55_dye_density_is_nonnegative": bool(np.all(dye >= 0.0)),
            }
        )
    if v56_physical_colour_authority:
        checks.update(
            {
                "v56_assigns_projection_colour_to_physical_spectra": (
                    model.PRINT_MONITOR_COLOUR_AUTHORITY
                    == "physical_spectral_v56"
                ),
                "v56_remains_an_observer_experiment": (
                    profile.PROFILE.get("release_class")
                    == (
                        "unidentified_interimage_boundary_experiment"
                        if v57_identity_interimage
                        else "evidence_enabled_observer_experiment"
                    )
                ),
                "v56_scan_reference_still_owns_neutral_display_scale_only": (
                    model.PRINT_2383_D60_RELATIVE_CHROMA_STRENGTH == 0.0
                    and len(model.PRINT_MONITOR_SCAN_LUMA_ANCHORS)
                    == len(model.PRINT_MONITOR_TARGET_LUMA_ANCHORS)
                ),
            }
        )
    if v57_identity_interimage:
        checks.update(
            {
                "v57_uses_identity_2383_interimage_boundary": np.array_equal(
                    np.asarray(model.PRINT_2383_INTERIMAGE_MATRIX, dtype=np.float32),
                    np.eye(3, dtype=np.float32),
                ),
                "v57_archive_empirical_interimage_remains_recoverable": bool(
                    not np.array_equal(
                        np.asarray(
                            model.PRINT_2383_INTERIMAGE_MATRIX_ARCHIVE,
                            dtype=np.float32,
                        ),
                        np.eye(3, dtype=np.float32),
                    )
                ),
            }
        )
    if v58_integral_lad_coordinate:
        solved_principal, solved_amounts, solved_residual = (
            model.solve_2383_lad_principal_density_rgb(
                model.PRINT_2383_LAD_STATUS_A_AIM_RGB
            )
        )
        reconstructed_status_a, reconstructed_amounts = (
            model.integral_status_a_from_2383_principal_density_rgb(
                solved_principal
            )
        )
        checks.update(
            {
                "v58_integral_lad_coordinate_policy_enabled": (
                    model.PRINT_2383_LAD_PRINCIPAL_POLICY
                    == "integral_spectral_inverse_v58"
                ),
                "v58_principal_density_matches_spectral_inverse": np.allclose(
                    np.asarray(
                        model.PRINT_2383_LAD_PRINCIPAL_DENSITY_RGB,
                        dtype=np.float32,
                    ),
                    solved_principal,
                    rtol=0.0,
                    atol=2e-7,
                ),
                "v58_integral_lad_inverse_is_numerically_closed": bool(
                    np.max(np.abs(solved_residual)) < 1e-7
                ),
                "v58_principal_triplet_forwards_to_official_integral_lad": np.allclose(
                    reconstructed_status_a,
                    model.PRINT_2383_LAD_STATUS_A_AIM_RGB,
                    rtol=0.0,
                    atol=2e-7,
                ),
                "v58_forward_and_inverse_dye_amounts_agree": np.allclose(
                    reconstructed_amounts,
                    solved_amounts,
                    rtol=0.0,
                    atol=2e-6,
                ),
                "v58_documented_principal_density_triplet": np.allclose(
                    solved_principal,
                    np.asarray([0.9898583, 0.8823338, 0.8419376]),
                    rtol=0.0,
                    atol=2e-6,
                ),
                "v58_documented_analytical_dye_triplet": np.allclose(
                    solved_amounts,
                    np.asarray([1.0545850, 1.0300304, 0.9626921]),
                    rtol=0.0,
                    atol=2e-6,
                ),
                "v58_archive_interimage_is_unchanged": np.array_equal(
                    np.asarray(model.PRINT_2383_INTERIMAGE_MATRIX),
                    np.asarray(model.PRINT_2383_INTERIMAGE_MATRIX_ARCHIVE),
                ),
                "v58_scan_referenced_colour_policy_is_unchanged": (
                    model.PRINT_MONITOR_COLOUR_AUTHORITY
                    == model.PRINT_MONITOR_COLOUR_AUTHORITY_ARCHIVE
                ),
            }
        )
    if v59_visual_neutral_base:
        base = np.asarray(
            model.PRINT_2383_DMIN_SPECTRAL_DENSITY, dtype=np.float32
        )
        visual_neutral = np.asarray(
            profile.PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY,
            dtype=np.float32,
        )
        dye_sum = np.sum(
            np.asarray(model.PRINT_DYE_CMY_SPECTRAL_DENSITY, dtype=np.float32),
            axis=1,
        )
        expected_base = np.maximum(visual_neutral - dye_sum, 0.0).astype(
            np.float32
        )
        solved_principal, solved_amounts, solved_residual = (
            model.solve_2383_lad_principal_density_rgb(
                model.PRINT_2383_LAD_STATUS_A_AIM_RGB
            )
        )
        reconstructed_status_a, reconstructed_amounts = (
            model.integral_status_a_from_2383_principal_density_rgb(
                solved_principal
            )
        )
        checks.update(
            {
                "v59_visual_neutral_trace_is_checksum_locked": (
                    profile.TRACE_SHA256
                    == "9bc1645f4afe79e01e917dc11c556d671eb2c3b367b884807e010d509bd1e90e"
                ),
                "v59_spectral_base_policy_enabled": (
                    model.PRINT_2383_DMIN_SPECTRAL_POLICY
                    == "vector_neutral_residual_v59"
                ),
                "v59_integral_lad_coordinate_policy_enabled": (
                    model.PRINT_2383_LAD_PRINCIPAL_POLICY
                    == "integral_spectral_inverse_v59"
                ),
                "v59_base_is_nonnegative_visual_neutral_residual": (
                    np.array_equal(base, expected_base)
                    and bool(np.all(base >= 0.0))
                ),
                "v59_equal_normalized_dyes_plus_base_rebuild_visual_neutral": np.allclose(
                    base + dye_sum,
                    visual_neutral,
                    rtol=0.0,
                    atol=2e-7,
                ),
                "v59_integral_lad_inverse_is_numerically_closed": bool(
                    np.max(np.abs(solved_residual)) < 1e-7
                ),
                "v59_principal_triplet_forwards_to_official_integral_lad": np.allclose(
                    reconstructed_status_a,
                    model.PRINT_2383_LAD_STATUS_A_AIM_RGB,
                    rtol=0.0,
                    atol=2e-7,
                ),
                "v59_forward_and_inverse_dye_amounts_agree": np.allclose(
                    reconstructed_amounts,
                    solved_amounts,
                    rtol=0.0,
                    atol=2e-6,
                ),
                "v59_documented_principal_density_triplet": np.allclose(
                    solved_principal,
                    np.asarray([0.99258363, 0.8840549, 0.8475401]),
                    rtol=0.0,
                    atol=2e-6,
                ),
                "v59_documented_analytical_dye_triplet": np.allclose(
                    solved_amounts,
                    np.asarray([1.0270529, 0.9971411, 0.9746268]),
                    rtol=0.0,
                    atol=2e-6,
                ),
                "v59_archive_interimage_is_unchanged": np.array_equal(
                    np.asarray(model.PRINT_2383_INTERIMAGE_MATRIX),
                    np.asarray(model.PRINT_2383_INTERIMAGE_MATRIX_ARCHIVE),
                ),
                "v59_scan_referenced_colour_policy_is_unchanged": (
                    model.PRINT_MONITOR_COLOUR_AUTHORITY
                    == model.PRINT_MONITOR_COLOUR_AUTHORITY_ARCHIVE
                ),
            }
        )
    if v60_dmin_registration:
        base = np.asarray(
            model.PRINT_2383_DMIN_SPECTRAL_DENSITY, dtype=np.float32
        )
        visual_neutral = np.asarray(
            profile.PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY,
            dtype=np.float32,
        )
        dye_sum = np.sum(
            np.asarray(model.PRINT_DYE_CMY_SPECTRAL_DENSITY, dtype=np.float32),
            axis=1,
        )
        solved_principal, solved_amounts, solved_residual = (
            model.solve_2383_lad_principal_density_rgb(
                model.PRINT_2383_LAD_STATUS_A_AIM_RGB
            )
        )
        reconstructed_status_a, reconstructed_amounts = (
            model.integral_status_a_from_2383_principal_density_rgb(
                solved_principal
            )
        )
        zero_amount_axes = model._print_2383_analytical_amount_axes(
            np.asarray(model.PRINT_2383_STATUS_A_DMIN_RGB, dtype=np.float32)
        )
        zero_amount_diagonal = np.asarray(
            [zero_amount_axes[channel][channel] for channel in range(3)]
        )
        checks.update(
            {
                "v60_preserves_checksum_locked_visual_neutral_residual": (
                    profile.TRACE_SHA256
                    == "9bc1645f4afe79e01e917dc11c556d671eb2c3b367b884807e010d509bd1e90e"
                    and np.allclose(
                        base + dye_sum,
                        visual_neutral,
                        rtol=0.0,
                        atol=2e-7,
                    )
                ),
                "v60_dmin_registered_spectral_policy_enabled": (
                    model.PRINT_2383_DMIN_SPECTRAL_POLICY
                    == "vector_neutral_residual_dmin_registered_v60"
                ),
                "v60_integral_lad_coordinate_policy_enabled": (
                    model.PRINT_2383_LAD_PRINCIPAL_POLICY
                    == "integral_spectral_inverse_v60"
                ),
                "v60_zero_dye_amount_is_exactly_hd_curve_dmin": bool(
                    np.max(np.abs(zero_amount_diagonal)) < 1e-12
                ),
                "v60_integral_lad_inverse_is_numerically_closed": bool(
                    np.max(np.abs(solved_residual)) < 1e-7
                ),
                "v60_principal_triplet_forwards_to_official_integral_lad": np.allclose(
                    reconstructed_status_a,
                    model.PRINT_2383_LAD_STATUS_A_AIM_RGB,
                    rtol=0.0,
                    atol=2e-7,
                ),
                "v60_forward_and_inverse_dye_amounts_agree": np.allclose(
                    reconstructed_amounts,
                    solved_amounts,
                    rtol=0.0,
                    atol=2e-6,
                ),
                "v60_documented_principal_density_triplet": np.allclose(
                    solved_principal,
                    np.asarray([0.9897172, 0.8820604, 0.84214854]),
                    rtol=0.0,
                    atol=2e-6,
                ),
                "v60_documented_analytical_dye_triplet": np.allclose(
                    solved_amounts,
                    np.asarray([1.0550362, 1.0296745, 0.9633866]),
                    rtol=0.0,
                    atol=2e-6,
                ),
                "v60_plus_interimage_matches_declared_profile": (
                    np.array_equal(
                        np.asarray(model.PRINT_2383_INTERIMAGE_MATRIX),
                        np.eye(3),
                    )
                    if v62_interimage_and_lattice
                    else np.array_equal(
                        np.asarray(model.PRINT_2383_INTERIMAGE_MATRIX),
                        np.asarray(model.PRINT_2383_INTERIMAGE_MATRIX_ARCHIVE),
                    )
                ),
                "v60_scan_referenced_colour_policy_is_unchanged": (
                    model.PRINT_MONITOR_COLOUR_AUTHORITY
                    == model.PRINT_MONITOR_COLOUR_AUTHORITY_ARCHIVE
                ),
            }
        )
    if v61_status_m_joint_inverse:
        status_m_wavelengths = np.asarray(
            model.NEGATIVE_5279_STATUS_M_WAVELENGTHS_NM, dtype=np.float32
        )
        status_m_weights = np.asarray(
            model.NEGATIVE_5279_STATUS_M_RGB_WEIGHTS, dtype=np.float32
        )
        analytical_reference = np.asarray(
            [0.47126241, 0.61012430, 0.73570945], dtype=np.float32
        )
        status_m_reference = (
            model.negative_5279_status_m_net_density_from_analytical_cmy(
                analytical_reference
            )
        )
        recovered_reference = (
            model.solve_5279_analytical_cmy_from_status_m_net_density(
                status_m_reference
            )
        )
        zero_status_m = (
            model.negative_5279_status_m_net_density_from_analytical_cmy(
                np.zeros(3, dtype=np.float32)
            )
        )
        checks.update(
            {
                "v61_checksum_locked_iso_status_m_table": (
                    profile.STATUS_M_TABLE_SHA256
                    == "732313ea2103ded0673bf99dfe8b2c6b964afede553fcb8a112af6497f5176f3"
                ),
                "v61_iso_status_m_policy_enabled": (
                    model.NEGATIVE_5279_STATUS_M_POLICY
                    == "iso5_3_spectral_products_1nm_v61"
                ),
                "v61_joint_analytical_inverse_enabled": (
                    model.NEGATIVE_5279_ANALYTICAL_DENSITY_POLICY
                    == "joint_iso_status_m_v61"
                ),
                "v61_status_m_grid_is_380_to_780_at_1nm": (
                    status_m_wavelengths.shape == (401,)
                    and _close(status_m_wavelengths[0], 380.0)
                    and _close(status_m_wavelengths[-1], 780.0)
                    and np.allclose(
                        np.diff(status_m_wavelengths), 1.0, rtol=0.0, atol=0.0
                    )
                ),
                "v61_status_m_receivers_have_official_peak_wavelengths": (
                    np.array_equal(
                        status_m_wavelengths[np.argmax(status_m_weights, axis=0)],
                        np.asarray([640.0, 540.0, 450.0], dtype=np.float32),
                    )
                ),
                "v61_zero_analytical_dye_is_registered_to_hd_dmin": bool(
                    np.max(np.abs(zero_status_m)) < 1e-7
                ),
                "v61_joint_status_m_inverse_is_numerically_closed": np.allclose(
                    recovered_reference,
                    analytical_reference,
                    rtol=0.0,
                    atol=2e-6,
                ),
                "v61_plus_2383_interimage_matches_declared_profile": (
                    model.PRINT_2383_INTERIMAGE_POLICY
                    == (
                        "unmeasured_identity_withheld_v62"
                        if v62_interimage_and_lattice
                        else model.PRINT_2383_INTERIMAGE_POLICY_ARCHIVE
                    )
                ),
                "v61_scan_referenced_colour_policy_is_unchanged": (
                    model.PRINT_MONITOR_COLOUR_AUTHORITY
                    == model.PRINT_MONITOR_COLOUR_AUTHORITY_ARCHIVE
                ),
            }
        )
    if v62_interimage_and_lattice:
        checks.update(
            {
                "v62_unmeasured_interimage_surrogate_is_withheld": (
                    model.PRINT_2383_INTERIMAGE_POLICY
                    == "unmeasured_identity_withheld_v62"
                ),
                "v62_interimage_endpoint_is_exact_identity": np.array_equal(
                    np.asarray(model.PRINT_2383_INTERIMAGE_MATRIX), np.eye(3)
                ),
                "v62_projection_colour_policy_is_unchanged": (
                    model.PRINT_MONITOR_COLOUR_AUTHORITY
                    == model.PRINT_MONITOR_COLOUR_AUTHORITY_ARCHIVE
                ),
                "v62_profile_declares_native_observer_lattice": (
                    profile.PROFILE.get(
                        "projection_grain_observer_lattice_policy"
                    )
                    == (
                        "profile_identical_v66"
                        if v66_cineon_printing_density
                        else (
                            "profile_identical_v64"
                            if v64_unshaped_print_density
                            else (
                                "profile_identical_v63"
                                if v63_neutral_trajectory
                                else "profile_identical_v62"
                            )
                        )
                    )
                ),
            }
        )
    if v63_neutral_trajectory:
        checks.update(
            {
                "v63_uses_actual_negative_to_print_neutral_trajectory": (
                    model.PRINT_2383_VIEW_NEUTRAL_POLICY
                    == "actual_5279_to_2383_neutral_trajectory_v63"
                ),
                "v63_keeps_scan_referenced_colour_authority_frozen": (
                    model.PRINT_MONITOR_COLOUR_AUTHORITY
                    == model.PRINT_MONITOR_COLOUR_AUTHORITY_ARCHIVE
                ),
                "v63_keeps_unmeasured_interimage_at_identity": (
                    model.PRINT_2383_INTERIMAGE_POLICY
                    == "unmeasured_identity_withheld_v62"
                    and np.array_equal(
                        np.asarray(model.PRINT_2383_INTERIMAGE_MATRIX),
                        np.eye(3),
                    )
                ),
                "v63_restores_declared_v31_chroma_configuration": (
                    model.PRINT_MONITOR_CHROMA_ADAPTATION == "absolute_chroma"
                ),
            }
        )
    if v64_unshaped_print_density:
        checks.update(
            {
                "v64_retains_published_separated_status_a_curves": (
                    model.PRINT_2383_DENSITY_NEUTRAL_POLICY
                    == "published_separated_status_a_curves_unshaped_v64"
                ),
                "v64_retains_v63_actual_view_neutral_trajectory": (
                    model.PRINT_2383_VIEW_NEUTRAL_POLICY
                    == "actual_5279_to_2383_neutral_trajectory_v63"
                ),
                "v64_keeps_scan_referenced_colour_authority_frozen": (
                    model.PRINT_MONITOR_COLOUR_AUTHORITY
                    == model.PRINT_MONITOR_COLOUR_AUTHORITY_ARCHIVE
                    and profile.PROFILE.get("projection_colour_policy")
                    == "scan_referenced_v31"
                ),
            }
        )
    if v66_cineon_printing_density:
        base_printing_density = (
            model.negative_total_printer_density_from_record_density(
                model.SENSITO_DMIN_RGB
            )
        )
        sample_record_density = np.asarray(
            [[0.22, 0.58, 1.12], [1.40, 0.90, 0.30]],
            dtype=np.float32,
        )
        expected_scanner_density = (
            model.negative_total_printer_density_from_record_density(
                sample_record_density
            )
            - base_printing_density
        )
        checks.update(
            {
                "v66_cineon_target_is_printing_density": (
                    model.SPIRIT_PRIMARY_CORRECTION_TARGET
                    == "active_2383_printing_density_v66"
                ),
                "v66_cineon_coordinate_is_numerically_exact": np.array_equal(
                    model.scanner_density_from_total_record_density(
                        sample_record_density
                    ),
                    expected_scanner_density,
                ),
                "v66_does_not_claim_measured_spirit_colour": (
                    "does not identify a particular Spirit"
                    in profile.PROFILE.get("evidence_boundary", "")
                ),
            }
        )
    if config.profile in {"v46", "v72"}:
        checks.update(
            {
                "v72_direct_record_mix_is_exact_identity": np.array_equal(
                    np.asarray(model.SUBEMULSION_DYE_RECORD_MIX),
                    np.repeat(np.eye(3)[None, ...], 3, axis=0),
                ),
                "v72_declares_minimum_assumption_not_measurement": (
                    profile.PROFILE.get("subemulsion_dye_record_mix_policy")
                    == "identity_v72"
                    and "not a measurement"
                    in profile.PROFILE.get("evidence_boundary", "")
                ),
            }
        )
    if config.profile == "v46":
        checks.update(
            {
                "v46_complete_stochastic_state_endpoint_hold": (
                    model.GRAIN_STOCHASTIC_EXPOSURE_POLICY
                    == "full_stochastic_state_endpoint_hold"
                ),
                "v46_certified_adaptive_printer_observer": (
                    model.NEGATIVE_5279_PRINTER_DENSITY_OBSERVER_POLICY
                    == "adaptive_active_set_129_plus_5cube_v46"
                ),
                "v46_projection_delta_lattice_is_declared_containment": (
                    profile.PROFILE.get(
                        "projection_grain_delta_lattice_policy"
                    )
                    == "frozen_v66_defect_containment_boundary_v79"
                ),
            }
        )
    image_model_conformant = all(checks.values())
    production_execution = config.mode is EngineMode.PRODUCTION_METAL
    return {
        "contract": {
            "v42": "accepted-v37-through-v42",
            "v43h": "accepted-v37-through-v42-plus-isolated-v43h-hypotheses",
            "v44": "accepted-v37-through-v42-plus-v44-observer-integrity",
            "v45": "accepted-v37-through-v44-plus-v45-official-cie-observer",
            "v48": "accepted-v37-through-v45-plus-v48-isotropic-site-integration",
            "v49": "accepted-v37-through-v48-plus-v49-microscopic-density-boundary",
            "v50": "accepted-v37-through-v49-plus-v50-vector-traced-granularity",
            "v51": "accepted-v37-through-v50-plus-v51-vector-traced-negative-spectra",
            "v52": "accepted-v37-through-v51-plus-v52-vector-traced-characteristic-curves",
            "v53": "accepted-v37-through-v52-plus-v53-vector-traced-2383-characteristic-curves",
            "v54": "accepted-v37-through-v53-plus-v54-vector-traced-2383-record-sensitivity",
            "v55": "accepted-v37-through-v54-plus-v55-vector-traced-2383-dye-spectra",
            "v56": "accepted-v37-through-v55-plus-v56-physical-colour-authority-experiment",
            "v57": "accepted-v37-through-v56-plus-v57-minimum-interimage-boundary-experiment",
            "v58": "accepted-v37-through-v55-plus-v58-integral-lad-coordinate-correction",
            "v59": "accepted-v37-through-v58-plus-v59-2383-visual-neutral-base-spectrum",
            "v60": "accepted-v37-through-v59-plus-v60-2383-dmin-coordinate-registration",
            "v61": "accepted-v37-through-v60-plus-v61-iso-status-m-joint-negative-inverse",
            "v62": "accepted-v37-through-v61-plus-v62-interimage-stage-and-observer-lattice-correction",
            "v63": "accepted-v37-through-v62-plus-v63-actual-neutral-trajectory-coordinate-correction",
            "v64": "accepted-v37-through-v63-plus-v64-published-separated-2383-density-boundary",
            "v66": "accepted-v37-through-v64-plus-v66-cineon-printing-density-coordinate",
            "v72": "accepted-v37-through-v66-plus-v72-evidence-minimal-record-formation",
            "v46": "public-v46-consolidation-plus-certified-spectral-inverse-and-endpoint-correction",
        }[config.profile],
        "checks": checks,
        "image_model_conformant": image_model_conformant,
        "production_execution_conformant": (
            image_model_conformant and production_execution
        ),
        "sampler": (
            "Philox-u32 Bernoulli Metal; 45 unique record/population/size "
            "identities per frame"
            if production_execution
            else "reference implementation of the same finite-site law"
        ),
        "delivery_authority": (
            "encoded 12-bit BT.1886 master; sRGB companion and still are "
            "derived from the delivered master"
        ),
    }


def assert_research_conformance(
    model: Any, profile: Any, config: EngineConfig
) -> dict[str, Any]:
    report = research_conformance(model, profile, config)
    failed = [name for name, passed in report["checks"].items() if not passed]
    if failed:
        raise ResearchConformanceError(
            "active engine violates accepted research boundaries: "
            + ", ".join(failed)
        )
    return report
