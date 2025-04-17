import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase once
if "firebase_initialized" not in st.session_state:
    cred = credentials.Certificate("firebase_secrets.json")  # <--- update this path
    firebase_admin.initialize_app(cred)
    st.session_state.firebase_initialized = True

db = firestore.client()


st.title("🎮 Player Information Dashboard")

# Get all player documents
players_ref = db.collection("players")
docs = players_ref.stream()

# Display each player's data
for doc in docs:
    player_ip = doc.id
    data = doc.to_dict()
    accounts = data.get("accounts", [])
    bans = data.get("bans_warnings", [])

    with st.container():
        st.subheader(f"🧑‍💻 Player IP: {player_ip}")
        st.markdown("**Accounts:**")
        for acc in accounts:
            st.markdown(f"- `{acc}`")

        st.markdown("**Bans / Warnings:**")
        if bans:
            for b in bans:
                st.markdown(f"- ⚠️ `{b}`")
        else:
            st.markdown("- ✅ No bans or warnings")

        st.markdown("---")
