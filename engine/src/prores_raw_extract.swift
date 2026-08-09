import AVFoundation
import CoreMedia
import CoreVideo
import Foundation

struct Options {
    let input: URL
    let outputDirectory: URL
    let startFrame: Int
    let frameCount: Int
    let writeRaw: Bool
}

func parseOptions() -> Options {
    let args = CommandLine.arguments
    guard args.count >= 3 else {
        fputs("usage: prores_raw_extract INPUT OUTPUT_DIR [--start-frame N] [--frames N] [--no-raw]\n", stderr)
        exit(2)
    }
    var startFrame = 0
    var frameCount = 1
    var writeRaw = true
    var index = 3
    while index < args.count {
        switch args[index] {
        case "--start-frame":
            index += 1
            guard index < args.count, let value = Int(args[index]) else { exit(2) }
            startFrame = value
        case "--frames":
            index += 1
            guard index < args.count, let value = Int(args[index]) else { exit(2) }
            frameCount = value
        case "--no-raw":
            writeRaw = false
        default:
            fputs("unknown option: \(args[index])\n", stderr)
            exit(2)
        }
        index += 1
    }
    return Options(
        input: URL(fileURLWithPath: args[1]),
        outputDirectory: URL(fileURLWithPath: args[2]),
        startFrame: startFrame,
        frameCount: frameCount,
        writeRaw: writeRaw
    )
}

func copyAttachment(_ buffer: CVPixelBuffer, _ key: CFString) -> CFTypeRef? {
    CVBufferCopyAttachment(buffer, key, nil)
}

func numberAttachment(_ buffer: CVPixelBuffer, _ key: CFString) -> NSNumber? {
    copyAttachment(buffer, key) as? NSNumber
}

func floatArrayAttachment(_ buffer: CVPixelBuffer, _ key: CFString) -> [Float]? {
    guard let data = copyAttachment(buffer, key) as? Data else { return nil }
    guard data.count % MemoryLayout<Float>.size == 0 else { return nil }
    return data.withUnsafeBytes { rawBuffer in
        Array(rawBuffer.bindMemory(to: Float.self))
    }
}

func fourCC(_ value: OSType) -> String {
    let bytes: [UInt8] = [
        UInt8((value >> 24) & 0xff), UInt8((value >> 16) & 0xff),
        UInt8((value >> 8) & 0xff), UInt8(value & 0xff),
    ]
    return String(bytes: bytes, encoding: .ascii) ?? String(value)
}

func percentile(_ histogram: [UInt64], _ count: UInt64, _ fraction: Double) -> Int {
    let target = UInt64((Double(count - 1) * fraction).rounded(.down))
    var cumulative: UInt64 = 0
    for (value, frequency) in histogram.enumerated() {
        cumulative += frequency
        if cumulative > target { return value }
    }
    return histogram.count - 1
}

func inspectAndOptionallyWrite(
    _ pixelBuffer: CVPixelBuffer,
    frameIndex: Int,
    outputDirectory: URL,
    writeRaw: Bool
) throws -> [String: Any] {
    let width = CVPixelBufferGetWidth(pixelBuffer)
    let height = CVPixelBufferGetHeight(pixelBuffer)
    let bytesPerRow = CVPixelBufferGetBytesPerRow(pixelBuffer)
    let format = CVPixelBufferGetPixelFormatType(pixelBuffer)
    guard format == kCVPixelFormatType_16VersatileBayer else {
        throw NSError(domain: "ProResRAWExtract", code: 1, userInfo: [
            NSLocalizedDescriptionKey: "decoder returned \(fourCC(format)), expected bp16"
        ])
    }

    CVPixelBufferLockBaseAddress(pixelBuffer, .readOnly)
    defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, .readOnly) }
    guard let base = CVPixelBufferGetBaseAddress(pixelBuffer) else {
        throw NSError(domain: "ProResRAWExtract", code: 2)
    }

    let blackLevel = numberAttachment(pixelBuffer, kCVPixelBufferProResRAWKey_BlackLevel)?.intValue ?? 0
    let whiteLevel = numberAttachment(pixelBuffer, kCVPixelBufferProResRAWKey_WhiteLevel)?.intValue ?? 65535
    let bayerPattern = numberAttachment(pixelBuffer, kCVPixelBufferVersatileBayerKey_BayerPattern)?.intValue ?? -1
    var histogram = [UInt64](repeating: 0, count: 65536)
    var atOrBelowBlack: UInt64 = 0
    var atOrAboveWhite: UInt64 = 0
    var maximum = 0
    var minimum = 65535
    var rawData = writeRaw ? Data(capacity: width * height * 2) : Data()

    for row in 0..<height {
        let rowPointer = base.advanced(by: row * bytesPerRow).assumingMemoryBound(to: UInt16.self)
        if writeRaw {
            rawData.append(UnsafeBufferPointer(start: rowPointer, count: width))
        }
        for column in 0..<width {
            let value = Int(UInt16(littleEndian: rowPointer[column]))
            histogram[value] += 1
            minimum = min(minimum, value)
            maximum = max(maximum, value)
            if value <= blackLevel { atOrBelowBlack += 1 }
            if value >= whiteLevel { atOrAboveWhite += 1 }
        }
    }

    if writeRaw {
        let path = outputDirectory.appendingPathComponent(String(format: "frame_%04d.raw16le", frameIndex))
        try rawData.write(to: path, options: .atomic)
    }

    let sampleCount = UInt64(width * height)
    let metadata: [String: Any] = [
        "frame_index": frameIndex,
        "width": width,
        "height": height,
        "bytes_per_row": bytesPerRow,
        "pixel_format": fourCC(format),
        "bayer_pattern": bayerPattern,
        "black_level": blackLevel,
        "white_level": whiteLevel,
        "white_balance_cct": numberAttachment(pixelBuffer, kCVPixelBufferProResRAWKey_WhiteBalanceCCT)?.intValue as Any,
        "white_balance_red_factor": numberAttachment(pixelBuffer, kCVPixelBufferProResRAWKey_WhiteBalanceRedFactor)?.doubleValue as Any,
        "white_balance_blue_factor": numberAttachment(pixelBuffer, kCVPixelBufferProResRAWKey_WhiteBalanceBlueFactor)?.doubleValue as Any,
        "gain_factor": numberAttachment(pixelBuffer, kCVPixelBufferProResRAWKey_GainFactor)?.doubleValue as Any,
        "color_matrix_camera_rgb_to_xyz_d65": floatArrayAttachment(pixelBuffer, kCVPixelBufferProResRAWKey_ColorMatrix) as Any,
        "recommended_crop_lrtb": floatArrayAttachment(pixelBuffer, kCVPixelBufferProResRAWKey_RecommendedCrop) as Any,
        "minimum": minimum,
        "p001": percentile(histogram, sampleCount, 0.001),
        "p01": percentile(histogram, sampleCount, 0.01),
        "p50": percentile(histogram, sampleCount, 0.50),
        "p99": percentile(histogram, sampleCount, 0.99),
        "p999": percentile(histogram, sampleCount, 0.999),
        "p9999": percentile(histogram, sampleCount, 0.9999),
        "maximum": maximum,
        "samples_at_or_below_black": atOrBelowBlack,
        "samples_at_or_above_white": atOrAboveWhite,
        "fraction_at_or_above_white": Double(atOrAboveWhite) / Double(sampleCount),
    ]
    return metadata
}

