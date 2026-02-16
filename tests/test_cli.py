"""Tests for CLI commands."""
import pytest
from typer.testing import CliRunner
from miswag_dbt_lineage.cli.main import app

runner = CliRunner()


class TestCLI:
    """Test CLI commands."""

    def test_version_command(self):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.stdout

    def test_help_command(self):
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "miswag-dbt-lineage" in result.stdout
        assert "generate" in result.stdout
        assert "build" in result.stdout

    def test_generate_help(self):
        """Test generate --help."""
        result = runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0
        assert "manifest" in result.stdout
        assert "catalog" in result.stdout
        assert "output" in result.stdout

    def test_build_help(self):
        """Test build --help."""
        result = runner.invoke(app, ["build", "--help"])
        assert result.exit_code == 0
        assert "project-dir" in result.stdout
        assert "output" in result.stdout

    def test_generate_missing_manifest(self):
        """Test generate fails gracefully with missing manifest."""
        result = runner.invoke(app, [
            "generate",
            "--manifest", "/nonexistent/manifest.json",
            "--output", "/tmp/test-lineage"
        ])
        # Should fail but not crash
        assert result.exit_code != 0

    def test_generate_invalid_dialect(self):
        """Test generate handles invalid dialect."""
        result = runner.invoke(app, [
            "generate",
            "--manifest", "/tmp/test-manifest.json",
            "--dialect", "invalid_dialect_name",
            "--output", "/tmp/test-lineage"
        ])
        # Should fail or warn, but not crash
        assert result.exit_code != 0 or "warning" in result.stdout.lower()
