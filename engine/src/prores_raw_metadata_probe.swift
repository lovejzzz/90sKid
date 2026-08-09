import AVFoundation
import CoreMedia
import CoreVideo
import Foundation

func copyDataAttachment(_ buffer: CVPixelBuffer, _ key: CFString) -> Data? {
    guard let value = CVBufferCopyAttachment(buffer, key, nil) else { return nil }
    return value as? Data
}

func littleEndianFloat32(_ data: Data) -> [Float] {
    data.withUnsafeBytes { bytes in
        stride(from: 0, to: data.count - 3, by: 4).map { offset in
            let bits = bytes.loadUnaligned(fromByteOffset: offset, as: UInt32.self)
            return Float(bitPattern: UInt32(littleEndian: bits))
        }
    }
}

func describeMetadataExtension(_ data: Data) -> String {
    let bytes = [UInt8](data)
    guard bytes.count >= 9 else { return "invalid" }
    let size = bytes[0...3].reduce(UInt32(0)) { ($0 << 8) | UInt32($1) }
    let fourcc = String(bytes: bytes[4...7], encoding: .ascii) ?? "?"
    let identifierLength = Int(bytes[8])
    guard bytes.count >= 9 + identifierLength else { return "invalid" }
    let identifier = String(
        bytes: bytes[9..<(9 + identifierLength)], encoding: .utf8
    ) ?? "?"
    let payload = Data(bytes.dropFirst(9 + identifierLength))
    return "size=\(size) fourcc=\(fourcc) identifier=\(identifier) payload=\(payload as NSData)"
}

guard CommandLine.arguments.count == 3,
      let requestedFrame = Int(CommandLine.arguments[2]) else {
    fputs("usage: prores_raw_metadata_probe INPUT FRAME\n", stderr)
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
            kCVPixelBufferPixelFormatTypeKey as String:
                Int(kCVPixelFormatType_16VersatileBayer)
        ]
    )
    output.alwaysCopiesSampleData = false
    guard reader.canAdd(output) else {
        throw NSError(
            domain: "ProResRAWMetadataProbe",
            code: 1,
            userInfo: [NSLocalizedDescriptionKey: "bp16 RAW output unavailable"]
        )
    }
    reader.add(output)
    guard reader.startReading() else { throw reader.error! }

    var frameIndex = 0
    var found = false
    while let sample = output.copyNextSampleBuffer() {
        defer { CMSampleBufferInvalidate(sample) }
        if frameIndex == requestedFrame,
           let pixelBuffer = CMSampleBufferGetImageBuffer(sample) {
            print("pixelFormat=\(CVPixelBufferGetPixelFormatType(pixelBuffer))")
            print("dimensions=\(CVPixelBufferGetWidth(pixelBuffer))x\(CVPixelBufferGetHeight(pixelBuffer))")
            if let attachments = CVBufferCopyAttachments(pixelBuffer, .shouldPropagate) {
                print("attachments=\(attachments)")
            }
            if let matrix = copyDataAttachment(pixelBuffer, kCVPixelBufferProResRAWKey_ColorMatrix) {
                print("colorMatrix=\(littleEndianFloat32(matrix))")
            }
            if let extensionData = copyDataAttachment(pixelBuffer, kCVPixelBufferProResRAWKey_MetadataExtension) {
                print("metadataExtension=\(describeMetadataExtension(extensionData))")
            }
            found = true
            break
        }
        frameIndex += 1
    }
    if !found {
        throw reader.error ?? NSError(
            domain: "ProResRAWMetadataProbe",
            code: 2,
            userInfo: [NSLocalizedDescriptionKey: "frame \(requestedFrame) unavailable"]
        )
    }
} catch {
    fputs("prores_raw_metadata_probe: \(error)\n", stderr)
    exit(1)
}
