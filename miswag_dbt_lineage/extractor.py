#!/usr/bin/env python3
"""
dbt Documentation & Column-Level Lineage Extractor (v2)
========================================================
Comprehensive extractor that parses manifest.json + catalog.json to build
a complete dbt documentation portal with column-level lineage.

Extracts:
- Models, sources, seeds, tests, macros, exposures, metrics
- Column-level lineage with transformation expressions
- Table-level lineage (model dependencies)
- Full metadata for documentation

Usage:
    python extract_lineage.py \
        --manifest target/manifest.json \
        --catalog target/catalog.json \
        --output lineage-site/data/lineage.json \
        --dialect clickhouse \
        --verbose
"""

import argparse
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import sqlglot
from sqlglot import exp
from sqlglot.lineage import lineage as sqlglot_lineage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LAYER_PATTERNS = {
    "source": [r"^source\."],
    "staging": [r"\.stg_", r"^staging"],
    "intermediate": [r"\.int_", r"^intermediate"],
    "mart": [r"\.mart", r"\.fct_", r"\.dim_", r"^marts"],
    "seed": [r"^seed\."],
}

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def classify_layer(unique_id: str, fqn: list = None) -> str:
    """Classify a dbt node into a data layer."""
    search_str = unique_id
    if fqn:
        search_str += " " + ".".join(fqn)

    for layer, patterns in LAYER_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, search_str, re.IGNORECASE):
                return layer
    return "other"


def extract_directory_from_path(path: str, fqn: list) -> str:
    """Extract directory grouping from model path/fqn."""
    if not fqn or len(fqn) < 3:
        return ""

    # fqn format: [project_name, directory1, directory2, ..., model_name]
    # We want everything between project_name and model_name
    directory_parts = fqn[1:-1]  # Skip first (project) and last (model name)

    if directory_parts:
        return "/".join(directory_parts)
    return ""


def safe_parse_sql(sql: str, dialect: str) -> Optional[exp.Expression]:
    """Safely parse SQL, return None on failure."""
    try:
        return sqlglot.parse_one(sql, read=dialect)
    except Exception as e:
        logger.debug(f"SQL parse error: {e}")
        return None


def extract_column_definition(sql: str, column_name: str, dialect: str) -> tuple[str, bool, str, list]:
    """
    Extract the SQL definition/transformation for a specific column.
    Returns (definition_sql, is_transformed, transformation_type, source_columns).
    """
    parsed = safe_parse_sql(sql, dialect)
    if not parsed:
        return ("", False, "unknown", [])

    select = parsed.find(exp.Select)
    if not select:
        return ("", False, "unknown", [])

    for expr in select.expressions:
        alias = expr.alias
        col_name = alias if alias else (expr.name if isinstance(expr, exp.Column) else "")

        if col_name and col_name.lower() == column_name.lower():
            # Found the column - extract its expression
            if isinstance(expr, exp.Alias):
                # Get the actual expression (not the alias)
                definition = expr.this.sql(dialect=dialect)
                trans_type = classify_transformation(expr)
            else:
                definition = expr.sql(dialect=dialect)
                trans_type = classify_transformation(expr)

            # Determine if it's transformed
            is_transformed = trans_type not in ("direct", "renamed")

            # Extract source column names
            source_cols = extract_column_sources_from_expression(expr)
            source_col_names = [col_name for _, col_name in source_cols]

            return (definition, is_transformed, trans_type, source_col_names)

    return ("", False, "unknown", [])


def get_column_schema(unique_id: str, catalog: dict, manifest: dict) -> dict:
    """Get column schema from catalog or manifest."""
    columns = {}

    # Try catalog first (has actual warehouse types)
    if catalog:
        cat_node = catalog.get("nodes", {}).get(unique_id) or \
                   catalog.get("sources", {}).get(unique_id, {})
        for col_name, col_info in cat_node.get("columns", {}).items():
            columns[col_name.lower()] = col_info.get("type", "unknown")

    # Fallback to manifest
    if not columns:
        node = manifest.get("nodes", {}).get(unique_id) or \
               manifest.get("sources", {}).get(unique_id, {})
        for col_name, col_info in node.get("columns", {}).items():
            columns[col_name.lower()] = col_info.get("data_type", "unknown")

    return columns


