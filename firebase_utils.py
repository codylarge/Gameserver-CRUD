import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_secrets.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def add_player(server_ip: str, player_ip: str, steam64: str, name: str = None) -> bool:
    '''
    Adds a player to the players collection of a given server.

    Returns:
        bool: True if player was added, False if player already exists, or the player was not added for any other reason.
    '''
    
    # Use steam64 as name if name is not provided
    if not name:
        name = steam64

    # Reference to players collection
    players_ref = db.collection("servers").document(server_ip).collection("players")

    # Check if player already exists
    player_doc = players_ref.document(player_ip)
    if player_doc.get().exists:
        print(f"Player with IP {player_ip} already exists in server {server_ip}. No action taken.")
        return False  # Player already exists

    # Create the players collection by adding the new player
    player_doc.set({
        "ip": player_ip,
        "steam64": steam64,
        "name": name
    })

    # Create empty sub-collections: accounts, bans, warnings
    player_doc.collection("accounts")
    player_doc.collection("bans")
    player_doc.collection("warnings")

    print(f"Player '{name}' added to server '{server_ip}' with IP: {player_ip}")
    return True

def delete_all_players(server_ip: str) -> int:
    '''
    Deletes all player documents in the players collection of a given server.

    Returns:
        int: The number of players deleted.
    '''
    
    players_ref = db.collection("servers").document(server_ip).collection("players")
    players = players_ref.stream()

    deleted_count = 0

    for player in players:
        player.reference.delete()
        deleted_count += 1

    print(f"Deleted {deleted_count} players from server {server_ip}.")
    return deleted_count

