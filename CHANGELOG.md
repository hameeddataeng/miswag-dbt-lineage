# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2024-02-16

### Added
- **Embedded data mode**: JSON data is now embedded directly into the HTML file
- Support for `file://` protocol - the generated website works without an HTTP server
- Single self-contained HTML file that can be shared via email/Slack and opened locally

### Changed
- Generator now embeds lineage data into `index.html` for offline/local usage
- Template updated to check for embedded data before falling back to fetch()
- Improved deployment instructions with direct file opening option

### Fixed
- Browser security restrictions preventing fetch() on `file://` protocol
- Removed unused `shutil` import from generator module

## [0.1.1] - 2024-02-16

### Changed
- **Default output directory**: Changed from `lineage-site` to `target/lineage_website` to follow dbt conventions
- CLI now places generated files in the `target/` directory alongside other dbt artifacts
- Updated all documentation examples and deployment instructions

### Fixed
- Updated GitHub repository URLs to reflect correct organization (hameeddataeng)
- Added PyPI link to documentation

## [0.1.0] - 2024-02-16

### Added
- Initial release of miswag-dbt-lineage
- Column-level lineage extraction from dbt artifacts
- Table-level lineage visualization
- Static site generator for interactive lineage portal
- CLI with `generate` and `build` commands
- Support for multiple SQL dialects (ClickHouse, Postgres, Snowflake, BigQuery, etc.)
- Layer-based model classification (staging, intermediate, mart)
- Transformation type detection (DIRECT, FUNCTION, CASE, AGG, CALC)
- Interactive web UI with pan/zoom capabilities
- Dark theme with color-coded layers
- Search and filter capabilities
- Comprehensive test suite
- GitHub Actions CI/CD workflows
- Documentation and examples

[Unreleased]: https://github.com/hameeddataeng/miswag-dbt-lineage/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/hameeddataeng/miswag-dbt-lineage/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/hameeddataeng/miswag-dbt-lineage/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/hameeddataeng/miswag-dbt-lineage/releases/tag/v0.1.0
