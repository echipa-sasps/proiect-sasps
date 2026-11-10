"""Sumarizeaza probele brute din benchmark/run.py pe varianta, scenariu si volum."""

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev

FIELDS = ["variant", "books", "scenario", "samples",
          "median_ms", "mean_ms", "stdev_ms", "min_ms", "max_ms",
          "median_peak_python_kib", "sql_queries"]


def summarize(rows: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row["variant"], int(row["books"]), row["scenario"])].append(row)
    summary = []
    for (variant, books, scenario), samples in groups.items():
        times = [float(sample["elapsed_ms"]) for sample in samples]
        memory = [float(sample["peak_python_kib"]) for sample in samples]
        queries = sorted({int(sample["sql_queries"]) for sample in samples})
        summary.append(dict(
            variant=variant, books=books, scenario=scenario, samples=len(samples),
            median_ms=f"{median(times):.4f}", mean_ms=f"{mean(times):.4f}",
            stdev_ms=f"{stdev(times):.4f}" if len(times) > 1 else "0.0000",
            min_ms=f"{min(times):.4f}", max_ms=f"{max(times):.4f}",
            median_peak_python_kib=f"{median(memory):.3f}",
            # De obicei o singura valoare; mai multe inseamna probe neuniforme.
            sql_queries="/".join(map(str, queries)),
        ))
    summary.sort(key=lambda item: (item["scenario"], item["books"], item["variant"]))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("rezultate/sumar.csv"))
    args = parser.parse_args()
    rows = []
    for path in args.inputs:
        with path.open(newline="", encoding="utf-8") as stream:
            rows.extend(csv.DictReader(stream))
    summary = summarize(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(summary)
    for item in summary:
        print(f"{item['scenario']:<18} {item['books']:>6} {item['variant']:<17} "
              f"{item['median_ms']:>11} ms  sql={item['sql_queries']}")
    print(f"Sumar: {args.output}")


if __name__ == "__main__":
    main()
