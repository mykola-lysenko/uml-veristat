#!/usr/bin/env python3
"""JIT expansion dumper — runs INSIDE the UML guest.

For each *.bpf.o object in --objects (optionally sharded), loads every
program via `bpftool prog loadall`, records per-program metadata from
`bpftool -j prog show pinned`, and saves gzipped xlated + jited text dumps.
Load failures are recorded and skipped; one bad object cannot sink the sweep.

Output layout (under --out):
  results-<shard>.jsonl   one row per program (or per failed object)
  dumps/<obj>__<prog>.xlated.txt.gz
  dumps/<obj>__<prog>.jited.txt.gz
  done-<shard>            marker written on completion
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import pathlib
import subprocess
import sys

CMD_TIMEOUT = 180


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=CMD_TIMEOUT
    )


def save_gz(path: pathlib.Path, text: str) -> None:
    with gzip.open(path, "wt") as f:
        f.write(text)


def unpin_all(pin_dir: pathlib.Path) -> None:
    if pin_dir.is_dir():
        for pin in pin_dir.iterdir():
            pin.unlink()
        pin_dir.rmdir()


def process_object(
    bpftool: str, obj: pathlib.Path, pin_dir: pathlib.Path, dumps: pathlib.Path
) -> list[dict]:
    stem = obj.name.removesuffix(".bpf.o")
    load = run([bpftool, "prog", "loadall", str(obj), str(pin_dir)])
    if load.returncode != 0:
        unpin_all(pin_dir)
        return [{
            "file": obj.name,
            "load_error": load.stderr.strip()[-500:],
        }]

    rows = []
    for pin in sorted(pin_dir.iterdir()):
        row = {"file": obj.name, "prog": pin.name}
        show = run([bpftool, "-j", "prog", "show", "pinned", str(pin)])
        if show.returncode == 0:
            info = json.loads(show.stdout)
            row.update({
                "id": info.get("id"),
                "type": info.get("type"),
                "bytes_xlated": info.get("bytes_xlated"),
                "bytes_jited": info.get("bytes_jited"),
            })
        else:
            row["show_error"] = show.stderr.strip()[-200:]

        for kind in ("xlated", "jited"):
            dump = run([bpftool, "prog", "dump", kind, "pinned", str(pin)])
            if dump.returncode == 0:
                save_gz(dumps / f"{stem}__{pin.name}.{kind}.txt.gz", dump.stdout)
            else:
                row[f"{kind}_error"] = dump.stderr.strip()[-200:]
        rows.append(row)

    unpin_all(pin_dir)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--objects", required=True)
    ap.add_argument("--bpftool", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--shard", default="0/1", help="k/N: process objects with index%%N==k")
    ap.add_argument("--limit", type=int, default=0, help="stop after N objects (smoke)")
    args = ap.parse_args()

    k, n = (int(x) for x in args.shard.split("/"))
    out = pathlib.Path(args.out)
    dumps = out / "dumps"
    dumps.mkdir(parents=True, exist_ok=True)
    pin_dir = pathlib.Path(f"/sys/fs/bpf/jd{k}")

    objects = sorted(pathlib.Path(args.objects).glob("*.bpf.o"))
    objects = [o for i, o in enumerate(objects) if i % n == k]
    if args.limit:
        objects = objects[: args.limit]

    n_progs = n_failed = 0
    with open(out / f"results-{k}.jsonl", "w") as results:
        for i, obj in enumerate(objects):
            try:
                rows = process_object(args.bpftool, obj, pin_dir, dumps)
            except Exception as exc:  # timeout, bad JSON, bpffs oddity
                unpin_all(pin_dir)
                rows = [{"file": obj.name, "load_error": f"driver: {exc}"}]
            for row in rows:
                if "load_error" in row:
                    n_failed += 1
                else:
                    n_progs += 1
                results.write(json.dumps(row) + "\n")
            results.flush()
            if (i + 1) % 25 == 0 or i + 1 == len(objects):
                print(
                    f"[shard {args.shard}] {i + 1}/{len(objects)} objects, "
                    f"{n_progs} progs, {n_failed} load failures",
                    flush=True,
                )

    (out / f"done-{k}").write_text(
        json.dumps({"objects": len(objects), "progs": n_progs, "failed": n_failed})
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