def build_schema_mapping(manifest: dict, catalog: dict) -> dict:
    """Build flat schema mapping for sqlglot."""
    schema = {}

    for collection in ["nodes", "sources"]:
        for unique_id, node in manifest.get(collection, {}).items():
            resource_type = node.get("resource_type", "")
            if resource_type not in ("model", "seed", "snapshot", "source"):
                continue

            name = node.get("alias") or node.get("name", "")
            columns = get_column_schema(unique_id, catalog, manifest)

            if columns:
                schema[name] = columns

    return schema


def extract_column_sources_from_expression(expression: exp.Expression) -> list:
    """
    Walk an AST expression and find all Column references.
    Returns list of (table_alias, column_name) tuples.
    """
    sources = []
    for col in expression.find_all(exp.Column):
        table = col.table or ""  # alias like 'wc', 'si', 'sr' or empty for unqualified
        name = col.name    # column name
        if name:
            sources.append((table, name.lower()))
    return sources


def build_alias_map(ast: exp.Expression) -> dict:
    """
    Build {alias: table_name} from FROM and JOIN clauses.
    Returns mapping of table aliases to actual table/CTE names.
    """
    alias_map = {}

    # Find all table references in FROM and JOIN clauses
    for table_ref in ast.find_all(exp.Table):
        table_name = table_ref.name
        table_alias = table_ref.alias

        # Use alias if present, otherwise use table name as its own alias
        key = table_alias if table_alias else table_name
        alias_map[key] = table_name

    return alias_map


def classify_transformation(expression: exp.Expression) -> str:
    """Classify how a column is transformed."""
    # Direct passthrough: just a column reference
    if isinstance(expression, exp.Column):
        return "direct"

    # Unwrap Alias to get the actual expression
    expr_to_check = expression
    if isinstance(expression, exp.Alias):
        expr_to_check = expression.this
        # Check if it's just a renamed column
        if isinstance(expr_to_check, exp.Column):
            if expression.alias != expr_to_check.name:
                return "renamed"
            return "direct"

    # Check for aggregation functions
    agg_funcs = list(expr_to_check.find_all(exp.AggFunc))
    if agg_funcs:
        return "aggregated"

    # Check for CASE WHEN
    if expr_to_check.find(exp.Case):
        return "case_expression"

    # Check for any function call (non-aggregate)
    funcs = list(expr_to_check.find_all(exp.Func))
    # Filter out aggregate functions we already checked
    non_agg_funcs = [f for f in funcs if not isinstance(f, exp.AggFunc)]
    if non_agg_funcs:
        return "function"

    # Check for arithmetic/binary operations
    if expr_to_check.find(exp.Binary):
        return "calculated"

    # Default to transformed
    return "transformed"


def resolve_ctes(ast: exp.Expression, dialect: str) -> dict:
    """
    Parse CTEs and return {cte_name: {output_col: [(source_table, source_col), ...]}}
    This builds a mapping of CTE columns to their source columns.
    """
    cte_lineage = {}

    # Find all CTEs
    ctes = list(ast.find_all(exp.CTE))

    for cte in ctes:
        cte_name = cte.alias
        cte_query = cte.this

        # Get the SELECT from the CTE
        select = cte_query.find(exp.Select)
        if not select:
            continue

        # Build alias map for this CTE's FROM/JOIN clauses
        cte_alias_map = build_alias_map(cte_query)

        # Extract each output column from the CTE's SELECT
        col_mapping = {}
        for expr in select.expressions:
            # Get output column name
            if isinstance(expr, exp.Alias):
                out_col = expr.alias.lower()
                source_expr = expr.this
            elif isinstance(expr, exp.Column):
                out_col = expr.name.lower()
                source_expr = expr
            elif isinstance(expr, exp.Star):
                # Handle SELECT * - we'll need to resolve this later
                continue
            else:
                # For complex expressions without alias, try to get a name
                out_col = expr.sql(dialect=dialect)[:50].lower()  # Use truncated SQL as name
                source_expr = expr

            # Extract source columns from this expression
            sources = extract_column_sources_from_expression(source_expr)

            # Resolve table aliases in sources
            resolved_sources = []
            for table_alias, col_name in sources:
                # Resolve the table alias to actual table/CTE name
                actual_table = cte_alias_map.get(table_alias, table_alias)
                resolved_sources.append((actual_table, col_name))

            col_mapping[out_col] = resolved_sources

        cte_lineage[cte_name] = col_mapping

    return cte_lineage


