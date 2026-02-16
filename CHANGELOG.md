# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/miswag/miswag-dbt-lineage/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/miswag/miswag-dbt-lineage/releases/tag/v0.1.0
