"""
CLI entry point for studio_access.

Usage
-----
    python main.py grant  --user-id 12345
    python main.py check  --user-id 12345
    python main.py remove --user-id 12345

Reads TD_API_KEY (required), TD_API_ENDPOINT, and TD_API_VERSION from a
local .env file (see .env.example) or from the shell environment.
"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from studio_access import StudioAccessClient, StudioAccessError


def build_client() -> StudioAccessClient:
    load_dotenv()

    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_API_ENDPOINT", "https://api.treasuredata.com")
    api_version = os.environ.get("TD_API_VERSION", "v4")

    if not api_key:
        print("ERROR: TD_API_KEY is not set. Copy .env.example to .env and fill it in.", file=sys.stderr)
        sys.exit(1)

    return StudioAccessClient(api_key=api_key, endpoint=endpoint, api_version=api_version)


def cmd_grant(client: StudioAccessClient, user_id: int) -> None:
    result = client.grant_access(user_id)
    print(f"Granted access to user {result.user_id}: {result.value} (HTTP {result.status_code})")


def cmd_check(client: StudioAccessClient, user_id: int) -> None:
    result = client.check_access(user_id)
    if result.has_access:
        print(f"User {result.user_id} HAS Studio access ({result.value})")
    else:
        print(f"User {result.user_id} does NOT have an explicit grant (value={result.value!r}, follows account default)")


def cmd_remove(client: StudioAccessClient, user_id: int) -> None:
    result = client.remove_access(user_id)
    print(f"Removed access grant for user {result.user_id} (HTTP {result.status_code})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Treasure AI Studio access for a user.")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("grant", "check", "remove"):
        p = sub.add_parser(name, help=f"{name.capitalize()} Studio access for a user")
        p.add_argument("--user-id", type=int, required=True, help="Target user ID (integer)")

    args = parser.parse_args()
    client = build_client()

    try:
        if args.command == "grant":
            cmd_grant(client, args.user_id)
        elif args.command == "check":
            cmd_check(client, args.user_id)
        elif args.command == "remove":
            cmd_remove(client, args.user_id)
    except StudioAccessError as exc:
        print(f"API error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