def trace_through_ctes(table_name: str, column_name: str, cte_lineage: dict, visited: set = None) -> list:
    """
    Recursively trace a column through CTEs to find the ultimate source tables/columns.
    Returns list of (table_name, column_name) tuples.
    """
    if visited is None:
        visited = set()

    # Prevent infinite recursion
    key = (table_name, column_name)
    if key in visited:
        return []
    visited.add(key)

    # Check if this table is a CTE
    if table_name not in cte_lineage:
        # Not a CTE - this is a base table
        return [(table_name, column_name)]

    # It's a CTE - get its source columns
    cte_cols = cte_lineage[table_name]
    if column_name not in cte_cols:
        # Column not found in CTE mapping
        return [(table_name, column_name)]

    # Recursively trace through source columns
    result = []
    for src_table, src_col in cte_cols[column_name]:
        traced = trace_through_ctes(src_table, src_col, cte_lineage, visited)
        result.extend(traced)

    return result if result else [(table_name, column_name)]


# ---------------------------------------------------------------------------
# Main Extraction Logic
# ---------------------------------------------------------------------------

def extract_all_metadata(
    manifest_path: str,
    catalog_path: str,
    dialect: str = "clickhouse",
    commit_sha: str = "local",
) -> dict:
    """
    Extract complete dbt metadata including models, sources, tests, macros, etc.
    Returns comprehensive JSON structure for documentation portal.
    """

    logger.info(f"Loading manifest from {manifest_path}")
    with open(manifest_path) as f:
        manifest = json.load(f)

    catalog = {}
    if catalog_path and Path(catalog_path).exists():
        logger.info(f"Loading catalog from {catalog_path}")
        with open(catalog_path) as f:
            catalog = json.load(f)

    # Build schema mapping for lineage
    schema_map = build_schema_mapping(manifest, catalog)
    logger.info(f"Built schema mapping for {len(schema_map)} tables")

    # Containers for output
    models = []
    sources = []
    seeds = []
    tests = []
    macros = []
    exposures = []
    metrics = []
    table_edges = []
    column_edges = []
    errors = []

    # Extract models
    logger.info("Extracting models...")
    model_nodes = {
        uid: node for uid, node in manifest.get("nodes", {}).items()
        if node.get("resource_type") == "model"
    }

    for uid, node in model_nodes.items():
        try:
            model_data = extract_model(uid, node, manifest, catalog, schema_map, dialect, column_edges, errors)
            models.append(model_data)

            # Extract table-level dependencies
            for dep_uid in node.get("depends_on", {}).get("nodes", []):
                table_edges.append({"source": dep_uid, "target": uid})

        except Exception as e:
            logger.error(f"Error extracting model {uid}: {e}")
            errors.append({"type": "model_extraction", "unique_id": uid, "error": str(e)})

    # Extract sources
    logger.info("Extracting sources...")
    for uid, source_node in manifest.get("sources", {}).items():
        try:
            source_data = extract_source(uid, source_node, catalog)
            sources.append(source_data)
        except Exception as e:
            logger.error(f"Error extracting source {uid}: {e}")
            errors.append({"type": "source_extraction", "unique_id": uid, "error": str(e)})

    # Extract seeds
    logger.info("Extracting seeds...")
    seed_nodes = {
        uid: node for uid, node in manifest.get("nodes", {}).items()
        if node.get("resource_type") == "seed"
    }

    for uid, seed_node in seed_nodes.items():
        try:
            seed_data = extract_seed(uid, seed_node, catalog)
            seeds.append(seed_data)
        except Exception as e:
            logger.error(f"Error extracting seed {uid}: {e}")

    # Extract tests
    logger.info("Extracting tests...")
    test_nodes = {
        uid: node for uid, node in manifest.get("nodes", {}).items()
        if node.get("resource_type") == "test"
    }

    for uid, test_node in test_nodes.items():
        try:
            test_data = extract_test(uid, test_node)
            tests.append(test_data)
        except Exception as e:
            logger.debug(f"Error extracting test {uid}: {e}")

    # Extract macros
    logger.info("Extracting macros...")
    for uid, macro_node in manifest.get("macros", {}).items():
        try:
            macro_data = extract_macro(uid, macro_node)
            macros.append(macro_data)
        except Exception as e:
            logger.debug(f"Error extracting macro {uid}: {e}")

    # Extract exposures
    for uid, exp_node in manifest.get("exposures", {}).items():
        try:
            exposure_data = extract_exposure(uid, exp_node)
            exposures.append(exposure_data)
        except Exception as e:
            logger.debug(f"Error extracting exposure {uid}: {e}")

    # Extract metrics
    for uid, metric_node in manifest.get("metrics", {}).items():
        try:
            metric_data = extract_metric(uid, metric_node)
            metrics.append(metric_data)
        except Exception as e:
            logger.debug(f"Error extracting metric {uid}: {e}")

    # Build final output
    result = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "commit_sha": commit_sha,
            "dbt_project": manifest.get("metadata", {}).get("project_name", "unknown"),
            "dbt_version": manifest.get("metadata", {}).get("dbt_version", "unknown"),
            "dialect": dialect,
            "stats": {
                "models": len(models),
                "sources": len(sources),
                "seeds": len(seeds),
                "tests": len(tests),
                "macros": len(macros),
                "exposures": len(exposures),
                "metrics": len(metrics),
                "columns": sum(len(m.get("columns", [])) for m in models),
                "table_edges": len(table_edges),
                "column_edges": len(column_edges),
                "errors": len(errors),
            }
        },
        "models": models,
        "sources": sources,
        "seeds": seeds,
        "tests": tests,
        "macros": macros,
        "exposures": exposures,
        "metrics": metrics,
        "table_edges": table_edges,
        "column_edges": column_edges,
        "errors": errors,
    }

    logger.info(f"✓ Extracted {len(models)} models, {len(sources)} sources, {len(column_edges)} column edges")

    return result


