"""Certified adaptive 5279 Status-M -> 2383 printer-density observer.

The base lattice stores the exact winning nonnegative active set at each
129^3 node.  Smooth regions use four-point tensor interpolation.  Cells that
cross an active-set boundary, or whose linear/cubic disagreement exceeds the
declared density tolerance, are replaced by a locally exact 5^3 microbrick.

Microbricks are intentionally demand-built from the density cells visited by
real footage.  Neighbouring bricks share solved nodes, and a restricted
active-set solve is accepted only after a per-node KKT certificate.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

import numpy as np

try:
    from numba import njit, prange
except ImportError:  # pragma: no cover - reference-only environments
    njit = None
    prange = range

from v46_status_m_active_set import (
    printer_density_from_cmy,
    solve_nnls_allowed_masks,
)


SUBDIVISIONS = 4
DISAGREEMENT_THRESHOLD_D = 0.00025


if njit is not None:
    @njit(cache=True, parallel=True, fastmath=False)
    def _sample_compiled(
        base,
        active_risk,
        axis,
        cell_to_block,
        blocks,
        points,
        subdivisions,
        disagreement_threshold,
    ):
        count = points.shape[0]
        output = np.empty((count, 3), dtype=np.float32)
        missing = np.zeros(count, dtype=np.uint8)
        axis_size = axis.shape[0]
        cell_side = axis_size - 1
        for point_index in prange(count):
            lower = np.empty(3, dtype=np.int16)
            fraction = np.empty(3, dtype=np.float64)
            clipped = np.empty(3, dtype=np.float64)
            for channel in range(3):
                value = points[point_index, channel]
                if value < axis[0]:
                    value = axis[0]
                elif value > axis[axis_size - 1]:
                    value = axis[axis_size - 1]
                clipped[channel] = value
                lo = 0
                hi = axis_size
                while lo < hi:
                    mid = (lo + hi) // 2
                    if axis[mid] <= value:
                        lo = mid + 1
                    else:
                        hi = mid
                cell = lo - 1
                if cell < 0:
                    cell = 0
                elif cell > axis_size - 2:
                    cell = axis_size - 2
                lower[channel] = cell
                fraction[channel] = (value - axis[cell]) / max(
                    axis[cell + 1] - axis[cell], 1e-30
                )

            use_brick = active_risk[
                lower[0], lower[1], lower[2]
            ]
            cubic = np.zeros(3, dtype=np.float64)
            if not use_brick:
                indices = np.empty((3, 4), dtype=np.int16)
                weights = np.ones((3, 4), dtype=np.float64)
                for channel in range(3):
                    first = lower[channel] - 1
                    if first < 0:
                        first = 0
                    elif first > axis_size - 4:
                        first = axis_size - 4
                    for column in range(4):
                        indices[channel, column] = first + column
                    for column in range(4):
                        value = 1.0
                        for other in range(4):
                            if column != other:
                                value *= (
                                    clipped[channel]
                                    - axis[indices[channel, other]]
                                ) / (
                                    axis[indices[channel, column]]
                                    - axis[indices[channel, other]]
                                )
                        weights[channel, column] = value
                for red in range(4):
                    for green in range(4):
                        for blue in range(4):
                            weight = (
                                weights[0, red]
                                * weights[1, green]
                                * weights[2, blue]
                            )
                            for channel in range(3):
                                cubic[channel] += base[
                                    indices[0, red],
                                    indices[1, green],
                                    indices[2, blue],
                                    channel,
                                ] * weight
                linear = np.zeros(3, dtype=np.float64)
                for red in range(2):
                    wr = fraction[0] if red else 1.0 - fraction[0]
                    for green in range(2):
                        wg = fraction[1] if green else 1.0 - fraction[1]
                        for blue in range(2):
                            wb = fraction[2] if blue else 1.0 - fraction[2]
                            weight = wr * wg * wb
                            for channel in range(3):
                                linear[channel] += base[
                                    lower[0] + red,
                                    lower[1] + green,
                                    lower[2] + blue,
                                    channel,
                                ] * weight
                disagreement = 0.0
                for channel in range(3):
                    difference = abs(cubic[channel] - linear[channel])
                    if difference > disagreement:
                        disagreement = difference
                use_brick = disagreement >= disagreement_threshold

            if use_brick:
                block_index = cell_to_block[
                    lower[0], lower[1], lower[2]
                ]
                if block_index < 0:
                    missing[point_index] = 1
                    for channel in range(3):
                        output[point_index, channel] = np.nan
                    continue
                local = np.empty(3, dtype=np.int16)
                local_fraction = np.empty(3, dtype=np.float64)
                for channel in range(3):
                    scaled = fraction[channel] * subdivisions
                    if scaled < 0.0:
                        scaled = 0.0
                    elif scaled >= subdivisions:
                        scaled = subdivisions - 1e-8
                    local[channel] = int(np.floor(scaled))
                    local_fraction[channel] = scaled - local[channel]
                refined = np.zeros(3, dtype=np.float64)
                for red in range(2):
                    wr = (
                        local_fraction[0]
                        if red
                        else 1.0 - local_fraction[0]
                    )
                    for green in range(2):
                        wg = (
                            local_fraction[1]
                            if green
                            else 1.0 - local_fraction[1]
                        )
                        for blue in range(2):
                            wb = (
                                local_fraction[2]
                                if blue
                                else 1.0 - local_fraction[2]
                            )
                            weight = wr * wg * wb
                            for channel in range(3):
                                refined[channel] += blocks[
                                    block_index,
                                    local[0] + red,
                                    local[1] + green,
                                    local[2] + blue,
                                    channel,
                                ] * weight
                for channel in range(3):
                    output[point_index, channel] = refined[channel]
            else:
                for channel in range(3):
                    output[point_index, channel] = cubic[channel]
        return output, missing
else:
    _sample_compiled = None


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cell_codes(cells: np.ndarray, side: int) -> np.ndarray:
    cells = np.asarray(cells, dtype=np.int64)
    return (cells[:, 0] * side + cells[:, 1]) * side + cells[:, 2]


def collapse_base_atlas(
    printer_path: Path,
    residual_path: Path,
    axis_path: Path,
    output_prefix: Path,
) -> dict[str, object]:
    """Collapse eight branch cubes into the exact winner stored at each node."""
    printer = np.load(printer_path, mmap_mode="r")
    residual = np.load(residual_path, mmap_mode="r")
    axis = np.load(axis_path).astype(np.float64)
    if printer.shape[:4] != residual.shape or printer.shape[0] != 8:
        raise ValueError("expected eight matching active-set branch cubes")
    node_mask = np.argmin(np.asarray(residual), axis=0).astype(np.uint8)
    combined = np.take_along_axis(
        np.asarray(printer), node_mask[None, ..., None], axis=0
    )[0].astype(np.float32)
    shape = tuple(value - 1 for value in node_mask.shape)
    active_risk = np.zeros(shape, dtype=bool)
    first = node_mask[:-1, :-1, :-1]
    for red in (0, 1):
        for green in (0, 1):
            for blue in (0, 1):
                active_risk |= (
                    node_mask[
                        red : red + shape[0],
                        green : green + shape[1],
                        blue : blue + shape[2],
                    ]
                    != first
                )
    paths = {
        "base": output_prefix.with_name(output_prefix.name + "_base.npy"),
        "node_mask": output_prefix.with_name(
            output_prefix.name + "_node_mask.npy"
        ),
        "active_risk": output_prefix.with_name(
            output_prefix.name + "_active_risk.npy"
        ),
        "axis": output_prefix.with_name(output_prefix.name + "_axis.npy"),
    }
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    np.save(paths["base"], combined)
    np.save(paths["node_mask"], node_mask)
    np.save(paths["active_risk"], active_risk)
    np.save(paths["axis"], axis.astype(np.float32))
    report: dict[str, object] = {
        "policy": "exact_node_active_set_collapse_power2_129",
        "size": int(axis.size),
        "active_boundary_cell_fraction": float(np.mean(active_risk)),
        "assets": {
            name: {"path": str(path), "sha256": _digest(path)}
            for name, path in paths.items()
        },
    }
    manifest = output_prefix.with_name(output_prefix.name + "_base.json")
    manifest.write_text(json.dumps(report, indent=2) + "\n")
    return report


def _corner_mask_sets(cells: np.ndarray, node_mask: np.ndarray) -> np.ndarray:
    sets = np.zeros((cells.shape[0], 8), dtype=bool)
    rows = np.arange(cells.shape[0])
    for red in (0, 1):
        for green in (0, 1):
            for blue in (0, 1):
                masks = node_mask[
                    cells[:, 0] + red,
                    cells[:, 1] + green,
                    cells[:, 2] + blue,
                ]
                sets[rows, masks] = True
    return sets


def _refined_node_keys(cells: np.ndarray, subdivisions: int) -> np.ndarray:
    offsets = np.stack(
        np.meshgrid(
            np.arange(subdivisions + 1, dtype=np.int16),
            np.arange(subdivisions + 1, dtype=np.int16),
            np.arange(subdivisions + 1, dtype=np.int16),
            indexing="ij",
        ),
        axis=-1,
    ).reshape(-1, 3)
    return (
        cells[:, None, :].astype(np.int32) * subdivisions
        + offsets[None, :, :]
    ).reshape(-1, 3)


def _targets_from_refined_keys(
    keys: np.ndarray, axis: np.ndarray, subdivisions: int
) -> np.ndarray:
    base = keys // subdivisions
    fraction = (keys % subdivisions).astype(np.float64) / subdivisions
    targets = axis[base]
    interpolated = fraction > 0.0
    safe_upper = np.minimum(base + 1, axis.size - 1)
    targets = targets * (1.0 - fraction) + axis[safe_upper] * fraction
    if not np.isfinite(targets).all():
        raise FloatingPointError("refined density coordinates are non-finite")
    return targets


def build_microbrick_cache(
    model,
    cells: np.ndarray,
    node_mask_path: Path,
    axis_path: Path,
    output_prefix: Path,
    *,
    subdivisions: int = SUBDIVISIONS,
    iterations: int = 6,
    chunk: int = 20_000,
) -> dict[str, object]:
    """Solve and persist a deduplicated collection of exact local bricks."""
    started = time.perf_counter()
    node_mask = np.load(node_mask_path, mmap_mode="r")
    axis = np.load(axis_path).astype(np.float64)
    cells = np.unique(np.asarray(cells, dtype=np.int16), axis=0)
    if cells.ndim != 2 or cells.shape[1] != 3:
        raise ValueError("cells must have shape (N, 3)")
    if np.any(cells < 0) or np.any(cells >= axis.size - 1):
        raise ValueError("microbrick cell outside base lattice")

    all_keys = _refined_node_keys(cells, subdivisions)
    unique_keys, inverse = np.unique(all_keys, axis=0, return_inverse=True)
    targets = _targets_from_refined_keys(unique_keys, axis, subdivisions)
    corner_sets = _corner_mask_sets(cells, node_mask)
    node_count = (subdivisions + 1) ** 3
    allowed = np.zeros((unique_keys.shape[0], 8), dtype=bool)
    for mask in range(8):
        repeated = np.repeat(corner_sets[:, mask], node_count)
        np.logical_or.at(allowed[:, mask], inverse, repeated)

    printer = np.empty((unique_keys.shape[0], 3), dtype=np.float32)
    winner_mask = np.empty(unique_keys.shape[0], dtype=np.uint8)
    audits: list[dict[str, int | float]] = []
    for start in range(0, targets.shape[0], chunk):
        stop = min(start + chunk, targets.shape[0])
        cmy, masks, _, audit = solve_nnls_allowed_masks(
            model,
            targets[start:stop],
            allowed[start:stop],
            iterations=iterations,
        )
        printer[start:stop] = printer_density_from_cmy(model, cmy)
        winner_mask[start:stop] = masks
        audits.append(audit)

    side = subdivisions + 1
    blocks = printer[inverse].reshape(
        cells.shape[0], side, side, side, 3
    )
    order = np.argsort(_cell_codes(cells, axis.size - 1))
    cells = cells[order]
    blocks = blocks[order]
    paths = {
        "cells": output_prefix.with_name(output_prefix.name + "_cells.npy"),
        "blocks": output_prefix.with_name(output_prefix.name + "_blocks.npy"),
    }
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    np.save(paths["cells"], cells)
    np.save(paths["blocks"], blocks)
    point_count = sum(int(row["point_count"]) for row in audits)
    branch_solves = sum(
        int(row["restricted_branch_point_solves"]) for row in audits
    )
    fallback = sum(int(row["kkt_fallback_point_count"]) for row in audits)
    report: dict[str, object] = {
        "policy": "deduplicated_5_cube_microbricks_restricted_kkt_certified",
        "cell_count": int(cells.shape[0]),
        "subdivisions": int(subdivisions),
        "duplicate_node_count": int(all_keys.shape[0]),
        "unique_node_count": int(unique_keys.shape[0]),
        "node_reuse_fraction": float(1.0 - unique_keys.shape[0] / all_keys.shape[0]),
        "solver_iterations": int(iterations),
        "restricted_branch_point_solves": branch_solves,
        "mean_restricted_masks_per_point": branch_solves / point_count,
        "kkt_fallback_point_count": fallback,
        "kkt_fallback_fraction": fallback / point_count,
        "build_seconds": float(time.perf_counter() - started),
        "assets": {
            name: {"path": str(path), "sha256": _digest(path)}
            for name, path in paths.items()
        },
    }
    manifest = output_prefix.with_name(output_prefix.name + "_microbricks.json")
    manifest.write_text(json.dumps(report, indent=2) + "\n")
    return report


def _lagrange4(axis: np.ndarray, values: np.ndarray):
    lower = np.searchsorted(axis, values, side="right") - 1
    base = np.clip(lower - 1, 0, axis.size - 4).astype(np.int16)
    indices = base[:, None] + np.arange(4, dtype=np.int16)[None, :]
    nodes = axis[indices]
    weights = np.ones_like(nodes, dtype=np.float64)
    for column in range(4):
        for other in range(4):
            if column != other:
                weights[:, column] *= (values - nodes[:, other]) / (
                    nodes[:, column] - nodes[:, other]
                )
    return indices, weights, lower.astype(np.int16)


def _tricubic(lut: np.ndarray, points: np.ndarray, axis: np.ndarray):
    clipped = np.clip(points, axis[0], axis[-1])
    ci, cw, cl = _lagrange4(axis, clipped[:, 0])
    mi, mw, ml = _lagrange4(axis, clipped[:, 1])
    yi, yw, yl = _lagrange4(axis, clipped[:, 2])
    result = np.zeros((points.shape[0], 3), dtype=np.float64)
    for red in range(4):
        for green in range(4):
            for blue in range(4):
                weight = cw[:, red] * mw[:, green] * yw[:, blue]
                result += lut[ci[:, red], mi[:, green], yi[:, blue]] * weight[:, None]
    return result, np.stack([cl, ml, yl], axis=1)


def _trilinear(lut: np.ndarray, points: np.ndarray, axis: np.ndarray):
    clipped = np.clip(points, axis[0], axis[-1])
    lower = np.searchsorted(axis, clipped, side="right") - 1
    lower = np.clip(lower, 0, axis.size - 2).astype(np.int16)
    upper = lower + 1
    fraction = (clipped - axis[lower]) / np.maximum(
        axis[upper] - axis[lower], 1e-30
    )
    result = np.zeros((points.shape[0], 3), dtype=np.float64)
    for red in (0, 1):
        for green in (0, 1):
            for blue in (0, 1):
                weight = (
                    (fraction[:, 0] if red else 1.0 - fraction[:, 0])
                    * (fraction[:, 1] if green else 1.0 - fraction[:, 1])
                    * (fraction[:, 2] if blue else 1.0 - fraction[:, 2])
                )
                result += lut[
                    lower[:, 0] + red,
                    lower[:, 1] + green,
                    lower[:, 2] + blue,
                ] * weight[:, None]
    return result, lower


def _parent_cells(points: np.ndarray, axis: np.ndarray) -> np.ndarray:
    clipped = np.clip(points, axis[0], axis[-1])
    lower = np.searchsorted(axis, clipped, side="right") - 1
    return np.clip(lower, 0, axis.size - 2).astype(np.int16)


def demanded_microbrick_cells(
    base: np.ndarray,
    active_risk: np.ndarray,
    axis: np.ndarray,
    source: np.ndarray,
    *,
    disagreement_threshold: float = DISAGREEMENT_THRESHOLD_D,
    chunk: int = 250_000,
) -> np.ndarray:
    """Return every parent cell demanded by the exact runtime risk test."""
    flat = np.maximum(np.asarray(source).reshape(-1, 3), 0.0).astype(
        np.float64, copy=False
    )
    cell_side = axis.size - 1
    code_chunks: list[np.ndarray] = []
    for start in range(0, flat.shape[0], chunk):
        stop = min(start + chunk, flat.shape[0])
        points = flat[start:stop]
        lower = _parent_cells(points, axis)
        active = active_risk[
            lower[:, 0], lower[:, 1], lower[:, 2]
        ]
        if np.any(active):
            code_chunks.append(
                np.unique(_cell_codes(lower[active], cell_side))
            )
        smooth_indices = np.flatnonzero(~active)
        if smooth_indices.size:
            smooth_points = points[smooth_indices]
            cubic, _ = _tricubic(base, smooth_points, axis)
            linear, _ = _trilinear(base, smooth_points, axis)
            curvature = (
                np.max(np.abs(cubic - linear), axis=1)
                >= float(disagreement_threshold)
            )
            if np.any(curvature):
                code_chunks.append(
                    np.unique(
                        _cell_codes(
                            lower[smooth_indices[curvature]], cell_side
                        )
                    )
                )
    if not code_chunks:
        return np.empty((0, 3), dtype=np.int16)
    codes = np.unique(np.concatenate(code_chunks))
    red = codes // (cell_side * cell_side)
    remainder = codes % (cell_side * cell_side)
    green = remainder // cell_side
    blue = remainder % cell_side
    return np.stack([red, green, blue], axis=1).astype(np.int16)


class AdaptivePrinterDensityObserver:
    """Read-only runtime for a certified base atlas plus local microbricks."""

    def __init__(
        self,
        base_path: Path,
        active_risk_path: Path,
        axis_path: Path,
        cells_path: Path,
        blocks_path: Path,
        *,
        subdivisions: int = SUBDIVISIONS,
        disagreement_threshold: float = DISAGREEMENT_THRESHOLD_D,
    ) -> None:
        self.base = np.load(base_path, mmap_mode="r")
        self.active_risk = np.load(active_risk_path, mmap_mode="r")
        self.axis = np.load(axis_path).astype(np.float64)
        self.cells = np.load(cells_path, mmap_mode="r")
        self.blocks = np.load(blocks_path, mmap_mode="r")
        self.subdivisions = int(subdivisions)
        self.disagreement_threshold = float(disagreement_threshold)
        self._codes = _cell_codes(self.cells, self.axis.size - 1)
        if np.any(np.diff(self._codes) <= 0):
            raise ValueError("microbrick cell table must be strictly sorted")
        self.cell_to_block = np.full(
            (self.axis.size - 1,) * 3, -1, dtype=np.int32
        )
        self.cell_to_block[
            self.cells[:, 0], self.cells[:, 1], self.cells[:, 2]
        ] = np.arange(self.cells.shape[0], dtype=np.int32)

    def _sample_blocks(
        self, points: np.ndarray, lower: np.ndarray, block_indices: np.ndarray
    ) -> np.ndarray:
        low = self.axis[lower]
        high = self.axis[lower + 1]
        scaled = np.clip(
            (points - low) / np.maximum(high - low, 1e-30)
            * self.subdivisions,
            0.0,
            self.subdivisions - 1e-8,
        )
        local = np.floor(scaled).astype(np.int16)
        fraction = scaled - local
        result = np.zeros((points.shape[0], 3), dtype=np.float64)
        for red in (0, 1):
            for green in (0, 1):
                for blue in (0, 1):
                    weight = (
                        (fraction[:, 0] if red else 1.0 - fraction[:, 0])
                        * (fraction[:, 1] if green else 1.0 - fraction[:, 1])
                        * (fraction[:, 2] if blue else 1.0 - fraction[:, 2])
                    )
                    result += self.blocks[
                        block_indices,
                        local[:, 0] + red,
                        local[:, 1] + green,
                        local[:, 2] + blue,
                    ] * weight[:, None]
        return result

    def sample(
        self,
        source: np.ndarray,
        *,
        chunk: int = 250_000,
        reference: bool = False,
    ) -> np.ndarray:
        original = np.asarray(source)
        flat = np.maximum(original.reshape(-1, 3), 0.0).astype(
            np.float64, copy=False
        )
        if _sample_compiled is not None and not reference:
            output, missing = _sample_compiled(
                self.base,
                self.active_risk,
                self.axis,
                self.cell_to_block,
                self.blocks,
                flat,
                self.subdivisions,
                self.disagreement_threshold,
            )
            if np.any(missing):
                absent = np.unique(
                    _parent_cells(flat[missing.astype(bool)], self.axis),
                    axis=0,
                )
                raise KeyError(
                    "adaptive printer atlas is missing "
                    f"{absent.shape[0]} demanded microbrick cells; "
                    "run the V46 coverage/bake step before release rendering"
                )
            return output.reshape(original.shape)
        result = np.empty_like(flat, dtype=np.float32)
        cell_side = self.axis.size - 1
        for start in range(0, flat.shape[0], chunk):
            stop = min(start + chunk, flat.shape[0])
            points = flat[start:stop]
            lower = _parent_cells(points, self.axis)
            active = self.active_risk[
                lower[:, 0], lower[:, 1], lower[:, 2]
            ]
            chunk_result = np.empty((points.shape[0], 3), dtype=np.float64)
            flagged = active.copy()
            smooth_indices = np.flatnonzero(~active)
            if smooth_indices.size:
                smooth_points = points[smooth_indices]
                cubic, _ = _tricubic(self.base, smooth_points, self.axis)
                linear, _ = _trilinear(self.base, smooth_points, self.axis)
                curvature = (
                    np.max(np.abs(cubic - linear), axis=1)
                    >= self.disagreement_threshold
                )
                chunk_result[smooth_indices[~curvature]] = cubic[~curvature]
                flagged[smooth_indices[curvature]] = True
            if np.any(flagged):
                codes = _cell_codes(lower[flagged], cell_side)
                indices = np.searchsorted(self._codes, codes)
                missing = (indices >= self._codes.size) | (
                    self._codes[np.minimum(indices, self._codes.size - 1)] != codes
                )
                if np.any(missing):
                    absent = np.unique(lower[flagged][missing], axis=0)
                    raise KeyError(
                        "adaptive printer atlas is missing "
                        f"{absent.shape[0]} demanded microbrick cells; "
                        "run the V46 coverage/bake step before release rendering"
                    )
                chunk_result[flagged] = self._sample_blocks(
                    points[flagged], lower[flagged], indices
                )
            result[start:stop] = chunk_result.astype(np.float32)
        return result.reshape(original.shape)

    def missing_microbrick_cells(self, source: np.ndarray) -> np.ndarray:
        """Audit demanded cells not present in this observer's baked cache."""
        if _sample_compiled is None:
            raise RuntimeError("compiled V46 audit requires numba")
        original = np.asarray(source)
        flat = np.maximum(original.reshape(-1, 3), 0.0).astype(
            np.float64, copy=False
        )
        _, missing = _sample_compiled(
            self.base,
            self.active_risk,
            self.axis,
            self.cell_to_block,
            self.blocks,
            flat,
            self.subdivisions,
            self.disagreement_threshold,
        )
        if not np.any(missing):
            return np.empty((0, 3), dtype=np.int16)
        return np.unique(
            _parent_cells(flat[missing.astype(bool)], self.axis), axis=0
        )
