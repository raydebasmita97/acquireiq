import streamlit as st
import anthropic
import json
import jwt
import time
import requests
import traceback
from simple_salesforce import Salesforce

st.set_page_config(
    page_title="AcquireIQ",
    page_icon="🏢",
    layout="centered"
)

if "stage" not in st.session_state:
    st.session_state.stage = "form"
if "form_data" not in st.session_state:
    st.session_state.form_data = {}
if "result" not in st.session_state:
    st.session_state.result = None

def get_sf_connection():
    private_key_path = st.secrets["SF_PRIVATE_KEY_PATH"]
    with open(private_key_path, "r") as f:
        private_key = f.read()

    payload = {
        "iss": st.secrets["SF_CONSUMER_KEY"],
        "sub": st.secrets["SF_USERNAME"],
        "aud": "https://login.salesforce.com",
        "exp": int(time.time()) + 300
    }

    token = jwt.encode(payload, private_key, algorithm="RS256")

    response = requests.post(
        "https://login.salesforce.com/services/oauth2/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": token
        }
    )

    result = response.json()
    return Salesforce(
        instance_url=result["instance_url"],
        session_id=result["access_token"]
    )

def extract_and_score(data):
    client = anthropic.Anthropic(
        api_key=st.secrets["ANTHROPIC_API_KEY"]
    )

    prompt = f"""
    Score this business acquisition inquiry out of 10.
    Normalize from 13 total possible points.

    Scoring criteria:
    - Revenue $4M or more: 3 points
    - Target industry (healthcare, trades, distribution,
      professional services, manufacturing): 2 points
    - Legacy motivated seller not just price: 2 points
    - Exit timeline 12 months or less: 1 point
    - Has management team fully or partially: 1 point
    - Complete contact info with phone: 1 point
    - Strong existing team mentioned in notes: 1 point
    - Years in business over 5: 1 point
    - Employees over 10: 1 point

    To normalize: score = round((raw_points / 13) * 10, 1)

    Return ONLY this JSON with no preamble or backticks:
    {{
      "raw_points": 0,
      "qualification_score": 0.0,
      "score_reasoning": "explain each criterion and points awarded",
      "recommended_action": "Route to BD Team or Add to Review Queue",
      "key_strengths": "comma separated list of strengths",
      "key_concerns": "comma separated list of concerns"
    }}

    Inquiry:
    Contact: {data.get("contact_name")}
    Title: {data.get("contact_title")}
    Business: {data.get("business_name")}
    Industry: {data.get("industry")}
    Annual Revenue: ${data.get("revenue"):,}
    Employees: {data.get("employees")}
    Years in Business: {data.get("years_in_business")}
    Exit Timeline: {data.get("exit_timeline")} months
    Motivation: {data.get("motivation")}
    Management Team: {data.get("management_team")}
    Location: {data.get("location")}
    How Found: {data.get("how_found")}
    Reason for Selling: {data.get("reason")}
    Phone: {data.get("phone")}
    Email: {data.get("email")}
    Notes: {data.get("notes", "None")}
    """

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system="You are an acquisition analyst. Always respond with only valid JSON. No preamble, no markdown, no backticks.",
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text
    clean = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)

