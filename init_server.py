import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("firebase_secrets.json")  # Make sure to provide the path to your Firebase key
firebase_admin.initialize_app(cred)

db = firestore.client()

# Define the server data
server_ip = "104.255.228.100"  # Server IP (unique ID)
server_data = {
    "name": "vanilla+",  # Server name
    "created_at": firestore.SERVER_TIMESTAMP,  # Creation timestamp
}

# Create the server document using the IP as the document ID
db.collection("servers").document(server_ip).set(server_data)

print(f"Server '{server_data['name']}' created with IP: {server_ip}")
