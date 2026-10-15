#!/usr/bin/env python3
"""mint_lease.py — mint a device lease for the standalone Theia SDK.

Exchanges a tenant API key for a short-lived access token, then activates a
device lease the SDK can verify offline via ``lease_token=`` / ``THEIA_LEASE``.

Usage:
    export THEIA_ACCESS_KEY="<tenant API key client_id>"
    export THEIA_SECRET_KEY="<tenant API key client_secret>"
    python scripts/mint_lease.py --device-id my-laptop-01 [--label "Jane's laptop"]

Prints the lease JWT to stdout (and nothing else there), so it can be
captured directly:

    export THEIA_LEASE=$(python scripts/mint_lease.py --device-id my-laptop-01)

Env:
    THEIA_ACCESS_KEY     tenant API key client_id (required)
    THEIA_SECRET_KEY     tenant API key client_secret (required)
    THEIA_IDENTITY_URL   override the identity service base URL
                         (default: https://identity.harmoneyes.io)
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

DEFAULT_IDENTITY_URL = "https://identity.harmoneyes.io"


def _post(url: str, body: bytes, headers: dict) -> tuple[int, dict]:
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"error": raw.decode(errors="replace")}
        return e.code, payload


def get_access_token(base_url: str, client_id: str, client_secret: str) -> str:
    """Exchange the tenant API key for an account-audience access token."""
    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    body = f"grant_type=client_credentials&scope=account&resource={base_url}/api".encode()
    headers = {
        "Authorization": f"Basic {creds}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    status, payload = _post(f"{base_url}/oidc/token", body, headers)
    if status != 200:
        sys.exit(f"[mint_lease] token exchange failed ({status}): {payload}")
    return payload["access_token"]


def lease_expiry(lease: str) -> datetime | None:
    """Decode the lease JWT's `exp` claim without verifying the signature.

    Safe here only because this is our own just-minted response, not
    untrusted input — the SDK itself still verifies the signature offline.
    """
    try:
        _, payload_b64, _ = lease.split(".")
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        claims = json.loads(base64.urlsafe_b64decode(padded))
        return datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
    except (ValueError, KeyError):
        return None


def mint_lease(base_url: str, access_token: str, device_identifier: str, label: str | None) -> str:
    data = {"deviceIdentifier": device_identifier}
    if label:
        data["label"] = label
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    status, payload = _post(f"{base_url}/api/leases", json.dumps(data).encode(), headers)
    if status != 200:
        sys.exit(f"[mint_lease] lease activation failed ({status}): {payload}")
    return payload["lease"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--device-id", required=True, help="Stable identifier for this machine")
    parser.add_argument("--label", default=None, help="Optional human-readable label for this device")
    args = parser.parse_args()

    client_id = os.environ.get("THEIA_ACCESS_KEY")
    client_secret = os.environ.get("THEIA_SECRET_KEY")
    if not client_id or not client_secret:
        sys.exit("[mint_lease] set THEIA_ACCESS_KEY and THEIA_SECRET_KEY in your environment")

    base_url = os.environ.get("THEIA_IDENTITY_URL", DEFAULT_IDENTITY_URL).rstrip("/")

    print(f"[mint_lease] requesting access token from {base_url}", file=sys.stderr)
    access_token = get_access_token(base_url, client_id, client_secret)

    print(f"[mint_lease] activating lease for device {args.device_id!r}", file=sys.stderr)
    lease = mint_lease(base_url, access_token, args.device_id, args.label)

    expires_at = lease_expiry(lease)
    if expires_at:
        print(f"[mint_lease] lease expires at {expires_at.isoformat()}", file=sys.stderr)
    else:
        print("[mint_lease] could not read expiry from the lease", file=sys.stderr)

    print(lease)


if __name__ == "__main__":
    main()
