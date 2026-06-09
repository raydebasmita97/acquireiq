import streamlit as st
import pandas as pd
import os
import datetime
import io
import json
import anthropic
from knowledge_base import BASE_DOCUMENTS
from data_store import (load_df, save_df, load_company, save_company,
                        load_custom_tabs, save_custom_tabs, load, save,
                        load_global_trash, save_global_trash, move_to_trash,
                        restore_from_trash, delete_from_trash,
                        load_kb_overrides, save_kb_overrides,
                        load_active_sections, save_active_sections,
                        delete_section, restore_section, ALL_SECTIONS)

st.set_page_config(page_title="AcquireIQ Admin", page_icon="⚙️", layout="wide")

ADMIN_PASSWORD = "dallas2026"

# ── Session State ─────────────────────────────────────────────────────────────
if "admin_authenticated"  not in st.session_state: st.session_state.admin_authenticated  = False
if "uploaded_docs"        not in st.session_state: st.session_state.uploaded_docs        = {}
if "kb_uploads_meta"      not in st.session_state: st.session_state.kb_uploads_meta      = []
if "tab_builder_file_text" not in st.session_state: st.session_state.tab_builder_file_text = ""
if "tab_builder_preview"  not in st.session_state: st.session_state.tab_builder_preview  = None
if "tab_builder_history"  not in st.session_state: st.session_state.tab_builder_history  = []

