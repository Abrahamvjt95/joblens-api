#!/usr/bin/env python3
"""
Creates (or recreates) the OpenSearch job-listings index.
Usage:
  python scripts/create_index.py              # create if not exists
  python scripts/create_index.py --recreate   # drop and recreate
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

from shared.opensearch_client import get_client, ensure_index, INDEX_NAME, INDEX_MAPPING


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--recreate", action="store_true", help="Drop and recreate the index")
    args = parser.parse_args()

    client = get_client()
    exists = client.indices.exists(index=INDEX_NAME)

    if args.recreate and exists:
        client.indices.delete(index=INDEX_NAME)
        print(f"Deleted index: {INDEX_NAME}")
        exists = False

    if not exists:
        client.indices.create(index=INDEX_NAME, body=INDEX_MAPPING)
        print(f"Created index: {INDEX_NAME}")
    else:
        print(f"Index already exists: {INDEX_NAME} (use --recreate to reset)")

    info = client.indices.get(index=INDEX_NAME)
    mapping = info[INDEX_NAME]["mappings"]["properties"]
    print(f"Fields: {list(mapping.keys())}")


if __name__ == "__main__":
    main()
