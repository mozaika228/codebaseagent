from __future__ import annotations

import argparse
import requests


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("--repo-id", required=True)
  parser.add_argument("--api", default="http://localhost:8000")
  args = parser.parse_args()

  resp = requests.post(f"{args.api}/index/repo", json={"repo_id": args.repo_id}, timeout=300)
  print(resp.status_code)
  print(resp.text)


if __name__ == "__main__":
  main()
