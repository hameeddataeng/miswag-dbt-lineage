"""
Main CLI entrypoint for miswag-dbt-lineage
"""
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from miswag_dbt_lineage import __version__
from miswag_dbt_lineage.extractor import main as extractor_main
from miswag_dbt_lineage.generator import generate_site

app = typer.Typer(
    name="miswag-dbt-lineage",
    help="Generate beautiful, interactive column-level lineage for dbt projects",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"[bold blue]miswag-dbt-lineage[/bold blue] version {__version__}")
        raise typer.Exit()


@app.callback()
def common(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
):
    """miswag-dbt-lineage: Column-level lineage for dbt"""
    pass


@app.command()
def generate(
    manifest: Path = typer.Option(
        "target/manifest.json",
        "--manifest",
        "-m",
        help="Path to dbt manifest.json",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    catalog: Optional[Path] = typer.Option(
        "target/catalog.json",
        "--catalog",
        "-c",
        help="Path to dbt catalog.json (optional but recommended)",
        exists=False,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    output: Path = typer.Option(
        "target/lineage_website",
        "--output",
        "-o",
        help="Output directory for the static site",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    dialect: str = typer.Option(
        "clickhouse",
        "--dialect",
        "-d",
        help="SQL dialect for parsing (clickhouse, postgres, snowflake, bigquery, etc.)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose logging",
    ),
):
    """
    Generate a static lineage website from dbt artifacts.

    This command:
    1. Parses your dbt manifest.json and catalog.json
    2. Extracts column-level lineage using SQL parsing
    3. Generates a static website you can deploy anywhere

    Example:
        miswag-dbt-lineage generate --manifest target/manifest.json --output target/lineage_website
    """
    console.print(Panel.fit(
        "[bold blue]miswag-dbt-lineage[/bold blue] 🚀\n"
        "Generating column-level lineage for your dbt project",
        border_style="blue"
    ))

    # Check if catalog exists
    if catalog and not catalog.exists():
        console.print(f"⚠️  [yellow]Catalog not found at {catalog}[/yellow]")
        console.print("   Run 'dbt docs generate' to create it for better lineage resolution")
        catalog = None

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Extract lineage
            task1 = progress.add_task("Extracting lineage from dbt artifacts...", total=None)

            # Create a temporary file for lineage output
            import tempfile
            import json

            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                tmp_output = Path(tmp_file.name)

            # Call the extractor
            sys.argv = [
                'extract_lineage',
                '--manifest', str(manifest),
                '--output', str(tmp_output),
                '--dialect', dialect,
            ]

            if catalog:
                sys.argv.extend(['--catalog', str(catalog)])

            if verbose:
                sys.argv.append('--verbose')

            # Run extractor
            extractor_main()

            progress.update(task1, completed=True)

            # Load the generated lineage data
            task2 = progress.add_task("Generating static website...", total=None)

            with open(tmp_output, 'r') as f:
                lineage_data = json.load(f)

            # Generate site
            generate_site(lineage_data, output)

            progress.update(task2, completed=True)

            # Clean up temp file
            tmp_output.unlink()

        console.print("\n[bold green]✅ Success![/bold green]")
        console.print(f"\n📂 Static site generated at: [bold]{output.absolute()}[/bold]")
        console.print(f"\n🌐 To view locally:")
        console.print(f"   [dim]cd {output.absolute()}[/dim]")
        console.print(f"   [dim]python -m http.server 8080[/dim]")
        console.print(f"\n📦 To deploy:")
        console.print(f"   [dim]aws s3 sync {output.absolute()} s3://your-bucket/[/dim]")

    except Exception as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {str(e)}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)


@app.command()
def build(
    project_dir: Path = typer.Option(
        ".",
        "--project-dir",
        "-p",
        help="Path to dbt project directory",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output: Path = typer.Option(
        "target/lineage_website",
        "--output",
        "-o",
        help="Output directory for the static site",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    skip_dbt_docs: bool = typer.Option(
        False,
        "--skip-dbt-docs",
        help="Skip running 'dbt docs generate'",
    ),
    dialect: str = typer.Option(
        "clickhouse",
        "--dialect",
        "-d",
        help="SQL dialect for parsing",
    ),
):
    """
    Build lineage site (runs 'dbt docs generate' + 'generate' command).

    This is a convenience command that:
    1. Runs 'dbt docs generate' to create manifest.json and catalog.json
    2. Generates the lineage site

    Example:
        miswag-dbt-lineage build --project-dir . --output target/lineage_website
    """
    import subprocess

    console.print(Panel.fit(
        "[bold blue]miswag-dbt-lineage build[/bold blue] 🔨\n"
        "Building dbt docs and generating lineage",
        border_style="blue"
    ))

    # Step 1: Run dbt docs generate (unless skipped)
    if not skip_dbt_docs:
        console.print("\n[bold]Step 1:[/bold] Running 'dbt docs generate'...")
        try:
            result = subprocess.run(
                ["dbt", "docs", "generate"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            console.print("[green]✓[/green] dbt docs generate completed")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✗[/red] dbt docs generate failed:\n{e.stderr}")
            raise typer.Exit(code=1)
        except FileNotFoundError:
            console.print("[red]✗[/red] dbt command not found. Is dbt installed?")
            raise typer.Exit(code=1)
    else:
        console.print("[yellow]⊘[/yellow] Skipping 'dbt docs generate'")

    # Step 2: Generate lineage site
    console.print("\n[bold]Step 2:[/bold] Generating lineage site...")

    manifest = project_dir / "target" / "manifest.json"
    catalog = project_dir / "target" / "catalog.json"

    if not manifest.exists():
        console.print(f"[red]✗[/red] Manifest not found at {manifest}")
        raise typer.Exit(code=1)

    # Call the generate command
    ctx = typer.Context(generate)
    ctx.invoke(
        generate,
        manifest=manifest,
        catalog=catalog if catalog.exists() else None,
        output=output,
        dialect=dialect,
        verbose=False,
    )


def main():
    """Main entrypoint"""
    app()


if __name__ == "__main__":
    main()
