import AVFoundation
import CoreMedia
import CoreVideo
import Foundation

guard CommandLine.arguments.count == 3 else {
    fputs("usage: prores_raw_contact_decode INPUT FRAME[,FRAME...]\n", stderr)
    exit(2)
}

let requested = CommandLine.arguments[2]
    .split(separator: ",")
    .compactMap { Int($0) }
    .sorted()
guard !requested.isEmpty, requested.first! >= 0 else {
    fputs("no valid frame indices\n", stderr)
    exit(2)
}
let requestedSet = Set(requested)
let lastRequested = requested.last!
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
            kCVPixelBufferPixelFormatTypeKey as String:
                Int(kCVPixelFormatType_128RGBAFloat)
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
        if requestedSet.contains(decodedIndex),
           let pixelBuffer = CMSampleBufferGetImageBuffer(sample) {
            let width = CVPixelBufferGetWidth(pixelBuffer)
            let height = CVPixelBufferGetHeight(pixelBuffer)
            let stride = CVPixelBufferGetBytesPerRow(pixelBuffer)
            guard CVPixelBufferGetPixelFormatType(pixelBuffer)
                == kCVPixelFormatType_128RGBAFloat else {
                throw NSError(domain: "ProResRAWContactDecode", code: 1)
            }
            CVPixelBufferLockBaseAddress(pixelBuffer, .readOnly)
            guard let base = CVPixelBufferGetBaseAddress(pixelBuffer) else {
                exit(1)
            }
            var rgbRow = [Float](repeating: 0, count: width * 3)
            for row in 0..<height {
                let rgba = base.advanced(by: row * stride)
                    .assumingMemoryBound(to: Float.self)
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
            fputs("decoded contact frame \(decodedIndex)\n", stderr)
        }
        if decodedIndex >= lastRequested { break }
        decodedIndex += 1
    }
    if emitted != requested.count {
        throw reader.error ?? NSError(
            domain: "ProResRAWContactDecode",
            code: 2,
            userInfo: [
                NSLocalizedDescriptionKey:
                    "emitted \(emitted) of \(requested.count) requested frames"
            ]
        )
    }
} catch {
    fputs("prores_raw_contact_decode: \(error)\n", stderr)
    exit(1)
}
