from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import requests


def _parse_proc_environ(raw: bytes) -> dict[str, str]:
    env: dict[str, str] = {}
    for item in raw.split(b"\0"):
        if not item or b"=" not in item:
            continue
        k, v = item.split(b"=", 1)
        env[k.decode("utf-8", errors="ignore")] = v.decode("utf-8", errors="ignore")
    return env


def _candidate_pids() -> list[int]:
    try:
        proc = subprocess.run(["pgrep", "-f", "notes_sync.server"], capture_output=True, text=True)
    except Exception:
        return []

    if proc.returncode != 0:
        return []

    pids: list[int] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            pids.append(int(line))
        except ValueError:
            continue
    return pids


def _search_token_from_running_server() -> str | None:
    for pid in _candidate_pids():
        env_path = Path(f"/proc/{pid}/environ")
        if not env_path.exists():
            continue
        try:
            env = _parse_proc_environ(env_path.read_bytes())
        except Exception:
            continue
        token = env.get("SEARCH_TOKEN") or env.get("INGEST_TOKEN")
        if token:
            return token
    return None


def resolve_token(explicit: str | None = None) -> str | None:
    return (
        explicit
        or os.getenv("NOTES_SEARCH_TOKEN")
        or os.getenv("SEARCH_TOKEN")
        or _search_token_from_running_server()
    )


def _build_payload(
    query: str,
    top_k: int,
    mode: str,
    folders: list[str] | None,
    from_date: str | None,
    to_date: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "query": query,
        "top_k": top_k,
        "mode": mode,
    }

    filters: dict[str, Any] = {}
    if folders:
        filters["folder"] = folders
    if from_date:
        filters["from_date"] = from_date
    if to_date:
        filters["to_date"] = to_date

    if filters:
        payload["filters"] = filters
    return payload


def notes_search(
    *,
    base_url: str,
    query: str,
    top_k: int,
    mode: str,
    token: str | None,
    folders: list[str] | None,
    from_date: str | None,
    to_date: str | None,
    timeout: float,
) -> dict[str, Any]:
    payload = _build_payload(query, top_k, mode, folders, from_date, to_date)

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    base = base_url.rstrip("/")
    endpoints = ["/tool/notes_search", "/search/apple-notes"]
    last_error: str | None = None

    for endpoint in endpoints:
        url = f"{base}{endpoint}"
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        except Exception as e:
            last_error = f"request failed for {url}: {e}"
            continue

        if resp.status_code == 404:
            continue

        if resp.status_code == 401:
            raise RuntimeError("Unauthorized (401). Provide SEARCH_TOKEN/NOTES_SEARCH_TOKEN or run API with token disabled.")

        if resp.status_code >= 400:
            text = resp.text.strip()
            raise RuntimeError(f"HTTP {resp.status_code} from {url}: {text}")

        try:
            return resp.json()
        except Exception as e:
            raise RuntimeError(f"Invalid JSON from {url}: {e}") from e

    raise RuntimeError(last_error or "No notes search endpoint found (tried /tool/notes_search and /search/apple-notes).")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Call Apple Notes notes_search endpoint without manual curl.")
    p.add_argument("query", nargs="?", help="Search query text")
    p.add_argument("--query", dest="query_opt", help="Search query text (same as positional query)")
    p.add_argument("--base-url", default=os.getenv("NOTES_SEARCH_BASE_URL", "http://127.0.0.1:8787"))
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--mode", choices=["search", "query"], default="search")
    p.add_argument("--token", default=None, help="Optional bearer token; defaults to env/process auto-detection")
    p.add_argument("--folder", action="append", default=None, help="Optional folder filter (repeatable)")
    p.add_argument("--from-date", default=None, help="Optional ISO date/datetime")
    p.add_argument("--to-date", default=None, help="Optional ISO date/datetime")
    p.add_argument("--timeout", type=float, default=20.0)
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    query = args.query_opt or args.query
    if not query:
        print("query is required (positional or --query)", flush=True)
        return 2

    token = resolve_token(args.token)

    try:
        result = notes_search(
            base_url=args.base_url,
            query=query,
            top_k=args.top_k,
            mode=args.mode,
            token=token,
            folders=args.folder,
            from_date=args.from_date,
            to_date=args.to_date,
            timeout=args.timeout,
        )
    except Exception as e:
        print(str(e), flush=True)
        return 1

    if args.pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    else:
        print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
