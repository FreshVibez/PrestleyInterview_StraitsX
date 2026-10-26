"""Generate unique, Luhn-valid 16-digit PANs within a batch."""

import argparse
import secrets
from pathlib import Path


def generate_pans(bin: str, count: int) -> list[str]:
    """Combine a six-digit BIN, unique nine-digit suffixes, and Luhn digits."""
    if len(bin) != 6 or not bin.isascii() or not bin.isdigit():
        raise ValueError("BIN must contain exactly 6 digits")
    if not 1 <= count <= 10**9:
        raise ValueError("Count must be between 1 and 1,000,000,000")

    suffixes = secrets.SystemRandom().sample(range(10**9), count)
    pans = []

    for suffix in suffixes:
        payload = f"{bin}{suffix:09d}"
        total = 0

        for i, char in enumerate(payload):
            digit = int(char)
            # In a 16-digit PAN, double positions 0, 2, ..., 14.
            if i % 2 == 0:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit

        check_digit = (-total) % 10
        pans.append(f"{payload}{check_digit}")

    return pans


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Luhn-valid PANs")
    parser.add_argument("bin", help="6-digit BIN")
    parser.add_argument("count", type=int, help="Number of PANs to generate")
    parser.add_argument("-o", "--output", help="Output file; defaults to stdout")
    args = parser.parse_args()

    try:
        output = "\n".join(generate_pans(args.bin, args.count)) + "\n"
    except ValueError as error:
        parser.error(str(error))

    if args.output:
        try:
            Path(args.output).write_text(output, encoding="utf-8")
        except OSError as error:
            parser.error(f"Could not write output: {error}")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