let options = parseOptions()
do {
    try FileManager.default.createDirectory(
        at: options.outputDirectory, withIntermediateDirectories: true
    )
    let asset = AVURLAsset(url: options.input)
    let tracks = asset.tracks(withMediaType: .video)
    guard let track = tracks.first else {
        throw NSError(domain: "ProResRAWExtract", code: 3, userInfo: [
            NSLocalizedDescriptionKey: "no video track"
        ])
    }
    let reader = try AVAssetReader(asset: asset)
    let outputSettings: [String: Any] = [
        kCVPixelBufferPixelFormatTypeKey as String: Int(kCVPixelFormatType_16VersatileBayer)
    ]
    let output = AVAssetReaderTrackOutput(track: track, outputSettings: outputSettings)
    output.alwaysCopiesSampleData = false
    guard reader.canAdd(output) else {
        throw NSError(domain: "ProResRAWExtract", code: 4, userInfo: [
            NSLocalizedDescriptionKey: "AVAssetReader cannot provide bp16 output"
        ])
    }
    reader.add(output)
    guard reader.startReading() else {
        throw reader.error ?? NSError(domain: "ProResRAWExtract", code: 5)
    }

    var decodedIndex = 0
    var results: [[String: Any]] = []
    while let sample = output.copyNextSampleBuffer() {
        defer { CMSampleBufferInvalidate(sample) }
        if decodedIndex >= options.startFrame,
           decodedIndex < options.startFrame + options.frameCount,
           let pixelBuffer = CMSampleBufferGetImageBuffer(sample) {
            var metadata = try inspectAndOptionallyWrite(
                pixelBuffer,
                frameIndex: decodedIndex,
                outputDirectory: options.outputDirectory,
                writeRaw: options.writeRaw
            )
            metadata["presentation_time_seconds"] = CMTimeGetSeconds(CMSampleBufferGetPresentationTimeStamp(sample))
            results.append(metadata)
            let maximum = metadata["maximum"] ?? "?"
            let saturated = metadata["fraction_at_or_above_white"] ?? "?"
            print("decoded raw frame \(decodedIndex): max=\(maximum), saturated=\(saturated)")
        }
        decodedIndex += 1
        if decodedIndex >= options.startFrame + options.frameCount { break }
    }
    if reader.status == .failed {
        throw reader.error ?? NSError(domain: "ProResRAWExtract", code: 6)
    }

    let document: [String: Any] = [
        "input": options.input.path,
        "requested_start_frame": options.startFrame,
        "requested_frame_count": options.frameCount,
        "frames": results,
    ]
    let json = try JSONSerialization.data(withJSONObject: document, options: [.prettyPrinted, .sortedKeys])
    try json.write(to: options.outputDirectory.appendingPathComponent("raw_metadata.json"), options: .atomic)
} catch {
    fputs("prores_raw_extract: \(error)\n", stderr)
    exit(1)
}
