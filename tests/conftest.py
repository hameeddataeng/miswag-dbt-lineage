"""Pytest configuration and fixtures."""
import json
import pytest
from pathlib import Path
import tempfile


@pytest.fixture
def sample_manifest():
    """Create a sample dbt manifest for testing."""
    return {
        "metadata": {
            "dbt_version": "1.7.0",
            "generated_at": "2024-01-01T00:00:00.000000Z"
        },
        "nodes": {
            "model.project.stg_customers": {
                "unique_id": "model.project.stg_customers",
                "name": "stg_customers",
                "resource_type": "model",
                "package_name": "project",
                "path": "staging/stg_customers.sql",
                "original_file_path": "models/staging/stg_customers.sql",
                "compiled_code": "SELECT id, name FROM source_customers",
                "depends_on": {
                    "nodes": ["source.project.raw.customers"]
                },
                "config": {
                    "materialized": "view"
                },
                "columns": {
                    "id": {"name": "id", "description": "Customer ID"},
                    "name": {"name": "name", "description": "Customer name"}
                }
            }
        },
        "sources": {
            "source.project.raw.customers": {
                "unique_id": "source.project.raw.customers",
                "name": "customers",
                "source_name": "raw",
                "resource_type": "source",
                "schema": "raw",
                "identifier": "customers",
                "columns": {
                    "id": {"name": "id"},
                    "name": {"name": "name"}
                }
            }
        }
    }


@pytest.fixture
def sample_catalog():
    """Create a sample dbt catalog for testing."""
    return {
        "nodes": {
            "model.project.stg_customers": {
                "unique_id": "model.project.stg_customers",
                "columns": {
                    "id": {"type": "INTEGER", "index": 1},
                    "name": {"type": "VARCHAR", "index": 2}
                }
            }
        },
        "sources": {
            "source.project.raw.customers": {
                "unique_id": "source.project.raw.customers",
                "columns": {
                    "id": {"type": "INTEGER", "index": 1},
                    "name": {"type": "VARCHAR", "index": 2}
                }
            }
        }
    }


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
