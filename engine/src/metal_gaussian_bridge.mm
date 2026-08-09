#import <Foundation/Foundation.h>
#import <Metal/Metal.h>

#include <cstdint>
#include <cstring>
#include <unistd.h>

struct Parameters {
    uint32_t width;
    uint32_t height;
    uint32_t channels;
    uint32_t radius;
    uint32_t borderMode;
    uint32_t sourceOffset;
    uint32_t sourceRowStride;
    uint32_t sourcePixelStride;
    uint32_t sourceChannelStride;
};

static id<MTLDevice> gDevice;
static id<MTLCommandQueue> gQueue;
static id<MTLComputePipelineState> gHorizontal;
static id<MTLComputePipelineState> gVertical;
static id<MTLBuffer> gScalarSource;
static id<MTLBuffer> gScalarTemporary;
static id<MTLBuffer> gScalarDestination;
static NSUInteger gScalarLength = 0;
static NSUInteger gScalarTemporaryLength = 0;
static id<MTLBuffer> gRGBSource;
static id<MTLBuffer> gRGBTemporary;
static id<MTLBuffer> gRGBDestination;
static NSUInteger gRGBLength = 0;
static NSUInteger gRGBTemporaryLength = 0;
static id<MTLBuffer> gKernel;
static NSUInteger gKernelLength = 0;
static dispatch_once_t gOnce;
static bool gReady = false;

struct GaussianFlight {
    __strong id<MTLCommandBuffer> command;
    __strong id<MTLBuffer> source;
    __strong id<MTLBuffer> temporary;
    __strong id<MTLBuffer> destination;
    __strong id<MTLBuffer> kernel;
    CFAbsoluteTime started;
};

static void initializeMetal() {
    dispatch_once(&gOnce, ^{
        gDevice = MTLCreateSystemDefaultDevice();
        gQueue = [gDevice newCommandQueue];
        NSString *source = [NSString stringWithUTF8String:R"METAL(
#include <metal_stdlib>
using namespace metal;
struct Parameters {
    uint width; uint height; uint channels; uint radius; uint borderMode;
    uint sourceOffset; uint sourceRowStride; uint sourcePixelStride;
    uint sourceChannelStride;
};
inline int reflected(int value, int extent, uint borderMode) {
    while (value < 0 || value >= extent) {
        if (borderMode == 2u) value = value < 0 ? -value - 1 : 2 * extent - value - 1;
        else value = value < 0 ? -value : 2 * extent - value - 2;
    }
    return value;
}

kernel void horizontal(device const float *source [[buffer(0)]],
                       device float *destination [[buffer(1)]],
                       constant Parameters &p [[buffer(2)]],
                       device const float *weights [[buffer(3)]],
                       uint3 position [[thread_position_in_grid]]) {
    if (position.x >= p.width || position.y >= p.height || position.z >= p.channels) return;
    float sum = 0.0f;
    int radius = int(p.radius);
    for (int offset = -radius; offset <= radius; ++offset) {
        int x = reflected(int(position.x) + offset, int(p.width), p.borderMode);
        uint index = p.sourceOffset + position.y * p.sourceRowStride
                   + uint(x) * p.sourcePixelStride
                   + position.z * p.sourceChannelStride;
        sum += source[index] * weights[offset + radius];
    }
    destination[(position.y * p.width + position.x) * p.channels + position.z] = sum;
}
kernel void vertical(device const float *source [[buffer(0)]],
                     device float *destination [[buffer(1)]],
                     constant Parameters &p [[buffer(2)]],
                     device const float *weights [[buffer(3)]],
                     uint3 position [[thread_position_in_grid]]) {
    if (position.x >= p.width || position.y >= p.height || position.z >= p.channels) return;
    float sum = 0.0f;
    int radius = int(p.radius);
    for (int offset = -radius; offset <= radius; ++offset) {
        int y = reflected(int(position.y) + offset, int(p.height), p.borderMode);
        uint index = (uint(y) * p.width + position.x) * p.channels + position.z;
        sum += source[index] * weights[offset + radius];
    }
    destination[(position.y * p.width + position.x) * p.channels + position.z] = sum;
}
)METAL"];
        MTLCompileOptions *options = [MTLCompileOptions new];
        options.mathMode = MTLMathModeSafe;
        NSError *error = nil;
        id<MTLLibrary> library = [gDevice newLibraryWithSource:source options:options error:&error];
        if (!library) return;
        id<MTLFunction> horizontal = [library newFunctionWithName:@"horizontal"];
        id<MTLFunction> vertical = [library newFunctionWithName:@"vertical"];
        gHorizontal = [gDevice newComputePipelineStateWithFunction:horizontal error:&error];
        if (!gHorizontal) return;
        gVertical = [gDevice newComputePipelineStateWithFunction:vertical error:&error];
        if (!gVertical) return;
        gReady = gQueue != nil;
    });
}

