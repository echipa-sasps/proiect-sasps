import argparse
from pathlib import Path

from web.app import create_app
from web.demo import create_demo


def main():
    parser = argparse.ArgumentParser(description="Catalogul de biblioteca — interfata locala")
    parser.add_argument("--database", type=Path, help="Baza existenta; implicit date/demo.db")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    database = args.database if args.database is not None else Path("date/demo.db")
    if not database.exists():
        if args.database is not None:
            parser.error(f"Baza nu exista: {database}. Genereaz-o cu python -m catalog.data.")
        create_demo(database)
        print(f"Catalog demonstrativ creat: {database}")
    print(f"Baza folosita: {database.resolve()}", flush=True)
    create_app(database).run(host="127.0.0.1", port=args.port, threaded=False)


if __name__ == "__main__":
    main()
