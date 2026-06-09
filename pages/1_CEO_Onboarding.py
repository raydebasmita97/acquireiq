import streamlit as st
import anthropic
import pandas as pd
import plotly.express as px
import datetime
from knowledge_base import BASE_DOCUMENTS, get_all_documents
from data_store import load_df, load_company, load_custom_tabs, load_active_sections

# ── Shared Data ──────────────────────────────────────────────────────────────

def months_until_renewal(month_name, year):
    month_map = {"January":1,"February":2,"March":3,"April":4,"May":5,"June":6,
                 "July":7,"August":8,"September":9,"October":10,"November":11,"December":12}
    now = datetime.date.today()
    try:
        renewal = datetime.date(int(year), month_map.get(month_name, 1), 1)
        return (renewal - now).days
    except Exception:
        return 999

@st.cache_data(ttl=10)
def get_all_data():
    active = load_active_sections()
    return {
        "active":      active,
        "customers":   load_df("customers").to_dict("records")  if "customers"   in active else None,
        "employees":   load_df("employees").to_dict("records")  if "employees"   in active else None,
        "vendors":     load_df("vendors").to_dict("records")    if "vendors"     in active else None,
        "financials":  load_df("financials").to_dict("records") if "financials"  in active else None,
        "company":     load_company(),
        "custom_tabs": load_custom_tabs()                       if "custom_tabs" in active else [],
    }

def refresh_data():
    get_all_data.clear()

_data        = get_all_data()
active_sections = _data["active"]
customers_df = pd.DataFrame(_data["customers"]) if _data["customers"] is not None else None
employees_df = pd.DataFrame(_data["employees"]) if _data["employees"] is not None else None
vendors_df   = pd.DataFrame(_data["vendors"])   if _data["vendors"]   is not None else None
financial_df = pd.DataFrame(_data["financials"])if _data["financials"]is not None else None
company_info = _data["company"]
custom_tabs  = _data["custom_tabs"]

# ── Claude ───────────────────────────────────────────────────────────────────

def ask_claude(question):
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    all_docs = get_all_documents()
    context_text = "\n\n".join([f"[{k}]:\n{v}" for k, v in all_docs.items()])
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system="""You are an AI assistant helping a newly appointed CEO understand
their acquired business. Answer based only on the provided context. Be specific
and concise. Always mention which document your answer comes from at the end
in italics like this:
*Source: [Document Name]*
If the answer is not in the context say:
I do not have that information in the loaded documents.""",
        messages=[{"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {question}"}]
    )
    return message.content[0].text

# ── Session State ─────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "input_value" not in st.session_state:
    st.session_state.input_value = ""
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = {}

