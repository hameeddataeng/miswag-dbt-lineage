"""Tests for lineage extractor."""
import json
from pathlib import Path
import pytest
from miswag_dbt_lineage.extractor import LineageExtractor


class TestLineageExtractor:
    """Test the LineageExtractor class."""

    def test_extractor_initialization(self):
        """Test that extractor can be initialized."""
        extractor = LineageExtractor(dialect="clickhouse")
        assert extractor.dialect == "clickhouse"

    def test_extractor_with_different_dialects(self):
        """Test extractor initialization with different SQL dialects."""
        dialects = ["postgres", "snowflake", "bigquery", "clickhouse"]
        for dialect in dialects:
            extractor = LineageExtractor(dialect=dialect)
            assert extractor.dialect == dialect

    def test_get_layer_from_path(self):
        """Test layer classification from model paths."""
        extractor = LineageExtractor()

        # Test staging layer
        assert extractor._get_layer_from_path("models/staging/stg_customers.sql") == "staging"

        # Test intermediate layer
        assert extractor._get_layer_from_path("models/intermediate/int_orders.sql") == "intermediate"

        # Test mart layer
        assert extractor._get_layer_from_path("models/marts/fct_sales.sql") == "mart"
        assert extractor._get_layer_from_path("models/marts/dim_products.sql") == "mart"

        # Test unknown layer
        assert extractor._get_layer_from_path("models/custom/my_model.sql") == "other"

    def test_classify_transformation(self):
        """Test transformation type classification."""
        extractor = LineageExtractor()

        # Test direct transformation
        assert extractor._classify_transformation("column_name", "table.column_name") == "DIRECT"

        # Test function transformation
        assert "FUNCTION" in extractor._classify_transformation(
            "upper_name", "UPPER(name)"
        )

        # Test case transformation
        assert "CASE" in extractor._classify_transformation(
            "status", "CASE WHEN active THEN 'Y' ELSE 'N' END"
        )

    def test_extract_with_empty_manifest(self):
        """Test extractor handles empty manifest gracefully."""
        extractor = LineageExtractor()

        # Create minimal empty manifest
        manifest = {
            "nodes": {},
            "sources": {},
            "metadata": {}
        }

        result = extractor.extract(manifest)

        assert "models" in result
        assert "sources" in result
        assert "columns" in result
        assert len(result["models"]) == 0
        assert len(result["sources"]) == 0
