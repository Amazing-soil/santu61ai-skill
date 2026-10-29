#!/usr/bin/env swift

import AppKit
import Foundation
import Vision

let paths = CommandLine.arguments.dropFirst().sorted()

for path in paths {
    autoreleasepool {
        guard let image = NSImage(contentsOfFile: path),
              let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil)
        else {
            fputs("warning: cannot load \(path)\n", stderr)
            return
        }

        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.usesLanguageCorrection = true
        request.recognitionLanguages = ["zh-Hans", "en-US"]

        do {
            try VNImageRequestHandler(cgImage: cgImage, options: [:]).perform([request])
            let lines = (request.results ?? []).compactMap { observation in
                observation.topCandidates(1).first?.string
            }
            print("--- \(URL(fileURLWithPath: path).lastPathComponent)")
            print(lines.joined(separator: "\n"))
        } catch {
            fputs("warning: OCR failed for \(path): \(error)\n", stderr)
        }
    }
}
