import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase with your service account

cred = credentials.Certificate("bank-management-system-a0944-firebase-adminsdk-fbsvc-290ad1ae1a.json")
firebase_admin.initialize_app(cred)

# Create Firestore client
db = firestore.client()
