
import streamlit as st
import pandas as pd
import plotly.express as px
from src.ai_service import generate_follow_up_email, generate_weekly_summary
from src.lead_assistant import answer_lead_question
from src.database import (
    initialize_database,
    get_all_leads,
    update_lead
)
from src.validators import detect_issues


# 1. Configure Streamlit
st.set_page_config(
    page_title="BIAI LeadPilot",
    page_icon="📊",
    layout="wide"
)


# 2. Load data from SQLite
initialize_database()

leads = get_all_leads()
issues = detect_issues(leads)

leads_df = pd.DataFrame(leads)
issues_df = pd.DataFrame(issues)


# 3. Calculate summary metrics
total_leads = len(leads)

flagged_leads = len({
    issue["lead_id"] for issue in issues
})

overdue_count = sum(
    issue["type"] == "Overdue follow-up"
    for issue in issues
)

total_pipeline_value = leads_df["deal_value_bdt"].sum()

proposal_value = leads_df.loc[
    leads_df["stage"] == "Proposal",
    "deal_value_bdt"
].sum()


# 4. Prepare pipeline chart data
stage_order = [
    "New",
    "Contacted",
    "Meeting",
    "Proposal",
    "Invoice sent",
    "Paid",
    "Lost"
]

stage_counts = (
    leads_df.groupby("stage")
    .size()
    .reindex(stage_order, fill_value=0)
    .reset_index(name="count")
)


# 5. Prepare overdue leads
overdue_ids = {
    issue["lead_id"]
    for issue in issues
    if issue["type"] == "Overdue follow-up"
}

overdue_df = leads_df[
    leads_df["lead_id"].isin(overdue_ids)
].copy()


# 6. Application heading
st.title("BIAI LeadPilot")
st.subheader("Corporate Leads Pipeline")


# 7. Main summary cards
col1, col2, col3 = st.columns(3)

col1.metric("Total Lead Records", total_leads)
col2.metric("Flagged Leads", flagged_leads)
col3.metric("Overdue Follow-ups", overdue_count)


