# BIAI LeadPilot — AI-Powered Corporate Leads CRM

An AI-assisted corporate leads management application built to help sales teams monitor opportunities, identify data-quality problems, prioritize follow-ups, and draft personalized outreach.

**Live Application:** https://biai-leadpilot-uf9vzr43j3ck6rinzq8g9e.streamlit.app/

## Problem Statement

Corporate sales teams often manage leads using spreadsheets. This can create duplicate records, inconsistent pipeline information, missed follow-ups, and time-consuming manual communication.

BIAI LeadPilot provides a centralized interface for reviewing leads, identifying operational issues, and supporting sales decisions with AI.

## Key Features

**1. Sales Dashboard**
- Overview of 25 sample corporate leads.
- Lead distribution across sales stages.
- Pipeline value visualization.
- Overdue follow-up monitoring.

**2. Data Quality Detection**
- Flags potential duplicate leads.
- Identifies missing contact information.
- Detects overdue follow-ups and inconsistent records.
- Supports exporting issues for review.

**3. AI Email Generator**
- Uses Google's Gemini API to draft contextual follow-up emails.
- Incorporates available lead information.
- Allows users to review and edit generated drafts before use.

**4. Ask LeadPilot AI**
- Provides a natural-language interface for questions about the lead pipeline.
- Uses calculated lead information to support answers.
- Helps users explore pipeline performance without manually filtering records.

**5. Review & Correct**
- Allows users to inspect and update lead information.
- Saves corrections to a SQLite database during the running application session.

## Technology Stack

- Python
- Streamlit
- SQLite
- Pandas
- Plotly
- Google Gemini API

## Running Locally

1. Clone the repository.
2. Install dependencies:

   `pip install -r requirements.txt`

3. Configure the `GEMINI_API_KEY` environment variable.
4. Start the application:

   `python -m streamlit run app.py`

## Architecture

- `app.py` — Streamlit interface and application workflows.
- `src/database.py` — SQLite database initialization and lead updates.
- `src/validators.py` — Data-quality validation rules.
- `src/ai_service.py` — AI-powered email drafting.
- `src/lead_assistant.py` — Natural-language lead assistant.
- `data/corporate-leads.csv` — Sample corporate leads dataset.

## Limitations

- The application uses a sample dataset rather than a live enterprise CRM.
- Pipeline totals may include duplicate records until they are reviewed.
- AI-generated responses require human verification.
- SQLite storage on Streamlit Community Cloud is not guaranteed to persist after application restarts.
- Authentication, role-based access and production-grade audit logging are not implemented.

## Future Improvements

- Persistent hosted database.
- User authentication and access controls.
- Automated follow-up notifications.
- CRM integrations and lead activity history.

## Project Context

Developed as a BIAI Round 2 technical assessment to demonstrate practical application development, AI integration, data validation, and business-focused problem solving.