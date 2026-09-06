# core/support_flow.py

SUPPORT_CATEGORIES = [
    {"id": "PAYMENT", "label": "Payment / Earnings"},
    {"id": "SERVICE", "label": "Service / Booking"},
    {"id": "WALLET", "label": "Wallet / Withdrawal"},
    {"id": "INCENTIVE", "label": "Incentive / Reward"},
    {"id": "TECH", "label": "App / Technical Issue"},
    {"id": "ACCOUNT", "label": "Account / Profile"},
    {"id": "OTHER", "label": "Other"},
]

SUPPORT_TREE = {
    "PAYMENT": {
        "question": "What problem are you facing with your payments?",
        "options": [
            {"id": "MISSING", "label": "Missing earnings", "next": "PAY_MISSING_1"},
            {"id": "DELAYED", "label": "Payment delayed", "next": "PAY_DELAYED_1"},
            {"id": "NOT_CREDITED", "label": "Completed service not credited", "next": "PAY_MISSING_1"},
            {"id": "INCORRECT", "label": "Incorrect earnings", "next": "PAY_INCORRECT_1"},
            {"id": "OTHER", "label": "Other payment issue", "next": "ESCALATE_PROMPT"}
        ]
    },
    "PAY_MISSING_1": {
        "text": "Please check whether the service is marked 'Completed' and check your Wallet -> Earnings section.",
        "question": "Did this solve your problem?",
        "options": [
            {"id": "YES", "label": "Yes, Problem Solved", "next": "SOLVED"},
            {"id": "NO", "label": "No, Still Having Problem", "next": "PAY_MISSING_2"}
        ]
    },
    "PAY_MISSING_2": {
        "text": "Sometimes there is a slight delay in syncing your completed jobs. Please try refreshing the app.",
        "question": "Did this solve your problem?",
        "options": [
            {"id": "YES", "label": "Yes, Problem Solved", "next": "SOLVED"},
            {"id": "NO", "label": "No, Still Having Problem", "next": "ESCALATE_PROMPT"}
        ]
    },
    "PAY_DELAYED_1": {
        "text": "Online payments can take up to 2-3 hours to reflect in your wallet after the customer pays.",
        "question": "Has it been more than 3 hours?",
        "options": [
            {"id": "YES", "label": "Yes", "next": "ESCALATE_PROMPT"},
            {"id": "NO", "label": "No", "next": "SOLVED_WAIT"}
        ]
    },
    "PAY_INCORRECT_1": {
        "text": "The final amount may be different if a discount or offer was applied to the booking.",
        "question": "Did this solve your problem?",
        "options": [
            {"id": "YES", "label": "Yes", "next": "SOLVED"},
            {"id": "NO", "label": "No, contact admin", "next": "ESCALATE_PROMPT"}
        ]
    },
    "SERVICE": {
        "question": "Which booking issue are you facing?",
        "options": [
            {"id": "CUSTOMER_ISSUE", "label": "Customer issue (not reachable/location wrong)", "next": "ESCALATE_PROMPT"},
            {"id": "CANCELLATION", "label": "Cancellation issue", "next": "ESCALATE_PROMPT"},
            {"id": "OTHER", "label": "Other", "next": "ESCALATE_PROMPT"}
        ]
    },
    "WALLET": {
        "question": "What wallet or withdrawal issue do you have?",
        "options": [
            {"id": "BAL_INCORRECT", "label": "Wallet balance incorrect", "next": "ESCALATE_PROMPT"},
            {"id": "WITHDRAW_PENDING", "label": "Withdrawal pending", "next": "WITHDRAW_1"},
            {"id": "WITHDRAW_FAILED", "label": "Withdrawal failed", "next": "ESCALATE_PROMPT"},
            {"id": "OTHER", "label": "Other", "next": "ESCALATE_PROMPT"}
        ]
    },
    "WITHDRAW_1": {
        "text": "Withdrawals typically take 24-48 business hours to process to your bank account.",
        "question": "Has it been more than 48 hours?",
        "options": [
            {"id": "YES", "label": "Yes", "next": "ESCALATE_PROMPT"},
            {"id": "NO", "label": "No", "next": "SOLVED_WAIT"}
        ]
    },
    "INCENTIVE": {
        "question": "What incentive problem are you facing?",
        "options": [
            {"id": "NOT_CREDITED", "label": "Incentive not credited", "next": "ESCALATE_PROMPT"},
            {"id": "CALCULATION", "label": "Reward calculation issue", "next": "ESCALATE_PROMPT"},
            {"id": "OTHER", "label": "Other", "next": "ESCALATE_PROMPT"}
        ]
    },
    "TECH": {
        "question": "What technical issue are you facing?",
        "options": [
            {"id": "GPS", "label": "GPS/Tracking issue", "next": "TECH_1"},
            {"id": "NOTIFICATIONS", "label": "Notification issue", "next": "TECH_1"},
            {"id": "OTHER", "label": "Other technical problem", "next": "ESCALATE_PROMPT"}
        ]
    },
    "TECH_1": {
        "text": "Please check if you have given Seva Bandhu app the necessary permissions in your phone's settings.",
        "question": "Did this solve your problem?",
        "options": [
            {"id": "YES", "label": "Yes", "next": "SOLVED"},
            {"id": "NO", "label": "No, Still Having Problem", "next": "ESCALATE_PROMPT"}
        ]
    },
    "ACCOUNT": {
        "question": "What profile issue do you have?",
        "options": [
            {"id": "INFO", "label": "Profile information problem", "next": "ESCALATE_PROMPT"},
            {"id": "LOGIN", "label": "Login problem", "next": "ESCALATE_PROMPT"},
            {"id": "OTHER", "label": "Other", "next": "ESCALATE_PROMPT"}
        ]
    },
    "OTHER": {
        "question": "Would you like to try guided support again or contact Admin?",
        "options": [
            {"id": "CONTACT", "label": "Contact Admin", "next": "ESCALATE_PROMPT"}
        ]
    },
    "SOLVED": {
        "text": "Great! We're glad we could help.",
        "end": True
    },
    "SOLVED_WAIT": {
        "text": "Please wait a little longer. If it's still not resolved later, you can reach out again.",
        "end": True
    },
    "ESCALATE_PROMPT": {
        "text": "We couldn't resolve your issue automatically.\nWould you like to contact an Admin?",
        "options": [
            {"id": "CONTACT_ADMIN", "label": "Contact Admin", "escalate": True},
            {"id": "END", "label": "No, thank you", "next": "SOLVED"}
        ]
    }
}

