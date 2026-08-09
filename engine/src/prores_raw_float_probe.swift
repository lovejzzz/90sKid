import AVFoundation
import CoreMedia
import CoreVideo
import Foundation

guard CommandLine.arguments.count == 3, let requestedFrame = Int(CommandLine.arguments[2]) else {
    fputs("usage: prores_raw_float_probe INPUT FRAME_INDEX\n", stderr)
    exit(2)
}

let asset = AVURLAsset(url: URL(fileURLWithPath: CommandLine.arguments[1]))
guard let track = asset.tracks(withMediaType: .video).first else { exit(1) }

do {
    let reader = try AVAssetReader(asset: asset)
    let output = AVAssetReaderTrackOutput(
        track: track,
        outputSettings: [
            kCVPixelBufferPixelFormatTypeKey as String: Int(kCVPixelFormatType_128RGBAFloat)
        ]
    )
    output.alwaysCopiesSampleData = false
    guard reader.canAdd(output) else {
        fputs("RGBA float output is not supported\n", stderr)
        exit(1)
    }
    reader.add(output)
    guard reader.startReading() else { throw reader.error! }

    var frame = 0
    while let sample = output.copyNextSampleBuffer() {
        if frame == requestedFrame, let pixelBuffer = CMSampleBufferGetImageBuffer(sample) {
            let width = CVPixelBufferGetWidth(pixelBuffer)
            let height = CVPixelBufferGetHeight(pixelBuffer)
            let stride = CVPixelBufferGetBytesPerRow(pixelBuffer)
            CVPixelBufferLockBaseAddress(pixelBuffer, .readOnly)
            defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, .readOnly) }
            guard let base = CVPixelBufferGetBaseAddress(pixelBuffer) else { exit(1) }
            var minima = [Float](repeating: .greatestFiniteMagnitude, count: 4)
            var maxima = [Float](repeating: -.greatestFiniteMagnitude, count: 4)
            var aboveOne = [UInt64](repeating: 0, count: 4)
            for row in 0..<height {
                let values = base.advanced(by: row * stride).assumingMemoryBound(to: Float.self)
                for column in 0..<width {
                    for channel in 0..<4 {
                        let value = values[column * 4 + channel]
                        minima[channel] = min(minima[channel], value)
                        maxima[channel] = max(maxima[channel], value)
                        if value > 1 { aboveOne[channel] += 1 }
                    }
                }
            }
            let fraction = aboveOne.map { Double($0) / Double(width * height) }
            print("format=\(CVPixelBufferGetPixelFormatType(pixelBuffer)) size=\(width)x\(height) stride=\(stride)")
            print("minima=\(minima)")
            print("maxima=\(maxima)")
            print("fraction_above_one=\(fraction)")
            print("attachments=\(String(describing: CVBufferCopyAttachments(pixelBuffer, .shouldPropagate)))")
            exit(0)
        }
        frame += 1
    }
    throw reader.error ?? NSError(domain: "ProResRAWFloatProbe", code: 1)
} catch {
    fputs("prores_raw_float_probe: \(error)\n", stderr)
    exit(1)
}
