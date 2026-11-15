"""Benchmark secvential; timing si memoria se masoara in treceri separate."""

import argparse
import csv
import platform
from pathlib import Path
import sqlite3
import tempfile
from time import perf_counter
import tracemalloc

from antipattern.catalog import AntiPatternCatalog, AntiPatternJoinCatalog
from baseline.catalog import BaselineCatalog
from catalog.data import create_database
from pattern.cache_proxy import CachedLibraryService
from pattern.service import LibraryService


# Colegii adauga aici fabricile; toate primesc Path si respecta Catalog.
VARIANTS = {
    "baseline": BaselineCatalog,
    "antipattern": AntiPatternCatalog,
    "antipattern_join": AntiPatternJoinCatalog,
    "pattern": LibraryService,
    "pattern_cache": CachedLibraryService,
}


def run(output: Path, sizes: list[int], repeats: int, variants: list[str]) -> None:
    if repeats < 1 or any(size < 1 for size in sizes):
        raise ValueError("Volumele si repetarile trebuie sa fie pozitive")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        fields = ["variant", "books", "scenario", "repeat", "elapsed_ms",
                  "peak_python_kib", "sql_queries", "python", "sqlite", "platform"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        with tempfile.TemporaryDirectory() as directory:
            for size in sizes:
                database = Path(directory) / f"catalog-{size}.db"
                create_database(database, size)
                for variant in variants:
                    for scenario in ("list_books", "search_books", "get_book_repeated"):
                        def operation(catalog):
                            if scenario == "list_books":
                                return catalog.list_books()
                            if scenario == "search_books":
                                return catalog.search_books("000")
                            return [catalog.get_book(1) for _ in range(100)]

                        # Incalzire SQLite/OS; fiecare proba foloseste un adaptor nou.
                        operation(VARIANTS[variant](database))
                        for repeat in range(1, repeats + 1):
                            catalog = VARIANTS[variant](database)
                            catalog.reset_metrics()
                            start = perf_counter()
                            result = operation(catalog)
                            elapsed = (perf_counter() - start) * 1000
                            queries = catalog.query_count
                            del result
                            memory_catalog = VARIANTS[variant](database)
                            tracemalloc.start()
                            try:
                                memory_result = operation(memory_catalog)
                                _, peak = tracemalloc.get_traced_memory()
                            finally:
                                tracemalloc.stop()
                            del memory_result
                            writer.writerow(dict(
                                variant=variant, books=size, scenario=scenario,
                                repeat=repeat, elapsed_ms=f"{elapsed:.6f}",
                                peak_python_kib=f"{peak / 1024:.3f}", sql_queries=queries,
                                python=platform.python_version(), sqlite=sqlite3.sqlite_version,
                                platform=platform.platform(),
                            ))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[100, 1000, 10000])
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--variants", nargs="+", choices=VARIANTS, default=list(VARIANTS))
    parser.add_argument("--output", type=Path, default=Path("rezultate/baseline.csv"))
    args = parser.parse_args()
    run(args.output, args.sizes, args.repeats, args.variants)
    print(f"Rezultate: {args.output}")


if __name__ == "__main__":
    main()
