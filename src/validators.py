
from datetime import date
from difflib import SequenceMatcher
import re

# BIAI assessment reference date
REFERENCE_DATE = date(2026, 11, 1)

CLOSED_STAGES = {"Paid", "Lost"}

REQUIRED_FIELDS = {
    "contact_name": "Contact name",
    "contact_role": "Contact role",
    "contact_email": "Contact email",
    "contact_phone": "Contact phone",
}


# 1. Remove extra spaces and handle missing values
def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


# 2. Standardize company names
def normalize_company(name):
    name = clean_text(name).lower()
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


# 3. Standardize email addresses for comparison
def normalize_email(email):
    return clean_text(email).lower()


# 4. Check basic email syntax
def is_valid_email(email):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.fullmatch(pattern, clean_text(email)))


# 5. Convert a date string into a Python date
def parse_date(value):
    value = clean_text(value)

    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


# 6. Compare company name and email domain
def check_email_company_similarity(company, email):
    if not company or not is_valid_email(email):
        return None

    # Example: shahidul@bogurateXtile.example
    # Domain label becomes "boguratextile"
    domain = email.split("@", 1)[1].split(".")[0].lower()

    # Example: "Bogura Textile Mills" -> "boguratextilemills"
    company_clean = re.sub(
        r"[^a-z0-9]",
        "",
        clean_text(company).lower()
    )

    similarity = SequenceMatcher(
        None,
        company_clean,
        domain
    ).ratio()

    return round(similarity, 2)


# 7. Detect all data quality issues
def detect_issues(leads, reference_date=REFERENCE_DATE):
    issues = []

    # Helper function for adding issues
    def add_issue(lead_id, category, details, severity="Medium"):
        issues.append({
            "lead_id": lead_id,
            "type": category,
            "details": details,
            "severity": severity
        })

    # Check every lead
    for lead in leads:
        lead_id = lead["lead_id"]
        company = clean_text(lead.get("company"))
        notes = clean_text(lead.get("notes")).lower()
        stage = clean_text(lead.get("stage"))

        email = clean_text(lead.get("contact_email"))
        phone = clean_text(lead.get("contact_phone"))

        # CHECK 1: Missing contact information
        for field, label in REQUIRED_FIELDS.items():
            if not clean_text(lead.get(field)):
                add_issue(
                    lead_id,
                    f"Missing {label.lower()}",
                    f"{label} is empty"
                )

        # CHECK 2: Invalid email syntax
        if email and not is_valid_email(email):
            add_issue(
                lead_id,
                "Invalid email format",
                "Email has an invalid structure",
                "High"
            )

        # CHECK 3: Email warnings in notes
        email_warning = (
            "email" in notes
            and any(
                word in notes
                for word in [
                    "typo",
                    "wrong",
                    "incorrect",
                    "verify",
                    "check before sending"
                ]
            )
        )

        if email_warning:
            add_issue(
                lead_id,
                "Email needs verification",
                "Notes indicate a possible email problem",
                "High"
            )

        # CHECK 4: Company/email similarity
        similarity = check_email_company_similarity(
            company,
            email
        )

        # Similarity is only a clue, not proof.
        # Do not flag solely because of a low score.
        # Companies can use unrelated or abbreviated domains.

        # CHECK 5: Conflicting contact information
        if (
            "no phone or email" in notes
            and (email or phone)
        ):
            add_issue(
                lead_id,
                "Contact information conflict",
                "Notes say no email or phone, but contact data exists"
            )

        # CHECK 6: Validate dates
        last_raw = clean_text(lead.get("last_contact"))
        next_raw = clean_text(lead.get("next_follow_up"))

        last_date = parse_date(last_raw)
        next_date = parse_date(next_raw)

        if last_raw and last_date is None:
            add_issue(
                lead_id,
                "Invalid last contact date",
                f"Invalid date: {last_raw}",
                "High"
            )

        if next_raw and next_date is None:
            add_issue(
                lead_id,
                "Invalid follow-up date",
                f"Invalid date: {next_raw}",
                "High"
            )

        # CHECK 7: Wrong date order
        date_inconsistent = (
            last_date is not None
            and next_date is not None
            and next_date < last_date
        )

        if date_inconsistent:
            add_issue(
                lead_id,
                "Date inconsistency",
                "Follow-up date is before last contact",
                "High"
            )

        # CHECK 8: Overdue follow-ups
        if (
            next_date is not None
            and next_date < reference_date
            and stage not in CLOSED_STAGES
        ):
            days = (reference_date - next_date).days

            details = f"Overdue by {days} days"

            if date_inconsistent:
                details += " (date needs correction)"

            add_issue(
                lead_id,
                "Overdue follow-up",
                details,
                "High"
            )

        # CHECK 9: Payment status conflict
        partial_payment = any(
            phrase in notes
            for phrase in [
                "50 percent",
                "partial payment",
                "second payment"
            ]
        )

        if stage == "Paid" and partial_payment:
            add_issue(
                lead_id,
                "Payment status conflict",
                "Paid stage conflicts with payment notes",
                "High"
            )

        # CHECK 10: Payment verification
        if (
            stage == "Invoice sent"
            and (
                "paid?" in notes
                or "check bank" in notes
            )
        ):
            add_issue(
                lead_id,
                "Payment verification needed",
                "Confirm payment before contacting client"
            )

    # CHECK 11: Detect duplicate leads
    for i in range(len(leads)):
        for j in range(i + 1, len(leads)):
            first = leads[i]
            second = leads[j]

            name_a = normalize_company(first["company"])
            name_b = normalize_company(second["company"])

            email_a = normalize_email(first["contact_email"])
            email_b = normalize_email(second["contact_email"])

            phone_a = clean_text(first["contact_phone"])
            phone_b = clean_text(second["contact_phone"])

            same_name = bool(name_a) and name_a == name_b
            same_email = bool(email_a) and email_a == email_b
            same_phone = bool(phone_a) and phone_a == phone_b

            similarity = SequenceMatcher(
                None,
                name_a,
                name_b
            ).ratio()

            duplicate = (
                same_name
                or (same_email and same_phone)
                or (same_email and similarity >= 0.65)
            )

            if duplicate:
                add_issue(
                    first["lead_id"],
                    "Possible duplicate",
                    f"Possible match with {second['lead_id']}",
                    "High"
                )

                add_issue(
                    second["lead_id"],
                    "Possible duplicate",
                    f"Possible match with {first['lead_id']}",
                    "High"
                )

    # Must be inside detect_issues(), after both loops
    return issues
