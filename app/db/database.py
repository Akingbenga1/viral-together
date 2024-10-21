from typing import Dict
import models

# In-memory mock database (replace this with actual DB in production)
fake_users_db: Dict[str, dict] = {}

# Function to add a new user to the mock database
def add_user_to_db(username: str, hashed_password: str):
    fake_users_db[username] = {"username": username, "hashed_password": hashed_password}

# Function to get a user by username
def get_user(username: str):
    return fake_users_db.get(username)
