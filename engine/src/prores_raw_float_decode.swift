import AVFoundation
import CoreMedia
import CoreVideo
import Foundation

guard CommandLine.arguments.count == 4,
      let startFrame = Int(CommandLine.arguments[2]),
      let frameCount = Int(CommandLine.arguments[3]) else {
    fputs("usage: prores_raw_float_decode INPUT START_FRAME FRAME_COUNT\n", stderr)
    exit(2)
}

let asset = AVURLAsset(url: URL(fileURLWithPath: CommandLine.arguments[1]))
guard let track = asset.tracks(withMediaType: .video).first else {
    fputs("no video track\n", stderr)
    exit(1)
}

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
        fputs("extended-range RGBA float decode is unavailable\n", stderr)
        exit(1)
    }
    reader.add(output)
    guard reader.startReading() else { throw reader.error! }

    var decodedIndex = 0
    var emitted = 0
    while let sample = output.copyNextSampleBuffer() {
        defer { CMSampleBufferInvalidate(sample) }
        if decodedIndex >= startFrame,
           decodedIndex < startFrame + frameCount,
           let pixelBuffer = CMSampleBufferGetImageBuffer(sample) {
            let width = CVPixelBufferGetWidth(pixelBuffer)
            let height = CVPixelBufferGetHeight(pixelBuffer)
            let stride = CVPixelBufferGetBytesPerRow(pixelBuffer)
            if emitted == 0,
               let attachments = CVBufferCopyAttachments(pixelBuffer, .shouldPropagate) {
                fputs("pixel-buffer attachments: \(attachments)\n", stderr)
            }
            guard CVPixelBufferGetPixelFormatType(pixelBuffer) == kCVPixelFormatType_128RGBAFloat else {
                throw NSError(domain: "ProResRAWFloatDecode", code: 1)
            }
            CVPixelBufferLockBaseAddress(pixelBuffer, .readOnly)
            guard let base = CVPixelBufferGetBaseAddress(pixelBuffer) else { exit(1) }
            var rgbRow = [Float](repeating: 0, count: width * 3)
            for row in 0..<height {
                let rgba = base.advanced(by: row * stride).assumingMemoryBound(to: Float.self)
                for column in 0..<width {
                    rgbRow[column * 3] = rgba[column * 4]
                    rgbRow[column * 3 + 1] = rgba[column * 4 + 1]
                    rgbRow[column * 3 + 2] = rgba[column * 4 + 2]
                }
                rgbRow.withUnsafeBytes { bytes in
                    FileHandle.standardOutput.write(Data(bytes))
                }
            }
            CVPixelBufferUnlockBaseAddress(pixelBuffer, .readOnly)
            emitted += 1
            fputs("decoded extended-linear frame \(decodedIndex) (\(emitted)/\(frameCount))\n", stderr)
        }
        decodedIndex += 1
        if emitted >= frameCount { break }
    }
    if emitted != frameCount {
        throw reader.error ?? NSError(
            domain: "ProResRAWFloatDecode", code: 2,
            userInfo: [NSLocalizedDescriptionKey: "only emitted \(emitted) frames"]
        )
    }
} catch {
    fputs("prores_raw_float_decode: \(error)\n", stderr)
    exit(1)
}
