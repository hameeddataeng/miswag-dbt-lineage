"""Tests for static site generator."""
import json
from pathlib import Path
import pytest
import tempfile
import shutil
from miswag_dbt_lineage.generator import StaticSiteGenerator


class TestStaticSiteGenerator:
    """Test the StaticSiteGenerator class."""

    def test_generator_initialization(self):
        """Test that generator can be initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = StaticSiteGenerator(output_dir=tmpdir)
            assert generator.output_dir == Path(tmpdir)

    def test_generate_creates_directories(self):
        """Test that generate creates required directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = StaticSiteGenerator(output_dir=tmpdir)

            # Create minimal lineage data
            lineage_data = {
                "models": [],
                "sources": [],
                "columns": [],
                "table_lineage": [],
                "column_lineage": []
            }

            generator.generate(lineage_data)

            # Check directories were created
            output_path = Path(tmpdir)
            assert (output_path / "data").exists()
            assert (output_path / "index.html").exists()
            assert (output_path / "data" / "lineage.json").exists()

    def test_generate_writes_lineage_json(self):
        """Test that lineage data is written correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = StaticSiteGenerator(output_dir=tmpdir)

            lineage_data = {
                "models": [{"id": "model1", "name": "test_model"}],
                "sources": [],
                "columns": [],
                "table_lineage": [],
                "column_lineage": []
            }

            generator.generate(lineage_data)

            # Read and verify the JSON
            json_path = Path(tmpdir) / "data" / "lineage.json"
            with open(json_path) as f:
                written_data = json.load(f)

            assert written_data["models"][0]["id"] == "model1"
            assert written_data["models"][0]["name"] == "test_model"

    def test_generate_copies_template(self):
        """Test that HTML template is copied."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = StaticSiteGenerator(output_dir=tmpdir)

            lineage_data = {
                "models": [],
                "sources": [],
                "columns": [],
                "table_lineage": [],
                "column_lineage": []
            }

            generator.generate(lineage_data)

            # Check HTML file exists and has content
            html_path = Path(tmpdir) / "index.html"
            assert html_path.exists()

            content = html_path.read_text()
            assert len(content) > 0
            assert "lineage" in content.lower()
