import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

from utils import add_player, get_players, load_players_cache, delete_player

# Initialize Firebase if not done already
if not firebase_admin._apps:  # If no apps are initialized, initialize Firebase
    cred = credentials.Certificate("firebase_secrets.json")  # Path to your Firebase key
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Fetch servers from Firestore
servers_ref = db.collection("servers")
servers = servers_ref.stream()

# Create a list of server names for the dropdown
server_names = []
server_data = {}

players = {}

for server in servers:
    data = server.to_dict()
    server_names.append(data["name"])
    server_data[data["name"]] = {
        "ip": server.id,
        "created_at": data["created_at"]
    }

# Streamlit UI: Dropdown to select a server
selected_server_name = st.selectbox("Select a Server", server_names)


# Display information for the selected server
if selected_server_name:
    server_info = server_data[selected_server_name]
    st.subheader(selected_server_name.capitalize())
    
    # Add Search Bar (search players by IP, name, or Steam64 ID)
    search_query = st.text_input("Search Player (by IP, name, or Steam64)", "")

    players = load_players_cache(server_info["ip"])

    print("PLAYERS", players)

    matching_players = get_players(
        search_query=search_query,
        players_dict=players
    )

    if matching_players:
        for idx, player in enumerate(matching_players):
            accounts = player.get("accounts", [])
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**IP**: {player['ip']}  \n")
                    num_accounts = 1
                    for account in accounts:
                        steam64 = account.get("steam64", "N/A")
                        name = account.get("name", "N/A")
                        st.markdown(f"**Account {num_accounts}**:  \n"
                                    f"**Steam64**: {steam64}  \t|\t"
                                    f"**Name**: {name}  \n")
                        num_accounts += 1

                with col2:
                    edit_key = f"edit_{idx}"
                    remove_key = f"remove_{idx}"

                    if st.button("✏️ Edit", key=edit_key):
                        st.session_state.editing_player = player  # or open a form etc.

                    if st.button("🗑️ Remove", key=remove_key):
                        delete_player(
                            server_ip=server_info["ip"],
                            player_ip=player["ip"],
                            players_dict=players
                        )
    else:
        st.write("No players found matching the search criteria.")

    # Add Player Button + Form
    # Initialize session state for showing form
    if "show_form" not in st.session_state:
        st.session_state.show_form = False

    # CREATE 
    if st.button("Add Player"):
        st.session_state.show_form = True

    # Display the form if button has been clicked
    if st.session_state.show_form:
        st.subheader("Add a New Player")

        with st.form(key="add_player_form"):
            player_ip = st.text_input("Player IP (required)", key="player_ip")
            steam64_id = st.text_input("Steam64 ID (required)", key="steam64")
            player_name = st.text_input("Player Name (optional)", key="player_name")

            submit_button = st.form_submit_button("Submit")

            if submit_button:
                print("Submitted")
                if player_ip and steam64_id:
                    success = add_player(
                        server_ip=server_info["ip"],
                        player_ip=player_ip,
                        steam64=steam64_id,
                        players_dict=players,
                        name=player_name if player_name else None
                    )
                    if success:
                        st.success(f"Player {player_name or steam64_id} added successfully!")
                    else:
                        st.warning("Player with this IP already exists.")
                else:
                    st.warning("Both Player IP and Steam64 ID are required.")
