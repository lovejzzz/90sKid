#import <Foundation/Foundation.h>
#import <Metal/Metal.h>

#include <cstdint>
#include <cstring>
#include <unistd.h>

static constexpr uint32_t kClassCount = 5;
static constexpr uint32_t kMaxDiskCoefficients = 81;
static constexpr uint32_t kMaxGaussianCoefficients = 17;

struct OpticalClassParameters {
    uint32_t count;
    uint32_t width;
    uint32_t height;
    uint32_t trials;
    uint32_t seedLow;
    uint32_t seedHigh;
    uint32_t diskSize;
    uint32_t gaussianSize;
    uint32_t classIndex;
    float inverseTrials;
    float offsetX;
    float offsetY;
    float weight;
};

static id<MTLDevice> gDevice;
static id<MTLCommandQueue> gQueue;
static id<MTLComputePipelineState> gSample;
static id<MTLComputePipelineState> gDisk;
static id<MTLComputePipelineState> gGaussianHorizontal;
static id<MTLComputePipelineState> gGaussianVertical;
static id<MTLComputePipelineState> gAccumulate;
static dispatch_once_t gOnce;
static bool gReady = false;

static void initializeMetal() {
    dispatch_once(&gOnce, ^{
        gDevice = MTLCreateSystemDefaultDevice();
        gQueue = [gDevice newCommandQueue];
        NSString *source = [NSString stringWithUTF8String:R"METAL(
#include <metal_stdlib>
using namespace metal;

constant uint kMaxDiskCoefficients = 81u;
constant uint kMaxGaussianCoefficients = 17u;

struct OpticalClassParameters {
    uint count;
    uint width;
    uint height;
    uint trials;
    uint seedLow;
    uint seedHigh;
    uint diskSize;
    uint gaussianSize;
    uint classIndex;
    float inverseTrials;
    float offsetX;
    float offsetY;
    float weight;
};

inline uint mul_hi(uint a, uint b) {
    return uint((ulong(a) * ulong(b)) >> 32);
}

inline uint4 philox4x32_10(uint4 counter, uint2 key) {
    constexpr uint M0 = 0xD2511F53u;
    constexpr uint M1 = 0xCD9E8D57u;
    constexpr uint W0 = 0x9E3779B9u;
    constexpr uint W1 = 0xBB67AE85u;
    for (uint round = 0; round < 10; ++round) {
        uint hi0 = mul_hi(M0, counter.x);
        uint lo0 = M0 * counter.x;
        uint hi1 = mul_hi(M1, counter.z);
        uint lo1 = M1 * counter.z;
        counter = uint4(hi1 ^ counter.y ^ key.x, lo1,
                        hi0 ^ counter.w ^ key.y, lo0);
        key += uint2(W0, W1);
    }
    return counter;
}

inline uint probability_threshold_u32(float probability) {
    uint bits = as_type<uint>(probability);
    int exponent = int((bits >> 23) & 0xffu) - 127;
    uint significand = (bits & 0x7fffffu) | 0x800000u;
    int shift = exponent + 9;
    return shift >= 0 ? (significand << uint(shift))
                      : (significand >> uint(-shift));
}

inline int reflect_index(int coordinate, int length) {
    if (length <= 1) return 0;
    int value = coordinate;
    while (value < 0 || value >= length) {
        value = value < 0 ? -value - 1 : 2 * length - value - 1;
    }
    return value;
}

kernel void sample_binomial_bernoulli(
                            device const float *probability [[buffer(0)]],
                            device float *output [[buffer(1)]],
                            constant OpticalClassParameters &p [[buffer(2)]],
                            uint index [[thread_position_in_grid]]) {
    if (index >= p.count) return;
    float target = probability[index];
    if (target <= 0.0f) {
        output[index] = 0.0f;
        return;
    }
    if (target >= 1.0f) {
        output[index] = 1.0f;
        return;
    }
    uint threshold = probability_threshold_u32(target);
    uint successes = 0u;
    uint2 key = uint2(p.seedLow, p.seedHigh ^ 0x9E3779B9u);
    for (uint block = 0u; block * 4u < p.trials; ++block) {
        uint4 bits = philox4x32_10(
            uint4(index, block, p.seedHigh, 0x52790002u), key
        );
        uint remaining = min(4u, p.trials - block * 4u);
        if (remaining > 0u) successes += bits.x < threshold;
        if (remaining > 1u) successes += bits.y < threshold;
        if (remaining > 2u) successes += bits.z < threshold;
        if (remaining > 3u) successes += bits.w < threshold;
    }
    output[index] = float(successes) * p.inverseTrials;
}

kernel void disk_filter(device const float *input [[buffer(0)]],
                        device float *output [[buffer(1)]],
                        device const float *coefficients [[buffer(2)]],
                        constant OpticalClassParameters &p [[buffer(3)]],
                        uint index [[thread_position_in_grid]]) {
    if (index >= p.count) return;
    int x = int(index % p.width);
    int y = int(index / p.width);
    int radius = int(p.diskSize / 2u);
    uint coefficientBase = p.classIndex * kMaxDiskCoefficients;
    float sum = 0.0f;
    for (uint ky = 0u; ky < p.diskSize; ++ky) {
        int sy = reflect_index(y + int(ky) - radius, int(p.height));
        for (uint kx = 0u; kx < p.diskSize; ++kx) {
            int sx = reflect_index(x + int(kx) - radius, int(p.width));
            float value = input[uint(sy) * p.width + uint(sx)];
            float coefficient = coefficients[
                coefficientBase + ky * p.diskSize + kx
            ];
            sum += value * coefficient;
        }
    }
    output[index] = sum;
}

kernel void gaussian_horizontal(
                        device const float *input [[buffer(0)]],
                        device float *output [[buffer(1)]],
                        device const float *coefficients [[buffer(2)]],
                        constant OpticalClassParameters &p [[buffer(3)]],
                        uint index [[thread_position_in_grid]]) {
    if (index >= p.count) return;
    int x = int(index % p.width);
    int y = int(index / p.width);
    int radius = int(p.gaussianSize / 2u);
    uint coefficientBase = p.classIndex * kMaxGaussianCoefficients;
    float sum = 0.0f;
    for (uint tap = 0u; tap < p.gaussianSize; ++tap) {
        int sx = reflect_index(x + int(tap) - radius, int(p.width));
        sum += input[uint(y) * p.width + uint(sx)]
             * coefficients[coefficientBase + tap];
    }
    output[index] = sum;
}

kernel void gaussian_vertical(
                        device const float *input [[buffer(0)]],
                        device float *output [[buffer(1)]],
                        device const float *coefficients [[buffer(2)]],
                        constant OpticalClassParameters &p [[buffer(3)]],
                        uint index [[thread_position_in_grid]]) {
    if (index >= p.count) return;
    int x = int(index % p.width);
    int y = int(index / p.width);
    int radius = int(p.gaussianSize / 2u);
    uint coefficientBase = p.classIndex * kMaxGaussianCoefficients;
    float sum = 0.0f;
    for (uint tap = 0u; tap < p.gaussianSize; ++tap) {
        int sy = reflect_index(y + int(tap) - radius, int(p.height));
        sum += input[uint(sy) * p.width + uint(x)]
             * coefficients[coefficientBase + tap];
    }
    output[index] = sum;
}

kernel void warp_subtract_accumulate(
                        device const float *sampled [[buffer(0)]],
                        device const float *expected [[buffer(1)]],
                        device float *accumulated [[buffer(2)]],
                        constant OpticalClassParameters &p [[buffer(3)]],
                        uint index [[thread_position_in_grid]]) {
    if (index >= p.count) return;
    int x = int(index % p.width);
    int y = int(index / p.width);
    float sourceX = float(x) - p.offsetX;
    float sourceY = float(y) - p.offsetY;
    int x0 = int(floor(sourceX));
    int y0 = int(floor(sourceY));
    float fractionX = sourceX - float(x0);
    float fractionY = sourceY - float(y0);
    int rx0 = reflect_index(x0, int(p.width));
    int rx1 = reflect_index(x0 + 1, int(p.width));
    int ry0 = reflect_index(y0, int(p.height));
    int ry1 = reflect_index(y0 + 1, int(p.height));
    uint i00 = uint(ry0) * p.width + uint(rx0);
    uint i01 = uint(ry0) * p.width + uint(rx1);
    uint i10 = uint(ry1) * p.width + uint(rx0);
    uint i11 = uint(ry1) * p.width + uint(rx1);
    float d00 = sampled[i00] - expected[i00];
    float d01 = sampled[i01] - expected[i01];
    float d10 = sampled[i10] - expected[i10];
    float d11 = sampled[i11] - expected[i11];
    float top = d00 + fractionX * (d01 - d00);
    float bottom = d10 + fractionX * (d11 - d10);
    float deviation = top + fractionY * (bottom - top);
    accumulated[index] += p.weight * deviation;
}
)METAL"];
        MTLCompileOptions *options = [MTLCompileOptions new];
        options.mathMode = MTLMathModeSafe;
        NSError *error = nil;
        id<MTLLibrary> library = [gDevice newLibraryWithSource:source
                                                       options:options
                                                         error:&error];
        if (!library) return;
        gSample = [gDevice newComputePipelineStateWithFunction:
            [library newFunctionWithName:@"sample_binomial_bernoulli"] error:&error];
        gDisk = [gDevice newComputePipelineStateWithFunction:
            [library newFunctionWithName:@"disk_filter"] error:&error];
        gGaussianHorizontal = [gDevice newComputePipelineStateWithFunction:
            [library newFunctionWithName:@"gaussian_horizontal"] error:&error];
        gGaussianVertical = [gDevice newComputePipelineStateWithFunction:
            [library newFunctionWithName:@"gaussian_vertical"] error:&error];
        gAccumulate = [gDevice newComputePipelineStateWithFunction:
            [library newFunctionWithName:@"warp_subtract_accumulate"] error:&error];
        gReady = gQueue && gSample && gDisk && gGaussianHorizontal
              && gGaussianVertical && gAccumulate;
    });
}

