def main():

    from shlex import split
    from getpass import getpass
    import sqlite3
    import hashlib
    import os

    info = "Booker v1.0.0"
    copyright = "Copyright (c) 2025 Chen Hang Tsz Henry"
    databasepath = os.path.realpath(os.path.dirname(__file__))+"/data.db"

    commands = {
        "help": {"help": "Show help message."},
        "man": {"args": ["command"], "help": "Show manual for a specific command."},
        "exit": {"help": "Exit Booker."},
        "ver": {"help": "Show current version info."},
        "cls": {"help": "Clear the screen."},
        "login": {"args": ["username"], "help": "Log in as a user."},
        "reg": {
            "args": ["username"],
            "help": "Register a new user. This command is only available for admin users.",
        },
        "dereg": {
            "args": ["usernames"],
            "help": "Deregister users. Separate names with commas without spaces. This command is only available for admin users.",
        },
        "users": {
            "help": "List all users. This command is only available for admin users.",
        },
        "build": {
            "args": ["roomIDs"],
            "help": "Create new rooms with specified IDs. Separate IDs with commas without spaces. This command is only available for admin users.",
        },
        "destroy": {
            "args": ["roomIDs"],
            "help": "Delete rooms with specified IDs. Separate IDs with commas without spaces. This command is only available for admin users.",
        },
        "reset": {
            "help": "Reset Booker by deleting all data and recreating the default admin user. This command is only available for admin users.",
        },
        "cp": {
            "help": "Change the password of the current user.",
        },
        "rooms": {
            "help": "List all rooms.",
        },
        "list": {
            "args": ["roomIDS", "usernames", "start", "end"],
            "help": "List bookings of the specified rooms booked by specified users within a given time. Separate IDs and names with commas without spaces. Time inputs must be quoted and in the format of YYYY-MM-DD HH:MM. Wildcard * can be used. e.g. 'list * * * *' will list all bookings.",
        },
        "show": {
            "args": ["bookingIDs"],
            "help": "Show bookings of specified booking IDs. Separate IDs with commas without spaces.",
        },
        "book": {
            "args": ["roomIDs", "start", "end"],
            "help": "Make a reservation for specified rooms at a given time. Separate IDs with commas without spaces. Time inputs must be quoted and in the format of YYYY-MM-DD HH:MM.",
        },
        "cancel": {"args": ["bookingIDs"], "help": "Cancel bookings by booking IDs. Separate IDs with commas without spaces. Standard users can only cancel their own bookings."},
        "clear": {
            "args": ["roomIDS", "usernames", "start", "end"],
            "help": "Cancel or shorten bookings to make available the specified rooms booked by specified users within a given time. Separate IDs and names with commas without spaces. Time inputs must be quoted and in the format of YYYY-MM-DD HH:MM. Standard users can only clear their own bookings.",
        },
        "search": {
            "args": ["start", "end", "duration"],
            "help": "Search for rooms that are available to be booked for a specified duration (in minutes) within a given time. Time inputs must be quoted and in the format of YYYY-MM-DD HH:MM.",
        },
        "sql": {
            "args": ["query"],
            "help": "Execute a raw SQL query. Be careful with this command as it can modify the database.",
        },
    }

    print(info)
    print(copyright)
    print("Type 'help' for a list of commands.")

    cursor = sqlite3.connect(databasepath).cursor()
    if cursor.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='users'").fetchone() is None:

        # Create users table if it does not exist
        cursor.execute(
            "CREATE TABLE users (username TEXT PRIMARY KEY, pwhash BLOB NOT NULL, isadmin BOOlEAN NOT NULL DEFAULT 0)"
        )
        cursor.execute("INSERT INTO users (username, pwhash, isadmin) VALUES (?, ?, ?)", ("admin", hashlib.sha3_512(b"admin").digest(), 1))

        print("Initialization: Created 'users' table and added default admin user.")

    if cursor.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='bookings'").fetchone() is None:

        # Create bookings table if it does not exist
        cursor.execute(
            "CREATE TABLE bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, roomID VARCHAR(8), username TEXT, start CHAR(16) NOT NULL, end CHAR(16) NOT NULL, FOREIGN KEY (username) REFERENCES users(username), FOREIGN KEY (roomID) REFERENCES rooms(id))"
        )

        print("Initialization: Created 'bookings' table.")

    if cursor.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='rooms'").fetchone() is None:

        # Create rooms table if it does not exist
        cursor.execute(
            "CREATE TABLE rooms (id VARCHAR(8) PRIMARY KEY)"
        )

        print("Initialization: Created 'rooms' table.")

    cursor.connection.commit()
    cursor.connection.close()

    currentuser = None  # Placeholder for current user
    isadmin = False  # Placeholder for admin status

    while True:
        args = split(input('\n' + (('\033[31m'+currentuser+'\033[0m' if isadmin else currentuser) if currentuser is not None else "") + "> ")) # Split input into arguments
        
        # Ignore empty input
        if len(args) == 0:
            continue

        # Check if command exists
        if args[0] not in commands:
            print(f"Unknown command '{args[0]}' entered. Type 'help' for a list of commands.")
            continue

        # Check required number of arguments
        if len(args)-1 != (len(commands[args[0]]['args']) if 'args' in commands[args[0]] else 0):
            print(f"Command '{args[0]}' requires {len(commands[args[0]]['args']) if 'args' in commands[args[0]] else 0} argument(s). Got {len(args)-1}.")
            continue

        # Handle commnands 
        if args[0] == "help":

            print("Command".ljust(25)+"Description")
            print("---".ljust(25)+"---")
            for cmd, details in commands.items():
                print(cmd.ljust(25)+details['help'])

        elif args[0] == "man":

            if args[1] in commands:
                print(
                    f"Usage: {args[1]} {"["+"] [".join(commands[args[1]]['args'])+"]" if 'args' in commands[args[1]] else ''}\n\n{commands[args[1]]['help']}"
                )
            else:
                print(f"No manual entry for command '{args[1]}'.")

        elif args[0] == "exit":

            exit(0)

        elif args[0] == "version":

            print(info)
            print(copyright)

        elif args[0] == "cls":

            os.system("cls" if os.name == "nt" else "clear")

        elif args[0] == "login":

            pwhash = hashlib.sha3_512(getpass("Password: ").encode()).digest()

            cursor = sqlite3.connect(databasepath).cursor()
            result = cursor.execute("SELECT * FROM users WHERE username=? AND pwhash=?", (args[1], pwhash)).fetchone()
            cursor.connection.commit()
            cursor.connection.close()

            if result is not None:
                currentuser = args[1]
                isadmin = result[2] == 1
                print(f"Logged in as '{'\033[31m'+currentuser+'\033[0m' if isadmin else currentuser}'.")
            else:
                print("Invalid username or password.")

        elif currentuser is not None:
            if args[0] == "cp":
                
                new_password = getpass("New Password: ")
                confirm_password = getpass("Confirm New Password: ")

                if new_password != confirm_password:
                    print("Passwords do not match. Please try again.")
                    continue

                new_pwhash = hashlib.sha3_512(new_password.encode()).digest()
                cursor = sqlite3.connect(databasepath).cursor()
                cursor.execute("UPDATE users SET pwhash=? WHERE username=?", (new_pwhash, currentuser))
                cursor.connection.commit()
                cursor.connection.close()

                print("Password changed successfully.")

            elif args[0] == "rooms":

                cursor = sqlite3.connect(databasepath).cursor()
                rooms = cursor.execute("SELECT id FROM rooms").fetchall()
                cursor.connection.commit()
                cursor.connection.close()

                if rooms:
                    print("Rooms found:")
                    for room in rooms:
                        print(room[0])
                else:
                    print("No rooms found. Please create rooms using the 'build' command.")

            elif args[0] == "list":

                room_ids = args[1].split(',')
                user_ids = args[2].split(',')
                start = args[3]
                end = args[4]

                params = []
                if room_ids[0] != '*':
                    params.extend(room_ids)
                if user_ids[0] != '*':
                    params.extend(user_ids)
                if start != '*':
                    params.append(start)
                if end != '*':
                    params.append(end)

                query = f"SELECT * FROM bookings WHERE {'roomID IN ('+','.join('?' for _ in room_ids)+')' if room_ids[0] != '*' else "TRUE"}" + f" AND {'username IN ('+','.join('?' for _ in user_ids)+')' if room_ids[0] != '*' else "TRUE"}" + f" AND {"left(timediff(?, end), 1) != '+'" if start != '*' else "TRUE"}" + f" AND {"left(timediff(start, ?), 1) != '+'" if end != '*' else "TRUE"}"

                cursor = sqlite3.connect(databasepath).cursor()
                bookings = cursor.execute(query, params).fetchall()
                cursor.connection.commit()
                cursor.connection.close()

                if bookings:
                    print("Bookings found:")
                    print("Booking ID".ljust(25)+"Room ID".ljust(25)+"User".ljust(25)+"Start Time".ljust(25)+"End Time")
                    print("---".ljust(25)+"---".ljust(25)+"---".ljust(25)+"---".ljust(25)+"---")
                    for booking in bookings:
                        print(str(booking[0]).ljust(25)+str(booking[1]).ljust(25)+str(booking[2]).ljust(25)+str(booking[3]).ljust(25)+str(booking[4]).ljust(25))
                else:
                    print("No bookings found.")

            elif args[0] == "show":

                booking_ids = args[1].split(',')
                bookings = []

                cursor = sqlite3.connect(databasepath).cursor()
                for booking_id in booking_ids:
                    booking = cursor.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
                    if booking is None:
                        print(f"Booking ID '{booking_id}' does not exist and is skipped.")
                        continue
                    bookings.append(booking)
                cursor.connection.commit()
                cursor.connection.close()

                if bookings:
                    print("Bookings found:")
                    print("Booking ID".ljust(25)+"Room ID".ljust(25)+"User".ljust(25)+"Start Time".ljust(25)+"End Time")
                    print("---".ljust(25)+"---".ljust(25)+"---".ljust(25)+"---".ljust(25)+"---")
                    for booking in bookings:
                        print(str(booking[0]).ljust(25)+str(booking[1]).ljust(25)+str(booking[2]).ljust(25)+str(booking[3]).ljust(25)+str(booking[4]).ljust(25))
                else:
                    print("No bookings found.")

            elif args[0] == "book":

                # Check if time slot booked

                room_ids = args[1].split(',')
                actual = []
                start = args[2]
                end = args[3]

                cursor = sqlite3.connect(databasepath).cursor()
                if cursor.execute("SELECT strftime('%%F %R', ?), strftime('%%F %R', ?)", (start, end)).fetchone() is not None:
                    for room_id in room_ids:
                        if cursor.execute("SELECT * FROM rooms WHERE id=?", (room_id,)).fetchone() is None:
                            print(f"Room '{room_id}' does not exist and is skipped.")
                            continue
                        actual.append(room_id)
                        cursor.execute("INSERT INTO bookings (roomID, username, start, end) VALUES (?, ?, strftime('%F %R', ?), strftime('%F %R', ?))", (room_id, currentuser, start, end))
                    cursor.connection.commit()
                    cursor.connection.close()
                    print(f"Booking(s) for the following room(s) created successfully:")
                    print("\t".join(actual))
                else:
                    print("Invalid time format. Please use 'YYYY-MM-DD HH:MM'.")

            elif isadmin:

                if args[0] == "reg":
                    
                    cursor = sqlite3.connect(databasepath).cursor()
                    if cursor.execute("SELECT * FROM users WHERE username=?", (args[1],)).fetchone() is None:
                        pwhash = hashlib.sha3_512(getpass("Password: ").encode()).digest()
                        cursor.execute("INSERT INTO users (username, pwhash) VALUES (?, ?)", (args[1], pwhash))
                        print(f"User '{args[1]}' registered successfully.")
                    else:
                        print(f"User '{args[1]}' already exists. Please choose a different username.")
                    cursor.connection.commit()
                    cursor.connection.close()                

                elif args[0] == "dereg":

                    # To add detect if only one admin left and being deregistered

                    usernames = args[1].split(',')
                    actual = []

                    cursor = sqlite3.connect(databasepath).cursor()
                    for username in usernames:
                        if cursor.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone() is None:
                            print(f"User '{username}' does not exist and is skipped.")
                            continue
                        actual.append(username)
                        cursor.execute("DELETE FROM users WHERE username=?", (username,))
                    cursor.connection.commit()
                    cursor.connection.close()

                    if actual:
                        print(f"The following users are deregistered successfully:")
                        print("\t".join(actual))
                    else:
                        print("No users were deregistered.")

                elif args[0] == "users":

                    cursor = sqlite3.connect(databasepath).cursor()
                    users = cursor.execute("SELECT username, isadmin FROM users").fetchall()
                    cursor.connection.commit()
                    cursor.connection.close()

                    if users:
                        print("Users found:")
                        print("Username".ljust(25)+"Admin")
                        print("---".ljust(25)+"---")
                        for user in users:
                            print(user[0].ljust(25)+("Yes" if user[1] else "No"))
                    else:
                        print("No users found.")

                elif args[0] == "build":

                    room_ids = args[1].split(',')
                    actual = []

                    cursor = sqlite3.connect(databasepath).cursor()
                    for room_id in room_ids:
                        if cursor.execute("SELECT * FROM rooms WHERE id=?", (room_id,)).fetchone() is not None:
                            print(f"Room '{room_id}' already exists and is skipped.")
                            continue
                        actual.append(room_id)
                        cursor.execute("INSERT INTO rooms (id) VALUES (?)", (room_id,))
                    cursor.connection.commit()
                    cursor.connection.close()

                    if actual:
                        print(f"The following rooms are created successfully:")
                        print("\t".join(actual))
                    else:
                        print("No rooms were created.")

                elif args[0] == "destroy":

                    room_ids = args[1].split(',')
                    actual = []

                    cursor = sqlite3.connect(databasepath).cursor()
                    for room_id in room_ids:
                        if cursor.execute("SELECT * FROM rooms WHERE id=?", (room_id,)).fetchone() is None:
                            print(f"Room '{room_id}' does not exist and is skipped.")
                            continue
                        actual.append(room_id)
                        cursor.execute("DELETE FROM rooms WHERE id=?", (room_id,))
                    cursor.connection.commit()
                    cursor.connection.close()

                    if actual:
                        print(f"The following rooms are deleted successfully:")
                        print("\t".join(actual))
                    else:
                        print("No rooms were deleted.")                  

                elif args[0] == "reset":

                    cursor = sqlite3.connect(databasepath).cursor()
                    if input("Are you sure you want to reset Booker? This will delete all data and recreate the default admin user 'admin'. Type 'yes' to confirm: ").strip().lower() != "yes":
                        print("Reset cancelled.")
                        continue
                    cursor.execute("DROP TABLE IF EXISTS users")
                    cursor.execute("DROP TABLE IF EXISTS bookings")
                    cursor.execute("DROP TABLE IF EXISTS rooms")
                    cursor.execute(
                        "CREATE TABLE users (username TEXT PRIMARY KEY, pwhash BLOB NOT NULL, isadmin BOOLEAN NOT NULL DEFAULT 0)"
                    )
                    cursor.execute("INSERT INTO users (username, pwhash, isadmin) VALUES (?, ?, ?)", ("admin", hashlib.sha3_512(b"admin").digest(), 1))
                    cursor.execute(
                        "CREATE TABLE bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, roomID VARCHAR(8), username TEXT, start CHAR(16) NOT NULL, end CHAR(16) NOT NULL, FOREIGN KEY (username) REFERENCES users(username), FOREIGN KEY (roomID) REFERENCES rooms(id))"
                    )
                    cursor.execute(
                        "CREATE TABLE rooms (id VARCHAR(8) PRIMARY KEY)"
                    )
                    cursor.connection.commit()
                    cursor.connection.close()

                    print("Booker has been reset successfully. Default admin user 'admin' has been recreated.")

            else:
                print(f"Command '{args[0]}' is not available for standard users.")
        else:
            print(f"You must be logged in to use the command '{args[0]}'. Use 'login' to log in as a user first.")

# Make sure the script can only be run as a standalone program
if __name__ == "__main__":
    main()
else:
    print("Booker cannot be imported as a module.")
