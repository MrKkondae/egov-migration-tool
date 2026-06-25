from __future__ import annotations

import argparse
from pathlib import Path

from .mapper_locations_helper import (
    build_mapper_locations_payload,
    payload_to_json,
    read_text,
    replace_mapper_locations_property,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Expand sqlMapConfig files into explicit MyBatis mapperLocations.")
    parser.add_argument("--source-root", required=True, help="Project root containing src/main/resources.")
    parser.add_argument("--db-type", required=True, help="Database type such as mysql/oracle/tibero/cubrid/altibase.")
    parser.add_argument("--spring-xml", help="Optional Spring XML file to patch with explicit mapperLocations.")
    parser.add_argument("--output-json", help="Optional JSON output path.")
    parser.add_argument("--apply", action="store_true", help="Apply mapperLocations expansion to --spring-xml.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = Path(args.source_root).expanduser().resolve()
    payload = build_mapper_locations_payload(source_root, args.db_type)

    if args.output_json:
        output_path = Path(args.output_json).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload_to_json(payload), encoding="utf-8")

    if args.apply:
        if not args.spring_xml:
            raise SystemExit("--apply requires --spring-xml")
        spring_xml_path = Path(args.spring_xml).expanduser().resolve()
        text = read_text(spring_xml_path)
        updated, count = replace_mapper_locations_property(text, list(payload["mapper_resources"]))
        if count == 0:
            raise SystemExit(f"mapperLocations/configLocations property not found: {spring_xml_path}")
        spring_xml_path.write_text(updated, encoding="utf-8")

    print(payload_to_json(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
