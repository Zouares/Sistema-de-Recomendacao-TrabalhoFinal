import os
import sys
import urllib.request
import zipfile

MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = SCRIPT_DIR
DEST_DIR = os.path.join(DATA_DIR, "ml-latest-small")
ZIP_PATH = os.path.join(DATA_DIR, "ml-latest-small.zip")


def download_movielens() -> None:
    if os.path.isdir(DEST_DIR) and os.path.exists(os.path.join(DEST_DIR, "ratings.csv")):
        print(f"Dataset já existe em: {DEST_DIR}")
        return

    print(f"Baixando MovieLens de:\n  {MOVIELENS_URL}")

    try:
        def _progress(block_num: int, block_size: int, total_size: int) -> None:
            downloaded = block_num * block_size
            pct = min(100, downloaded * 100 // total_size) if total_size > 0 else 0
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            sys.stdout.write(f"\r  [{bar}] {pct}%")
            sys.stdout.flush()

        urllib.request.urlretrieve(MOVIELENS_URL, ZIP_PATH, reporthook=_progress)
        print("\nDownload concluído.")
    except Exception as exc:
        print(f"\nErro no download: {exc}")
        sys.exit(1)

    try:
        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            zf.extractall(DATA_DIR)
        os.remove(ZIP_PATH)
        print(f"Extração concluída em: {DEST_DIR}")
    except Exception as exc:
        print(f"Erro na extração: {exc}")
        sys.exit(1)

    try:
        import csv
        with open(os.path.join(DEST_DIR, "ratings.csv")) as f:
            total_ratings = sum(1 for _ in f) - 1
        with open(os.path.join(DEST_DIR, "movies.csv")) as f:
            total_movies = sum(1 for _ in f) - 1
        print(f"\nDataset baixado:")
        print(f"  Filmes:  {total_movies:,}")
        print(f"  Ratings: {total_ratings:,}")
    except Exception:
        pass


if __name__ == "__main__":
    download_movielens()