// Experimental asynchronous API. Every submission owns its mutable Metal
// resources, so calls cannot overwrite a shared kernel or temporary plane.
// The caller must keep the page-aligned input and output allocations alive and
// immutable until metal_gaussian_wait releases the returned flight handle.
extern "C" void *metal_gaussian_submit_f32(
    const float *input,
    float *output,
    int width,
    int height,
    int channels,
    const float *weights,
    int radius,
    int borderMode
) {
    @autoreleasepool {
        initializeMetal();
        if (!gReady || !input || !output || !weights || width < 1 ||
            height < 1 || channels < 1 || radius < 0 ||
            (borderMode != 2 && borderMode != 4)) return nullptr;
        NSUInteger length =
            (NSUInteger)width * height * channels * sizeof(float);
        NSUInteger weightLength =
            (NSUInteger)(2 * radius + 1) * sizeof(float);
        NSUInteger pageSize = (NSUInteger)getpagesize();
        if (((uintptr_t)input % pageSize) != 0 ||
            ((uintptr_t)output % pageSize) != 0 ||
            (length % pageSize) != 0) return nullptr;

        auto *flight = new GaussianFlight();
        flight->started = CFAbsoluteTimeGetCurrent();
        flight->source = [gDevice
            newBufferWithBytesNoCopy:(void *)input
            length:length
            options:MTLResourceStorageModeShared
            deallocator:nil];
        flight->destination = [gDevice
            newBufferWithBytesNoCopy:(void *)output
            length:length
            options:MTLResourceStorageModeShared
            deallocator:nil];
        flight->temporary = [gDevice
            newBufferWithLength:length
            options:MTLResourceStorageModePrivate];
        flight->kernel = [gDevice
            newBufferWithBytes:weights
            length:weightLength
            options:MTLResourceStorageModeShared];
        if (!flight->source || !flight->destination || !flight->temporary ||
            !flight->kernel) {
            delete flight;
            return nullptr;
        }

        Parameters parameters = {
            (uint32_t)width,
            (uint32_t)height,
            (uint32_t)channels,
            (uint32_t)radius,
            (uint32_t)borderMode,
            0u,
            (uint32_t)(width * channels),
            (uint32_t)channels,
            1u,
        };
        @synchronized (gQueue) {
            flight->command = [gQueue commandBuffer];
        }
        if (!flight->command) {
            delete flight;
            return nullptr;
        }
        id<MTLComputeCommandEncoder> first =
            [flight->command computeCommandEncoder];
        [first setComputePipelineState:gHorizontal];
        [first setBuffer:flight->source offset:0 atIndex:0];
        [first setBuffer:flight->temporary offset:0 atIndex:1];
        [first setBytes:&parameters length:sizeof(parameters) atIndex:2];
        [first setBuffer:flight->kernel offset:0 atIndex:3];
        [first dispatchThreads:MTLSizeMake(width, height, channels)
             threadsPerThreadgroup:MTLSizeMake(16, 8, 1)];
        [first endEncoding];
        id<MTLComputeCommandEncoder> second =
            [flight->command computeCommandEncoder];
        [second setComputePipelineState:gVertical];
        [second setBuffer:flight->temporary offset:0 atIndex:0];
        [second setBuffer:flight->destination offset:0 atIndex:1];
        [second setBytes:&parameters length:sizeof(parameters) atIndex:2];
        [second setBuffer:flight->kernel offset:0 atIndex:3];
        [second dispatchThreads:MTLSizeMake(width, height, channels)
              threadsPerThreadgroup:MTLSizeMake(16, 8, 1)];
        [second endEncoding];
        @synchronized (gQueue) {
            [flight->command commit];
        }
        return flight;
    }
}

extern "C" int metal_gaussian_wait(void *handle, double *elapsedSeconds) {
    @autoreleasepool {
        if (!handle) return -30;
        auto *flight = static_cast<GaussianFlight *>(handle);
        [flight->command waitUntilCompleted];
        int result = flight->command.status == MTLCommandBufferStatusCompleted
            ? 0
            : -31;
        if (elapsedSeconds) {
            *elapsedSeconds =
                CFAbsoluteTimeGetCurrent() - flight->started;
        }
        delete flight;
        return result;
    }
}

