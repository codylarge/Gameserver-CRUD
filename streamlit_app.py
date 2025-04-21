import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

from firebase_utils import add_player, delete_all_players

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

    # READ 
    if search_query:
        players_ref = db.collection("servers").document(server_info["ip"]).collection("players")
        players = players_ref.stream()
        
        matching_players = []
        for player in players:
            player_data = player.to_dict()
            if (search_query.lower() in player.id.lower() or  # Search by IP
                search_query.lower() in player_data.get("name", "").lower() or  # Search by name
                search_query.lower() in str(player_data.get("steam64", "")).lower()):  # Search by Steam64
                matching_players.append(player_data)
        
        if matching_players:
            st.write(f"Found {len(matching_players)} player(s):")
            
            for idx, player in enumerate(matching_players):
                with st.container():
                    # Box-style background
                    st.markdown(
                        """
                        <style>
                        .player-box {
                            background-color: #f1f3f6;
                            padding: 1rem;
                            margin-bottom: 1rem;
                            border-radius: 10px;
                            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
                        }

                        
                        </style>
                        """,
                        unsafe_allow_html=True
                    )

                    with st.markdown(f'<div class="player-box">', unsafe_allow_html=True):
                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.markdown(f"**IP**: {player['ip']}  \n"
                                        f"**Name**: {player['name']}  \n"
                                        f"**Steam64**: {player.get('steam64', 'N/A')}")
                        
                        with col2:
                            edit_key = f"edit_{idx}"
                            remove_key = f"remove_{idx}"

                            if st.button("✏️ Edit", key=edit_key):
                                st.session_state.editing_player = player  # or open a form etc.

                            if st.button("🗑️ Remove", key=remove_key):
                                st.session_state.remove_player = player  # or trigger deletion logic
                                
                    st.markdown("</div>", unsafe_allow_html=True)

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
                        name=player_name if player_name else None
                    )
                    if success:
                        st.success(f"Player {player_name or steam64_id} added successfully!")
                        st.session_state.show_form = False  # Optionally hide form again
                    else:
                        st.warning("Player with this IP already exists.")
                else:
                    st.warning("Both Player IP and Steam64 ID are required.")