# 8. Create three tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Dashboard",
    "All Leads",
    "Data Quality Issues",
    "AI Email Generator",
    "Ask LeadPilot AI",
    "Review & Correct"
])
# TAB 1: DASHBOARD
with tab1:
    st.header("Sales Pipeline Dashboard")

    st.caption(
        "Reference date: November 1, 2026. "
        "Deal values include unreviewed duplicate records."
    )

    # Financial summary
    m1, m2 = st.columns(2)

    m1.metric(
        "Total Recorded Deal Value",
        f"৳{total_pipeline_value:,.0f}"
    )

    m2.metric(
        "Proposal Stage Value",
        f"৳{proposal_value:,.0f}"
    )

    # Chart 1: Number of leads by stage
    st.subheader("Leads by Pipeline Stage")

    fig = px.bar(
        stage_counts,
        x="stage",
        y="count",
        color="stage",
        text="count",
        category_orders={"stage": stage_order},
        labels={
            "stage": "Pipeline Stage",
            "count": "Number of Leads"
        }
    )

    fig.update_layout(showlegend=False)

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # Chart 2: Deal value by stage
    st.subheader("Deal Value by Stage")

    stage_values = (
        leads_df.groupby("stage")["deal_value_bdt"]
        .sum()
        .reindex(stage_order, fill_value=0)
        .reset_index()
    )

    value_fig = px.bar(
        stage_values,
        x="stage",
        y="deal_value_bdt",
        text="deal_value_bdt",
        category_orders={"stage": stage_order},
        labels={
            "stage": "Pipeline Stage",
            "deal_value_bdt": "Deal Value (BDT)"
        }
    )

    st.plotly_chart(
        value_fig,
        use_container_width=True
    )

    # Overdue follow-up queue
    st.subheader("Overdue Follow-up Queue")

    if not overdue_df.empty:
        st.dataframe(
            overdue_df[
                [
                    "lead_id",
                    "company",
                    "contact_name",
                    "stage",
                    "next_follow_up",
                    "notes"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "L25 has inconsistent dates and needs review "
            "before its follow-up deadline is trusted."
        )
    else:
        st.success("No overdue follow-ups.")

    # Duplicate warning
    duplicate_issues = [
        issue
        for issue in issues
        if issue["type"] == "Possible duplicate"
    ]

    if duplicate_issues:
        st.warning(
            "Possible duplicate records detected. "
            "Pipeline totals may be overstated."
        )
    # AI WEEKLY SALES SUMMARY
    st.divider()
    st.subheader("AI Weekly Sales Priorities")

    st.write(
        "Generate an AI-powered weekly action plan "
        "to identify which corporate leads to chase first."
    )

    if st.button("Generate Weekly AI Summary", type="primary"):
        try:
            with st.spinner("Generating weekly sales priorities..."):
                summary = generate_weekly_summary(get_all_leads())

            st.session_state["weekly_ai_summary"] = summary

        except Exception as error:
            st.error(f"Summary generation failed: {error}")

    if st.session_state.get("weekly_ai_summary"):
        st.markdown(st.session_state["weekly_ai_summary"])

        st.download_button(
            label="Download Weekly Summary",
            data=st.session_state["weekly_ai_summary"],
            file_name="BIAI_Weekly_Sales_Summary.txt",
            mime="text/plain"
        )

# TAB 2: ALL LEADS
with tab2:
    st.header("All Corporate Leads")

    st.dataframe(
        leads_df,
        use_container_width=True,
        hide_index=True
    )
    st.subheader("Export Sales Pipeline")

    pipeline_df = pd.DataFrame(get_all_leads())

    st.download_button(
      label="Download Full Pipeline (CSV)",
      data=pipeline_df.to_csv(index=False).encode("utf-8-sig"),
      file_name="BIAI_LeadPilot_Pipeline.csv",
      mime="text/csv",
      key="download_full_pipeline"
)


# TAB 3: DATA QUALITY ISSUES
with tab3:
    st.subheader("Data Quality Review")

    st.write(
        "Issues are flagged for review. "
        "Original lead records are preserved."
    )

    if not issues_df.empty:
        unique_flagged = issues_df["lead_id"].nunique()

        high_priority = (
            issues_df["severity"] == "High"
        ).sum()

        col_a, col_b, col_c = st.columns(3)

        col_a.metric(
            "Flagged Lead Records",
            unique_flagged
        )

        col_b.metric(
            "Total Issue Flags",
            len(issues_df)
        )

        col_c.metric(
            "High Severity Flags",
            int(high_priority)
        )

        selected_type = st.selectbox(
            "Filter by issue type",
            ["All"] + sorted(
                issues_df["type"].unique().tolist()
            )
        )

        filtered = issues_df.copy()

        if selected_type != "All":
            filtered = filtered[
                filtered["type"] == selected_type
            ]

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Export Issues CSV",
            data=issues_df.to_csv(index=False),
            file_name="biai_data_quality_report.csv",
            mime="text/csv"
        )

    else:
        st.success("No issues detected.")

# TAB 4: AI EMAIL GENERATOR
with tab4:
    st.header("AI Follow-up Email Generator")

    st.caption("Powered by Google Gemini AI")

    lead_options = {
        f"{lead['lead_id']} - {lead['company']}": lead
        for lead in leads
    }

    selected_label = st.selectbox(
        "Select a corporate lead",
        list(lead_options.keys())
    )

    selected_lead = lead_options[selected_label]
    selected_id = selected_lead["lead_id"]

    st.subheader("Lead Information")

    st.write("**Company:**", selected_lead["company"])
    st.write("**Contact:**", selected_lead["contact_name"])
    st.write("**Stage:**", selected_lead["stage"])
    st.write("**Notes:**", selected_lead["notes"])

    # Clear the previous draft when switching leads
    if st.session_state.get("active_lead_id") != selected_id:
        st.session_state["active_lead_id"] = selected_id
        st.session_state["email_draft"] = ""

    if st.button("Generate AI Email", type="primary"):
        with st.spinner("Generating personalized email..."):
            try:
                draft = generate_follow_up_email(selected_lead)
                st.session_state["email_draft"] = draft

            except Exception as error:
                st.error(f"Email generation failed: {error}")

    if st.session_state.get("email_draft"):
        st.subheader("Generated Email Draft")

        edited_draft = st.text_area(
            "Review and edit the email",
            value=st.session_state["email_draft"],
            height=300
        )

        st.download_button(
            "Download Email Draft",
            data=edited_draft,
            file_name=f"followup_{selected_id}.txt",
            mime="text/plain"
        )

        st.info(
            "AI-generated draft. Review before sending. "
            "No email is sent automatically."
        )

# TAB 5: NATURAL LANGUAGE LEAD ASSISTANT
with tab5:
    st.header("Ask LeadPilot AI")

    st.write(
        "Ask questions about the corporate leads, "
        "sales pipeline, and data quality."
    )

    question = st.text_input(
        "Your question",
        placeholder="Which leads are overdue?"
    )

    if st.button("Ask AI", type="primary"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Analyzing lead data..."):
                try:
                    answer = answer_lead_question(
                        question,
                        leads,
                        issues
                    )

                    st.session_state["lead_answer"] = answer

                except Exception as error:
                    st.error(f"Could not answer: {error}")

    if st.session_state.get("lead_answer"):
        st.subheader("AI Answer")
        st.write(st.session_state["lead_answer"])

# TAB 6: REVIEW AND CORRECT
with tab6:
    st.header("Review & Correct Lead Records")

    st.write(
        "Select a lead, review its information, "
        "and save corrections to the SQLite database."
    )

    lead_lookup = {
        f"{lead['lead_id']} - {lead['company']}": lead
        for lead in leads
    }

    selected_label = st.selectbox(
        "Choose a lead to review",
        list(lead_lookup.keys()),
        key="correction_lead"
    )

    selected_lead = lead_lookup[selected_label]

    lead_issues = [
        issue
        for issue in issues
        if issue["lead_id"] == selected_lead["lead_id"]
    ]

    if lead_issues:
        st.warning(
            f"{len(lead_issues)} issue(s) detected "
            "for this lead."
        )

        st.dataframe(
            pd.DataFrame(lead_issues),
            hide_index=True,
            use_container_width=True
        )
    else:
        st.success("No issues currently flagged.")

    with st.form(
        key=f"lead_correction_form_{selected_lead['lead_id']}"
        ):

        company = st.text_input(
            "Company",
            value=selected_lead["company"] or ""
        )

        contact_name = st.text_input(
            "Contact Name",
            value=selected_lead["contact_name"] or ""
        )

        contact_role = st.text_input(
            "Contact Role",
            value=selected_lead["contact_role"] or ""
        )

        contact_email = st.text_input(
            "Contact Email",
            value=selected_lead["contact_email"] or ""
        )

        contact_phone = st.text_input(
            "Contact Phone",
            value=selected_lead["contact_phone"] or ""
        )

        stages = [
            "New",
            "Contacted",
            "Meeting",
            "Proposal",
            "Invoice sent",
            "Paid",
            "Lost"
        ]

        stage = st.selectbox(
            "Sales Stage",
            stages,
            index=stages.index(selected_lead["stage"])
        )

        last_contact = st.text_input(
            "Last Contact (YYYY-MM-DD)",
            value=selected_lead["last_contact"] or ""
        )

        next_follow_up = st.text_input(
            "Next Follow-up (YYYY-MM-DD)",
            value=selected_lead["next_follow_up"] or ""
        )

        notes = st.text_area(
            "Notes",
            value=selected_lead["notes"] or ""
        )

        submitted = st.form_submit_button(
            "Save Corrections",
            type="primary"
        )

        if submitted:
            updates = {
                "company": company,
                "contact_name": contact_name,
                "contact_role": contact_role,
                "contact_email": contact_email,
                "contact_phone": contact_phone,
                "stage": stage,
                "last_contact": last_contact,
                "next_follow_up": next_follow_up,
                "notes": notes
            }

            try:
                success = update_lead(
                    selected_lead["lead_id"],
                    updates
                )

                if success:
                    st.success("Lead updated successfully!")
                    st.rerun()
                else:
                    st.error(
                        "No record was updated. "
                        "Check the lead ID."
                    )

            except Exception as error:
                st.error(f"Database error: {error}")