def extract_model(uid, node, manifest, catalog, schema_map, dialect, column_edges, errors):
    """Extract complete model metadata."""
    name = node.get("alias") or node.get("name", "")
    fqn = node.get("fqn", [])
    layer = classify_layer(uid, fqn)
    directory = extract_directory_from_path(node.get("path", ""), fqn)

    # Get SQL
    raw_code = node.get("raw_code", "") or node.get("raw_sql", "")
    compiled_code = node.get("compiled_code", "") or node.get("compiled_sql", "")

    # Get stats from catalog
    stats = {"row_count": None, "bytes": None}
    if catalog:
        cat_node = catalog.get("nodes", {}).get(uid, {})
        stats_data = cat_node.get("stats", {})
        stats["row_count"] = stats_data.get("row_count", {}).get("value")
        stats["bytes"] = stats_data.get("bytes", {}).get("value")

    # Get columns
    columns_list = []
    manifest_columns = node.get("columns", {})
    catalog_columns = catalog.get("nodes", {}).get(uid, {}).get("columns", {}) if catalog else {}

    # Get all column names (from compiled SQL or catalog)
    column_names = set()
    if compiled_code:
        parsed = safe_parse_sql(compiled_code, dialect)
        if parsed:
            select = parsed.find(exp.Select)
            if select:
                for expr in select.expressions:
                    if isinstance(expr, exp.Star):
                        # Resolve SELECT *
                        col_schema = get_column_schema(uid, catalog, manifest)
                        column_names.update(col_schema.keys())
                    else:
                        alias = expr.alias if expr.alias else (expr.name if isinstance(expr, exp.Column) else "")
                        if alias:
                            column_names.add(alias.lower())

    # Add columns from manifest/catalog
    column_names.update(k.lower() for k in manifest_columns.keys())
    column_names.update(k.lower() for k in catalog_columns.keys())

    # Build column list
    for col_name in sorted(column_names):
        col_meta = manifest_columns.get(col_name, {})
        cat_col = catalog_columns.get(col_name, catalog_columns.get(col_name.upper(), {}))

        data_type = cat_col.get("type") or col_meta.get("data_type", "unknown")

        # Extract column definition
        definition, is_transformed, transformation_type, source_columns = "", False, "unknown", []
        if compiled_code:
            definition, is_transformed, transformation_type, source_columns = extract_column_definition(compiled_code, col_name, dialect)

        # Extract tests
        column_tests = []
        test_meta = col_meta.get("meta", {})
        if test_meta.get("test_not_null"):
            column_tests.append("not_null")
        if test_meta.get("test_unique"):
            column_tests.append("unique")

        columns_list.append({
            "name": col_name,
            "description": col_meta.get("description", ""),
            "data_type": data_type,
            "definition": definition,
            "is_transformed": is_transformed,
            "transformation_type": transformation_type,
            "source_columns": source_columns,
            "tests": column_tests,
            "tags": col_meta.get("tags", []),
            "meta": col_meta.get("meta", {}),
        })

        # Extract column lineage
        if compiled_code and schema_map:
            extract_column_lineage(
                uid, col_name, compiled_code, schema_map, dialect,
                node, manifest, column_edges, errors
            )

    return {
        "unique_id": uid,
        "name": name,
        "description": node.get("description", ""),
        "schema": node.get("schema", ""),
        "database": node.get("database", ""),
        "materialized": node.get("config", {}).get("materialized", "view"),
        "layer": layer,
        "directory": directory,
        "fqn": fqn,
        "path": node.get("path", ""),
        "tags": node.get("tags", []),
        "owner": node.get("meta", {}).get("owner", ""),
        "raw_code": raw_code,
        "compiled_code": compiled_code,
        "depends_on": node.get("depends_on", {}).get("nodes", []),
        "columns": columns_list,
        "stats": stats,
    }


