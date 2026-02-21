#!/usr/bin/env python3
import argparse
import os
import re
import sys
from urllib.parse import unquote

import requests

PATTERN = re.compile(r"https://hackmd\.io/_uploads/[A-Za-z0-9_\-./%]+\.png", re.IGNORECASE)

def uniq_keep_order(items):
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def main():
    ap = argparse.ArgumentParser(description="Download all HackMD _uploads .png images from a webpage and save as 1.png, 2.png, ...")
    ap.add_argument("page_url", help="Page URL, e.g. https://nduc193.github.io/posts/writeup_kma_ctf/")
    ap.add_argument("-o", "--out", default="images", help="Output directory (default: images)")
    ap.add_argument("--timeout", type=int, default=25, help="Timeout seconds (default: 25)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    sess = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Referer": args.page_url,
    }

    # 1) Fetch page HTML
    r = sess.get(args.page_url, headers=headers, timeout=args.timeout)
    r.raise_for_status()
    html = r.text

    # 2) Extract matching URLs
    urls = PATTERN.findall(html)
    urls = [unquote(u) for u in urls]
    urls = uniq_keep_order(urls)

    if not urls:
        print("No matching HackMD _uploads .png URLs found.", file=sys.stderr)
        return 2

    print(f"Found {len(urls)} images.")
    # 3) Download sequentially as 1.png, 2.png, ...
    for idx, url in enumerate(urls, start=1):
        out_path = os.path.join(args.out, f"{idx}.png")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            print(f"[skip] {out_path} exists")
            continue

        try:
            with sess.get(url, headers=headers, timeout=args.timeout, stream=True) as resp:
                resp.raise_for_status()
                with open(out_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 128):
                        if chunk:
                            f.write(chunk)
            print(f"[ok] {idx}.png  <- {url}")
        except Exception as e:
            print(f"[err] {idx}.png  <- {url} :: {e}", file=sys.stderr)

    print("Done.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())