def create_salesforce_lead(form_data, ai_result):
    try:
        print("Attempting Salesforce connection...")
        sf = get_sf_connection()
        print("Salesforce connection successful.")

        name_parts = form_data.get("contact_name", "Unknown").strip().split(" ")
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "Unknown"

        location = form_data.get("location", "")

        description = form_data.get("reason", "")
        if form_data.get("notes"):
            description += " " + form_data.get("notes")

        state_data = {"CountryCode": "US", "StateCode": form_data.get("state", ""), "City": form_data.get("city", "")}

        lead_data = {
            "FirstName": first_name,
            "LastName": last_name,
            "Title": form_data.get("contact_title", ""),
            "Company": form_data.get("business_name", ""),
            "Email": form_data.get("email", ""),
            "Phone": form_data.get("phone", ""),
            "Industry": form_data.get("industry", ""),
            "LeadSource": form_data.get("how_found", ""),
            "AnnualRevenue": form_data.get("revenue", 0),
            "NumberOfEmployees": form_data.get("employees", 0),
            "Description": f"Location: {form_data.get('location', '')}\n{form_data.get('notes', '')}".strip(),
            **state_data,
            "Reason_for_Selling__c": form_data.get("reason", ""),
            "Years_in_Business__c": form_data.get("years_in_business", 0),
            "Exit_Timeline__c": form_data.get("exit_timeline", 99),
            "Primary_Motivation__c": form_data.get("motivation", ""),
            "Has_Management_Team__c": form_data.get("management_team", ""),
            "Qualification_Score__c": ai_result.get("qualification_score", 0),
            "Score_Reasoning__c": ai_result.get("score_reasoning", ""),
            "Key_Strengths__c": ai_result.get("key_strengths", ""),
            "Key_Concerns__c": ai_result.get("key_concerns", ""),
            "Recommended_Action__c": ai_result.get("recommended_action", "")
        }

        print("Lead data to be submitted:")
        print(json.dumps(lead_data, indent=2, default=str))

        result = sf.Lead.create(lead_data)
        print(f"Lead created: {result['id']}")
        return result

    except Exception as e:
        print(f"Salesforce error: {e}")
        traceback.print_exc()
        return None

# SCREEN 1 - FORM
if st.session_state.stage == "form":

    st.markdown("<h1 style='color:#1F4E79;margin-bottom:0;'>AcquireIQ</h1>", unsafe_allow_html=True)
    st.caption("Intelligent Lead Qualification for Business Acquisitions")
    st.subheader("Business Acquisition Inquiry")
    st.caption("Tell us about your business. We review every inquiry personally and respond within one business day.")
    st.divider()

    st.markdown("#### Contact Information")
    contact_name = st.text_input("Contact Person Full Name *", placeholder="First and last name")
    contact_title = st.selectbox("Your Title *", [
        "Select title", "Owner", "CEO", "President",
        "Partner", "Co-Founder", "Other"
    ])
    email = st.text_input("Contact Email *", placeholder="you@yourbusiness.com")
    phone = st.text_input("Contact Phone *", placeholder="e.g. 214-555-1234")

    st.divider()
    st.markdown("#### Business Information")

    business_name = st.text_input("Business Name *", placeholder="Your company name")
    industry = st.selectbox("Industry *", [
        "Select industry", "Home Healthcare",
        "HVAC and Heating and Air", "Plumbing",
        "Roofing and Siding", "Electrical",
        "Distribution and Supply", "Pharmacy",
        "Professional Services", "Manufacturing", "Other"
    ])

    col1, col2 = st.columns(2)
    with col1:
        revenue = st.number_input(
            "Annual Revenue ($) *",
            min_value=0,
            value=0,
            step=100000,
            help="Enter your annual revenue in dollars"
        )
    with col2:
        exit_timeline = st.number_input(
            "Exit Timeline (in months) *",
            min_value=1,
            max_value=120,
            value=12,
            help="How many months until you want to complete the sale?"
        )

    col3, col4 = st.columns(2)
    with col3:
        employees = st.number_input(
            "Number of Employees *",
            min_value=1,
            value=1
        )
    with col4:
        years_in_business = st.number_input(
            "Years in Business *",
            min_value=1,
            value=1
        )

    motivation = st.selectbox("Primary Motivation *", [
        "Select motivation", "Legacy and employees",
        "Best price", "Retirement", "Other"
    ])
    management_team = st.selectbox(
        "Does a management team exist that can run without you? *",
        ["Select option", "Yes Fully", "Partially", "No Just Me"]
    )
    city = st.text_input("City *", placeholder="e.g. Dallas")
    state = st.selectbox("State *", [
        "Select state",
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
    ])
    how_found = st.selectbox("How Did You Find Us? *", [
        "Select option", "Google search", "Broker referral",
        "Friend or colleague", "Social media", "Other"
    ])

    st.divider()
    st.markdown("#### Tell Us More")
    reason = st.text_area(
        "Reason for Selling *",
        placeholder="Tell us why you are considering a sale and what matters most to you in this process...",
        height=120
    )
    notes = st.text_area(
        "Additional Notes (optional)",
        placeholder="Anything else you would like us to know — employees, customers, history, etc.",
        height=100
    )

    st.divider()

    if st.button("Submit Inquiry", type="primary", use_container_width=True):
        if not all([
            contact_name,
            contact_title != "Select title",
            business_name,
            industry != "Select industry",
            revenue > 0,
            motivation != "Select motivation",
            management_team != "Select option",
            city,
            state != "Select state",
            how_found != "Select option",
            reason,
            email,
            phone
        ]):
            st.error("Please fill in all required fields marked with *")
        else:
            st.session_state.form_data = {
                "contact_name": contact_name,
                "contact_title": contact_title,
                "business_name": business_name,
                "industry": industry,
                "revenue": revenue,
                "employees": employees,
                "years_in_business": years_in_business,
                "exit_timeline": exit_timeline,
                "motivation": motivation,
                "management_team": management_team,
                "city": city,
                "state": state,
                "location": f"{city}, {state}",
                "how_found": how_found,
                "reason": reason,
                "email": email,
                "phone": phone,
                "notes": notes
            }
            st.session_state.stage = "processing"
            st.rerun()

