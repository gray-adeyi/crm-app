ALLOWED_ORDER_STATUSES = frozenset(
    {"PENDING", "PARTIAL", "PAID", "DELIVERED", "CANCELLED"}
)


def compute_balance(total_price: int, amount_paid: int) -> int:
    return int(total_price) - int(amount_paid)


def derive_payment_status(total_price: int, amount_paid: int) -> str:
    """
    Automatic payment-derived status:
    - amount_paid == 0 -> pending
    - balance > 0 (and some paid) -> partial
    - balance == 0 -> paid
    """
    balance = compute_balance(total_price, amount_paid)
    if int(amount_paid) == 0:
        return "PENDING"
    if balance > 0:
        return "PARTIAL"
    return "PAID"


def compute_order_status(
    total_price: int, amount_paid: int, preferred_status: str
) -> str:
    """
    Combines payment rules with optional workflow state `delivered`.
    """
    if preferred_status not in ALLOWED_ORDER_STATUSES:
        preferred_status = "PENDING"

    if preferred_status == "CANCELLED":
        return "CANCELLED"

    if preferred_status == "DELIVERED":
        return "DELIVERED"

    return derive_payment_status(total_price, amount_paid)
