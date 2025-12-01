# CHANGELOG

<!-- version list -->

## v3.0.0 (2025-12-01)

### Refactoring

- **core**: Remove engine-specific HOCR conversion from core utils
  ([`3fb2ca0`](https://github.com/OCRBridge/ocrbridge-core/commit/3fb2ca03f5e6c647611c6d3ceb8d3ed975fc3c5d))

### Breaking Changes

- **core**: `easyocr_to_hocr()` function removed from `ocrbridge.core.utils.hocr`. Users must
  migrate to engine-specific packages for HOCR conversion functionality.


## v2.0.0 (2025-11-29)

### Documentation

- Remove version section from README
  ([`a86486e`](https://github.com/OCRBridge/ocrbridge-core/commit/a86486edbc4cd0a2f7c464819d7a0da239a5fb30))

### Features

- Add comprehensive parameter validation utilities
  ([`a7c575a`](https://github.com/OCRBridge/ocrbridge-core/commit/a7c575a665ed628cb3a390bde0f3621240b6b223))

### Breaking Changes

- Expanded public API with new validation module exports. The version has been bumped from 1.0.0 to
  2.0.0 to reflect the significant API surface expansion.


## v1.0.0 (2025-11-24)

- Initial Release

## v1.0.0 (2025-11-24)

- Initial Release

## v1.0.0 (2025-11-23)

- Initial Release
