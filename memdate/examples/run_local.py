#!/usr/bin/env python3
"""CLI for memdate. Fully offline — no model, no network.

Usage:
    PYTHONPATH=src python3 examples/run_local.py --root /tmp/memo init
    PYTHONPATH=src python3 examples/run_local.py --root /tmp/memo \\
        capture --domain work --text "Fixed the flaky test." --source terminal
    PYTHONPATH=src python3 examples/run_local.py --root /tmp/memo \\
        distill --domain work --file /tmp/work-distilled.md \\
        --entities "Acme Corp,Priya" --informs personal \\
        --questions "Does the contract renew?" --lifecycle ITERATIVE
    PYTHONPATH=src python3 examples/run_local.py --root /tmp/memo \\
        index --touched work,personal
    PYTHONPATH=src python3 examples/run_local.py --root /tmp/memo sweep

A YAML or JSON config (--config) can set the root and domain list; see
examples/domains.example.yaml.
"""

from __future__ import annotations

import argparse
import sys

from memdate import (
    MemoryConfig,
    capture,
    default_adapter,
    distill,
    ensure_layout,
    regenerate_index,
    sweep_new,
)


def load_config(args) -> MemoryConfig:
    if args.config:
        if args.config.endswith(".json"):
            cfg = MemoryConfig.from_json(args.config)
        else:
            cfg = MemoryConfig.from_yaml(args.config)
        if args.root:
            cfg.root = args.root
        return cfg
    if not args.root:
        sys.exit("error: --root is required (or --config with a root key)")
    return MemoryConfig(root=args.root)


def main() -> None:
    parser = argparse.ArgumentParser(description="memdate CLI")
    parser.add_argument("--root", help="memory root directory")
    parser.add_argument("--config", help="JSON or YAML config file")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="create root, DROP dirs, domain dirs")

    p = sub.add_parser("capture", help="append a raw record")
    p.add_argument("--domain", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--source", default="")
    p.add_argument("--force", action="store_true",
                   help="record an interpretation-check bypass explicitly")

    p = sub.add_parser("distill", help="write a domain's distilled.md")
    p.add_argument("--domain", required=True)
    p.add_argument("--file", required=True,
                   help="file holding the consolidated body text")
    p.add_argument("--entities", default="",
                   help="comma-separated entity names")
    p.add_argument("--informs", default="",
                   help="comma-separated domains this domain informs")
    p.add_argument("--questions", default="",
                   help="open questions, separated by ' | '")
    p.add_argument("--lifecycle", default="ITERATIVE")

    p = sub.add_parser("index", help="regenerate the cross-domain index")
    p.add_argument("--touched", required=True,
                   help="comma-separated domains the distill pass updated")

    sub.add_parser("sweep", help="route files in DROP/NEW/")

    args = parser.parse_args()
    cfg = load_config(args)
    store = default_adapter(cfg.root)

    if args.cmd == "init":
        ensure_layout(cfg, adapter=store)
        print(f"initialized {cfg.root} with domains: {', '.join(cfg.domains)}")

    elif args.cmd == "capture":
        result = capture(cfg, args.domain, args.text, source=args.source,
                         force=args.force, adapter=store)
        print(f"captured -> {result.path} at {result.timestamp}")

    elif args.cmd == "distill":
        with open(args.file, encoding="utf-8") as f:
            body = f.read()
        result = distill(
            cfg, args.domain, body,
            entities=[e.strip() for e in args.entities.split(",") if e.strip()],
            informs=[d.strip() for d in args.informs.split(",") if d.strip()],
            open_questions=[q.strip() for q in args.questions.split(" | ")
                            if q.strip()],
            lifecycle=args.lifecycle,
            adapter=store,
        )
        print(f"distilled -> {result.path} [{result.lifecycle}], "
              f"raw untouched: {result.raw_untouched}")

    elif args.cmd == "index":
        touched = [d.strip() for d in args.touched.split(",") if d.strip()]
        result = regenerate_index(cfg, touched, adapter=store)
        if result.skipped:
            print(f"skipped: {result.reason}")
        else:
            print(f"index -> {result.path}: {result.cross_domain_entities} "
                  f"entities, {result.open_questions} questions, "
                  f"{result.hot_zones} hot zones [{result.lifecycle}]")

    elif args.cmd == "sweep":
        results = sweep_new(cfg, adapter=store)
        if not results:
            print("DROP/NEW is empty.")
        for item in results:
            detail = f" -> {item.domain}" if item.domain else ""
            reason = f" ({item.reason})" if item.reason else ""
            print(f"{item.filename}: {item.outcome}{detail}{reason}")


if __name__ == "__main__":
    main()
