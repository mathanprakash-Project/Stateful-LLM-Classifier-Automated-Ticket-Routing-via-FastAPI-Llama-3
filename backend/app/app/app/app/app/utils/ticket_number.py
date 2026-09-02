"""
Ticket number generator helper.
Format: TKT-YYMMDD-XXXX (e.g. TKT-260827-0042)
"""

from datetime import datetime, timezone
import random


def generate_ticket_number(seq: int = 1) -> str:
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%y%m%d")
    random_suffix = random.randint(1000, 9999)
    return f"TKT-{date_str}-{random_suffix}"

