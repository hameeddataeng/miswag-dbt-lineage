"""
Static site generator for dbt lineage portal
"""
import json
import shutil
from pathlib import Path
from typing import Dict, Any


def generate_site(lineage_data: Dict[str, Any], output_dir: Path) -> None:
    """
    Generate a static lineage website from lineage data.

    Args:
        lineage_data: The lineage graph data (models, sources, edges, etc.)
        output_dir: Directory where the static site will be generated
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create data directory
    data_dir = output_dir / "data"
    data_dir.mkdir(exist_ok=True)

    # Write lineage.json
    lineage_file = data_dir / "lineage.json"
    with open(lineage_file, 'w', encoding='utf-8') as f:
        json.dump(lineage_data, f, indent=2, ensure_ascii=False)

    # Copy index.html template
    template_dir = Path(__file__).parent / "static" / "templates"
    index_template = template_dir / "index.html"

    if index_template.exists():
        shutil.copy(index_template, output_dir / "index.html")
    else:
        raise FileNotFoundError(f"Template not found: {index_template}")

    print(f"✅ Static site generated at: {output_dir.absolute()}")
    print(f"📊 Lineage data written to: {lineage_file.absolute()}")
    print(f"\n🚀 To view locally:")
    print(f"   cd {output_dir.absolute()}")
    print(f"   python -m http.server 8080")
    print(f"\n📦 To deploy:")
    print(f"   aws s3 sync {output_dir.absolute()} s3://your-bucket/")
    print(f"   # or")
    print(f"   gsutil rsync -r {output_dir.absolute()} gs://your-bucket/")