static void dispatchPipeline(
    id<MTLCommandBuffer> command,
    id<MTLComputePipelineState> pipeline,
    NSArray<id<MTLBuffer>> *buffers,
    const OpticalClassParameters &parameters
) {
    id<MTLComputeCommandEncoder> encoder = [command computeCommandEncoder];
    [encoder setComputePipelineState:pipeline];
    for (NSUInteger index = 0; index < buffers.count; ++index) {
        [encoder setBuffer:buffers[index] offset:0 atIndex:index];
    }
    [encoder setBytes:&parameters length:sizeof(parameters) atIndex:buffers.count];
    NSUInteger width = pipeline.threadExecutionWidth;
    NSUInteger group = MIN(pipeline.maxTotalThreadsPerThreadgroup, width * 8);
    [encoder dispatchThreads:MTLSizeMake(parameters.count, 1, 1)
        threadsPerThreadgroup:MTLSizeMake(group, 1, 1)];
    [encoder endEncoding];
}

extern "C" double metal_emulsion_population_f32(
    const float *probability,
    float *output,
    uint32_t width,
    uint32_t height,
    const uint32_t *trials,
    const uint64_t *seeds,
    const float *weights,
    const float *offsetsXY,
    const uint32_t *diskSizes,
    const float *diskCoefficients,
    const uint32_t *gaussianSizes,
    const float *gaussianCoefficients
) {
    @autoreleasepool {
        initializeMetal();
        if (!gReady || !probability || !output || width < 1 || height < 1
            || !trials || !seeds || !weights || !offsetsXY || !diskSizes
            || !diskCoefficients || !gaussianSizes || !gaussianCoefficients) {
            return -1.0;
        }
        uint64_t wideCount = uint64_t(width) * uint64_t(height);
        if (wideCount > UINT32_MAX) return -2.0;
        uint32_t count = uint32_t(wideCount);
        NSUInteger length = NSUInteger(count) * sizeof(float);
        NSUInteger pageSize = NSUInteger(getpagesize());
        bool sourceNoCopy = ((uintptr_t)probability % pageSize) == 0
                         && (length % pageSize) == 0;
        bool outputNoCopy = ((uintptr_t)output % pageSize) == 0
                         && (length % pageSize) == 0;
        id<MTLBuffer> sourceBuffer;
        if (sourceNoCopy) {
            sourceBuffer = [gDevice newBufferWithBytesNoCopy:(void *)probability
                                                     length:length
                                                    options:MTLResourceStorageModeShared
                                                deallocator:nil];
        } else {
            sourceBuffer = [gDevice newBufferWithLength:length
                                                options:MTLResourceStorageModeShared];
            if (sourceBuffer) std::memcpy(sourceBuffer.contents, probability, length);
        }
        id<MTLBuffer> outputBuffer;
        bool directOutput = false;
        if (outputNoCopy) {
            outputBuffer = [gDevice newBufferWithBytesNoCopy:(void *)output
                                                     length:length
                                                    options:MTLResourceStorageModeShared
                                                deallocator:nil];
            directOutput = outputBuffer != nil;
        }
        if (!outputBuffer) {
            outputBuffer = [gDevice newBufferWithLength:length
                                                options:MTLResourceStorageModeShared];
        }
        id<MTLBuffer> scratchA = [gDevice newBufferWithLength:length
                                                      options:MTLResourceStorageModePrivate];
        id<MTLBuffer> scratchB = [gDevice newBufferWithLength:length
                                                      options:MTLResourceStorageModePrivate];
        id<MTLBuffer> scratchC = [gDevice newBufferWithLength:length
                                                      options:MTLResourceStorageModePrivate];
        NSUInteger diskBytes = kClassCount * kMaxDiskCoefficients * sizeof(float);
        NSUInteger gaussianBytes = kClassCount * kMaxGaussianCoefficients * sizeof(float);
        id<MTLBuffer> diskBuffer = [gDevice newBufferWithBytes:diskCoefficients
                                                       length:diskBytes
                                                      options:MTLResourceStorageModeShared];
        id<MTLBuffer> gaussianBuffer = [gDevice newBufferWithBytes:gaussianCoefficients
                                                           length:gaussianBytes
                                                          options:MTLResourceStorageModeShared];
        if (!sourceBuffer || !outputBuffer || !scratchA || !scratchB || !scratchC
            || !diskBuffer || !gaussianBuffer) return -3.0;

        CFAbsoluteTime started = CFAbsoluteTimeGetCurrent();
        id<MTLCommandBuffer> command = [gQueue commandBuffer];
        id<MTLBlitCommandEncoder> clear = [command blitCommandEncoder];
        [clear fillBuffer:outputBuffer range:NSMakeRange(0, length) value:0];
        [clear endEncoding];
        for (uint32_t classIndex = 0; classIndex < kClassCount; ++classIndex) {
            if (trials[classIndex] < 1 || diskSizes[classIndex] < 1
                || diskSizes[classIndex] * diskSizes[classIndex] > kMaxDiskCoefficients
                || gaussianSizes[classIndex] < 1
                || gaussianSizes[classIndex] > kMaxGaussianCoefficients) {
                return -4.0;
            }
            OpticalClassParameters parameters = {
                count, width, height, trials[classIndex],
                uint32_t(seeds[classIndex]), uint32_t(seeds[classIndex] >> 32),
                diskSizes[classIndex], gaussianSizes[classIndex], classIndex,
                1.0f / float(trials[classIndex]),
                offsetsXY[classIndex * 2], offsetsXY[classIndex * 2 + 1],
                weights[classIndex]
            };
            dispatchPipeline(command, gSample, @[sourceBuffer, scratchA], parameters);
            dispatchPipeline(command, gDisk,
                             @[scratchA, scratchB, diskBuffer], parameters);
            dispatchPipeline(command, gDisk,
                             @[sourceBuffer, scratchC, diskBuffer], parameters);
            dispatchPipeline(command, gGaussianHorizontal,
                             @[scratchB, scratchA, gaussianBuffer], parameters);
            dispatchPipeline(command, gGaussianVertical,
                             @[scratchA, scratchB, gaussianBuffer], parameters);
            dispatchPipeline(command, gGaussianHorizontal,
                             @[scratchC, scratchA, gaussianBuffer], parameters);
            dispatchPipeline(command, gGaussianVertical,
                             @[scratchA, scratchC, gaussianBuffer], parameters);
            dispatchPipeline(command, gAccumulate,
                             @[scratchB, scratchC, outputBuffer], parameters);
        }
        [command commit];
        [command waitUntilCompleted];
        if (command.status != MTLCommandBufferStatusCompleted) return -5.0;
        if (!directOutput) std::memcpy(output, outputBuffer.contents, length);
        return CFAbsoluteTimeGetCurrent() - started;
    }
}