# ── Login ─────────────────────────────────────────────────────────────────────
if not st.session_state.admin_authenticated:
    st.markdown("""
        <div style='text-align:center; margin-top:100px;'>
            <h1 style='color:#1F4E79;'>AcquireIQ</h1>
            <p style='color:#555; font-size:1.1rem;'>Admin Panel</p>
        </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("#### Sign In")
        pwd = st.text_input("Password", type="password", placeholder="Enter admin password")
        if st.button("Login", type="primary", use_container_width=True):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h2 style='color:#1F4E79;'>AcquireIQ Admin</h2>", unsafe_allow_html=True)
    st.caption("🔐 Logged in as Admin")
    st.divider()
    nav = st.radio("Section", [
        "🏢 Company Info",
        "📚 Knowledge Base",
        "👥 Customers",
        "🧑‍💼 Employees",
        "🤝 Vendors",
        "📈 Financials",
        "➕ Custom Tabs",
        "🗑️ Trash",
    ])
    st.divider()
    if st.button("Logout", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.rerun()
    st.markdown(
        "<a href='https://acquireiq-ceo.streamlit.app/' target='_blank' style='color:#1F4E79; font-size:0.85rem;'>← CEO Onboarding</a>",
        unsafe_allow_html=True
    )

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"<h1 style='color:#1F4E79;'>Admin Panel</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:#555; margin-top:-12px;'>{nav}</p>", unsafe_allow_html=True)
st.divider()

SOURCE_LABELS = {
    "customers":   ("👥", "Customers"),
    "employees":   ("🧑‍💼", "Employees"),
    "vendors":     ("🤝", "Vendors"),
    "financials":  ("📈", "Financials"),
    "custom_tabs": ("📋", "Custom Tabs"),
}

# ════════════════════════════════════════════════════════════════════════════
# COMPANY INFO
# ════════════════════════════════════════════════════════════════════════════
if nav == "🏢 Company Info":
    info = load_company()
    st.markdown("### Company Settings")
    st.caption("These appear in the CEO Onboarding header and sidebar stats.")

    with st.form("company_form"):
        name     = st.text_input("Company Name",    value=info.get("name", ""))
        tagline  = st.text_input("Tagline",          value=info.get("tagline", ""))
        rev      = st.text_input("Annual Revenue",   value=info.get("annual_revenue", ""))
        emp      = st.text_input("Employees",        value=info.get("employees", ""))
        patients = st.text_input("Active Patients",  value=info.get("active_patients", ""))
        margin   = st.text_input("Gross Margin",     value=info.get("gross_margin", ""))
        if st.form_submit_button("💾 Save", type="primary"):
            save_company({"name": name, "tagline": tagline, "annual_revenue": rev,
                          "employees": emp, "active_patients": patients, "gross_margin": margin})
            st.success("Company info saved.")

# ════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE BASE
# ════════════════════════════════════════════════════════════════════════════
elif nav == "📚 Knowledge Base":

    kb_overrides = load_kb_overrides()

    st.markdown("### Built-in Documents")
    st.caption("Click any document to edit its content. Changes are saved and reflected live in the CEO Onboarding Agent.")

    for doc_name, doc_text in BASE_DOCUMENTS.items():
        current_text = kb_overrides.get(doc_name, doc_text)
        is_edited = doc_name in kb_overrides
        label = f"✏️ {doc_name} *(edited)*" if is_edited else f"📄 {doc_name}"
        with st.expander(label):
            edited_text = st.text_area(
                "Content", value=current_text, height=200, key=f"kb_{doc_name}"
            )
            c1, c2, c3 = st.columns([1, 1, 4])
            with c1:
                if st.button("💾 Save", key=f"kb_save_{doc_name}", type="primary"):
                    kb_overrides[doc_name] = edited_text
                    save_kb_overrides(kb_overrides)
                    st.success("Saved.")
                    st.rerun()
            with c2:
                if is_edited and st.button("↩️ Reset", key=f"kb_reset_{doc_name}"):
                    del kb_overrides[doc_name]
                    save_kb_overrides(kb_overrides)
                    st.success("Reset to original.")
                    st.rerun()

    st.divider()
    st.markdown("### Add New Document")
    with st.form("new_kb_doc"):
        new_doc_name = st.text_input("Document Name", placeholder="e.g. Board Meeting Notes")
        new_doc_text = st.text_area("Content", height=150, placeholder="Enter document content...")
        if st.form_submit_button("➕ Add Document", type="primary"):
            if new_doc_name and new_doc_text:
                kb_overrides[new_doc_name] = new_doc_text
                save_kb_overrides(kb_overrides)
                st.success(f"'{new_doc_name}' added to knowledge base.")
                st.rerun()
            else:
                st.error("Please fill in both name and content.")

    st.divider()
    st.markdown("### Upload Document Files")
    uploaded_files = st.file_uploader(
        "Upload PDF, TXT, or DOCX", type=["pdf","txt","docx"], accept_multiple_files=True
    )
    if uploaded_files:
        os.makedirs("uploaded_docs", exist_ok=True)
        for f in uploaded_files:
            content = f.read()
            with open(os.path.join("uploaded_docs", f.name), "wb") as out:
                out.write(content)
            doc_name = f.name.rsplit(".", 1)[0].replace("_"," ").replace("-"," ").title()
            text = content.decode("utf-8", errors="ignore")
            if doc_name not in st.session_state.uploaded_docs:
                st.session_state.uploaded_docs[doc_name] = text
                st.session_state.kb_uploads_meta.append({
                    "name": doc_name, "filename": f.name,
                    "type": f.name.rsplit(".",1)[-1].upper(),
                    "date_added": datetime.date.today().strftime("%b %d, %Y"),
                    "word_count": len(text.split())
                })
        st.success("✅ Documents uploaded.")
        st.rerun()

    if st.session_state.kb_uploads_meta:
        st.markdown("#### Uploaded Files")
        for meta in st.session_state.kb_uploads_meta:
            c1, c2, c3, c4, c5 = st.columns([4, 1.2, 1.5, 1, 0.5])
            c1.markdown(f"📄 **{meta['name']}**")
            c2.caption(meta["type"])
            c3.caption(meta["date_added"])
            c4.caption(f"{meta['word_count']} words")
            if c5.button("🗑️", key=f"del_{meta['name']}"):
                del st.session_state.uploaded_docs[meta["name"]]
                try:
                    os.remove(os.path.join("uploaded_docs", meta["filename"]))
                except Exception:
                    pass
                st.session_state.kb_uploads_meta = [
                    m for m in st.session_state.kb_uploads_meta if m["name"] != meta["name"]
                ]
                st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# CUSTOMERS
# ════════════════════════════════════════════════════════════════════════════
elif nav == "👥 Customers":
    c_head, c_del = st.columns([6, 1])
    c_head.markdown("### Customer Data")
    c_head.caption("Edit cells directly. Check rows to move individual rows to Trash.")
    if c_del.button("🗑️ Delete Section", key="del_section_customers"):
        delete_section("customers")
        st.success("Customers section moved to Trash.")
        st.rerun()

    df = load_df("customers")
    df.insert(0, "Select", False)

    edited = st.data_editor(
        df,
        num_rows="fixed",
        use_container_width=True,
        column_config={
            "Select": st.column_config.CheckboxColumn("🗑️", width="small"),
            "annual_contract_value": st.column_config.NumberColumn("Annual Value ($)", format="$%d"),
            "renewal_year": st.column_config.NumberColumn("Renewal Year", format="%d"),
            "relationship_years": st.column_config.NumberColumn("Rel. Years"),
            "rank": st.column_config.NumberColumn("Rank"),
        },
        key="customers_editor"
    )

    c1, c2, c3 = st.columns([1.2, 1.5, 4])
    with c1:
        if st.button("💾 Save Changes", type="primary"):
            to_keep = edited[edited["Select"] == False].drop(columns=["Select"])
            to_trash = edited[edited["Select"] == True].drop(columns=["Select"])
            if not to_trash.empty:
                move_to_trash("customers", to_trash.to_dict(orient="records"))
            save_df("customers", to_keep)
            st.success(f"Saved. {len(to_trash)} row(s) moved to Trash.")
            st.rerun()
    with c2:
        if st.button("↩️ Reset to Default"):
            if os.path.exists("data/customers.json"):
                os.remove("data/customers.json")
            st.success("Reset to defaults.")
            st.rerun()

    st.caption("🗑️ Deleted rows go to the global Trash — restore them from the Trash section in the sidebar.")

# ════════════════════════════════════════════════════════════════════════════
# EMPLOYEES
# ════════════════════════════════════════════════════════════════════════════
elif nav == "🧑‍💼 Employees":
    c_head, c_del = st.columns([6, 1])
    c_head.markdown("### Employee Roster")
    c_head.caption("Edit cells directly. Check rows to move to Trash.")
    if c_del.button("🗑️ Delete Section", key="del_section_employees"):
        delete_section("employees")
        st.success("Employees section moved to Trash.")
        st.rerun()

    df = load_df("employees")
    df.insert(0, "Select", False)

    edited = st.data_editor(
        df,
        num_rows="fixed",
        use_container_width=True,
        column_config={
            "Select": st.column_config.CheckboxColumn("🗑️", width="small"),
            "tenure_years": st.column_config.NumberColumn("Tenure (yrs)"),
            "performance": st.column_config.SelectboxColumn(
                "Performance", options=["Top Performer", "Strong Performer", "Average Performer"]
            ),
            "department": st.column_config.SelectboxColumn(
                "Department", options=["Clinical", "Operations", "Finance", "HR", "Marketing", "IT", "Other"]
            ),
        },
        key="employees_editor"
    )

    c1, c2 = st.columns([1.2, 1.5])
    with c1:
        if st.button("💾 Save Changes", type="primary"):
            to_keep  = edited[edited["Select"] == False].drop(columns=["Select"])
            to_trash = edited[edited["Select"] == True].drop(columns=["Select"])
            if not to_trash.empty:
                move_to_trash("employees", to_trash.to_dict(orient="records"))
            save_df("employees", to_keep)
            st.success(f"Saved. {len(to_trash)} row(s) moved to Trash.")
            st.rerun()
    with c2:
        if st.button("↩️ Reset to Default"):
            if os.path.exists("data/employees.json"):
                os.remove("data/employees.json")
            st.success("Reset to defaults.")
            st.rerun()

    st.caption("🗑️ Deleted rows go to the global Trash — restore them from the Trash section in the sidebar.")

# ════════════════════════════════════════════════════════════════════════════
# VENDORS
# ════════════════════════════════════════════════════════════════════════════
elif nav == "🤝 Vendors":
    c_head, c_del = st.columns([6, 1])
    c_head.markdown("### Vendor Contracts")
    c_head.caption("Edit cells directly. Check rows to move to Trash.")
    if c_del.button("🗑️ Delete Section", key="del_section_vendors"):
        delete_section("vendors")
        st.success("Vendors section moved to Trash.")
        st.rerun()

    df = load_df("vendors")
    df.insert(0, "Select", False)

    edited = st.data_editor(
        df,
        num_rows="fixed",
        use_container_width=True,
        column_config={
            "Select": st.column_config.CheckboxColumn("🗑️", width="small"),
            "annual_cost": st.column_config.NumberColumn("Annual Cost ($)", format="$%d"),
            "renewal_year": st.column_config.NumberColumn("Renewal Year", format="%d"),
            "critical": st.column_config.CheckboxColumn("Critical"),
            "renewal_month": st.column_config.SelectboxColumn(
                "Renewal Month",
                options=["January","February","March","April","May","June",
                         "July","August","September","October","November","December"]
            ),
        },
        key="vendors_editor"
    )

    c1, c2 = st.columns([1.2, 1.5])
    with c1:
        if st.button("💾 Save Changes", type="primary"):
            to_keep  = edited[edited["Select"] == False].drop(columns=["Select"])
            to_trash = edited[edited["Select"] == True].drop(columns=["Select"])
            if not to_trash.empty:
                move_to_trash("vendors", to_trash.to_dict(orient="records"))
            save_df("vendors", to_keep)
            st.success(f"Saved. {len(to_trash)} row(s) moved to Trash.")
            st.rerun()
    with c2:
        if st.button("↩️ Reset to Default"):
            if os.path.exists("data/vendors.json"):
                os.remove("data/vendors.json")
            st.success("Reset to defaults.")
            st.rerun()

    st.caption("🗑️ Deleted rows go to the global Trash — restore them from the Trash section in the sidebar.")

# ════════════════════════════════════════════════════════════════════════════
# FINANCIALS
# ════════════════════════════════════════════════════════════════════════════
elif nav == "📈 Financials":
    c_head, c_del = st.columns([6, 1])
    c_head.markdown("### Financial Data")
    c_head.caption("Edit monthly revenue figures. Check rows to move to Trash.")
    if c_del.button("🗑️ Delete Section", key="del_section_financials"):
        delete_section("financials")
        st.success("Financials section moved to Trash.")
        st.rerun()

    df = load_df("financials")
    df.insert(0, "Select", False)

    edited = st.data_editor(
        df,
        num_rows="fixed",
        use_container_width=True,
        column_config={
            "Select": st.column_config.CheckboxColumn("🗑️", width="small"),
            "total_revenue":    st.column_config.NumberColumn("Total Revenue ($)",  format="$%d"),
            "medicare_revenue": st.column_config.NumberColumn("Medicare ($)",       format="$%d"),
            "medicaid_revenue": st.column_config.NumberColumn("Medicaid ($)",       format="$%d"),
            "private_revenue":  st.column_config.NumberColumn("Private Pay ($)",    format="$%d"),
            "year":             st.column_config.NumberColumn("Year",               format="%d"),
            "month": st.column_config.SelectboxColumn(
                "Month", options=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
            ),
        },
        key="financials_editor"
    )

    c1, c2 = st.columns([1.2, 1.5])
    with c1:
        if st.button("💾 Save Changes", type="primary"):
            to_keep  = edited[edited["Select"] == False].drop(columns=["Select"])
            to_trash = edited[edited["Select"] == True].drop(columns=["Select"])
            if not to_trash.empty:
                move_to_trash("financials", to_trash.to_dict(orient="records"))
            save_df("financials", to_keep)
            st.success(f"Saved. {len(to_trash)} row(s) moved to Trash.")
            st.rerun()
    with c2:
        if st.button("↩️ Reset to Default"):
            if os.path.exists("data/financials.json"):
                os.remove("data/financials.json")
            st.success("Reset to defaults.")
            st.rerun()

    st.caption("🗑️ Deleted rows go to the global Trash — restore them from the Trash section in the sidebar.")

# ════════════════════════════════════════════════════════════════════════════
# CUSTOM TABS
# ════════════════════════════════════════════════════════════════════════════
elif nav == "➕ Custom Tabs":

    def extract_file_text(f):
        name = f.name.lower()
        if name.endswith(".csv") or name.endswith((".xlsx", ".xls")):
            f.seek(0)
            df = pd.read_csv(f) if name.endswith(".csv") else pd.read_excel(f)
            # For large files, send schema + sample + stats instead of full dump
            summary = f"File: {f.name}\nRows: {len(df)} | Columns: {len(df.columns)}\n"
            summary += f"Columns: {', '.join(df.columns.tolist())}\n\n"
            summary += f"First 30 rows:\n{df.head(30).to_string(index=False)}\n\n"
            summary += f"Summary statistics:\n{df.describe(include='all').to_string()}"
            return summary
        elif name.endswith(".txt"):
            return f.read().decode("utf-8", errors="ignore")
        elif name.endswith(".pdf"):
            try:
                import pdfplumber, io as _io
                text = ""
                with pdfplumber.open(_io.BytesIO(f.read())) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t: text += t + "\n"
                return text
            except Exception:
                return f.read().decode("utf-8", errors="ignore")
        else:
            return f.read().decode("utf-8", errors="ignore")

    def render_chart(c):
        import plotly.express as px
        if not c or not c.get("data"):
            st.warning("Chart has no data — try regenerating.")
            return
        try:
            chart_df = pd.DataFrame(c["data"])
            if chart_df.empty:
                st.warning("Chart data is empty — try regenerating.")
                return

            # Fuzzy column match
            def match_col(name, cols):
                if name in cols: return name
                norm = name.lower().replace(" ", "_")
                for col in cols:
                    if col.lower().replace(" ", "_") == norm:
                        return col
                return cols[0] if cols else name

            cols       = list(chart_df.columns)
            x_col      = match_col(c.get("x", ""), cols)
            y_col      = match_col(c.get("y", ""), cols)
            chart_type = c.get("type", "bar")
            title      = c.get("title", "")

            if chart_type == "bar":
                fig = px.bar(chart_df, x=x_col, y=y_col, title=title, color_discrete_sequence=["#1F4E79"])
            elif chart_type == "line":
                fig = px.line(chart_df, x=x_col, y=y_col, title=title, markers=True)
            elif chart_type == "scatter":
                fig = px.scatter(chart_df, x=x_col, y=y_col, title=title,
                                 trendline="ols" if len(chart_df) > 2 else None,
                                 color_discrete_sequence=["#1F4E79"])
            elif chart_type == "pie":
                fig = px.pie(chart_df, names=x_col, values=y_col, title=title)
            else:
                fig = px.bar(chart_df, x=x_col, y=y_col, title=title, color_discrete_sequence=["#1F4E79"])
            fig.update_layout(plot_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Chart could not render: {e}")

    def render_preview(spec):
        """Render a tab spec as a live preview."""
        st.markdown(f"### {spec.get('icon','📋')} {spec.get('title','Preview')}")
        if spec.get("content"):
            st.markdown(spec["content"])
        # Support both new "charts" list and legacy "chart" single
        charts = spec.get("charts") or ([spec["chart"]] if spec.get("chart") else [])
        for c in charts:
            if c:
                render_chart(c)
        if spec.get("table"):
            t = spec["table"]
            if t.get("title"): st.markdown(f"**{t['title']}**")
            try:
                st.dataframe(pd.DataFrame(t["data"]), use_container_width=True, hide_index=True)
            except Exception as e:
                st.warning(f"Table could not render: {e}")

    def generate_tab(file_text, instruction, history):
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        history_text = ""
        if history:
            history_text = "\n\nPrevious attempts and feedback:\n" + "\n".join(
                [f"- Attempt {i+1}: {h['feedback']}" for i, h in enumerate(history)]
            )
        prompt = f"""You are a dashboard builder. Based on the uploaded data and the user's request,
generate a tab specification as valid JSON only. No preamble, no markdown, no backticks.
Start your response with {{ and end with }}.

The JSON must follow this exact structure:
{{
  "title": "Tab name",
  "icon": "emoji",
  "content": "markdown text shown at top (can be empty string)",
  "charts": [
    {{
      "type": "bar|line|scatter|pie",
      "title": "Chart title",
      "data": [{{"x_col": "value", "y_col": number}}, ...],
      "x": "x_col",
      "y": "y_col"
    }}
  ],
  "table": {{
    "title": "Table title",
    "data": [{{"col1": "val", "col2": "val"}}, ...]
  }}
}}

Rules:
- "charts" is a list — include as many charts as the user requests (bar, line, scatter, pie)
- Use "scatter" type for scatter plots or trend lines
- Include "table" only if the user asks for a table
- Include "content" for any markdown summary text
- Keep data arrays concise (max 25 rows)
- Use null for keys not needed
- ONLY return the JSON object, nothing else
- Match chart types EXACTLY to what the user asks for
{history_text}

Uploaded data:
{file_text[:6000]}

User request: {instruction}"""

        msg = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4000,
            system="You are a dashboard builder. You MUST respond with only a valid JSON object. Start with {{ and end with }}. No markdown, no backticks, no explanation.",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = msg.content[0].text.strip()

        # Strip markdown code fences if Claude added them anyway
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()

        # Find the JSON object boundaries
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start != -1 and end > start:
            raw = raw[start:end]

        if not raw:
            raise ValueError("Claude returned an empty response. Please try again.")

        return json.loads(raw)

    # Section delete
    c_head, c_del = st.columns([6, 1])
    c_head.markdown("### AI Tab Builder")
    if c_del.button("🗑️ Delete Section", key="del_section_custom_tabs"):
        delete_section("custom_tabs")
        save_custom_tabs([])
        st.success("Custom Tabs section moved to Trash.")
        st.rerun()

    st.markdown("&nbsp;", unsafe_allow_html=True)
    st.caption("Upload a file, describe what you want, and Claude will build the dashboard tab for you.")

    left, right = st.columns([1, 1])

    with left:
        st.markdown("#### 1. Upload File")
        uploaded = st.file_uploader(
            "Upload CSV, Excel, PDF, or TXT",
            type=["csv", "xlsx", "xls", "txt", "pdf"],
            key="tab_builder_upload"
        )
        if uploaded:
            with st.spinner("Reading file..."):
                st.session_state.tab_builder_file_text = extract_file_text(uploaded)
            st.success(f"✅ {uploaded.name} loaded — {len(st.session_state.tab_builder_file_text.split())} words extracted")
            with st.expander("Preview extracted content"):
                # Show as table if CSV/Excel, otherwise raw text
                raw_text = st.session_state.tab_builder_file_text
                if uploaded.name.lower().endswith((".csv", ".xlsx", ".xls")):
                    try:
                        uploaded.seek(0)
                        if uploaded.name.lower().endswith(".csv"):
                            preview_df = pd.read_csv(uploaded)
                        else:
                            preview_df = pd.read_excel(uploaded)
                        st.dataframe(preview_df, use_container_width=True, hide_index=True)
                    except Exception:
                        st.text(raw_text[:1500])
                else:
                    st.text(raw_text[:1500])

        st.markdown("#### 2. Describe What You Want")
        instruction = st.text_area(
            "What should this tab show?",
            height=130,
            placeholder="e.g. Show a bar chart of revenue by month, and a summary table with totals. Title it 'Revenue Dashboard'."
        )

        col1, col2 = st.columns(2)
        with col1:
            generate_clicked = st.button("✨ Generate Tab", type="primary", use_container_width=True,
                                         disabled=not (st.session_state.tab_builder_file_text and instruction))
        with col2:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.tab_builder_preview = None
                st.session_state.tab_builder_history = []
                st.session_state.tab_builder_file_text = ""
                st.rerun()

        if generate_clicked:
            with st.spinner("Claude is building your dashboard..."):
                try:
                    spec = generate_tab(
                        st.session_state.tab_builder_file_text,
                        instruction,
                        st.session_state.tab_builder_history
                    )
                    st.session_state.tab_builder_preview = spec
                except Exception as e:
                    st.error(f"Generation failed: {e}")

        # Feedback / change request
        if st.session_state.tab_builder_preview:
            st.divider()
            st.markdown("#### 3. Request Changes")
            feedback = st.text_area(
                "Not quite right? Describe what to change:",
                height=100,
                placeholder="e.g. Use a line chart instead of bar. Add a pie chart for revenue mix. Change the title."
            )
            if st.button("🔁 Regenerate with Changes", use_container_width=True, disabled=not feedback):
                st.session_state.tab_builder_history.append({
                    "spec": st.session_state.tab_builder_preview,
                    "feedback": feedback
                })
                with st.spinner("Applying changes..."):
                    try:
                        spec = generate_tab(
                            st.session_state.tab_builder_file_text,
                            instruction + "\n\nChange request: " + feedback,
                            st.session_state.tab_builder_history
                        )
                        st.session_state.tab_builder_preview = spec
                        st.rerun()
                    except Exception as e:
                        st.error(f"Regeneration failed: {e}")

    with right:
        st.markdown("#### Preview")
        if st.session_state.tab_builder_preview:
            spec = st.session_state.tab_builder_preview
            with st.container(border=True):
                render_preview(spec)

            st.divider()
            st.markdown("#### 4. Approve & Publish")
            st.success("Happy with this? Publish it to the CEO Onboarding app.")
            if st.button("✅ Approve & Add to Onboarding", type="primary", use_container_width=True):
                custom_tabs = load_custom_tabs()
                # Strip chart/table data to storable format
                tab_to_save = {
                    "title":   spec.get("title", "Custom Tab"),
                    "icon":    spec.get("icon", "📋"),
                    "content": spec.get("content", ""),
                    "charts":  spec.get("charts") or ([spec["chart"]] if spec.get("chart") else []),
                    "table":   spec.get("table"),
                }
                custom_tabs.append(tab_to_save)
                save_custom_tabs(custom_tabs)
                st.session_state.tab_builder_preview = None
                st.session_state.tab_builder_history = []
                st.session_state.tab_builder_file_text = ""
                st.balloons()
                st.success("Tab published! It now appears in the CEO Onboarding app.")
                st.rerun()
        else:
            st.info("Your generated dashboard will appear here for preview before publishing.")
            if st.session_state.tab_builder_history:
                st.caption(f"Iteration {len(st.session_state.tab_builder_history)} — refining...")

    # ── Published Custom Tabs ──
    st.divider()
    st.markdown("### Published Custom Tabs")
    custom_tabs = load_custom_tabs()

    if not custom_tabs:
        st.caption("No published tabs yet.")
    else:
        for i, tab in enumerate(custom_tabs):
            with st.expander(f"{tab.get('icon','📋')} {tab['title']}"):
                # Edit fields
                c1, c2, c3 = st.columns([3, 3, 1])
                with c1:
                    new_title = st.text_input("Title", value=tab["title"], key=f"etitle_{i}")
                    new_icon  = st.text_input("Icon",  value=tab.get("icon","📋"), key=f"eicon_{i}")
                with c2:
                    new_content = st.text_area("Content (markdown)", value=tab.get("content",""),
                                               height=100, key=f"econtent_{i}")
                with c3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("💾 Save", key=f"esave_{i}"):
                        custom_tabs[i]["title"]   = new_title
                        custom_tabs[i]["icon"]    = new_icon
                        custom_tabs[i]["content"] = new_content
                        save_custom_tabs(custom_tabs)
                        st.success("Saved.")
                        st.rerun()
                    if st.button("🗑️ Trash", key=f"edel_{i}"):
                        move_to_trash("custom_tabs", [tab])
                        custom_tabs.pop(i)
                        save_custom_tabs(custom_tabs)
                        st.rerun()

                # Chart/table preview
                import plotly.express as px
                charts = tab.get("charts") or ([tab["chart"]] if tab.get("chart") else [])
                if charts:
                    st.markdown("**📊 Chart Preview**")
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
                                fig = px.scatter(chart_df, x=c["x"], y=c["y"], title=title, color_discrete_sequence=["#1F4E79"])
                            elif chart_type == "pie":
                                fig = px.pie(chart_df, names=c["x"], values=c["y"], title=title)
                            else:
                                fig = px.bar(chart_df, x=c["x"], y=c["y"], title=title, color_discrete_sequence=["#1F4E79"])
                            fig.update_layout(plot_bgcolor="white", height=350)
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.warning(f"Chart preview error: {e}")

                if tab.get("table"):
                    t = tab["table"]
                    st.markdown(f"**📋 {t.get('title','Table')}**")
                    try:
                        st.dataframe(pd.DataFrame(t["data"]), use_container_width=True, hide_index=True)
                    except Exception as e:
                        st.warning(f"Table preview error: {e}")

    st.caption("🗑️ Deleted tabs go to the global Trash — restore them from the Trash section in the sidebar.")

# ════════════════════════════════════════════════════════════════════════════
# GLOBAL TRASH
# ════════════════════════════════════════════════════════════════════════════
elif nav == "🗑️ Trash":

    trash = load_global_trash()
    total = len(trash)

    st.markdown(f"### 🗑️ Trash &nbsp; <span style='color:#999; font-size:1rem;'>({total} item{'s' if total != 1 else ''})</span>", unsafe_allow_html=True)
    st.caption("Deleted rows and entire sections appear here. Restore to bring them back, or permanently delete.")

    if not trash:
        st.info("Trash is empty.")
    else:
        # Separate section-level vs row-level items
        section_items = [(i, item) for i, item in enumerate(trash) if item.get("_source") == "__section__"]
        row_items     = [(i, item) for i, item in enumerate(trash) if item.get("_source") != "__section__"]

        # ── Deleted Sections ──
        if section_items:
            st.markdown("#### 📁 Deleted Sections")
            st.caption("These are entire sections deleted from the onboarding app.")
            for global_idx, item in section_items:
                sec_key    = item.get("_section_key", "")
                icon, label = SOURCE_LABELS.get(sec_key, ("📦", sec_key.title()))
                row_count  = len(item.get("_section_data", []))
                deleted_at = item.get("_deleted_at", "")

                with st.container(border=True):
                    c1, c2, c3 = st.columns([5, 1, 1])
                    c1.markdown(f"{icon} **{label} Section** &nbsp; <span style='color:#aaa; font-size:0.8rem;'>{row_count} rows · deleted {deleted_at}</span>", unsafe_allow_html=True)
                    with c2:
                        if st.button("↩️ Restore", key=f"sec_restore_{global_idx}"):
                            restore_section(global_idx)
                            st.success(f"{label} section restored.")
                            st.rerun()
                    with c3:
                        if st.button("❌ Delete", key=f"sec_delete_{global_idx}"):
                            delete_from_trash(global_idx)
                            st.rerun()
            st.divider()

        # ── Deleted Rows ──
        if row_items:
            st.markdown("#### 📄 Deleted Rows")
            # Group by source
            grouped = {}
            for i, item in row_items:
                src = item.get("_source", "unknown")
                grouped.setdefault(src, []).append((i, item))

            for src, items in grouped.items():
                icon, label = SOURCE_LABELS.get(src, ("📦", src.title()))
                st.markdown(f"**{icon} {label}** &nbsp; <span style='color:#999; font-size:0.85rem;'>({len(items)} row{'s' if len(items)!=1 else ''})</span>", unsafe_allow_html=True)

                for global_idx, item in items:
                    name_map = {
                        "customers":   item.get("customer_name", "—"),
                        "employees":   item.get("name", "—"),
                        "vendors":     item.get("vendor_name", "—"),
                        "financials":  f"{item.get('month','')} {item.get('year','')}",
                        "custom_tabs": f"{item.get('icon','')} {item.get('title','')}",
                    }
                    display_name = name_map.get(src, "—")
                    deleted_at   = item.get("_deleted_at", "")

                    c1, c2, c3 = st.columns([5, 1, 1])
                    c1.markdown(f"&nbsp;&nbsp; **{display_name}** &nbsp; <span style='color:#aaa; font-size:0.8rem;'>deleted {deleted_at}</span>", unsafe_allow_html=True)
                    with c2:
                        if st.button("↩️ Restore", key=f"g_restore_{global_idx}"):
                            restore_from_trash(global_idx)
                            st.success(f"'{display_name}' restored.")
                            st.rerun()
                    with c3:
                        if st.button("❌ Delete", key=f"g_delete_{global_idx}"):
                            delete_from_trash(global_idx)
                            st.rerun()
                st.markdown("---")

        # Bulk action
        if st.button("🗑️ Empty All Trash", type="primary"):
            save_global_trash([])
            st.success("All trash permanently deleted.")
            st.rerun()
