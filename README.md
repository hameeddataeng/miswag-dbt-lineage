# miswag-dbt-lineage

> 🔍 Generate beautiful, interactive **column-level lineage** for your dbt projects

[![PyPI version](https://badge.fury.io/py/miswag-dbt-lineage.svg)](https://pypi.org/project/miswag-dbt-lineage/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**miswag-dbt-lineage** is a lightweight, dbt-native tool that generates a **static website** with interactive column-level lineage visualization. No backend, no servers—just beautiful, deployable lineage documentation.

![Lineage Portal Screenshot](https://via.placeholder.com/800x400?text=Lineage+Portal+Screenshot)

## ✨ Features

- 🔗 **Column-level lineage** — trace data flow through transformations
- 📊 **Table-level lineage** — visualize model dependencies
- 🎨 **Interactive visualization** — pan, zoom, and explore your data pipelines
- 🚀 **Static output** — deploy to S3, GCS, GitHub Pages, or any static host
- 🎯 **dbt-native** — works with your existing dbt artifacts (no code changes needed)
- ⚡ **Fast** — handles 1000+ models and 10,000+ columns
- 🌈 **Beautiful UI** — dark theme, color-coded layers, transformation indicators

## 🎯 What It Does

1. **Reads** your dbt artifacts (`manifest.json`, `catalog.json`)
2. **Extracts** column-level lineage using SQL parsing (powered by sqlglot)
3. **Generates** a static website with an interactive lineage explorer
4. **Deploys** anywhere — S3, GCS, Azure Blob, GitHub Pages, etc.

## 📦 Installation

```bash
pip install miswag-dbt-lineage
```

Or install from source:

```bash
git clone https://github.com/hameeddataeng/miswag-dbt-lineage.git
cd miswag-dbt-lineage
pip install -e .
```

## 🚀 Quick Start

### Basic Usage

```bash
# Navigate to your dbt project
cd my-dbt-project

# Generate lineage site (output defaults to target/lineage_website)
miswag-dbt-lineage generate \
  --manifest target/manifest.json \
  --catalog target/catalog.json
```

### All-in-One Build

```bash
# Runs 'dbt docs generate' + generates lineage site (output defaults to target/lineage_website)
miswag-dbt-lineage build
```

### View Locally

```bash
cd target/lineage_website
python -m http.server 8080
# Open http://localhost:8080
```

## 📚 Usage

### Commands

#### `generate` — Generate lineage site from artifacts

```bash
miswag-dbt-lineage generate [OPTIONS]
```

**Options:**
- `--manifest, -m PATH` — Path to manifest.json (default: `target/manifest.json`)
- `--catalog, -c PATH` — Path to catalog.json (optional but recommended)
- `--output, -o PATH` — Output directory (default: `target/lineage_website`)
- `--dialect, -d TEXT` — SQL dialect: `clickhouse`, `postgres`, `snowflake`, `bigquery`, etc. (default: `clickhouse`)
- `--verbose` — Enable verbose logging
- `--help` — Show help

**Example:**
```bash
miswag-dbt-lineage generate \
  --manifest target/manifest.json \
  --catalog target/catalog.json \
  --output docs/lineage \
  --dialect snowflake
```

---

#### `build` — Build lineage (runs dbt docs + generate)

```bash
miswag-dbt-lineage build [OPTIONS]
```

**Options:**
- `--project-dir, -p PATH` — dbt project directory (default: `.`)
- `--output, -o PATH` — Output directory (default: `target/lineage_website`)
- `--skip-dbt-docs` — Skip running `dbt docs generate`
- `--dialect, -d TEXT` — SQL dialect (default: `clickhouse`)
- `--help` — Show help

**Example:**
```bash
miswag-dbt-lineage build --dialect postgres
```

---

### Supported SQL Dialects

- `clickhouse` (default)
- `postgres`
- `snowflake`
- `bigquery`
- `redshift`
- `databricks`
- `mysql`
- `tsql` (SQL Server)
- And more — [see sqlglot docs](https://github.com/tobymao/sqlglot)

---

## 🌐 Deployment

The generated site is a **fully static** collection of HTML/CSS/JS files. Deploy it anywhere:

### AWS S3

```bash
aws s3 sync target/lineage_website s3://my-bucket/lineage-docs/
aws s3 website s3://my-bucket --index-document index.html
```

### Google Cloud Storage

```bash
gsutil -m rsync -r target/lineage_website gs://my-bucket/lineage-docs/
gsutil web set -m index.html gs://my-bucket
```

### Azure Blob Storage

```bash
az storage blob upload-batch \
  --account-name mystorageaccount \
  --destination '$web' \
  --source target/lineage_website
```

### GitHub Pages

```bash
# Push to gh-pages branch
cd target/lineage_website
git init
git checkout -b gh-pages
git add .
git commit -m "Deploy lineage site"
git remote add origin https://github.com/your-org/your-repo.git
git push -f origin gh-pages
```

---

## 🎨 Features Walkthrough

### Table Lineage

- ✅ Visualize upstream & downstream model dependencies
- ✅ Color-coded layers (source, staging, intermediate, mart, seed)
- ✅ Click any model to see its lineage
- ✅ Inline model metadata (layer, materialization, columns, tests, deps)
- ✅ Adjustable depth (1-5 levels)

### Column Lineage

- ✅ Trace column-to-column data flow
- ✅ Transformation type indicators (DIRECT, RENAMED, FUNCTION, CASE, AGG, CALC)
- ✅ Color-coded edges for transformation types
- ✅ Inline column metadata (name, type, model, transformation SQL)
- ✅ Click any column to pivot to its lineage
- ✅ Adjustable depth (1-5 levels)

### Catalog Views

- ✅ **Models** — browse all models with metadata
- ✅ **Sources** — view all data sources
- ✅ **Tests** — see all data quality tests
- ✅ Search and filter by layer, directory, etc.

---

## 🛠️ How It Works

### Architecture

```
dbt artifacts → SQL parsing → Lineage graph → Static website
    ↓               ↓              ↓               ↓
manifest.json   sqlglot      lineage.json    index.html
catalog.json                                  + data/
```

### Lineage Resolution

1. **Read dbt artifacts** — Parse `manifest.json` and `catalog.json`
2. **Extract dependencies** — Identify model → model relationships
3. **Parse compiled SQL** — Use sqlglot to analyze SELECT statements
4. **Resolve columns** — Match columns across CTEs, aliases, and transformations
5. **Classify transformations** — Detect aggregations, functions, CASE expressions, etc.
6. **Generate graph** — Build node/edge graph with metadata
7. **Create static site** — Bundle HTML + JSON for deployment

---

## 📖 Configuration

### Layer Classification

By default, models are classified into layers based on naming conventions:

- **source**: `source.*`
- **staging**: `.stg_`, `staging`
- **intermediate**: `.int_`, `intermediate`
- **mart**: `.mart`, `.fct_`, `.dim_`, `marts`
- **seed**: `seed.*`

You can customize this in the extractor code (`miswag_dbt_lineage/extractor.py`).

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone repo
git clone https://github.com/hameeddataeng/miswag-dbt-lineage.git
cd miswag-dbt-lineage

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
ruff check .
```

---

## 📝 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built for the dbt community
- Powered by [sqlglot](https://github.com/tobymao/sqlglot) for SQL parsing
- Inspired by dbt docs and various lineage visualization tools

---

## 📧 Contact

- **Author**: Hameed Mahmood
- **GitHub**: [hameeddataeng/miswag-dbt-lineage](https://github.com/hameeddataeng/miswag-dbt-lineage)
- **PyPI**: [miswag-dbt-lineage](https://pypi.org/project/miswag-dbt-lineage/)
- **Issues**: [Report a bug](https://github.com/hameeddataeng/miswag-dbt-lineage/issues)

---

**⭐ If you find this useful, please star the repo!**
