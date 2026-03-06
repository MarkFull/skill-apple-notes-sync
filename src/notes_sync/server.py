from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    p = argparse.ArgumentParser(description="Run Apple Notes QMD bridge API")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8787)
    args = p.parse_args()

    uvicorn.run("notes_sync.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
