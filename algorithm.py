"""
algorithm.py
------------
Greedy max-heap-based debt simplification (Optimal Account Balancing).

Given a dict of {name: net_balance}, produces the minimum set of
(debtor, creditor, amount) transactions that bring all balances to zero.

Complexity: O(k log k) where k = number of participants with non-zero balance.
"""

import heapq
from collections import defaultdict


def simplify_debts(balances: dict[str, float]) -> list[dict]:
    """
    Compute the minimum set of transactions to settle all debts.

    Args:
        balances: {participant_name: net_balance}
                  positive → owed money (creditor)
                  negative → owes money  (debtor)

    Returns:
        List of dicts: [{"from": debtor, "to": creditor, "amount": value}, ...]
    """
    # Max-heap for creditors (store negative values so heapq works as max-heap)
    # Max-heap for debtors (store positive amounts, max = biggest debtor)
    creditors = []  # (-balance, name)  → largest credit at top
    debtors = []    # (-balance, name)  → largest debt at top

    for name, bal in balances.items():
        rounded_bal = round(bal, 2)
        if rounded_bal > 0.009:
            heapq.heappush(creditors, (-rounded_bal, name))
        elif rounded_bal < -0.009:
            heapq.heappush(debtors, (rounded_bal, name))  # rounded_bal is negative; smallest at top = biggest debt

    transactions = []

    while creditors and debtors:
        # Largest creditor
        cred_neg, cred_name = heapq.heappop(creditors)
        cred_bal = -cred_neg   # positive

        # Largest debtor (most negative balance → smallest value in min-heap)
        debt_bal, debt_name = heapq.heappop(debtors)
        debt_bal = abs(debt_bal)  # make positive for comparison

        settle = min(cred_bal, debt_bal)
        settle = round(settle, 2)

        if settle > 0.009:
            transactions.append({
                "from": debt_name,
                "to": cred_name,
                "amount": settle,
            })

        remaining_cred = round(cred_bal - settle, 2)
        remaining_debt = round(debt_bal - settle, 2)

        if remaining_cred > 0.009:
            heapq.heappush(creditors, (-remaining_cred, cred_name))
        if remaining_debt > 0.009:
            heapq.heappush(debtors, (-remaining_debt, debt_name))

    return transactions


def compute_balances(expenses: list, participants: list) -> dict[str, float]:
    """
    Compute each participant's net balance from a list of expense records.

    Args:
        expenses: list of Expense ORM objects with attributes:
                  paid_by (str), amount (float), split_among (str, comma-separated)
        participants: list of Participant ORM objects with attribute: name (str)

    Returns:
        {name: net_balance}
    """
    balances = {p.name: 0.0 for p in participants}

    for expense in expenses:
        payer = expense.paid_by
        amount = float(expense.amount)
        split_names = [n.strip() for n in expense.split_among.split(",") if n.strip()]

        if not split_names:
            continue

        share = round(amount / len(split_names), 2)

        # Payer gains credit equal to the full amount
        balances[payer] = round(balances.get(payer, 0.0) + amount, 2)

        # Everyone in the split owes their share
        for name in split_names:
            balances[name] = round(balances.get(name, 0.0) - share, 2)

    return balances
