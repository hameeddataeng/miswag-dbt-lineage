"""
miswag-dbt-lineage: Generate beautiful, interactive column-level lineage for dbt projects
"""

__version__ = "0.1.2"
__author__ = "Miswag Hameed"
__license__ = "Apache-2.0"

from miswag_dbt_lineage.extractor import extract_all_metadata
from miswag_dbt_lineage.generator import generate_site

__all__ = ["extract_all_metadata", "generate_site", "__version__"]
