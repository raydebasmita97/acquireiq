from simple_salesforce import Salesforce
import streamlit as st
import jwt
import time
import requests

try:
    # Load private key
    with open("server.key", "r") as f:
        private_key = f.read()

    # Build JWT claim
    payload = {
        "iss": st.secrets["SF_CONSUMER_KEY"],
        "sub": st.secrets["SF_USERNAME"],
        "aud": "https://login.salesforce.com",
        "exp": int(time.time()) + 300
    }

    token = jwt.encode(payload, private_key, algorithm="RS256")

    # Exchange JWT for access token
    response = requests.post("https://login.salesforce.com/services/oauth2/token", data={
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": token
    })

    if not response.ok:
        print(f"OAuth error: {response.status_code} — {response.json()}")
        raise Exception("JWT token exchange failed")

    auth = response.json()

    # Connect to Salesforce
    sf = Salesforce(
        instance_url=auth["instance_url"],
        session_id=auth["access_token"]
    )

    print("Connected successfully")
    print(f"Salesforce version: {sf.sf_version}")

    # Test query
    result = sf.query("SELECT Id, Name FROM Lead LIMIT 1")
    print(f"Query successful. Records found: {result['totalSize']}")

except Exception as e:
    print(f"Connection failed: {e}")