# SCREEN 2 - PROCESSING
elif st.session_state.stage == "processing":
    st.markdown("<h1 style='color:#1F4E79;'>AcquireIQ</h1>", unsafe_allow_html=True)
    st.divider()

    with st.spinner("Reviewing your inquiry..."):
        try:
            result = extract_and_score(st.session_state.form_data)
            create_salesforce_lead(st.session_state.form_data, result)
            st.session_state.result = result
            st.session_state.stage = "confirmation"
            st.rerun()
        except Exception as e:
            st.error(f"Something went wrong: {e}")
            if st.button("Try Again"):
                st.session_state.stage = "form"
                st.rerun()

# SCREEN 3 - PUBLIC CONFIRMATION
elif st.session_state.stage == "confirmation":

    first_name = st.session_state.form_data.get("contact_name", "").split(" ")[0]
    business = st.session_state.form_data.get("business_name", "your business")

    st.markdown("<h1 style='color:#1F4E79;'>AcquireIQ</h1>", unsafe_allow_html=True)
    st.divider()

    st.markdown("<div style='text-align:center; font-size:4rem;'>✅</div>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center;'>Thank you, {first_name}.</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; font-size:1.1rem;'>We have received your inquiry about <strong>{business}</strong>.</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#666;'>Our team personally reviews every submission and will be in touch within one business day.</p>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### What happens next")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
            <div style='background:#F5F5F5; padding:1.2rem;
            border-radius:8px; text-align:center; height:160px;'>
            <h2 style='color:#1F4E79;'>1</h2>
            <p style='font-size:0.9rem;'>A member of our Business Development team will reach out to learn more about your business</p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div style='background:#F5F5F5; padding:1.2rem;
            border-radius:8px; text-align:center; height:160px;'>
            <h2 style='color:#1F4E79;'>2</h2>
            <p style='font-size:0.9rem;'>If there is a potential fit we will schedule a confidential conversation at your convenience</p>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
            <div style='background:#F5F5F5; padding:1.2rem;
            border-radius:8px; text-align:center; height:160px;'>
            <h2 style='color:#1F4E79;'>3</h2>
            <p style='font-size:0.9rem;'>We move at your pace — no pressure, no obligation</p>
            </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.caption("AcquireIQ — Intelligent Lead Qualification | Built by Debasmita Ray")

    if st.button("Submit Another Inquiry", use_container_width=True):
        st.session_state.stage = "form"
        st.session_state.form_data = {}
        st.session_state.result = None
        st.rerun()
