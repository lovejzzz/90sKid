#import <Foundation/Foundation.h>
#import <Metal/Metal.h>

#include <cstdint>
#include <cstring>
#include <unistd.h>

struct BinomialParameters {
    uint32_t count;
    uint32_t trials;
    uint32_t seedLow;
    uint32_t seedHigh;
    uint32_t originX;
    uint32_t originY;
    uint32_t tileWidth;
    uint32_t fullWidth;
};

static id<MTLDevice> gDevice;
static id<MTLCommandQueue> gQueue;
static id<MTLComputePipelineState> gBinomial;
static id<MTLComputePipelineState> gBinomialBernoulli;
static dispatch_once_t gOnce;
static bool gReady = false;

struct BinomialFlight {
    __strong id<MTLCommandBuffer> command;
    __strong id<MTLBuffer> source;
    __strong id<MTLBuffer> destination;
    float *output;
    NSUInteger length;
    bool directOutput;
    CFAbsoluteTime started;
};

static void initializeMetal() {
    dispatch_once(&gOnce, ^{
        gDevice = MTLCreateSystemDefaultDevice();
        gQueue = [gDevice newCommandQueue];
        NSString *source = [NSString stringWithUTF8String:R"METAL(
#include <metal_stdlib>
using namespace metal;

struct BinomialParameters {
    uint count;
    uint trials;
    uint seedLow;
    uint seedHigh;
    uint originX;
    uint originY;
    uint tileWidth;
    uint fullWidth;
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

inline float uniform_open_24(uint bits) {
    return (float(bits >> 8) + 0.5f) * 0x1.0p-24f;
}

inline uint probability_threshold_u32(float probability) {
    // Convert a positive normal float32 probability to floor(p * 2^32)
    // using its IEEE-754 fields. This avoids reducing a 32-bit Philox word to
    // float's 24-bit mantissa before the Bernoulli comparison.
    uint bits = as_type<uint>(probability);
    int exponent = int((bits >> 23) & 0xffu) - 127;
    uint significand = (bits & 0x7fffffu) | 0x800000u;
    int shift = exponent + 9;
    return shift >= 0 ? (significand << uint(shift))
                      : (significand >> uint(-shift));
}

inline uint inverse_binomial(float sourceP, uint n, float u) {
    if (sourceP <= 0.0f) return 0u;
    if (sourceP >= 1.0f) return n;
    bool mirror = sourceP > 0.5f;
    float p = mirror ? (1.0f - sourceP) : sourceP;
    float q = 1.0f - p;
    float mass = powr(q, float(n));
    float cumulative = mass;
    uint value = 0u;
    while (u > cumulative && value < n) {
        mass *= (float(n - value) / float(value + 1u)) * (p / q);
        cumulative += mass;
        value += 1u;
    }
    return mirror ? (n - value) : value;
}

kernel void sample_binomial(device const float *probability [[buffer(0)]],
                            device float *output [[buffer(1)]],
                            constant BinomialParameters &p [[buffer(2)]],
                            uint index [[thread_position_in_grid]]) {
    if (index >= p.count) return;
    uint localX = index % p.tileWidth;
    uint localY = index / p.tileWidth;
    uint globalIndex = (p.originY + localY) * p.fullWidth + p.originX + localX;
    uint4 counter = uint4(globalIndex, 0u, p.seedHigh, 0x52790001u);
    uint2 key = uint2(p.seedLow, p.seedHigh ^ 0x9E3779B9u);
    uint randomBits = philox4x32_10(counter, key).x;
    float uniform = uniform_open_24(randomBits);
    output[index] = float(inverse_binomial(probability[index], p.trials, uniform));
}

kernel void sample_binomial_bernoulli(
                            device const float *probability [[buffer(0)]],
                            device float *output [[buffer(1)]],
                            constant BinomialParameters &p [[buffer(2)]],
                            uint index [[thread_position_in_grid]]) {
    if (index >= p.count) return;
    float target = probability[index];
    if (target <= 0.0f) {
        output[index] = 0.0f;
        return;
    }
    if (target >= 1.0f) {
        output[index] = float(p.trials);
        return;
    }
    uint threshold = probability_threshold_u32(target);
    uint successes = 0u;
    uint2 key = uint2(p.seedLow, p.seedHigh ^ 0x9E3779B9u);
    for (uint block = 0u; block * 4u < p.trials; ++block) {
        uint localX = index % p.tileWidth;
        uint localY = index / p.tileWidth;
        uint globalIndex = (p.originY + localY) * p.fullWidth + p.originX + localX;
        uint4 bits = philox4x32_10(
            uint4(globalIndex, block, p.seedHigh, 0x52790002u), key
        );
        uint remaining = min(4u, p.trials - block * 4u);
        if (remaining > 0u) successes += bits.x < threshold;
        if (remaining > 1u) successes += bits.y < threshold;
        if (remaining > 2u) successes += bits.z < threshold;
        if (remaining > 3u) successes += bits.w < threshold;
    }
    output[index] = float(successes);
}
)METAL"];
        MTLCompileOptions *options = [MTLCompileOptions new];
        options.mathMode = MTLMathModeSafe;
        NSError *error = nil;
        id<MTLLibrary> library = [gDevice newLibraryWithSource:source
                                                       options:options
                                                         error:&error];
        if (!library) return;
        id<MTLFunction> function = [library newFunctionWithName:@"sample_binomial"];
        gBinomial = [gDevice newComputePipelineStateWithFunction:function error:&error];
        if (!gBinomial) return;
        id<MTLFunction> bernoulli = [library newFunctionWithName:@"sample_binomial_bernoulli"];
        gBinomialBernoulli = [gDevice newComputePipelineStateWithFunction:bernoulli error:&error];
        if (!gBinomialBernoulli) return;
        gReady = gQueue != nil;
    });
}

extern "C" void *metal_binomial_submit_f32(
    const float *probability,
    float *output,
    uint32_t count,
    uint32_t trials,
    uint64_t seed,
    uint32_t originX,
    uint32_t originY,
    uint32_t tileWidth,
    uint32_t fullWidth,
    uint32_t mode
) {
    @autoreleasepool {
        initializeMetal();
        if (!gReady || !probability || !output || count < 1 || trials < 1) return nullptr;
        auto *flight = new BinomialFlight();
        flight->length = (NSUInteger)count * sizeof(float);
        flight->output = output;
        flight->directOutput = false;
        flight->started = CFAbsoluteTimeGetCurrent();
        NSUInteger pageSize = (NSUInteger)getpagesize();
        bool sourceNoCopy = ((uintptr_t)probability % pageSize) == 0 &&
                            (flight->length % pageSize) == 0;
        bool outputNoCopy = ((uintptr_t)output % pageSize) == 0 &&
                            (flight->length % pageSize) == 0;
        if (sourceNoCopy) {
            flight->source = [gDevice newBufferWithBytesNoCopy:(void *)probability
                                                        length:flight->length
                                                       options:MTLResourceStorageModeShared
                                                   deallocator:nil];
        } else {
            flight->source = [gDevice newBufferWithLength:flight->length
                                                   options:MTLResourceStorageModeShared];
            if (flight->source) std::memcpy(flight->source.contents, probability, flight->length);
        }
        if (outputNoCopy) {
            flight->destination = [gDevice newBufferWithBytesNoCopy:(void *)output
                                                             length:flight->length
                                                            options:MTLResourceStorageModeShared
                                                        deallocator:nil];
            flight->directOutput = flight->destination != nil;
        }
        if (!flight->destination) {
            flight->destination = [gDevice newBufferWithLength:flight->length
                                                        options:MTLResourceStorageModeShared];
        }
        if (!flight->source || !flight->destination) {
            delete flight;
            return nullptr;
        }
        BinomialParameters parameters = {
            count, trials, (uint32_t)seed, (uint32_t)(seed >> 32),
            originX, originY, tileWidth, fullWidth
        };
        flight->command = [gQueue commandBuffer];
        id<MTLComputeCommandEncoder> encoder = [flight->command computeCommandEncoder];
        id<MTLComputePipelineState> pipeline =
            mode == 1u ? gBinomialBernoulli : gBinomial;
        [encoder setComputePipelineState:pipeline];
        [encoder setBuffer:flight->source offset:0 atIndex:0];
        [encoder setBuffer:flight->destination offset:0 atIndex:1];
        [encoder setBytes:&parameters length:sizeof(parameters) atIndex:2];
        NSUInteger width = pipeline.threadExecutionWidth;
        NSUInteger group = MIN(pipeline.maxTotalThreadsPerThreadgroup, width * 8);
        [encoder dispatchThreads:MTLSizeMake(count, 1, 1)
            threadsPerThreadgroup:MTLSizeMake(group, 1, 1)];
        [encoder endEncoding];
        [flight->command commit];
        return flight;
    }
}

extern "C" int metal_binomial_wait(void *handle, double *elapsedSeconds) {
    @autoreleasepool {
        if (!handle) return -30;
        auto *flight = static_cast<BinomialFlight *>(handle);
        [flight->command waitUntilCompleted];
        int result = flight->command.status == MTLCommandBufferStatusCompleted ? 0 : -31;
        if (result == 0 && !flight->directOutput) {
            std::memcpy(flight->output, flight->destination.contents, flight->length);
        }
        if (elapsedSeconds) *elapsedSeconds = CFAbsoluteTimeGetCurrent() - flight->started;
        delete flight;
        return result;
    }
}

extern "C" double metal_binomial_f32(
    const float *probability,
    float *output,
    uint32_t count,
    uint32_t trials,
    uint64_t seed,
    uint32_t originX,
    uint32_t originY,
    uint32_t tileWidth,
    uint32_t fullWidth
) {
    @autoreleasepool {
        initializeMetal();
        if (!gReady || !probability || !output || count < 1 || trials < 1) {
            return -1.0;
        }
        NSUInteger length = (NSUInteger)count * sizeof(float);
        id<MTLBuffer> source = [gDevice newBufferWithLength:length
                                                    options:MTLResourceStorageModeShared];
        id<MTLBuffer> destination = [gDevice newBufferWithLength:length
                                                         options:MTLResourceStorageModeShared];
        if (!source || !destination) return -2.0;
        std::memcpy(source.contents, probability, length);
        BinomialParameters parameters = {
            count,
            trials,
            (uint32_t)seed,
            (uint32_t)(seed >> 32),
            originX,
            originY,
            tileWidth,
            fullWidth,
        };
        CFAbsoluteTime started = CFAbsoluteTimeGetCurrent();
        id<MTLCommandBuffer> command = [gQueue commandBuffer];
        id<MTLComputeCommandEncoder> encoder = [command computeCommandEncoder];
        [encoder setComputePipelineState:gBinomial];
        [encoder setBuffer:source offset:0 atIndex:0];
        [encoder setBuffer:destination offset:0 atIndex:1];
        [encoder setBytes:&parameters length:sizeof(parameters) atIndex:2];
        NSUInteger width = gBinomial.threadExecutionWidth;
        NSUInteger group = MIN(gBinomial.maxTotalThreadsPerThreadgroup, width * 8);
        [encoder dispatchThreads:MTLSizeMake(count, 1, 1)
            threadsPerThreadgroup:MTLSizeMake(group, 1, 1)];
        [encoder endEncoding];
        [command commit];
        [command waitUntilCompleted];
        if (command.status != MTLCommandBufferStatusCompleted) return -3.0;
        std::memcpy(output, destination.contents, length);
        return CFAbsoluteTimeGetCurrent() - started;
    }
}

extern "C" double metal_binomial_bernoulli_f32(
    const float *probability,
    float *output,
    uint32_t count,
    uint32_t trials,
    uint64_t seed,
    uint32_t originX,
    uint32_t originY,
    uint32_t tileWidth,
    uint32_t fullWidth
) {
    @autoreleasepool {
        initializeMetal();
        if (!gReady || !probability || !output || count < 1 || trials < 1) return -1.0;
        NSUInteger length = (NSUInteger)count * sizeof(float);
        id<MTLBuffer> source = [gDevice newBufferWithLength:length options:MTLResourceStorageModeShared];
        id<MTLBuffer> destination = [gDevice newBufferWithLength:length options:MTLResourceStorageModeShared];
        if (!source || !destination) return -2.0;
        std::memcpy(source.contents, probability, length);
        BinomialParameters parameters = {
            count, trials, (uint32_t)seed, (uint32_t)(seed >> 32),
            originX, originY, tileWidth, fullWidth
        };
        CFAbsoluteTime started = CFAbsoluteTimeGetCurrent();
        id<MTLCommandBuffer> command = [gQueue commandBuffer];
        id<MTLComputeCommandEncoder> encoder = [command computeCommandEncoder];
        [encoder setComputePipelineState:gBinomialBernoulli];
        [encoder setBuffer:source offset:0 atIndex:0];
        [encoder setBuffer:destination offset:0 atIndex:1];
        [encoder setBytes:&parameters length:sizeof(parameters) atIndex:2];
        NSUInteger width = gBinomialBernoulli.threadExecutionWidth;
        NSUInteger group = MIN(gBinomialBernoulli.maxTotalThreadsPerThreadgroup, width * 8);
        [encoder dispatchThreads:MTLSizeMake(count, 1, 1)
            threadsPerThreadgroup:MTLSizeMake(group, 1, 1)];
        [encoder endEncoding];
        [command commit];
        [command waitUntilCompleted];
        if (command.status != MTLCommandBufferStatusCompleted) return -3.0;
        std::memcpy(output, destination.contents, length);
        return CFAbsoluteTimeGetCurrent() - started;
    }
}