def extract_column_lineage(uid, col_name, sql, schema_map, dialect, node, manifest, column_edges, errors):
    """
    Extract lineage for a single column using AST walking.
    This replaces the old sqlglot.lineage approach.
    """
    try:
        # Parse the SQL
        ast = safe_parse_sql(sql, dialect)
        if not ast:
            logger.debug(f"Failed to parse SQL for {uid}.{col_name}")
            return

        # Build table alias mapping
        alias_map = build_alias_map(ast)

        # Resolve CTEs
        cte_lineage = resolve_ctes(ast, dialect)

        # Find the final SELECT statement
        select = ast.find(exp.Select)
        if not select:
            return

        # Find the output column definition
        col_expression = None
        col_definition = ""
        transformation_type = "direct"

        for expr in select.expressions:
            # Check if this is our target column
            if isinstance(expr, exp.Alias):
                if expr.alias.lower() == col_name.lower():
                    col_expression = expr.this
                    col_definition = expr.this.sql(dialect=dialect)
                    transformation_type = classify_transformation(expr)
                    break
            elif isinstance(expr, exp.Column):
                if expr.name.lower() == col_name.lower():
                    col_expression = expr
                    col_definition = expr.sql(dialect=dialect)
                    transformation_type = "direct"
                    break
            elif isinstance(expr, exp.Star):
                # SELECT * - we'll handle this via fallback
                continue

        if not col_expression:
            # Fallback: match by column name
            for dep_uid in node.get("depends_on", {}).get("nodes", []):
                dep_columns = get_column_schema(dep_uid, {}, manifest)
                if col_name in dep_columns:
                    column_edges.append({
                        "source": f"{dep_uid}.{col_name}",
                        "target": f"{uid}.{col_name}",
                        "transformation": "",
                        "type": "direct",
                    })
            return

        # Extract all source columns from the expression
        source_refs = extract_column_sources_from_expression(col_expression)

        # For each source column, trace through CTEs and resolve to actual tables
        for table_alias, source_col_name in source_refs:
            # Resolve alias to table name
            table_name = alias_map.get(table_alias, table_alias) if table_alias else ""

            # If no table name and we have only one dependency, use that
            if not table_name and len(node.get("depends_on", {}).get("nodes", [])) == 1:
                dep_uid = node.get("depends_on", {}).get("nodes", [])[0]
                column_edges.append({
                    "source": f"{dep_uid}.{source_col_name}",
                    "target": f"{uid}.{col_name}",
                    "transformation": col_definition,
                    "type": transformation_type,
                })
                continue

            # Trace through CTEs if applicable
            if table_name:
                final_sources = trace_through_ctes(table_name, source_col_name, cte_lineage)
            else:
                final_sources = [(table_name, source_col_name)]

            # Map each final source to a dbt unique_id
            for src_table, src_col in final_sources:
                src_uid = find_upstream_uid(src_table, node, manifest)
                if src_uid:
                    column_edges.append({
                        "source": f"{src_uid}.{src_col}",
                        "target": f"{uid}.{col_name}",
                        "transformation": col_definition,
                        "type": transformation_type,
                    })
                else:
                    # Log as debug - table might be a CTE or unresolved
                    logger.debug(f"Could not resolve table '{src_table}' for {uid}.{col_name}")

    except Exception as e:
        logger.debug(f"Error extracting lineage for {uid}.{col_name}: {e}")
        errors.append({
            "type": "column_lineage_extraction",
            "unique_id": uid,
            "column": col_name,
            "error": str(e)
        })


def find_upstream_uid(table_name, node, manifest):
    """Find upstream unique_id from table name."""
    for dep_uid in node.get("depends_on", {}).get("nodes", []):
        dep_node = manifest.get("nodes", {}).get(dep_uid) or manifest.get("sources", {}).get(dep_uid, {})
        dep_name = dep_node.get("alias") or dep_node.get("name", "")

        if table_name.endswith(dep_name) or dep_name in table_name:
            return dep_uid

    return None