SUGGESTED_QUESTIONS = [
    "Who are my top 3 customers and when do they renew?",
    "Which employees are critical to retain?",
    "What is our monthly revenue trend?",
    "Which vendor contracts expire soonest?",
    "What should I focus on in my first week?",
    "What is our billing rejection rate?",
    "What is our revenue mix by payer type?",
    "Who handles clinical emergencies?"
]

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("<h2 style='color:#1F4E79;'>CEO Onboarding Agent</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#555; margin-top:-10px;'>{company_info.get('name','')}</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown("**📚 Knowledge Base**")
    for doc_name, doc_text in BASE_DOCUMENTS.items():
        with st.expander(f"✅ {doc_name}"):
            st.markdown(doc_text)
    if st.session_state.uploaded_docs:
        for doc_name, doc_text in st.session_state.uploaded_docs.items():
            with st.expander(f"📄 {doc_name}"):
                st.markdown(doc_text[:2000] + ("..." if len(doc_text) > 2000 else ""))

    st.divider()
    st.markdown("**📊 Quick Stats**")
    st.metric("Annual Revenue", company_info.get("annual_revenue", "$8.03M"))
    st.metric("Employees",      company_info.get("employees", "45"))
    st.metric("Active Patients",company_info.get("active_patients", "180"))
    st.metric("Gross Margin",   company_info.get("gross_margin", "22%"))


# ── Main Tabs ─────────────────────────────────────────────────────────────────

col_title, col_refresh, col_admin = st.columns([7, 1, 1])
with col_title:
    st.markdown("<h1 style='color:#1F4E79;'>CEO Onboarding Agent</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color:#555; margin-top:-10px;'>{company_info.get('name','')}</h3>", unsafe_allow_html=True)
with col_refresh:
    st.markdown("<div style='padding-top:1.2rem;'>", unsafe_allow_html=True)
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_data()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
with col_admin:
    st.markdown("<div style='text-align:right; padding-top:1.2rem;'>", unsafe_allow_html=True)
    st.markdown(
        "<a href='/Admin' target='_blank' style='background:#1F4E79; color:white; padding:0.4rem 0.9rem; border-radius:6px; text-decoration:none; font-size:0.85rem;'>⚙️ Admin</a>",
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

# Build tab list dynamically based on active sections
tab_config = [("ai",          "💬 AI Assistant", True)]
if customers_df is not None:  tab_config.append(("customers",   "👥 Customers",   True))
if employees_df is not None:  tab_config.append(("employees",   "🧑‍💼 Employees",  True))
if vendors_df   is not None:  tab_config.append(("vendors",     "🤝 Vendors",     True))
if financial_df is not None:  tab_config.append(("financials",  "📈 Financials",  True))
for t in custom_tabs:
    tab_config.append((f"custom_{t['title']}", f"{t['icon']} {t['title']}", False))

all_tab_labels = [c[1] for c in tab_config]
all_tabs       = st.tabs(all_tab_labels)
tab_map        = {c[0]: all_tabs[i] for i, c in enumerate(tab_config)}

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — AI CHAT
# ════════════════════════════════════════════════════════════════════════════

with tab_map["ai"]:
    st.info("Welcome. I have been loaded with everything you need to know about Johnson Home Health Services. Ask me anything about your customers, employees, financials, operations, or vendors.")

    st.markdown("#### 💡 Suggested Questions")
    cols = st.columns(2)
    for i, question in enumerate(SUGGESTED_QUESTIONS):
        with cols[i % 2]:
            if st.button(question, key=f"suggested_{i}", use_container_width=True):
                st.session_state.input_value = question

    st.divider()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("Ask about your business...")

    if st.session_state.input_value and not user_input:
        user_input = st.session_state.input_value
        st.session_state.input_value = ""

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                response = ask_claude(user_input)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — CUSTOMERS
# ════════════════════════════════════════════════════════════════════════════

if customers_df is not None:
 with tab_map["customers"]:
    df = customers_df.copy()
    df["days_to_renewal"] = df.apply(lambda r: months_until_renewal(r["renewal_month"], r["renewal_year"]), axis=1)
    total_acv = df["annual_contract_value"].sum()
    renewing_90 = (df["days_to_renewal"] <= 90).sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Customers", len(df))
    c2.metric("Total Contract Value", f"${total_acv/1_000_000:.2f}M")
    c3.metric("Avg Relationship", f"{df['relationship_years'].mean():.1f} yrs")
    c4.metric("Renewing in 90 Days", int(renewing_90))

    st.markdown("#### Filters")
    f1, f2, f3 = st.columns(3)
    with f1:
        min_val = st.slider("Min Contract Value ($)", 0, 500000, 0, step=10000, format="$%d")
    with f2:
        max_rel = st.slider("Max Relationship Years", 0, 20, 20)
    with f3:
        all_months = df["renewal_month"].unique().tolist()
        sel_months = st.multiselect("Renewal Month", all_months, default=all_months, key="cust_months")

    filtered = df[
        (df["annual_contract_value"] >= min_val) &
        (df["relationship_years"] <= max_rel) &
        (df["renewal_month"].isin(sel_months))
    ]

    display = filtered[["rank","customer_name","annual_contract_value","relationship_years","key_contact","renewal_month","renewal_year","status"]].rename(columns={
        "rank": "Rank", "customer_name": "Customer", "annual_contract_value": "Annual Value",
        "relationship_years": "Years", "key_contact": "Key Contact",
        "renewal_month": "Renewal Month", "renewal_year": "Renewal Year", "status": "Status"
    })
    display["Annual Value"] = display["Annual Value"].apply(lambda x: f"${x:,.0f}")
    st.dataframe(display, use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — EMPLOYEES
# ════════════════════════════════════════════════════════════════════════════

if employees_df is not None:
 with tab_map["employees"]:
    df = employees_df.copy()
    top_count = (df["performance"] == "Top Performer").sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Employees", len(df))
    c2.metric("Top Performers", int(top_count))
    c3.metric("Avg Tenure", f"{df['tenure_years'].mean():.1f} yrs")
    c4.metric("Departments", int(df["department"].nunique()))

    st.markdown("#### Filters")
    f1, f2, f3 = st.columns(3)
    with f1:
        all_depts = df["department"].unique().tolist()
        sel_depts = st.multiselect("Department", all_depts, default=all_depts, key="emp_depts")
    with f2:
        min_tenure = st.slider("Min Tenure (years)", 0, 15, 0)
    with f3:
        all_perf = df["performance"].unique().tolist()
        sel_perf = st.multiselect("Performance", all_perf, default=all_perf, key="emp_perf")

    filtered = df[
        (df["department"].isin(sel_depts)) &
        (df["tenure_years"] >= min_tenure) &
        (df["performance"].isin(sel_perf))
    ]

    perf_colors = {
        "Top Performer":     "background-color: #d4edda",
        "Strong Performer":  "background-color: #d0e8f7",
        "Average Performer": "background-color: #e9ecef"
    }

    display = filtered[["name","role","department","tenure_years","performance","notes"]].rename(columns={
        "name": "Name", "role": "Role", "department": "Department",
        "tenure_years": "Tenure (yrs)", "performance": "Performance", "notes": "Notes"
    })
    st.dataframe(
        display.style.map(lambda v: perf_colors.get(v, ""), subset=["Performance"]),
        use_container_width=True, hide_index=True
    )

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — VENDORS
# ════════════════════════════════════════════════════════════════════════════

if vendors_df is not None:
 with tab_map["vendors"]:
    df = vendors_df.copy()
    df["days_to_renewal"] = df.apply(lambda r: months_until_renewal(r["renewal_month"], r["renewal_year"]), axis=1)
    total_spend = df["annual_cost"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Vendors", len(df))
    c2.metric("Total Annual Spend", f"${total_spend/1000:.0f}K")
    c3.metric("Critical Vendors", int(df["critical"].sum()))
    c4.metric("Expiring in 90 Days", int((df["days_to_renewal"] <= 90).sum()))

    st.markdown("#### Filters")
    f1, f2 = st.columns(2)
    with f1:
        critical_only = st.checkbox("Critical vendors only")
    with f2:
        all_months = df["renewal_month"].unique().tolist()
        sel_months = st.multiselect("Renewal Month", all_months, default=all_months, key="vend_months")

    filtered = df[df["renewal_month"].isin(sel_months)]
    if critical_only:
        filtered = filtered[filtered["critical"] == True]

    def highlight_vendor(row):
        if row.get("days_to_renewal", 999) <= 90:
            return ["background-color: #fff3cd"] * len(row)
        if row.get("critical", False):
            return ["background-color: #fde8e8"] * len(row)
        return [""] * len(row)

    display = filtered[["vendor_name","product","annual_cost","renewal_month","renewal_year","critical","notes"]].rename(columns={
        "vendor_name": "Vendor", "product": "Product", "annual_cost": "Annual Cost",
        "renewal_month": "Renewal Month", "renewal_year": "Renewal Year",
        "critical": "Critical", "notes": "Notes"
    })
    display["Annual Cost"] = display["Annual Cost"].apply(lambda x: f"${x:,.0f}")
    st.dataframe(display.style.apply(highlight_vendor, axis=1), use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — FINANCIALS
# ════════════════════════════════════════════════════════════════════════════

if financial_df is not None:
 with tab_map["financials"]:
    df = financial_df.copy()
    total_rev = df["total_revenue"].sum()
    avg_monthly = df["total_revenue"].mean()
    best_month = df.loc[df["total_revenue"].idxmax(), "month"]
    growth = ((df["total_revenue"].iloc[-1] - df["total_revenue"].iloc[0]) / df["total_revenue"].iloc[0]) * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Annual Revenue", f"${total_rev/1_000_000:.2f}M")
    c2.metric("Avg Monthly Revenue", f"${avg_monthly/1000:.0f}K")
    c3.metric("Best Month", best_month)
    c4.metric("Revenue Growth", f"{growth:.1f}%")

    st.markdown("#### Filters")
    f1, f2 = st.columns(2)
    with f1:
        rev_types = st.multiselect(
            "Revenue Type",
            ["Total", "Medicare", "Medicaid", "Private Pay"],
            default=["Total", "Medicare", "Medicaid", "Private Pay"]
        )
    with f2:
        month_range = st.slider("Month Range", 1, 12, (1, 12))

    col_map = {"Total": "total_revenue", "Medicare": "medicare_revenue",
               "Medicaid": "medicaid_revenue", "Private Pay": "private_revenue"}
    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    filtered = df.iloc[month_range[0]-1 : month_range[1]]
    selected_cols = [col_map[t] for t in rev_types if t in col_map]

    if selected_cols:
        plot_df = filtered.melt(id_vars=["month"], value_vars=selected_cols,
                                var_name="Revenue Type", value_name="Revenue")
        plot_df["Revenue Type"] = plot_df["Revenue Type"].map({v: k for k, v in col_map.items()})
        plot_df["month"] = pd.Categorical(plot_df["month"], categories=month_order, ordered=True)
        plot_df = plot_df.sort_values("month")

        fig = px.line(plot_df, x="month", y="Revenue", color="Revenue Type", markers=True,
                      title="Monthly Revenue by Type",
                      color_discrete_map={"Total": "#1F4E79", "Medicare": "#2e86c1",
                                          "Medicaid": "#27ae60", "Private Pay": "#e67e22"})
        fig.update_layout(plot_bgcolor="white", yaxis_tickprefix="$",
                          yaxis_tickformat=",.0f", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    display = filtered[["month"] + selected_cols].rename(columns={
        "month": "Month", "total_revenue": "Total", "medicare_revenue": "Medicare",
        "medicaid_revenue": "Medicaid", "private_revenue": "Private Pay"
    })
    for col in display.columns[1:]:
        display[col] = display[col].apply(lambda x: f"${x:,.0f}")
    st.dataframe(display, use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════════════════════
# CUSTOM TABS (created from Admin)
# ════════════════════════════════════════════════════════════════════════════

for tab_data in custom_tabs:
    tab_key = f"custom_{tab_data['title']}"
    if tab_key not in tab_map:
        continue
    with tab_map[tab_key]:
        if tab_data.get("content"):
            st.markdown(tab_data["content"])
        charts = tab_data.get("charts") or ([tab_data["chart"]] if tab_data.get("chart") else [])
        for c in charts:
            if not c: continue
            try:
                chart_df   = pd.DataFrame(c["data"])
                chart_type = c.get("type", "bar")
                title      = c.get("title", "")
                if chart_type == "bar":
                    fig = px.bar(chart_df, x=c["x"], y=c["y"], title=title, color_discrete_sequence=["#1F4E79"])
                elif chart_type == "line":
                    fig = px.line(chart_df, x=c["x"], y=c["y"], title=title, markers=True)
                elif chart_type == "scatter":
                    fig = px.scatter(chart_df, x=c["x"], y=c["y"], title=title,
                                     trendline="ols" if len(chart_df) > 2 else None,
                                     color_discrete_sequence=["#1F4E79"])
                elif chart_type == "pie":
                    fig = px.pie(chart_df, names=c["x"], values=c["y"], title=title)
                else:
                    fig = px.bar(chart_df, x=c["x"], y=c["y"], title=title, color_discrete_sequence=["#1F4E79"])
                fig.update_layout(plot_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Chart could not render: {e}")
        if tab_data.get("table"):
            t = tab_data["table"]
            if t.get("title"): st.markdown(f"**{t['title']}**")
            try:
                st.dataframe(pd.DataFrame(t["data"]), use_container_width=True, hide_index=True)
            except Exception as e:
                st.warning(f"Table could not render: {e}")

