import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_secrets.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# READ 
def get_players(server_ip: str, search_query: str) -> list:
    '''
    Fetches all players whos NAME, IP, or STEAM64 match the search query.
    '''
    if search_query:
        players_ref = db.collection("servers").document(server_ip).collection("players")
        players = players_ref.stream()
        
        matching_players = []
        for player in players:
            player_data = player.to_dict()
            if (search_query.lower() in player.id or  # Search by IP
                search_query.lower() in player_data.get("name", "").lower() or  # Search by name
                search_query.lower() in str(player_data.get("steam64", ""))):  # Search by Steam64
                matching_players.append(player_data)

        print(f"Found {len(matching_players)} player(s):")
        
        return matching_players


def add_player(server_ip: str, player_ip: str, steam64: str, name: str = None) -> bool:
    '''
    Adds a player to the players collection of a given server.

    - Creates a player document using player_ip if it doesn't already exist.
    - Adds a new account (steam64 + name) under the player's "accounts" subcollection.

    Returns:
        bool: True if the player and account were added, False if the player already exists.
    '''

    # Fallback name if not provided
    if not name:
        name = steam64

    # References
    players_ref = db.collection("servers").document(server_ip).collection("players")
    player_doc = players_ref.document(player_ip)

    # If the player doesn't exist, create the doc + subcollections
    if not player_doc.get().exists:
        try:
            player_doc.set({
                "ip": player_ip
            })
            # Initialize empty subcollections
            player_doc.collection("bans")
            player_doc.collection("warnings")
            print(f"New player created for IP: {player_ip}")
        except Exception as e:
            print(f"Error creating player: {e}")
            return False

    # Add the account to the accounts subcollection
    accounts_ref = player_doc.collection("accounts")
    account_doc = accounts_ref.document(steam64)

    if account_doc.get().exists:
        print(f"Account with Steam64 {steam64} already exists for player {player_ip}")
        return False  # Account already exists

    try:
        account_doc.set({
            "steam64": steam64,
            "name": name
        })
        print(f"Added account '{name}' with Steam64 {steam64} to player {player_ip}")
        return True
    except Exception as e:
        print(f"Error adding account: {e}")
        return False


def delete_player(server_ip: str, player_ip: str, player_name: str, player_steam: str) -> bool:
    '''
    Deletes a player document in the players collection of a given server.

    Returns:
        bool: True if player was deleted, False if player does not exist.
    '''
    
    players_ref = db.collection("servers").document(server_ip).collection("players")
    player_doc = players_ref.document(player_ip)

    # Check if player exists
    if not player_doc.get().exists:
        print(f"Player with IP {player_ip} does not exist in server {server_ip}. No action taken.")
        return False  # Player does not exist

    # Delete the player document
    player_doc.delete()
    print(f"Player with IP {player_ip} deleted from server {server_ip}.")
    return True