def extract_source(uid, source_node, catalog):
    """Extract source metadata."""
    columns_list = []
    source_columns = source_node.get("columns", {})
    cat_columns = catalog.get("sources", {}).get(uid, {}).get("columns", {}) if catalog else {}

    all_cols = set(source_columns.keys()) | set(cat_columns.keys())

    for col_name in sorted(all_cols):
        col_meta = source_columns.get(col_name, {})
        cat_col = cat_columns.get(col_name, {})

        columns_list.append({
            "name": col_name,
            "description": col_meta.get("description", ""),
            "data_type": cat_col.get("type") or col_meta.get("data_type", "unknown"),
        })

    return {
        "unique_id": uid,
        "name": source_node.get("name", ""),
        "description": source_node.get("description", ""),
        "database": source_node.get("database", ""),
        "schema": source_node.get("schema", ""),
        "loader": source_node.get("loader", ""),
        "columns": columns_list,
        "freshness": source_node.get("freshness", {}),
    }


def extract_seed(uid, seed_node, catalog):
    """Extract seed metadata."""
    columns_list = []
    seed_columns = seed_node.get("columns", {})

    for col_name, col_meta in seed_columns.items():
        columns_list.append({
            "name": col_name,
            "description": col_meta.get("description", ""),
            "data_type": col_meta.get("data_type", "unknown"),
        })

    return {
        "unique_id": uid,
        "name": seed_node.get("name", ""),
        "description": seed_node.get("description", ""),
        "schema": seed_node.get("schema", ""),
        "columns": columns_list,
    }


def extract_test(uid, test_node):
    """Extract test metadata."""
    return {
        "unique_id": uid,
        "name": test_node.get("name", ""),
        "test_type": "generic" if test_node.get("test_metadata", {}).get("name") else "singular",
        "severity": test_node.get("config", {}).get("severity", "ERROR"),
        "model": test_node.get("depends_on", {}).get("nodes", [None])[0],
        "column": test_node.get("column_name", ""),
        "description": test_node.get("description", ""),
    }


def extract_macro(uid, macro_node):
    """Extract macro metadata."""
    return {
        "unique_id": uid,
        "name": macro_node.get("name", ""),
        "description": macro_node.get("description", ""),
        "arguments": macro_node.get("arguments", []),
        "sql": macro_node.get("macro_sql", ""),
    }


def extract_exposure(uid, exposure_node):
    """Extract exposure metadata."""
    return {
        "unique_id": uid,
        "name": exposure_node.get("name", ""),
        "description": exposure_node.get("description", ""),
        "type": exposure_node.get("type", ""),
        "owner": exposure_node.get("owner", {}).get("name", ""),
        "depends_on": exposure_node.get("depends_on", {}).get("nodes", []),
        "url": exposure_node.get("url", ""),
    }


def extract_metric(uid, metric_node):
    """Extract metric metadata."""
    return {
        "unique_id": uid,
        "name": metric_node.get("name", ""),
        "description": metric_node.get("description", ""),
        "type": metric_node.get("type", ""),
        "expression": metric_node.get("expression", ""),
        "depends_on": metric_node.get("depends_on", {}).get("nodes", []),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extract comprehensive dbt metadata and lineage"
    )
    parser.add_argument("--manifest", required=True, help="Path to manifest.json")
    parser.add_argument("--catalog", default=None, help="Path to catalog.json")
    parser.add_argument("--output", default="lineage.json", help="Output path")
    parser.add_argument("--dialect", default="clickhouse", help="SQL dialect")
    parser.add_argument("--commit-sha", default=os.environ.get("GITHUB_SHA", "local"), help="Git commit SHA")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--compiled-dir", default=None, help="(Deprecated)")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    result = extract_all_metadata(
        manifest_path=args.manifest,
        catalog_path=args.catalog,
        dialect=args.dialect,
        commit_sha=args.commit_sha,
    )

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    logger.info(f"✓ Written to {output_path}")
    logger.info(f"  Models: {result['metadata']['stats']['models']}")
    logger.info(f"  Sources: {result['metadata']['stats']['sources']}")
    logger.info(f"  Column edges: {result['metadata']['stats']['column_edges']}")
    logger.info(f"  Errors: {result['metadata']['stats']['errors']}")


if __name__ == "__main__":
    main()
