"""
Static site generator for dbt lineage portal
"""
import json
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

    # Write lineage.json (for reference/debugging)
    lineage_file = data_dir / "lineage.json"
    with open(lineage_file, 'w', encoding='utf-8') as f:
        json.dump(lineage_data, f, indent=2, ensure_ascii=False)

    # Read template
    template_dir = Path(__file__).parent / "static" / "templates"
    index_template = template_dir / "index.html"

    if not index_template.exists():
        raise FileNotFoundError(f"Template not found: {index_template}")

    with open(index_template, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Embed JSON data directly into HTML
    # Convert data to compact JSON (no indentation to reduce file size)
    json_data = json.dumps(lineage_data, ensure_ascii=False, separators=(',', ':'))

    # Insert the embedded data script before the closing </body> tag
    embedded_script = f'\n<script>\n// Embedded lineage data for file:// protocol support\nwindow.EMBEDDED_DATA = {json_data};\n</script>\n</body>'

    # Replace the closing body tag with our embedded script + closing body tag
    html_with_embedded_data = template_content.replace('</body>', embedded_script)

    # Write the final HTML file
    output_html = output_dir / "index.html"
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_with_embedded_data)

    print(f"✅ Static site generated at: {output_dir.absolute()}")
    print(f"📊 Lineage data embedded in: {output_html.absolute()}")
    print(f"📊 Lineage data also saved to: {lineage_file.absolute()}")
    print(f"\n🚀 To view:")
    print(f"   Option 1 (Direct): Open {output_html.absolute()} in your browser")
    print(f"   Option 2 (Server): cd {output_dir.absolute()} && python -m http.server 8080")
    print(f"\n📦 To deploy:")
    print(f"   aws s3 sync {output_dir.absolute()} s3://your-bucket/")
    print(f"   # or")
    print(f"   gsutil rsync -r {output_dir.absolute()} gs://your-bucket/")
