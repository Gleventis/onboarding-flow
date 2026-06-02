"""
Scenario fixture data for the CLI flow runner.

Each fixture dict matches the form schema for that step, with field values
chosen to trigger the desired mock outcome via the MAPPERS chain.
"""

PRIVATE_FIXTURES: dict[str, dict[str, dict]] = {
    "happy": {
        "personal_details": {
            "first_name": "Anna",
            "last_name": "Svensson",
            "personnummer": "199001013",
        },
        "contact_info": {
            "street": "Kungsgatan 1",
            "city": "Stockholm",
            "postal_code": "11143",
            "phone": "+46701234567",
            "email": "anna@example.com",
        },
        "employment": {
            "employer_name": "Spotify",
            "employment_status": "employed",
            "income": 50000.0,
            "debt": 0.0,
        },
        "bank_account": {
            "iban": "SE3550000000054910000003",
            "bank_name": "SEB",
            "account_holder_name": "Anna Svensson",
        },
        "consent": {"terms_accepted": True},
    },
    "rejected": {
        "personal_details": {
            "first_name": "confirmed_Anna",
            "last_name": "Target",
            "personnummer": "199001013",
        },
    },
    "manual-review": {
        "personal_details": {
            "first_name": "possible",
            "last_name": "Person",
            "personnummer": "199001013",
        },
        "contact_info": {
            "street": "Storgatan 5",
            "city": "Gothenburg",
            "postal_code": "41101",
            "phone": "+46709876543",
            "email": "possible@example.com",
        },
        "employment": {
            "employer_name": "Startup AB",
            "employment_status": "employed",
            "income": 30.0,
            "debt": 0.0,
        },
        "bank_account": {
            "iban": "SE3550000000054910000003",
            "bank_name": "Nordea",
            "account_holder_name": "possible Person",
        },
        "consent": {"terms_accepted": True},
    },
}

BUSINESS_FIXTURES: dict[str, dict[str, dict]] = {
    "happy": {
        "company_details": {
            "company_name": "Acme AB",
            "registration_number": "5591234567",
        },
        "personal_details": {
            "first_name": "Erik",
            "last_name": "Johansson",
            "personnummer": "198505053",
        },
        "contact_info": {
            "street": "Vasagatan 10",
            "city": "Stockholm",
            "postal_code": "11120",
            "phone": "+46701112233",
            "email": "erik@acme.se",
        },
        "bank_account": {
            "iban": "SE4550000000058398257466",
            "bank_name": "Handelsbanken",
            "account_holder_name": "Acme AB",
        },
        "consent": {"terms_accepted": True},
    },
    "rejected": {
        "company_details": {
            "company_name": "confirmed Corp",
            "registration_number": "5591234567",
        },
    },
    "manual-review": {
        "company_details": {
            "company_name": "possible Ventures",
            "registration_number": "5591234567",
        },
        "personal_details": {
            "first_name": "Lars",
            "last_name": "Nilsson",
            "personnummer": "197003033",
        },
        "contact_info": {
            "street": "Drottninggatan 20",
            "city": "Malmo",
            "postal_code": "21141",
            "phone": "+46704445566",
            "email": "lars@possible.se",
        },
        "bank_account": {
            "iban": "SE6550000000052601100116",
            "bank_name": "Swedbank",
            "account_holder_name": "possible Ventures",
        },
        "consent": {"terms_accepted": True},
    },
}


if __name__ == "__main__":
    print(f"PRIVATE_FIXTURES scenarios: {list(PRIVATE_FIXTURES.keys())}")
    print(f"BUSINESS_FIXTURES scenarios: {list(BUSINESS_FIXTURES.keys())}")