extern "C" double metal_gaussian_f32(
    const float *input,
    float *output,
    int width,
    int height,
    int channels,
    const float *weights,
    int radius,
    int borderMode
) {
    @autoreleasepool {
        initializeMetal();
        if (!gReady || !input || !output || !weights || width < 1 || height < 1 ||
            channels < 1 || radius < 0 || (borderMode != 2 && borderMode != 4)) return -1.0;
        NSUInteger length = (NSUInteger)width * height * channels * sizeof(float);
        NSUInteger weightLength = (NSUInteger)(2 * radius + 1) * sizeof(float);
        CFAbsoluteTime started = CFAbsoluteTimeGetCurrent();
        @synchronized (gQueue) {
        id<MTLBuffer> source;
        id<MTLBuffer> temporary;
        id<MTLBuffer> destination;
        bool noCopy = false;
        @synchronized (gQueue) {
            if (channels == 1) {
                if (gScalarLength < length) {
                    gScalarSource = [gDevice newBufferWithLength:length options:MTLResourceStorageModeShared];
                    gScalarTemporary = [gDevice newBufferWithLength:length options:MTLResourceStorageModePrivate];
                    gScalarDestination = [gDevice newBufferWithLength:length options:MTLResourceStorageModeShared];
                    gScalarLength = length;
                    gScalarTemporaryLength = length;
                }
                source = gScalarSource;
                temporary = gScalarTemporary;
                destination = gScalarDestination;
            } else {
                if (gRGBLength < length) {
                    gRGBSource = [gDevice newBufferWithLength:length options:MTLResourceStorageModeShared];
                    gRGBTemporary = [gDevice newBufferWithLength:length options:MTLResourceStorageModePrivate];
                    gRGBDestination = [gDevice newBufferWithLength:length options:MTLResourceStorageModeShared];
                    gRGBLength = length;
                    gRGBTemporaryLength = length;
                }
                source = gRGBSource;
                temporary = gRGBTemporary;
                destination = gRGBDestination;
            }
            if (gKernelLength < weightLength) {
                gKernel = [gDevice newBufferWithLength:weightLength options:MTLResourceStorageModeShared];
                gKernelLength = weightLength;
            }
        }
        if (!source || !temporary || !destination || !gKernel) return -2.0;
        NSUInteger pageSize = (NSUInteger)getpagesize();
        bool pageAligned =
            ((uintptr_t)input % pageSize) == 0 &&
            ((uintptr_t)output % pageSize) == 0 &&
            (length % pageSize) == 0;
        if (pageAligned) {
            id<MTLBuffer> directSource = [gDevice
                newBufferWithBytesNoCopy:(void *)input
                length:length
                options:MTLResourceStorageModeShared
                deallocator:nil];
            id<MTLBuffer> directDestination = [gDevice
                newBufferWithBytesNoCopy:(void *)output
                length:length
                options:MTLResourceStorageModeShared
                deallocator:nil];
            if (directSource && directDestination) {
                source = directSource;
                destination = directDestination;
                noCopy = true;
            }
        }
        if (!noCopy) std::memcpy(source.contents, input, length);
        std::memcpy(gKernel.contents, weights, weightLength);
        Parameters parameters = {
            (uint32_t)width,
            (uint32_t)height,
            (uint32_t)channels,
            (uint32_t)radius,
            (uint32_t)borderMode,
            0u,
            (uint32_t)(width * channels),
            (uint32_t)channels,
            1u,
        };
        id<MTLCommandBuffer> command = [gQueue commandBuffer];
        id<MTLComputeCommandEncoder> first = [command computeCommandEncoder];
        [first setComputePipelineState:gHorizontal];
        [first setBuffer:source offset:0 atIndex:0];
        [first setBuffer:temporary offset:0 atIndex:1];
        [first setBytes:&parameters length:sizeof(parameters) atIndex:2];
        [first setBuffer:gKernel offset:0 atIndex:3];
        [first dispatchThreads:MTLSizeMake(width, height, channels)
             threadsPerThreadgroup:MTLSizeMake(16, 8, 1)];
        [first endEncoding];
        id<MTLComputeCommandEncoder> second = [command computeCommandEncoder];
        [second setComputePipelineState:gVertical];
        [second setBuffer:temporary offset:0 atIndex:0];
        [second setBuffer:destination offset:0 atIndex:1];
        [second setBytes:&parameters length:sizeof(parameters) atIndex:2];
        [second setBuffer:gKernel offset:0 atIndex:3];
        [second dispatchThreads:MTLSizeMake(width, height, channels)
              threadsPerThreadgroup:MTLSizeMake(16, 8, 1)];
        [second endEncoding];
        [command commit];
        [command waitUntilCompleted];
        if (command.status != MTLCommandBufferStatusCompleted) return -3.0;
        if (!noCopy) std::memcpy(output, destination.contents, length);
            return CFAbsoluteTimeGetCurrent() - started;
        }
    }
}

