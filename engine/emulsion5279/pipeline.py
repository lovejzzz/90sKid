"""Explicit-stage research-conformant frame engine with isolated profiles."""

from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass
import threading
import time

import cv2
import numpy as np

from .assets import (
    CIE_1931_2DEG_1NM,
    projection_lattice_for_profile,
    verify_v46_runtime_assets,
)
from .contracts import (
    DeliveryEncoding,
    EncodedObserverPair,
    EngineConfig,
    EngineMode,
    ObserverPair,
    RenderedFrame,
)
from .conformance import assert_research_conformance
from . import legacy
from .view_policy import (
    CineonViewPolicy,
    LEGACY_MANAGED_PROJECTION_CONTRACT,
    LEGACY_MANAGED_SCAN_CONTRACT,
    POLICY_CONTRACTS,
    render_cineon_view,
)


_CONFIGURE_LOCK = threading.Lock()
_RENDER_LOCK = threading.Lock()
_ACTIVE_CONFIG: EngineConfig | None = None


@dataclass(slots=True)
class FormedNegative:
    """Mean and realized density from one shared 5279 exposure."""

    mean_record_density: np.ndarray
    formed_record_density: np.ndarray


class Emulsion5279Engine:
    """Own one configured graph without exposing historical profile mutation."""

    def __init__(self, config: EngineConfig | None = None) -> None:
        self.config = config or EngineConfig()
        self.profile = legacy.profile_for(self.config.profile)
        self._configured = False
        self._observer_executor: concurrent.futures.ThreadPoolExecutor | None = None

    @property
    def provenance(self) -> dict[str, object]:
        self.configure()
        print_lattice = projection_lattice_for_profile(self.config.profile)
        sampler_audit: dict[str, object] | None = None
        if self.config.mode is EngineMode.PRODUCTION_METAL:
            import v35_accel

            sampler_audit = v35_accel.sampler_audit_snapshot()
        return {
            "engine_api": f"emulsion5279-{self.config.profile}",
            "profile": self.config.profile,
            "input_colour_contract": self.config.input_colour.value,
            "delivery_contract": [
                DeliveryEncoding.REFERENCE_BT1886.value,
                DeliveryEncoding.QUICKTIME_SRGB.value,
            ],
            "cineon_exchange_contract": {
                "container": "SMPTE_ST_268-1_DPX_v2.0",
                "image_element": "RGB_unsigned_10bit",
                "transfer_characteristic": "printing_density_code_1",
                "colorimetric_specification": "printing_density_code_1",
                "reference_low": {"code": 0, "density": 0.0},
                "reference_high": {"code": 1023, "density": 2.048},
                "reference_black_aim_code": 95,
                "display_ready": False,
            },
            "cineon_view_policies": {
                policy.value: contract
                for policy, contract in POLICY_CONTRACTS.items()
            },
            "legacy_scan_delivery_contract": LEGACY_MANAGED_SCAN_CONTRACT,
            "legacy_projection_delivery_contract": (
                LEGACY_MANAGED_PROJECTION_CONTRACT
            ),
            "active_projection_delivery_contract": (
                {
                    "name": "v48_direct_mean_managed_grain_delta",
                    "deterministic_mean": "direct_5279_to_2383_xenon_cie_observer",
                    "stochastic_delta": "frozen_v46_managed_formed_minus_mean",
                    "classification": "first_principles_observer_ownership",
                }
                if self.config.profile == "v48r"
                else (
                    {
                        "name": "v49_common_density_direct_material_observers",
                        "deterministic_mean": "direct_5279_to_2383_xenon_cie_observer",
                        "stochastic_domain": "formed_common_status_m_density",
                        "display_rgb_reinjection": False,
                        "classification": "conservative_unidentified_joint_law_boundary",
                    }
                    if self.config.profile == "v49r"
                    else LEGACY_MANAGED_PROJECTION_CONTRACT
                )
            ),
            "print_lattice_sha256": print_lattice.sha256,
            "cie_observer_sha256": (
                CIE_1931_2DEG_1NM.sha256
                if self.config.profile
                in {"v45", "v46", "v48r", "v49r", "v48", "v49", "v50", "v51", "v52", "v53", "v54", "v55", "v56", "v57", "v58", "v59", "v60", "v61", "v62", "v63", "v64", "v66", "v72"}
                else None
            ),
            "research_conformance": assert_research_conformance(
                legacy.model, self.profile, self.config
            ),
            "production_sampler_audit": sampler_audit,
            "execution": {
                "observer_branch_workers": self.config.observer_branch_workers,
                "observer_schedule": (
                    "parallel_projection_and_scan"
                    if self.config.observer_branch_workers == 2
                    else "sequential_projection_and_scan"
                ),
            },
            **legacy.source_fingerprints(self.profile),
        }

    def validate_rendered_frames(self, expected_frames: int) -> dict[str, object] | None:
        """Close the Production identity gate before an output is published."""
        if self.config.mode is not EngineMode.PRODUCTION_METAL:
            return None
        import v35_accel

        audit = v35_accel.sampler_audit_snapshot()
        if audit["frames_audited"] != int(expected_frames):
            raise RuntimeError(
                "Production sampler audit did not cover every rendered frame: "
                f"{audit['frames_audited']}/{expected_frames}"
            )
        if audit["total_calls"] != int(expected_frames) * 45:
            raise RuntimeError(
                "Production sampler call count drifted from 45 identities per frame"
            )
        if audit["duplicate_identity_count"] != 0:
            raise RuntimeError("Production sampler produced duplicate identities")
        return audit

    def configure(self) -> None:
        """Select one profile and install its evidence-gated execution graph."""
        global _ACTIVE_CONFIG
        if self._configured:
            return
        with _CONFIGURE_LOCK:
            if self._configured:
                return
            if _ACTIVE_CONFIG is not None and _ACTIVE_CONFIG != self.config:
                raise RuntimeError(
                    "the recovered V41 backend owns process-global caches; use one "
                    "EngineConfig per process until the remaining kernels are lifted"
                )
            print_lattice = projection_lattice_for_profile(self.config.profile)
            if self.config.profile in {"v46", "v48r", "v49r"}:
                verify_v46_runtime_assets()
            e = legacy.model
            self.profile.apply(e)
            cv2.setNumThreads(self.config.opencv_threads)
            e.BINOMIAL_PARALLEL_WORKERS = self.config.binomial_workers
            e._PRINT_2383_MONITOR_OUTPUT_LUT = np.load(
                print_lattice.path, allow_pickle=False
            )
            if self.config.mode in (
                EngineMode.ARCHIVE_EXACT_CPU,
                EngineMode.PRODUCTION_METAL,
            ):
                import v27_accel

                v27_accel.apply(
                    e,
                    numba_threads=self.config.numba_threads,
                    array_workers=self.config.array_workers,
                    exact_only=True,
                )
                v27_accel.warm(e)
            if self.config.mode is EngineMode.PRODUCTION_METAL:
                import v27_production_accel
                import v35_accel

                v27_production_accel.apply(e)
                v35_accel.apply_metal_binomial(
                    e,
                    mode="bernoulli",
                    asynchronous=True,
                    domain_salt=self.config.grain_domain_salt,
                )
                v35_accel.warm_metal_binomial("bernoulli")
            assert_research_conformance(e, self.profile, self.config)
            if self.config.observer_branch_workers == 2:
                self._observer_executor = concurrent.futures.ThreadPoolExecutor(
                    max_workers=2,
                    thread_name_prefix="emulsion-observer",
                )
            _ACTIVE_CONFIG = self.config
            self._configured = True

    def close(self) -> None:
        """Release persistent execution resources owned by this engine."""
        if self._observer_executor is not None:
            self._observer_executor.shutdown(wait=True, cancel_futures=False)
            self._observer_executor = None

    @staticmethod
    def _validate_raw_frame(raw: np.ndarray) -> np.ndarray:
        frame = np.asarray(raw, dtype=np.float32)
        if frame.ndim != 3 or frame.shape[-1] != 3:
            raise ValueError("decoded RAW frame must have shape height x width x RGB")
        if not np.all(np.isfinite(frame)):
            raise ValueError("decoded RAW frame contains non-finite samples")
        # Extended-linear highlights are deliberately allowed above one.
        return frame

    def _apply_negative_publication_boundary(
        self,
        mean: np.ndarray,
        formed: np.ndarray,
        marginal_sigma: np.ndarray | None = None,
    ) -> np.ndarray:
        """Apply a declared stochastic boundary before material observation."""
        policy = self.profile.PROFILE.get(
            "negative_stochastic_publication_policy", "full_record_density"
        )
        if policy == "full_record_density":
            return np.asarray(formed, dtype=np.float32)
        if policy != "symmetric_minimum_marginal_common_density_v49":
            raise ValueError(f"unknown negative stochastic policy: {policy}")
        # Kodak's marginal curves do not identify an opponent-density law.
        # Retain only the scalar component common to the three analytical
        # records. This happens before either observer: it is not denoise,
        # chroma suppression, or an RGB overlay.
        if marginal_sigma is None:
            raise ValueError("V49 common-density boundary requires marginal RMS")
        sigma = np.maximum(np.asarray(marginal_sigma, dtype=np.float32), 1e-6)
        residual = np.asarray(formed, dtype=np.float32) - np.asarray(mean, dtype=np.float32)
        # Symmetric normalized projection: if the three currently sampled
        # marginal fields are independent, division by sqrt(3) gives one unit-
        # variance latent field without privileging a colour record. Scaling by
        # min(sigma_R,G,B) makes the published component no stronger than any
        # Kodak marginal. The unallocated variance is explicitly withheld.
        common_latent = np.sum(residual / sigma, axis=2, keepdims=True) / np.sqrt(3.0)
        common_sigma = np.min(sigma, axis=2, keepdims=True)
        common_density = common_latent * common_sigma
        return np.maximum(mean + common_density, 0.0).astype(np.float32)

    def form_negative(self, raw: np.ndarray, absolute_frame: int) -> FormedNegative:
        self.configure()
        e = legacy.model
        frame = self._validate_raw_frame(raw)
        film_rgb = e.scene_to_5279_film_rgb(
            frame,
            exposure_stops=self.config.exposure_stops,
            raw_colour=self.profile.PROFILE["raw_colour"],
            include_optical_scatter=True,
            sensor_noise_treatment="photochemical",
        )
        records = e.film_records_from_rgb(film_rgb)
        log_exposure = np.log10(np.maximum(records, 1e-8)) - 1.0
        activations = e.subemulsion_activation_probabilities(log_exposure)
        mean = e.develop_5279_record_density_from_log_exposure(
            log_exposure,
            precomputed_activations=activations,
        )
        formed = e.form_5279_multilayer_record_density(
            records,
            int(absolute_frame),
            self.config.grain_scale,
            self.config.oversample,
            precomputed_mean_density=(mean if self.config.oversample == 1 else None),
            precomputed_log_exposure=(
                log_exposure if self.config.oversample == 1 else None
            ),
            precomputed_activations=(
                activations if self.config.oversample == 1 else None
            ),
        )
        formed = self._apply_negative_publication_boundary(
            mean, formed, e.published_5279_granularity_sigma(log_exposure)
        )
        return FormedNegative(mean, formed)

    def _publish_projection_colour(
        self, projection: np.ndarray, scan: np.ndarray
    ) -> np.ndarray:
        """Apply only the selected observer-publication boundary.

        V42/V43H retain their historical V31 scan-referenced monitor result for
        reproducibility. V44 also retains that accepted normal-process colour
        boundary after the direct analytical colour failed the native opponent-
        tail gate; its revision concerns unsupported hypotheses and declared
        display-scale sampling, not an invented projection colour difference.
        """
        policy = self.profile.PROFILE.get(
            "projection_colour_policy", "scan_referenced_v31"
        )
        if policy in {"direct_observer", "physical_spectral_v56"}:
            return np.asarray(projection, dtype=np.float32)
        if policy != "scan_referenced_v31":
            raise ValueError(f"unknown projection colour policy: {policy}")
        from apply_v31_normal_process_adapter import adapt_frame_linear

        return adapt_frame_linear(
            projection,
            scan,
            self.profile.PROFILE.get(
                "final_adapter_opponent_high_frequency_retention", 1.0
            ),
        )

    def _publish_projection_pair(
        self,
        formed_projection: np.ndarray,
        formed_scan: np.ndarray,
        mean_projection: np.ndarray,
        mean_scan: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Publish projection colour without changing stochastic ownership.

        V48's deterministic mean is the direct 2383 spectral observer.  The
        historical V46 publication transform is evaluated for both formed and
        mean pairs and only their signed difference is retained.  Therefore a
        scan-referenced safety policy cannot silently become the colour grade
        of the projected print.
        """
        policy = self.profile.PROFILE.get(
            "projection_colour_policy", "scan_referenced_v31"
        )
        if policy != "direct_mean_managed_grain_delta_v48":
            return (
                self._publish_projection_colour(formed_projection, formed_scan),
                self._publish_projection_colour(mean_projection, mean_scan),
            )
        managed_formed = self._publish_projection_colour_v46(
            formed_projection, formed_scan
        )
        managed_mean = self._publish_projection_colour_v46(
            mean_projection, mean_scan
        )
        published = (
            np.asarray(mean_projection, dtype=np.float32)
            + managed_formed
            - managed_mean
        )
        return (
            np.clip(published, 0.0, 1.0).astype(np.float32),
            np.asarray(mean_projection, dtype=np.float32),
        )

    def _publish_projection_colour_v46(
        self, projection: np.ndarray, scan: np.ndarray
    ) -> np.ndarray:
        """Evaluate the frozen V46 publication transform for delta ownership."""
        from apply_v31_normal_process_adapter import adapt_frame_linear

        return adapt_frame_linear(
            projection,
            scan,
            self.profile.PROFILE.get(
                "final_adapter_opponent_high_frequency_retention", 1.0
            ),
        )

    def observe(self, negative: FormedNegative, absolute_frame: int) -> ObserverPair:
        self.configure()
        if self.profile.PROFILE.get("projection_colour_policy") == (
            "direct_mean_managed_grain_delta_v48"
        ):
            formed, _mean = self.observe_with_mean(negative, absolute_frame)
            return formed
        projection, scan = legacy.model.reconstruct_density_pair_to_dual_display_v39(
            negative.mean_record_density,
            negative.formed_record_density,
            int(absolute_frame),
            self.config.grain_scale,
            "linear_rec709",
            branch_executor=self._observer_executor,
        )
        projection = self._publish_projection_colour(projection, scan)
        return ObserverPair(projection, scan)

    def observe_with_cineon_data(
        self, negative: FormedNegative, absolute_frame: int
    ) -> tuple[ObserverPair, np.ndarray]:
        """Return both display observers and their pre-display Cineon data.

        The DPX payload is produced inside the shared observer traversal from
        the same formed negative, scanner-density transform, and Spirit 2K
        aperture that feed the scan view.  It therefore cannot silently drift
        into a second stochastic realization or a duplicate scan model.
        """
        self.configure()
        first_principles_projection = self.profile.PROFILE.get(
            "projection_colour_policy"
        ) == "direct_mean_managed_grain_delta_v48"
        rendered = legacy.model.reconstruct_density_pair_to_dual_display_v39(
            negative.mean_record_density,
            negative.formed_record_density,
            int(absolute_frame),
            self.config.grain_scale,
            "linear_rec709",
            return_mean_pair=first_principles_projection,
            return_cineon_code=True,
            branch_executor=self._observer_executor,
        )
        if first_principles_projection:
            projection, scan, mean_projection, mean_scan, cineon_code = rendered
            projection, _ = self._publish_projection_pair(
                projection,
                scan,
                mean_projection,
                mean_scan,
            )
        else:
            projection, scan, cineon_code = rendered
            projection = self._publish_projection_colour(projection, scan)
        return ObserverPair(projection, scan), cineon_code

    def observe_with_mean(
        self, negative: FormedNegative, absolute_frame: int
    ) -> tuple[ObserverPair, ObserverPair]:
        """Return physical and deterministic observers from shared intermediates."""
        self.configure()
        if self.config.profile == "v49r":
            # V49 deliberately has no observer-side mean+RGB-delta graph.
            # Evaluate the formed and mean negatives as two complete material
            # observations; the public frame still uses only the formed pass.
            projection, scan = (
                legacy.model.reconstruct_density_pair_to_dual_display_v39(
                    negative.mean_record_density,
                    negative.formed_record_density,
                    int(absolute_frame),
                    self.config.grain_scale,
                    "linear_rec709",
                    branch_executor=self._observer_executor,
                )
            )
            mean_projection, mean_scan = (
                legacy.model.reconstruct_density_pair_to_dual_display_v39(
                    negative.mean_record_density,
                    negative.mean_record_density,
                    int(absolute_frame),
                    0.0,
                    "linear_rec709",
                    branch_executor=self._observer_executor,
                )
            )
            return (
                ObserverPair(projection, scan),
                ObserverPair(mean_projection, mean_scan),
            )
        projection, scan, mean_projection, mean_scan = (
            legacy.model.reconstruct_density_pair_to_dual_display_v39(
                negative.mean_record_density,
                negative.formed_record_density,
                int(absolute_frame),
                self.config.grain_scale,
                "linear_rec709",
                return_mean_pair=True,
                branch_executor=self._observer_executor,
            )
        )
        published_projection, published_mean_projection = (
            self._publish_projection_pair(
                projection,
                scan,
                mean_projection,
                mean_scan,
            )
        )
        return (
            ObserverPair(published_projection, scan),
            ObserverPair(published_mean_projection, mean_scan),
        )

    def view_cineon_data(
        self,
        cineon_code: np.ndarray,
        policy: CineonViewPolicy,
    ) -> np.ndarray:
        """View V66 printing-density data through one named single-input policy."""
        self.configure()
        if self.config.profile not in {"v46", "v48r", "v49r", "v66", "v72"}:
            raise ValueError(
                "the named Cineon policies require profile='v66' or 'v72'"
            )
        return render_cineon_view(cineon_code, policy)

    @staticmethod
    def encode_reference(observers: ObserverPair) -> EncodedObserverPair:
        e = legacy.model
        return EncodedObserverPair(
            projection=e.bt1886_reference_encode(observers.projection_linear_rec709),
            scan=e.bt1886_reference_encode(observers.scan_linear_rec709),
            encoding=DeliveryEncoding.REFERENCE_BT1886,
        )

    @staticmethod
    def encode(observers: ObserverPair) -> tuple[EncodedObserverPair, EncodedObserverPair]:
        """Analytical transfer-pair helper for tests, not release file writing."""
        e = legacy.model
        master = Emulsion5279Engine.encode_reference(observers)
        quicktime = EncodedObserverPair(
            projection=e.srgb_encode(observers.projection_linear_rec709).astype(np.float32),
            scan=e.srgb_encode(observers.scan_linear_rec709).astype(np.float32),
            encoding=DeliveryEncoding.QUICKTIME_SRGB,
        )
        return master, quicktime

    def render_frame(self, raw: np.ndarray, absolute_frame: int) -> RenderedFrame:
        """Form one negative once, then derive both observers and deliveries."""
        # The recovered backend still owns mutable module caches. Serializing
        # frame entry prevents an accidental multi-instance race from changing
        # colour or stochastic state. A future resident Metal backend will own
        # per-instance resources and can remove this compatibility lock.
        with _RENDER_LOCK:
            started = time.perf_counter()
            negative = self.form_negative(raw, absolute_frame)
            formed_at = time.perf_counter()
            observers, cineon_code = self.observe_with_cineon_data(
                negative, absolute_frame
            )
            observed_at = time.perf_counter()
            master = self.encode_reference(observers)
            encoded_at = time.perf_counter()
        return RenderedFrame(
            absolute_frame=int(absolute_frame),
            observers=observers,
            reference_master=master,
            quicktime_companion=None,
            cineon_printing_density_code=cineon_code,
            stage_seconds={
                "negative_formation": formed_at - started,
                "dual_observer": observed_at - formed_at,
                "delivery_encoding": encoded_at - observed_at,
                "total": encoded_at - started,
            },
        )
