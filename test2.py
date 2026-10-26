"""Card authorization CLI. Pass a JSON transaction as an argument or on stdin."""

import argparse
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
import re
import sys


@dataclass(frozen=True)
class Card:
    spending_limit: Decimal
    blocked: bool
    allowed_regions: frozenset[str]


# Demo limits are per transaction, in the transaction's currency units.
# Regions are represented by ISO two-letter merchant country codes.
CARDS = {
    "card_001": Card(Decimal("1000.00"), False, frozenset({"SG", "US"})),
    "card_002": Card(Decimal("500.00"), True, frozenset({"SG"})),
}


def authorize(transaction: dict) -> dict:
    """Validate input and apply declines before checking for manual review.

    Invalid requests (including unknown cards) raise ValueError rather than
    receiving a business authorization decision.
    """
    if not isinstance(transaction, dict):
        raise ValueError("Transaction must be a JSON object")

    required = (
        "card_id", "amount", "currency", "merchant_category_code",
        "merchant_country",
    )
    missing = [field for field in required if field not in transaction]
    if missing:
        raise ValueError("Missing required fields: " + ", ".join(missing))

    card_id = transaction["card_id"]
    if not isinstance(card_id, str) or card_id not in CARDS:
        raise ValueError("Unknown card_id")

    raw_amount = transaction["amount"]
    if isinstance(raw_amount, bool) or not isinstance(raw_amount, (str, int, float, Decimal)):
        raise ValueError("amount must be a positive finite number")
    try:
        amount = Decimal(str(raw_amount))
    except InvalidOperation as exc:
        raise ValueError("amount must be a positive finite number") from exc
    if not amount.is_finite() or amount <= 0:
        raise ValueError("amount must be a positive finite number")

    currency = transaction["currency"]
    if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("currency must be a three-letter uppercase code, e.g. USD")
    mcc = transaction["merchant_category_code"]
    if not isinstance(mcc, str) or not re.fullmatch(r"[0-9]{4}", mcc):
        raise ValueError("merchant_category_code must be a four-digit string")
    country = transaction["merchant_country"]
    if not isinstance(country, str) or not re.fullmatch(r"[A-Z]{2}", country):
        raise ValueError("merchant_country must be a two-letter uppercase code, e.g. SG")

    card = CARDS[card_id]
    if card.blocked:
        return {"decision": "decline", "reason": "card_blocked"}
    if amount > card.spending_limit:
        return {"decision": "decline", "reason": "spending_limit_exceeded"}
    if country not in card.allowed_regions:
        return {"decision": "refer", "reason": "merchant_country_not_allowed"}
    return {"decision": "approve", "reason": "all_checks_passed"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transaction", nargs="?", help="JSON transaction; defaults to stdin")
    args = parser.parse_args()
    try:
        raw = args.transaction if args.transaction is not None else sys.stdin.read()
        transaction = json.loads(raw, parse_float=Decimal)
        result = authorize(transaction)
    except (ValueError, RecursionError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
