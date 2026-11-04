
import os
import json
import pandas as pd
from google import genai


MODEL_NAME = "gemini-3.5-flash-lite"


def answer_lead_question(question, leads, issues):
    """
    Answer questions using verified lead data.
    Gemini explains the results.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing.")

    df = pd.DataFrame(leads)

    # Calculate facts using Python
    stage_counts = df["stage"].value_counts().to_dict()

    stage_values = (
        df.groupby("stage")["deal_value_bdt"]
        .sum()
        .to_dict()
    )

    overdue_ids = sorted({
        issue["lead_id"]
        for issue in issues
        if issue["type"] == "Overdue follow-up"
    })

    duplicate_issues = [
        issue
        for issue in issues
        if issue["type"] == "Possible duplicate"
    ]

    flagged_ids = sorted({
        issue["lead_id"]
        for issue in issues
    })

    facts = {
        "reference_date": "2026-11-01",
        "total_leads": len(leads),
        "stage_counts": stage_counts,
        "stage_values_bdt": stage_values,
        "overdue_lead_ids": overdue_ids,
        "duplicate_warnings": duplicate_issues,
        "flagged_lead_ids": flagged_ids,
        "total_issue_flags": len(issues),
        "lead_records": [
            {
                "lead_id": lead["lead_id"],
                "company": lead["company"],
                "stage": lead["stage"],
                "deal_value_bdt": lead["deal_value_bdt"],
                "next_follow_up": lead["next_follow_up"]
            }
            for lead in leads
        ]
    }

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are BIAI LeadPilot's analytics assistant.

Answer the user's question using ONLY the supplied facts.

Question:
{question}

Verified dataset:
{json.dumps(facts, default=str)}

Rules:
- Never invent company names, dates or numbers.
- Deal values are in Bangladeshi Taka (BDT).
- Raw totals may include duplicate opportunities.
- Do not call recorded deal values actual revenue.
- Overdue status is based on November 1, 2026.
- L25 has inconsistent dates and needs review.
- If the data does not support an answer, say so.
- Keep answers clear and concise.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    if not response.text:
        raise RuntimeError("AI returned an empty response.")

    return response.text
