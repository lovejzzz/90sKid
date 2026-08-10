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
    observer_integrity = config.profile in {"v44", "v45"}
    official_observer = config.profile == "v45"

    checks = {
        # V37: independent sites, stable numerical integration operator.
        "v37_stable_balanced_phase": model.GRAIN_SUBPIXEL_PHASE_MODE
        == "stable_balanced",
        "v37_phase_radius_0_38_native_px": _close(
            model.GRAIN_SUBPIXEL_PHASE_RADIUS_PX, 0.38
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
                    expected.get("release_class")
                    == (
                        "measured_observer_revision"
                        if official_observer
                        else "evidence_boundary_revision"
                    )
                ),
                "v44_retains_accepted_normal_process_colour_boundary": (
                    expected.get("projection_colour_policy")
                    == "scan_referenced_v31"
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
                "v45_is_measured_observer_revision": (
                    profile.PROFILE.get("release_class")
                    == "measured_observer_revision"
                ),
                "v45_uses_official_cie_1931_1nm_observer": (
                    model.PRINT_2383_CMF_MODE
                    == "cie_1931_2deg_official_1nm"
                ),
            }
        )
    image_model_conformant = all(checks.values())
    production_execution = config.mode is EngineMode.PRODUCTION_METAL
    return {
        "contract": (
            "accepted-v37-through-v42-plus-isolated-v43h-hypotheses"
            if hypothesis
            else (
                (
                    "accepted-v37-through-v44-plus-v45-official-cie-observer"
                    if official_observer
                    else "accepted-v37-through-v42-plus-v44-observer-integrity"
                )
                if observer_integrity
                else "accepted-v37-through-v42"
            )
        ),
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
