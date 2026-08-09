#!/usr/bin/env swift

import Foundation
import Metal

struct Parameters {
    var width: UInt32
    var height: UInt32
    var radius: UInt32
}

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

guard CommandLine.arguments.count == 8 else {
    fail("usage: metal_gaussian_benchmark INPUT WEIGHTS OUTPUT WIDTH HEIGHT RADIUS ITERATIONS")
}
let inputURL = URL(fileURLWithPath: CommandLine.arguments[1])
let weightsURL = URL(fileURLWithPath: CommandLine.arguments[2])
let outputURL = URL(fileURLWithPath: CommandLine.arguments[3])
guard
    let width = UInt32(CommandLine.arguments[4]),
    let height = UInt32(CommandLine.arguments[5]),
    let radius = UInt32(CommandLine.arguments[6]),
    let iterations = Int(CommandLine.arguments[7]),
    iterations > 0
else { fail("invalid numeric argument") }

let source = try Data(contentsOf: inputURL, options: .mappedIfSafe)
let weights = try Data(contentsOf: weightsURL, options: .mappedIfSafe)
let expectedBytes = Int(width) * Int(height) * 3 * MemoryLayout<Float>.size
guard source.count == expectedBytes else {
    fail("input has \(source.count) bytes; expected \(expectedBytes)")
}
guard weights.count == Int(2 * radius + 1) * MemoryLayout<Float>.size else {
    fail("weight count does not match radius")
}
guard let device = MTLCreateSystemDefaultDevice() else { fail("Metal unavailable") }
guard let queue = device.makeCommandQueue() else { fail("cannot create Metal queue") }

let sourceCode = #"""
#include <metal_stdlib>
using namespace metal;

struct Parameters { uint width; uint height; uint radius; };

inline int reflect_index(int value, int extent) {
    if (value < 0) return -value - 1;
    if (value >= extent) return 2 * extent - value - 1;
    return value;
}

kernel void horizontal(
    device const packed_float3 *source [[buffer(0)]],
    device packed_float3 *destination [[buffer(1)]],
    constant Parameters &parameters [[buffer(2)]],
    device const float *weights [[buffer(3)]],
    uint2 position [[thread_position_in_grid]]) {
    if (position.x >= parameters.width || position.y >= parameters.height) return;
    float3 sum = float3(0.0f);
    int radius = int(parameters.radius);
    for (int offset = -radius; offset <= radius; ++offset) {
        int x = reflect_index(int(position.x) + offset, int(parameters.width));
        sum += float3(source[position.y * parameters.width + uint(x)]) * weights[offset + radius];
    }
    destination[position.y * parameters.width + position.x] = packed_float3(sum);
}

kernel void vertical(
    device const packed_float3 *source [[buffer(0)]],
    device packed_float3 *destination [[buffer(1)]],
    constant Parameters &parameters [[buffer(2)]],
    device const float *weights [[buffer(3)]],
    uint2 position [[thread_position_in_grid]]) {
    if (position.x >= parameters.width || position.y >= parameters.height) return;
    float3 sum = float3(0.0f);
    int radius = int(parameters.radius);
    for (int offset = -radius; offset <= radius; ++offset) {
        int y = reflect_index(int(position.y) + offset, int(parameters.height));
        sum += float3(source[uint(y) * parameters.width + position.x]) * weights[offset + radius];
    }
    destination[position.y * parameters.width + position.x] = packed_float3(sum);
}
"""#

let library = try device.makeLibrary(source: sourceCode, options: nil)
guard
    let horizontalFunction = library.makeFunction(name: "horizontal"),
    let verticalFunction = library.makeFunction(name: "vertical")
else { fail("Metal functions unavailable") }
let horizontalPipeline = try device.makeComputePipelineState(function: horizontalFunction)
let verticalPipeline = try device.makeComputePipelineState(function: verticalFunction)
guard
    let sourceBuffer = source.withUnsafeBytes({ bytes in
        device.makeBuffer(bytes: bytes.baseAddress!, length: source.count, options: .storageModeShared)
    }),
    let weightsBuffer = weights.withUnsafeBytes({ bytes in
        device.makeBuffer(bytes: bytes.baseAddress!, length: weights.count, options: .storageModeShared)
    }),
    let intermediate = device.makeBuffer(length: expectedBytes, options: .storageModePrivate),
    let output = device.makeBuffer(length: expectedBytes, options: .storageModeShared)
else { fail("cannot allocate Metal buffers") }

var parameters = Parameters(width: width, height: height, radius: radius)
let grid = MTLSize(width: Int(width), height: Int(height), depth: 1)
let group = MTLSize(width: 16, height: 16, depth: 1)

func encode(_ commandBuffer: MTLCommandBuffer) {
    guard let first = commandBuffer.makeComputeCommandEncoder() else { fail("encoder unavailable") }
    first.setComputePipelineState(horizontalPipeline)
    first.setBuffer(sourceBuffer, offset: 0, index: 0)
    first.setBuffer(intermediate, offset: 0, index: 1)
    first.setBytes(&parameters, length: MemoryLayout<Parameters>.stride, index: 2)
    first.setBuffer(weightsBuffer, offset: 0, index: 3)
    first.dispatchThreads(grid, threadsPerThreadgroup: group)
    first.endEncoding()
    guard let second = commandBuffer.makeComputeCommandEncoder() else { fail("encoder unavailable") }
    second.setComputePipelineState(verticalPipeline)
    second.setBuffer(intermediate, offset: 0, index: 0)
    second.setBuffer(output, offset: 0, index: 1)
    second.setBytes(&parameters, length: MemoryLayout<Parameters>.stride, index: 2)
    second.setBuffer(weightsBuffer, offset: 0, index: 3)
    second.dispatchThreads(grid, threadsPerThreadgroup: group)
    second.endEncoding()
}

guard let warm = queue.makeCommandBuffer() else { fail("command buffer unavailable") }
encode(warm)
warm.commit()
warm.waitUntilCompleted()

var gpuSeconds = 0.0
let wallStart = ContinuousClock.now
for _ in 0..<iterations {
    guard let command = queue.makeCommandBuffer() else { fail("command buffer unavailable") }
    encode(command)
    command.commit()
    command.waitUntilCompleted()
    if command.status != .completed { fail("Metal command failed") }
    gpuSeconds += command.gpuEndTime - command.gpuStartTime
}
let wallDuration = ContinuousClock.now - wallStart
let wallSeconds = Double(wallDuration.components.seconds)
    + Double(wallDuration.components.attoseconds) / 1e18
let outputData = Data(bytes: output.contents(), count: expectedBytes)
try outputData.write(to: outputURL, options: .atomic)
let report: [String: Any] = [
    "device": device.name,
    "width": width,
    "height": height,
    "radius": radius,
    "iterations": iterations,
    "gpu_seconds_total": gpuSeconds,
    "gpu_seconds_mean": gpuSeconds / Double(iterations),
    "wall_seconds_total": wallSeconds,
    "wall_seconds_mean": wallSeconds / Double(iterations),
]
let json = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
FileHandle.standardOutput.write(json)
FileHandle.standardOutput.write(Data("\n".utf8))
