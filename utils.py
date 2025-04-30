import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_secrets.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Create Local Database 
def load_players_cache(server_ip: str):
    cache = {}
    players_ref = db.collection("servers").document(server_ip).collection("players")
    players = players_ref.stream()

    for player in players:
        player_ip = player.id
        accounts_ref = players_ref.document(player_ip).collection("accounts")
        accounts = [doc.to_dict() for doc in accounts_ref.stream()]

        cache[player_ip] = {
            "ip": player_ip,
            "accounts": accounts
        }

    return cache


# READ 
def get_players(search_query: str, players_dict: dict) -> list:
    '''
    Fetches all players where the IP, or any account's Steam64 or Name matches the search query.
    Returns a list of full player dictionaries with their IP and ALL their accounts.
    '''
    matching_players = []

    for player_ip, player_data in players_dict.items():
        accounts = player_data.get("accounts", [])

        # Match on IP
        if search_query in player_ip:
            matching_players.append({
                "ip": player_ip,
                "accounts": accounts  # return all accounts
            })
            continue  # no need to check accounts

        # Match on any account name or steam64
        for account in accounts:
            steam64 = account.get("steam64", "")
            name = account.get("name", "")

            if (search_query.lower() in steam64.lower() or
                search_query.lower() in name.lower()):
                matching_players.append({
                    "ip": player_ip,
                    "accounts": accounts  # include all accounts
                })
                break  # stop checking other accounts for this player

    print(f"Found {len(matching_players)} matching player(s).")
    return matching_players


# CREATE
def add_player(server_ip: str, player_ip: str, steam64: str, players_dict: dict, name: str = None) -> bool:
    '''
    Adds a player to Firestore and updates the local players_dict cache.

    - Creates a player document using player_ip if it doesn't already exist.
    - Adds a new account (steam64 + name) under the player's "accounts" subcollection.
    - Also updates the provided players_dict if given.

    Returns:
        bool: True if the player/account was added, False if it already exists or failed.
    '''
    if not name:
        name = steam64

    players_ref = db.collection("servers").document(server_ip).collection("players")
    player_doc = players_ref.document(player_ip)

    # Check if player exists
    player_exists = player_doc.get().exists

    if not player_exists:
        try:
            player_doc.set({
                "ip": player_ip
            })
            player_doc.collection("bans")
            player_doc.collection("warnings")
            print(f"New player created for IP: {player_ip}")
        except Exception as e:
            print(f"Error creating player: {e}")
            return False
    else:
        print(f"Player with IP {player_ip} already exists.")
        return False

    # Check if account already exists
    accounts_ref = player_doc.collection("accounts")
    account_doc = accounts_ref.document(steam64)

    if account_doc.get().exists:
        print(f"Account with Steam64 {steam64} already exists for player {player_ip}")
        return False

    # Try adding account to Firestore
    try:
        account_doc.set({
            "steam64": steam64,
            "name": name
        })
        print(f"Added account '{name}' with Steam64 {steam64} to player {player_ip}")
    except Exception as e:
        print(f"Error adding account: {e}")
        return False

    # Update players_dict
    if players_dict is not None:
        if player_ip not in players_dict:
            players_dict[player_ip] = {
                "ip": player_ip,
                "accounts": []
            }

        # Avoid duplicates in cache too
        if not any(acc["steam64"] == steam64 for acc in players_dict[player_ip]["accounts"]):
            players_dict[player_ip]["accounts"].append({
                "steam64": steam64,
                "name": name
            })

    return True


# DELETE
def delete_player(server_ip: str, player_ip: str, players_dict: dict) -> bool:
    '''
    Deletes an entire player (all accounts) from Firestore and players_dict

    Returns:
        bool: True if deletion was successful, False otherwise.
    '''
    players_ref = db.collection("servers").document(server_ip).collection("players")
    player_doc = players_ref.document(player_ip)

    # Check if the player exists
    if not player_doc.get().exists:
        print(f"Player with IP {player_ip} does not exist in server {server_ip}.")
        return False

    try:
        # Delete all accounts first
        accounts_ref = player_doc.collection("accounts")
        accounts = accounts_ref.stream()
        for account in accounts:
            account.reference.delete()

        # Delete player document itself
        player_doc.delete()

        # Update players_dict
        if player_ip in players_dict:
            del players_dict[player_ip]

        print(f"Deleted entire player {player_ip} and all associated accounts.")
        return True

    except Exception as e:
        print(f"Error deleting player {player_ip}: {e}")
        return False

def delete_account(server_ip: str, player_ip: str, player_steam: str, players_dict: dict) -> bool:
    '''
    Deletes a specific account (by Steam64) under a player in Firestore.
    If no accounts remain, deletes the player entirely.
    Also updates the players_dict accordingly.

    Returns:
        bool: True if deletion was successful, False otherwise.
    '''
    players_ref = db.collection("servers").document(server_ip).collection("players")
    player_doc = players_ref.document(player_ip)

    # Check if the player exists
    if not player_doc.get().exists:
        print(f"Player with IP {player_ip} does not exist in server {server_ip}.")
        return False

    accounts_ref = player_doc.collection("accounts")
    account_doc = accounts_ref.document(player_steam)

    if not account_doc.get().exists:
        print(f"Account with Steam64 {player_steam} does not exist for player {player_ip}.")
        return False

    try:
        # Delete the specific account
        account_doc.delete()
        print(f"Deleted account {player_steam} under player {player_ip}.")

        # Update players_dict
        if player_ip in players_dict:
            accounts = players_dict[player_ip]["accounts"]
            updated_accounts = [acc for acc in accounts if acc["steam64"] != player_steam]
            players_dict[player_ip]["accounts"] = updated_accounts

            # If no accounts left, delete the player
            if not updated_accounts:
                player_doc.delete()
                del players_dict[player_ip]
                print(f"No accounts left for player {player_ip}. Deleted player document.")

        return True

    except Exception as e:
        print(f"Error deleting account {player_steam}: {e}")
        return False
