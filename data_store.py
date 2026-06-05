import json
import os
import pandas as pd

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULTS = {
    "customers": [
        {"rank": 1,  "customer_name": "Sunrise Senior Living",   "annual_contract_value": 420000, "relationship_years": 8,  "key_contact": "Maria Chen",       "renewal_month": "March",     "renewal_year": 2027, "status": "Active"},
        {"rank": 2,  "customer_name": "Presbyterian Hospital",   "annual_contract_value": 380000, "relationship_years": 5,  "key_contact": "Dr. James Wilson",  "renewal_month": "June",      "renewal_year": 2026, "status": "Active"},
        {"rank": 3,  "customer_name": "Baylor Scott White",      "annual_contract_value": 340000, "relationship_years": 3,  "key_contact": "Sarah Mitchell",    "renewal_month": "September", "renewal_year": 2026, "status": "Active"},
        {"rank": 4,  "customer_name": "Methodist Health",        "annual_contract_value": 290000, "relationship_years": 6,  "key_contact": "Tom Bradley",       "renewal_month": "December",  "renewal_year": 2026, "status": "Active"},
        {"rank": 5,  "customer_name": "Kindred Healthcare",      "annual_contract_value": 265000, "relationship_years": 4,  "key_contact": "Lisa Park",         "renewal_month": "February",  "renewal_year": 2027, "status": "Active"},
        {"rank": 6,  "customer_name": "Encompass Health",        "annual_contract_value": 240000, "relationship_years": 2,  "key_contact": "Robert Hayes",      "renewal_month": "August",    "renewal_year": 2026, "status": "Active"},
        {"rank": 7,  "customer_name": "Amedisys",                "annual_contract_value": 210000, "relationship_years": 5,  "key_contact": "Jennifer Wu",       "renewal_month": "November",  "renewal_year": 2026, "status": "Active"},
        {"rank": 8,  "customer_name": "LHC Group",               "annual_contract_value": 195000, "relationship_years": 3,  "key_contact": "David Kim",         "renewal_month": "May",       "renewal_year": 2027, "status": "Active"},
        {"rank": 9,  "customer_name": "Acadia Healthcare",       "annual_contract_value": 175000, "relationship_years": 2,  "key_contact": "Amanda Torres",     "renewal_month": "July",      "renewal_year": 2026, "status": "Active"},
        {"rank": 10, "customer_name": "Select Medical",          "annual_contract_value": 160000, "relationship_years": 1,  "key_contact": "Michael Brown",     "renewal_month": "October",   "renewal_year": 2026, "status": "Active"},
    ],
    "employees": [
        {"name": "Sarah Martinez",  "role": "Director of Nursing",   "tenure_years": 12, "performance": "Top Performer",     "department": "Clinical",   "notes": "Manages all clinical staff. Critical to retain."},
        {"name": "James Wilson",    "role": "Operations Manager",    "tenure_years": 8,  "performance": "Strong Performer",  "department": "Operations", "notes": "Handles scheduling and logistics."},
        {"name": "Lisa Chen",       "role": "Billing Manager",       "tenure_years": 6,  "performance": "Top Performer",     "department": "Finance",    "notes": "99% billing accuracy."},
        {"name": "Robert Davis",    "role": "HR Manager",            "tenure_years": 4,  "performance": "Strong Performer",  "department": "HR",         "notes": ""},
        {"name": "Maria Rodriguez", "role": "Lead RN",               "tenure_years": 10, "performance": "Top Performer",     "department": "Clinical",   "notes": "Patients love her."},
        {"name": "Tom Anderson",    "role": "Physical Therapist",    "tenure_years": 7,  "performance": "Strong Performer",  "department": "Clinical",   "notes": ""},
        {"name": "Jennifer Lee",    "role": "Caregiver Supervisor",  "tenure_years": 5,  "performance": "Strong Performer",  "department": "Clinical",   "notes": ""},
        {"name": "David Park",      "role": "IT Coordinator",        "tenure_years": 3,  "performance": "Average Performer", "department": "IT",         "notes": "Knows all the systems."},
        {"name": "Amanda Johnson",  "role": "Marketing Coordinator", "tenure_years": 2,  "performance": "Strong Performer",  "department": "Marketing",  "notes": ""},
        {"name": "Michael Chen",    "role": "Finance Analyst",       "tenure_years": 4,  "performance": "Top Performer",     "department": "Finance",    "notes": "Knows the books inside out."},
    ],
    "vendors": [
        {"vendor_name": "MedBridge",           "product": "Training Platform",  "annual_cost": 48000,  "renewal_month": "March",   "renewal_year": 2026, "critical": True,  "notes": "Critical for staff training."},
        {"vendor_name": "Brightree",           "product": "EMR System",         "annual_cost": 96000,  "renewal_month": "July",    "renewal_year": 2026, "critical": True,  "notes": "Core operations system."},
        {"vendor_name": "Sandata",             "product": "Visit Verification", "annual_cost": 36000,  "renewal_month": "January", "renewal_year": 2026, "critical": True,  "notes": "Medicare compliance required."},
        {"vendor_name": "Paychex",             "product": "Payroll",            "annual_cost": 24000,  "renewal_month": "April",   "renewal_year": 2026, "critical": False, "notes": ""},
        {"vendor_name": "Travelers Insurance", "product": "Business Insurance", "annual_cost": 72000,  "renewal_month": "June",    "renewal_year": 2026, "critical": True,  "notes": "Must not lapse."},
    ],
    "financials": [
        {"month": "Jan", "year": 2025, "total_revenue": 620000, "medicare_revenue": 341000, "medicaid_revenue": 155000, "private_revenue": 124000},
        {"month": "Feb", "year": 2025, "total_revenue": 635000, "medicare_revenue": 349250, "medicaid_revenue": 158750, "private_revenue": 127000},
        {"month": "Mar", "year": 2025, "total_revenue": 658000, "medicare_revenue": 361900, "medicaid_revenue": 164500, "private_revenue": 131600},
        {"month": "Apr", "year": 2025, "total_revenue": 642000, "medicare_revenue": 353100, "medicaid_revenue": 160500, "private_revenue": 128400},
        {"month": "May", "year": 2025, "total_revenue": 671000, "medicare_revenue": 369050, "medicaid_revenue": 167750, "private_revenue": 134200},
        {"month": "Jun", "year": 2025, "total_revenue": 689000, "medicare_revenue": 378950, "medicaid_revenue": 172250, "private_revenue": 137800},
        {"month": "Jul", "year": 2025, "total_revenue": 695000, "medicare_revenue": 382250, "medicaid_revenue": 173750, "private_revenue": 139000},
        {"month": "Aug", "year": 2025, "total_revenue": 702000, "medicare_revenue": 386100, "medicaid_revenue": 175500, "private_revenue": 140400},
        {"month": "Sep", "year": 2025, "total_revenue": 718000, "medicare_revenue": 394900, "medicaid_revenue": 179500, "private_revenue": 143600},
        {"month": "Oct", "year": 2025, "total_revenue": 725000, "medicare_revenue": 398750, "medicaid_revenue": 181250, "private_revenue": 145000},
        {"month": "Nov", "year": 2025, "total_revenue": 731000, "medicare_revenue": 402050, "medicaid_revenue": 182750, "private_revenue": 146200},
        {"month": "Dec", "year": 2025, "total_revenue": 748000, "medicare_revenue": 411400, "medicaid_revenue": 187000, "private_revenue": 149600},
    ],
    "custom_tabs": [],
    "company_info": {
        "name": "Johnson Home Health Services",
        "tagline": "Your AI guide to your new business",
        "annual_revenue": "$8.03M",
        "employees": "45",
        "active_patients": "180",
        "gross_margin": "22%"
    }
}


