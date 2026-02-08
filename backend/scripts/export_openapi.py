"""
Export OpenAPI specification to JSON file.

Usage:
    poetry run python scripts/export_openapi.py
"""

import json
from pathlib import Path

from app.main import create_app


def export_openapi():
    """Export OpenAPI spec"""
    app = create_app()

    # Get OpenAPI schema
    openapi_schema = app.openapi()

    # Save to file
    docs_dir = Path(__file__).parent.parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    output_path = docs_dir / "openapi.json"

    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"OpenAPI specification exported to: {output_path}")
    print(f"Endpoints: {len(openapi_schema['paths'])}")


if __name__ == "__main__":
    export_openapi()
