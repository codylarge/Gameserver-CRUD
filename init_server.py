import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("firebase_secrets.json")  # Make sure to provide the path to your Firebase key
firebase_admin.initialize_app(cred)

db = firestore.client()

SERVER_NAME = "vanilla+"  # Server name
SERVER_IP = "104.255.228.100"

# Define the server data
server_ip = SERVER_IP  # Server IP (unique ID)
server_data = {
    "name": SERVER_NAME,  # Server name
    "created_at": firestore.SERVER_TIMESTAMP,  # Creation timestamp
}
# Check if server already exists
existing_server_ref = db.collection("servers").document(server_ip)
existing_server = existing_server_ref.get()

if existing_server.exists:
    print(f"Server with IP {server_ip} already exists. No action taken.")
else:
    db.collection("servers").document(server_ip).set(server_data)
    print(f"Server '{server_data['name']}' created with IP: {server_ip}")
