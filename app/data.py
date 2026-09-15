MEMBERS = {}

for number in range(10001, 10031):
    member_id = str(number)

    MEMBERS[member_id] = {
        "name": f"Test Member {number}",
        "checking_balance": round(
            1000 + (number % 17) * 137.25,
            2,
        ),
        "savings_balance": round(
            2500 + (number % 23) * 211.40,
            2,
        ),
    }


MEMBERS["12345"] = {
    "name": "Alex Morgan",
    "checking_balance": 2450.75,
    "savings_balance": 7481.22,
}

MEMBERS["55555"] = {
    "name": "Jordan Lee",
    "checking_balance": 980.10,
    "savings_balance": 5229.91,
}

MEMBERS["88888"] = {
    "name": "Taylor Brooks",
    "checking_balance": 1735.40,
    "savings_balance": 6310.25,
}

MEMBERS["33333"] = {
    "name": "Morgan Reed",
    "checking_balance": 1840.60,
    "savings_balance": 9025.45,
}


SPECIAL_CASES = {
    "77777": "permission_denied",
    "88888": "slow_response",
    "66666": "session_expired",
    "33333": "human_approval_required",
    "22222": "application_error",
}