"""Create the delivered full-universe derived CSV from individual ticker files."""

from src.evaluation.full_universe import FULL_PATH, build_full_universe


def main() -> int:
    full, _, missing = build_full_universe()
    print(
        f"Built {FULL_PATH}: {len(full)} rows across "
        f"{full['symbole'].nunique()} symbols ({len(missing)} beyond the old combined file)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