extern "C" double metal_gaussian_strided_f32(
    const float *inputBase,
    size_t inputLengthBytes,
    size_t inputOffsetFloats,
    int sourceRowStride,
    int sourcePixelStride,
    int sourceChannelStride,
    float *output,
    int width,
    int height,
    int channels,
    const float *weights,
    int radius,
    int borderMode
) {
    @autoreleasepool {
        initializeMetal();
        if (!gReady || !inputBase || !output || !weights || width < 1 ||
            height < 1 || channels < 1 || radius < 0 ||
            (borderMode != 2 && borderMode != 4) || sourceRowStride < 1 ||
            sourcePixelStride < 1 || sourceChannelStride < 1) return -10.0;
        NSUInteger outputLength =
            (NSUInteger)width * height * channels * sizeof(float);
        NSUInteger weightLength = (NSUInteger)(2 * radius + 1) * sizeof(float);
        NSUInteger pageSize = (NSUInteger)getpagesize();
        if (((uintptr_t)inputBase % pageSize) != 0 ||
            ((uintptr_t)output % pageSize) != 0 ||
            (inputLengthBytes % pageSize) != 0 ||
            (outputLength % pageSize) != 0 || inputOffsetFloats > UINT32_MAX)
            return -11.0;
        size_t last = inputOffsetFloats
            + (size_t)(height - 1) * sourceRowStride
            + (size_t)(width - 1) * sourcePixelStride
            + (size_t)(channels - 1) * sourceChannelStride;
        if ((last + 1) * sizeof(float) > inputLengthBytes) return -12.0;

        CFAbsoluteTime started = CFAbsoluteTimeGetCurrent();
        @synchronized (gQueue) {
            id<MTLBuffer> source = [gDevice
                newBufferWithBytesNoCopy:(void *)inputBase
                length:inputLengthBytes
                options:MTLResourceStorageModeShared
                deallocator:nil];
            id<MTLBuffer> destination = [gDevice
                newBufferWithBytesNoCopy:(void *)output
                length:outputLength
                options:MTLResourceStorageModeShared
                deallocator:nil];
            id<MTLBuffer> temporary;
            if (channels == 1) {
                if (gScalarTemporaryLength < outputLength) {
                    gScalarTemporary = [gDevice
                        newBufferWithLength:outputLength
                        options:MTLResourceStorageModePrivate];
                    gScalarTemporaryLength = outputLength;
                }
                temporary = gScalarTemporary;
            } else {
                if (gRGBTemporaryLength < outputLength) {
                    gRGBTemporary = [gDevice
                        newBufferWithLength:outputLength
                        options:MTLResourceStorageModePrivate];
                    gRGBTemporaryLength = outputLength;
                }
                temporary = gRGBTemporary;
            }
            if (gKernelLength < weightLength) {
                gKernel = [gDevice newBufferWithLength:weightLength
                    options:MTLResourceStorageModeShared];
                gKernelLength = weightLength;
            }
            if (!source || !destination || !temporary || !gKernel) return -13.0;
            std::memcpy(gKernel.contents, weights, weightLength);
            Parameters parameters = {
                (uint32_t)width,
                (uint32_t)height,
                (uint32_t)channels,
                (uint32_t)radius,
                (uint32_t)borderMode,
                (uint32_t)inputOffsetFloats,
                (uint32_t)sourceRowStride,
                (uint32_t)sourcePixelStride,
                (uint32_t)sourceChannelStride,
            };
            id<MTLCommandBuffer> command = [gQueue commandBuffer];
            id<MTLComputeCommandEncoder> first = [command computeCommandEncoder];
            [first setComputePipelineState:gHorizontal];
            [first setBuffer:source offset:0 atIndex:0];
            [first setBuffer:temporary offset:0 atIndex:1];
            [first setBytes:&parameters length:sizeof(parameters) atIndex:2];
            [first setBuffer:gKernel offset:0 atIndex:3];
            [first dispatchThreads:MTLSizeMake(width, height, channels)
                 threadsPerThreadgroup:MTLSizeMake(16, 8, 1)];
            [first endEncoding];
            id<MTLComputeCommandEncoder> second = [command computeCommandEncoder];
            [second setComputePipelineState:gVertical];
            [second setBuffer:temporary offset:0 atIndex:0];
            [second setBuffer:destination offset:0 atIndex:1];
            [second setBytes:&parameters length:sizeof(parameters) atIndex:2];
            [second setBuffer:gKernel offset:0 atIndex:3];
            [second dispatchThreads:MTLSizeMake(width, height, channels)
                  threadsPerThreadgroup:MTLSizeMake(16, 8, 1)];
            [second endEncoding];
            [command commit];
            [command waitUntilCompleted];
            if (command.status != MTLCommandBufferStatusCompleted) return -14.0;
        }
        return CFAbsoluteTimeGetCurrent() - started;
    }
}
