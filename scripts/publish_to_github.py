#!/usr/bin/env python3
"""Create GitHub repo (if missing) and push current branch.

Requires:
  - Git installed, run from repo root (or any path inside repo)
  - GH_TOKEN: fine-grained token (Contents + Metadata) or classic PAT with `repo`

Usage (PowerShell):
  $env:GH_TOKEN = "ghp_...."   # or fine-grained
  python scripts/publish_to_github.py

Optional env:
  GITHUB_OWNER   default: gyutaetae
  GITHUB_REPO    default: harness
  DEFAULT_BRANCH default: main
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com"
OWNER = os.environ.get("GITHUB_OWNER", "gyutaetae")
REPO = os.environ.get("GITHUB_REPO", "harness")
BRANCH = os.environ.get("DEFAULT_BRANCH", "main")


def run_git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def find_root(start: Path) -> Path:
    cur = start.resolve()
    while cur != cur.parent:
        if (cur / ".git").is_dir():
            return cur
        cur = cur.parent
    raise SystemExit("ERROR: not inside a git repository")


def api_request(method: str, url: str, token: str, data: dict | None = None) -> tuple[int, dict | list | str]:
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "harness-publish",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            if not raw:
                return resp.status, {}
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = raw
        return e.code, payload


def main() -> None:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: Set GH_TOKEN (or GITHUB_TOKEN) to a GitHub PAT with repo access.")
        sys.exit(1)

    root = find_root(Path(__file__).resolve().parent)
    r = run_git("rev-parse", "--abbrev-ref", "HEAD", cwd=root)
    if r.returncode != 0:
        print(r.stderr)
        sys.exit(1)
    current = r.stdout.strip()

    if current != BRANCH:
        print(f"Renaming branch {current} -> {BRANCH}")
        rr = run_git("branch", "-M", BRANCH, cwd=root)
        if rr.returncode != 0:
            print(rr.stderr)
            sys.exit(1)

    # Create repo if 404 on GET
    get_url = f"{API}/repos/{OWNER}/{REPO}"
    code, body = api_request("GET", get_url, token)
    if code == 404:
        print(f"Creating repo {OWNER}/{REPO} ...")
        create_url = f"{API}/user/repos"
        ccode, cbody = api_request(
            "POST",
            create_url,
            token,
            {
                "name": REPO,
                "private": False,
                "description": "Codex plan-and-build harness (task/phase runner)",
                "auto_init": False,
            },
        )
        if ccode not in (200, 201):
            print(f"ERROR: create repo failed ({ccode}): {cbody}")
            sys.exit(1)
        print("Repo created.")
    elif code != 200:
        print(f"ERROR: cannot read repo ({code}): {body}")
        sys.exit(1)
    else:
        print(f"Repo {OWNER}/{REPO} already exists.")

    remote_url = f"https://{token}@github.com/{OWNER}/{REPO}.git"
    run_git("remote", "remove", "origin", cwd=root)
    ra = run_git("remote", "add", "origin", remote_url, cwd=root)
    if ra.returncode != 0:
        print(ra.stderr)
        sys.exit(1)

    pu = run_git("push", "-u", "origin", BRANCH, cwd=root)
    if pu.returncode != 0:
        print(pu.stderr or pu.stdout)
        # scrub token from remote for safety
        run_git("remote", "set-url", "origin", f"https://github.com/{OWNER}/{REPO}.git", cwd=root)
        sys.exit(1)

    run_git("remote", "set-url", "origin", f"https://github.com/{OWNER}/{REPO}.git", cwd=root)
    print(f"Done: https://github.com/{OWNER}/{REPO}")


if __name__ == "__main__":
    main()
