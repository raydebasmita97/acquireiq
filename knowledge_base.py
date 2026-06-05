import streamlit as st
import os

BASE_DOCUMENTS = {
    "Company Overview": """Johnson Home Health Services, Dallas TX. Founded 2005.
45 employees. $8M annual revenue. Provides skilled nursing, physical therapy,
and personal care services. Serves 180 active patients across Dallas, Plano,
and Frisco. Medicare and Medicaid certified. Owner David Johnson retiring after
20 years. Strong community reputation built over two decades.""",

    "Top 10 Customers": """1. Sunrise Senior Living - $420K annual, 8 year relationship,
contact Maria Chen, renewal March 2027.
2. Presbyterian Hospital - $380K annual, 5 year relationship, contact Dr. James Wilson,
renewal June 2026.
3. Baylor Scott White - $340K annual, 3 year relationship, contact Sarah Mitchell,
renewal September 2026.
4. Methodist Health - $290K annual, 6 year relationship, contact Tom Bradley,
renewal December 2026.
5. Kindred Healthcare - $265K annual, 4 year relationship, contact Lisa Park,
renewal February 2027.
6. Encompass Health - $240K annual, 2 year relationship, contact Robert Hayes,
renewal August 2026.
7. Amedisys - $210K annual, 5 year relationship, contact Jennifer Wu,
renewal November 2026.
8. LHC Group - $195K annual, 3 year relationship, contact David Kim,
renewal May 2027.
9. Acadia Healthcare - $175K annual, 2 year relationship, contact Amanda Torres,
renewal July 2026.
10. Select Medical - $160K annual, 1 year relationship, contact Michael Brown,
renewal October 2026.""",

    "Employee Roster": """1. Sarah Martinez - Director of Nursing, 12 years tenure,
top performer, manages all clinical staff, critical to retain.
2. James Wilson - Operations Manager, 8 years tenure, strong performer,
handles scheduling and logistics.
3. Lisa Chen - Billing Manager, 6 years tenure, top performer,
99 percent billing accuracy.
4. Robert Davis - HR Manager, 4 years tenure, strong performer.
5. Maria Rodriguez - Lead RN, 10 years tenure, top performer,
patients love her.
6. Tom Anderson - Physical Therapist, 7 years tenure, strong performer.
7. Jennifer Lee - Caregiver Supervisor, 5 years tenure, strong performer.
8. David Park - IT Coordinator, 3 years tenure, average performer,
knows all the systems.
9. Amanda Johnson - Marketing Coordinator, 2 years tenure, strong performer.
10. Michael Chen - Finance Analyst, 4 years tenure, top performer,
knows the books inside out.""",

    "Financial Summary": """Monthly revenue last 12 months in thousands:
Jan 620, Feb 635, Mar 658, Apr 642, May 671, Jun 689, Jul 695, Aug 702,
Sep 718, Oct 725, Nov 731, Dec 748. Total annual revenue 8.03M.
Top expenses: Caregiver salaries 45 percent, Administrative 15 percent,
Medical supplies 10 percent, Insurance 8 percent, Technology 5 percent.
Gross margin 22 percent. Accounts receivable average 38 days.
Revenue mix: Medicare 55 percent, Medicaid 25 percent, Private pay 20 percent.""",

    "Operational SOPs": """Caregiver Scheduling: Requests via phone or portal.
Scheduler matches caregiver to patient based on skills location and availability.
Confirmation sent 24 hours before visit. Average response time 4 hours.
Billing Process: Visit completed, caregiver submits notes within 2 hours.
Billing team reviews and submits claim within 48 hours. Average approval 38 days.
Rejection rate 3.2 percent.
Patient Intake: Referral received, intake coordinator contacts within 24 hours,
assessment scheduled within 72 hours, first visit within 5 days of referral.
Emergency Protocol: On-call RN available 24/7, escalation to Director of Nursing
within 30 minutes for critical issues.""",

    "Vendor Contracts": """1. MedBridge training platform - $48K annual,
renews March 2026, critical for staff training.
2. Brightree EMR system - $96K annual, renews July 2026, core operations system.
3. Sandata visit verification - $36K annual, renews January 2026,
Medicare compliance required.
4. Paychex payroll - $24K annual, renews April 2026.
5. Travelers Insurance - $72K annual, renews June 2026, must not lapse.""",

    "First 90 Days Priorities": """Week 1: Meet all 10 key employees individually.
Review last 3 months of financials. Understand top 5 customer relationships.
Week 2 to 4: Ride-along with caregivers. Review billing rejection reasons.
Meet top 3 customers in person.
Month 2: Assess operational bottlenecks. Review all vendor contracts.
Identify automation opportunities.
Month 3: Present 90 day findings to SIG board. Propose first year growth plan.
Identify first hire if needed."""
}


def get_all_documents():
    """Return base documents (with any admin edits) merged with uploaded documents."""
    # Load admin edits/overrides to base docs
    try:
        from data_store import load_kb_overrides
        overrides = load_kb_overrides()
    except Exception:
        overrides = {}

    # Merge: start with base, apply overrides, allow new docs added via admin
    merged_base = {**BASE_DOCUMENTS}
    for name, text in overrides.items():
        merged_base[name] = text  # edit existing or add new

    # Uploaded docs from session state
    uploaded = {}
    if "uploaded_docs" in st.session_state:
        uploaded = st.session_state.uploaded_docs

    # Also load from uploaded_docs folder
    folder = "uploaded_docs"
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            doc_name = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
            if doc_name not in uploaded and doc_name not in merged_base:
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        uploaded[doc_name] = f.read()
                except Exception:
                    pass

    return {**merged_base, **uploaded}
