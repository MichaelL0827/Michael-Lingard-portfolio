import hashlib
import json
import os
import getpass
import pwinput
#Michael Lingard portion
#All comment out portions were to test if it all works.
#Call the .JSON file 
#user_pass = "user_pass.json"

#Hash the password in a hash format
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

#Load users function
#def load_users():
    #if os.path.exists(user_pass):
       # try:
        #    with open(user_pass, 'r') as file:
          #      return json.load(file)
        #except json.JSONDecodeError:
        #    print(f"Error reading JSON from '{user_pass}'. File may be empty or corrupted.")
   # return {}

#Save users function
#def save_users(users):
    #try:
      #  with open(user_pass, 'w')as file:
        #    json.dump(users, file, indent=4)
   # except Exception as e:
    #    print(f"Error saving user to file: {e}")

#Validate Username and Password
def validate_username(username):
    errors = []
    if not username.strip():
        errors.append("Username cannot be empty.")
    return errors

def Validate_password (password,min_length=5, max_length=10):
    errors = []
    if not password.strip():
        errors.append("Password cannot be empty.")
    if " " in password:
        errors.append("Password cannot contain spaces.")
    if len(password) < min_length or len(password) > max_length:
        errors.append(f"Password must be between {min_length} and {max_length} characters.")
    return errors

# Register a new user
#def register_user(username, password):
    #users = load_users()

#    if username in users:
#        print(f"User '{username}' already exists.")
#        return False

#    users[username] = hash_password(password)
#    save_users(users)
#    print("User successfully created!")
#    return True

# Check user login
#def check_login(username, password):
#    users = load_users()
#    hashed_password = users.get(username)
#    return hashed_password == hash_password(password)

# Prompt Log-in
#def prompt_credentials(action):
#    username = input("Enter username: ")
#    password = input("Enter password: ")
#    errors = validate_username_password(username, password)
#    if errors:
#        for error in errors:
#            print(error)
#        return None, None
#    return username, password

# Handle login or signup
#def login_or_signup():
#   print("Welcome to IMS!")
#    action = input("(L)ogin or (S)ignup? ").lower()
#
#    if action not in ['l', 's']:
#        print("Invalid choice. Please choose 'L' or 'S'.")
#        return

#    while True:
#        username, password = prompt_credentials(action)
#        if not username or not password:
#            continue

#        if action == 's':  # Signup flow
#            if register_user(username, password):
#                break
#        elif action == 'l':  # Login flow
#           if check_login(username, password):
#                print("Welcome to your Inventory!")
#                break
#            else:
#                print("Username or password incorrect. Try again.")

#login_or_signup()