def _path(key):
    return os.path.join(DATA_DIR, f"{key}.json")


def load(key):
    path = _path(key)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return DEFAULTS.get(key, [])


def save(key, data):
    with open(_path(key), "w") as f:
        json.dump(data, f, indent=2)


def load_df(key):
    return pd.DataFrame(load(key))


def save_df(key, df):
    save(key, df.to_dict(orient="records"))


def load_company():
    return load("company_info")


def save_company(info):
    save("company_info", info)


def load_custom_tabs():
    return load("custom_tabs")


def save_custom_tabs(tabs):
    save("custom_tabs", tabs)


def load_global_trash():
    return load("global_trash") if os.path.exists(_path("global_trash")) else []


def save_global_trash(trash):
    save("global_trash", trash)


def move_to_trash(source_key, rows):
    """Move rows to the global trash, tagged with their source."""
    import datetime
    trash = load_global_trash()
    for row in rows:
        row = dict(row)
        row["_source"] = source_key
        row["_deleted_at"] = datetime.date.today().strftime("%b %d, %Y")
        trash.append(row)
    save_global_trash(trash)


def restore_from_trash(index):
    """Restore a row from global trash back to its source dataset."""
    trash = load_global_trash()
    row = dict(trash.pop(index))
    source = row.pop("_source", None)
    row.pop("_deleted_at", None)
    save_global_trash(trash)
    if source:
        data = load(source)
        data.append(row)
        save(source, data)


def delete_from_trash(index):
    trash = load_global_trash()
    trash.pop(index)
    save_global_trash(trash)


def load_kb_overrides():
    return load("kb_overrides") if os.path.exists(_path("kb_overrides")) else {}


def save_kb_overrides(overrides):
    save("kb_overrides", overrides)


ALL_SECTIONS = ["customers", "employees", "vendors", "financials", "custom_tabs"]

def load_active_sections():
    if os.path.exists(_path("active_sections")):
        return load("active_sections")
    return ALL_SECTIONS[:]


def save_active_sections(sections):
    save("active_sections", sections)


def delete_section(section_key):
    import datetime
    # Move entire section data to global trash as one entry
    data = load(section_key)
    trash = load_global_trash()
    trash.append({
        "_source": "__section__",
        "_section_key": section_key,
        "_section_data": data,
        "_deleted_at": datetime.date.today().strftime("%b %d, %Y"),
    })
    save_global_trash(trash)
    # Remove from active sections
    active = load_active_sections()
    if section_key in active:
        active.remove(section_key)
    save_active_sections(active)


def restore_section(global_index):
    trash = load_global_trash()
    item = trash.pop(global_index)
    section_key = item.get("_section_key")
    section_data = item.get("_section_data", [])
    save_global_trash(trash)
    if section_key:
        save(section_key, section_data)
        active = load_active_sections()
        if section_key not in active:
            active.append(section_key)
        save_active_sections(active)
