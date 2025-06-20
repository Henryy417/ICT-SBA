def main():

    from shlex import split
    from getpass import getpass
    from hashlib import sha3_512
    import sqlite3
    import os

    info = "Booker v1.0.0"
    copyright = "Copyright (c) 2025 Chen Hang Tsz Henry"
    databasepath = os.path.realpath(os.path.dirname(__file__))+"/data.db"

    currentuser = None  # Placeholder for current user
    isadmin = False  # Placeholder for admin status

    commands = {
        # Commands usable before login
        "help": {"help": "Show help message."},
        "man": {"args": ["command"], "help": "Show manual for a specific command."},
        "exit": {"help": "Exit Booker."},
        "ver": {"help": "Show current version info."},
        "cls": {"help": "Clear the screen."},
        "login": {"args": ["username"], "help": "Log in as a user."},
        # Commands usable as admins
        "reg": {
            "args": ["username"],
            "help": "Register a new user. This command is only available for admin users.",
        },
        "dereg": {
            "args": ["usernames"],
            "help": "Deregister users. Separate names with commas without spaces. This command is only available for admin users.",
        },
        "cpx": {
            "args": ["username"],
            "help": "Change the password of a user. This command is only available for admin users.",
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
        "sql": {
            "args": ["query"],
            "help": "Execute a raw SQL query. The SQL query must be quoted. Be careful with this command as it can modify the database.",
        },
        # Commands usable as standard users
        "cp": {
            "help": "Change the password of the current user.",
        },
        "rooms": {
            "help": "List all rooms.",
        },
        "search": {
            "args": ["roomIDs", "usernames", "start", "end"],
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
        "cancel": {
            "args": ["bookingIDs"],
            "help": "Cancel bookings by booking IDs. Separate IDs with commas without spaces. Standard users can only cancel their own bookings."
        },
        "clear": {
            "args": ["roomIDs", "usernames", "start", "end"],
            "help": "Cancel bookings to make available the specified rooms booked by specified users within a given time. Separate IDs and names with commas without spaces. Time inputs must be quoted and in the format of YYYY-MM-DD HH:MM. Standard users can only clear their own bookings.",
        }
    }

    print(info)
    print(copyright)
    print("Type 'help' for a list of commands.")

    cursor = sqlite3.connect(databasepath).cursor()

    if cursor.execute("SELECT type FROM sqlite_master WHERE type='table' AND name='users'").fetchone() is None:

        # Create users table if it does not exist
        cursor.execute(
            "CREATE TABLE users (username TEXT PRIMARY KEY, pwhash BLOB NOT NULL, isadmin BOOLEAN NOT NULL DEFAULT 0)"
        )
        cursor.execute("INSERT INTO users (username, pwhash, isadmin) VALUES (?, ?, ?)", ("admin", sha3_512(b"admin").digest(), 1))

        print("Initialization: Created 'users' table and added default admin user.")
    
    if cursor.execute("SELECT type FROM sqlite_master WHERE type='table' AND name='rooms'").fetchone() is None:

       # Create rooms table if it does not exist
       cursor.execute(
           "CREATE TABLE rooms (id TEXT PRIMARY KEY)"
       )

       print("Initialization: Created 'rooms' table.")

    if cursor.execute("SELECT type FROM sqlite_master WHERE type='table' AND name='bookings'").fetchone() is None:

        # Create bookings table if it does not exist
        cursor.execute(
            "CREATE TABLE bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, roomID TEXT, username TEXT, start TEXT NOT NULL, end TEXT NOT NULL, FOREIGN KEY (username) REFERENCES users(username), FOREIGN KEY (roomID) REFERENCES rooms(id))"
        )

        # Create indexes
        cursor.execute("CREATE INDEX idx_bookings_room_user ON bookings (roomID, username)")
        cursor.execute("CREATE INDEX idx_bookings_user ON bookings (username)")
        cursor.execute("CREATE INDEX idx_bookings_time ON bookings (start)")

        print("Initialization: Created 'bookings' table.")

    cursor.connection.commit()
    cursor.connection.close()

    print()

    while True:
        # Split input into arguments
        args = split(input((('\033[31m'+currentuser+'\033[0m' if isadmin else currentuser) if currentuser is not None else "") + "> "))
        
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

            pwhash = sha3_512(getpass("Password: ").encode()).digest()

            cursor = sqlite3.connect(databasepath).cursor()
            result = cursor.execute("SELECT isadmin FROM users WHERE username=? AND pwhash=?", (args[1], pwhash)).fetchone()
            cursor.connection.commit()
            cursor.connection.close()

            if result is not None:
                currentuser = args[1]
                isadmin = result[0] == 1
                print(f"Logged in as '{'\033[31m'+currentuser+'\033[0m' if isadmin else currentuser}'.")
            else:
                print("Invalid username or password.")

        elif currentuser is not None:
            if args[0] == "cp":

                if (new_password := getpass("New Password: ")) == getpass("Confirm New Password: "):
                    new_pwhash = sha3_512(new_password.encode()).digest()

                    cursor = sqlite3.connect(databasepath).cursor()
                    cursor.execute("UPDATE users SET pwhash=? WHERE username=?", (new_pwhash, currentuser))
                    cursor.connection.commit()
                    cursor.connection.close()

                    print("Password changed successfully.")
                else:
                    print("Passwords do not match. Please try again.")

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

            elif args[0] == "search":

                room_ids = args[1].split(',')
                user_ids = args[2].split(',')
                start = args[3]
                end = args[4]

                cursor = sqlite3.connect(databasepath).cursor()

                params = []
                if room_ids[0] != '*':
                    room_ids = [room for room in room_ids if cursor.execute("SELECT id FROM rooms WHERE id=?", (room)).fetchone() is not None or print(f"Room '{room}' does not exist and is skipped.")]
                    params.extend(room_ids)
                if user_ids[0] != '*':
                    user_ids = [user for user in user_ids if cursor.execute("SELECT username FROM users WHERE username=?", (user)).fetchone() is not None or print(f"User '{user}' does not exist and is skipped.")]
                    params.extend(user_ids)
                if start != '*':
                    params.append(start)
                if end != '*':
                    params.append(end)

                query = f"SELECT * FROM bookings WHERE {'roomID IN ('+','.join('?' for _ in room_ids)+')' if not room_ids or room_ids[0] != '*' else "TRUE"} AND {'username IN ('+','.join('?' for _ in user_ids)+')' if not user_ids or user_ids[0] != '*' else "TRUE"} AND {"substr(timediff(?, end),1,1) = '-'" if start != '*' else "TRUE"} AND {"substr(timediff(start, ?),1,1) = '-'" if end != '*' else "TRUE"}"
                
                bookings = cursor.execute(query, params).fetchall()
                cursor.connection.commit()
                cursor.connection.close()

                if bookings:
                    print("Bookings found:")
                    print("Booking ID".ljust(25)+"Room ID".ljust(25)+"User".ljust(25)+"Start Time".ljust(25)+"End Time".ljust(25))
                    print("---".ljust(25)+"---".ljust(25)+"---".ljust(25)+"---".ljust(25)+"---".ljust(25))
                    for booking in bookings:
                        print(str(booking[0]).ljust(25)+booking[1].ljust(25)+booking[2].ljust(25)+booking[3].ljust(25)+booking[4].ljust(25))
                else:
                    print("No bookings found.")

            elif args[0] == "show":

                booking_ids = args[1].split(',')
                bookings = []

                cursor = sqlite3.connect(databasepath).cursor()
                for booking_id in booking_ids:
                    booking = cursor.execute("SELECT * FROM bookings WHERE id=?", (booking_id)).fetchone()
                    if booking is None:
                        print(f"Booking ID '{booking_id}' does not exist and is skipped.")
                        continue
                    bookings.append(booking)
                cursor.connection.commit()
                cursor.connection.close()

                if bookings:
                    print("Bookings found:")
                    print("Booking ID".ljust(25)+"Room ID".ljust(25)+"User".ljust(25)+"Start Time".ljust(25)+"End Time".ljust(25))
                    print("---".ljust(25)+"---".ljust(25)+"---".ljust(25)+"---".ljust(25)+"---".ljust(25))
                    for booking in bookings:
                        print(str(booking[0]).ljust(25)+booking[1].ljust(25)+booking[2].ljust(25)+booking[3].ljust(25)+booking[4].ljust(25))
                else:
                    print("No bookings found.")

            elif args[0] == "book":

                room_ids = args[1].split(',')
                start = args[2]
                end = args[3]
                actual_room_ids = []

                cursor = sqlite3.connect(databasepath).cursor()

                if cursor.execute("SELECT strftime('%F %R', ?) IS NOT NULL AND strftime('%F %R', ?) IS NOT NULL", (start, end)).fetchone()[0] == 1:
                    if cursor.execute("SELECT substr(timediff(strftime('%F %R', ?), strftime('%F %R', ?)),1,1)", (end, start)).fetchone()[0] == "+":

                        for room_id in room_ids:
                            if cursor.execute("SELECT id FROM rooms WHERE id=?", (room_id)).fetchone() is None:
                                print(f"Room '{room_id}' does not exist and is skipped.")
                                continue
                            
                            booked = cursor.execute(f"SELECT id FROM bookings WHERE roomID = {room_id} AND substr(timediff(?, end),1,1) = '-' AND substr(timediff(start, ?),1,1) = '-'", (start, end)).fetchone()

                            if booked is not None:
                                print(f"Time slot is already booked (Booking ID: {booked[0]}) for room {room_id} and is skipped.")
                                continue

                            actual_room_ids.append(room_id)
                            cursor.execute("INSERT INTO bookings (roomID, username, start, end) VALUES (?, ?, strftime('%F %R', ?), strftime('%F %R', ?))", (room_id, currentuser, start, end))

                        if actual_room_ids:
                            print(f"Booking(s) for the following room(s) created successfully:")
                            print("\t".join(actual_room_ids))

                        else:
                            print("No bookings were created. Please check the time slot and room IDs.")
                    else:
                        print("Time slot is invalid. The end time must be after the start time.")
                else:
                    print("Invalid time format. Please use 'YYYY-MM-DD HH:MM'.")

                cursor.connection.commit()
                cursor.connection.close()

            elif args[0] == "cancel":

                booking_ids = args[1].split(',')
                actual_booking_ids = []

                cursor = sqlite3.connect(databasepath).cursor()

                for booking_id in booking_ids:
                    booking = cursor.execute("SELECT username FROM bookings WHERE id=?", (booking_id)).fetchone()
                    if booking is None:
                        print(f"Booking ID '{booking_id}' does not exist and is skipped.")
                        continue
                    if booking[0] != currentuser and not isadmin:
                        print(f"You can only cancel your own bookings as a standard user. Booking ID '{booking_id}' is skipped.")
                        continue
                    actual_booking_ids.append(booking_id)
                    cursor.execute("DELETE FROM bookings WHERE id=?", (booking_id))

                cursor.connection.commit()
                cursor.connection.close()

                if actual_booking_ids:
                    print(f"The following bookings are cancelled successfully:")
                    print("\t".join(actual_booking_ids))
                else:
                    print("No bookings were cancelled.")

            elif args[0] == "clear":

                room_ids = args[1].split(',')
                user_ids = args[2].split(',')
                start = args[3]
                end = args[4]
                actual_booking_ids = []

                cursor = sqlite3.connect(databasepath).cursor()

                params = []
                if room_ids[0] != '*':
                    room_ids = [room for room in room_ids if cursor.execute("SELECT id FROM rooms WHERE id=?", (room)).fetchone() is not None or print(f"Room '{room}' does not exist and is skipped.")]
                    params.extend(room_ids)
                if user_ids[0] != '*':
                    user_ids = [user for user in user_ids if cursor.execute("SELECT username FROM users WHERE username=?", (user)).fetchone() is not None or print(f"User '{user}' does not exist and is skipped.")]
                    params.extend(user_ids)
                if start != '*':
                    params.append(start)
                if end != '*':
                    params.append(end)

                query = f"SELECT id, username FROM bookings WHERE {'roomID IN ('+','.join('?' for _ in room_ids)+')' if not room_ids or room_ids[0] != '*' else "TRUE"} AND {'username IN ('+','.join('?' for _ in user_ids)+')' if not user_ids or user_ids[0] != '*' else "TRUE"} AND {"substr(timediff(?, end),1,1) = '-'" if start != '*' else "TRUE"} AND {"substr(timediff(start, ?),1,1) = '-'" if end != '*' else "TRUE"}"

                bookings = cursor.execute(query, params).fetchall()

                if bookings:
                    for booking in bookings:
                        if booking[1] != currentuser and not isadmin:
                            print(f"You can only clear your own bookings as a standard user. Booking ID '{booking[0]}' is skipped.")
                            continue
                        actual_booking_ids.append(booking[0])
                        cursor.execute("DELETE FROM bookings WHERE id=?", (booking[0]))

                if actual_booking_ids:
                    print(f"The following bookings are cleared successfully:")
                    print("\t".join(actual_booking_ids))
                else:
                    print("No bookings were cleared.")

                cursor.connection.commit()
                cursor.connection.close()
                
            elif isadmin:

                if args[0] == "reg":
                    
                    cursor = sqlite3.connect(databasepath).cursor()

                    if cursor.execute("SELECT username FROM users WHERE username=?", (args[1])).fetchone() is None:
                        pwhash = sha3_512(getpass("Password: ").encode()).digest()
                        cursor.execute("INSERT INTO users (username, pwhash) VALUES (?, ?)", (args[1], pwhash))
                        print(f"User '{args[1]}' registered successfully.")
                    else:
                        print(f"User '{args[1]}' already exists. Please choose a different username.")

                    cursor.connection.commit()
                    cursor.connection.close()                

                elif args[0] == "dereg":

                    if input(f"Are you sure you want to deregister the following users: {args[1]}? Their bookings will be as well cancelled. (yes/no): ").lower() == "yes":
                        usernames = args[1].split(',')
                        actual_usernames = []

                        cursor = sqlite3.connect(databasepath).cursor()
                        cursor.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints

                        for username in usernames:
                            if cursor.execute("SELECT username FROM users WHERE username=?", (username)).fetchone() is None:
                                print(f"User '{username}' does not exist and is skipped.")
                                continue
                            elif username == currentuser:
                                print(f"You cannot deregister yourself. Please log in as another user first. Your username is skipped.")
                                continue
                            actual_usernames.append(username)
                            cursor.execute("DELETE FROM bookings WHERE username=?", (username))
                            cursor.execute("DELETE FROM users WHERE username=?", (username))
                            
                        cursor.connection.commit()
                        cursor.connection.close()

                        if actual_usernames:
                            print(f"The following users are deregistered successfully:")
                            print("\t".join(actual_usernames))
                        else:
                            print("No users were deregistered.")
                    else:
                        print("Deregistration cancelled.")
                
                elif args[0] == "cpx":

                    cursor = sqlite3.connect(databasepath).cursor()

                    if cursor.execute("SELECT username FROM users WHERE username=?", (args[1])).fetchone() is not None:
                        new_password = getpass("New Password: ")
                        confirm_password = getpass("Confirm New Password: ")
                        if new_password == confirm_password:
                            new_pwhash = sha3_512(new_password.encode()).digest()
                            cursor.execute("UPDATE users SET pwhash=? WHERE username=?", (new_pwhash, args[1]))
                            print(f"Password for user '{args[1]}' changed successfully.")
                        else:    
                            print("Passwords do not match. Please try again.")
                    else:
                        print(f"User '{args[1]}' does not exist.")
                    
                    cursor.connection.commit()
                    cursor.connection.close()

                elif args[0] == "users":

                    cursor = sqlite3.connect(databasepath).cursor()
                    users = cursor.execute("SELECT * FROM users").fetchall()
                    cursor.connection.commit()
                    cursor.connection.close()

                    if users:
                        print("Users found:")
                        print("Username".ljust(25)+"Admin")
                        print("---".ljust(25)+"---".ljust(25))
                        for user in users:
                            print(user[0].ljust(25)+("Yes" if user[1] else "No").ljust(25))
                    else:
                        print("No users found.")

                elif args[0] == "build":

                    room_ids = args[1].split(',')
                    actual_room_ids = []

                    cursor = sqlite3.connect(databasepath).cursor()
                    
                    for room_id in room_ids:
                        if cursor.execute("SELECT id FROM rooms WHERE id=?", (room_id)).fetchone() is not None:
                            print(f"Room '{room_id}' already exists and is skipped.")
                            continue
                        actual_room_ids.append(room_id)
                        cursor.execute("INSERT INTO rooms (id) VALUES (?)", (room_id))

                    cursor.connection.commit()
                    cursor.connection.close()

                    if actual_room_ids:
                        print(f"The following rooms are created successfully:")
                        print("\t".join(actual_room_ids))
                    else:
                        print("No rooms were created.")

                elif args[0] == "destroy":

                    if input(f"Are you sure you want to delete the following rooms: {args[1]}? Their bookings will be as well cancelled. (yes/no): ").lower() == "yes":
                        room_ids = args[1].split(',')
                        actual_room_ids = []

                        cursor = sqlite3.connect(databasepath).cursor()
                        cursor.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints

                        for room_id in room_ids:
                            if cursor.execute("SELECT id FROM rooms WHERE id=?", (room_id)).fetchone() is None:
                                print(f"Room '{room_id}' does not exist and is skipped.")
                                continue
                            actual_room_ids.append(room_id)
                            cursor.execute("DELETE FROM bookings WHERE roomID=?", (room_id))
                            cursor.execute("DELETE FROM rooms WHERE id=?", (room_id))

                        cursor.connection.commit()
                        cursor.connection.close()

                        if actual_room_ids:
                            print(f"The following rooms are deleted successfully:")
                            print("\t".join(actual_room_ids))
                        else:
                            print("No rooms were deleted.")
                    else:
                        print("Deletion cancelled.")
                
                elif args[0] == "sql":

                    cursor = sqlite3.connect(databasepath).cursor()
                    cursor.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints

                    try:
                        result = cursor.execute(args[1]).fetchall()
                        for row in result:
                            for colindex in range(len(row)-1):
                                print(str(row[colindex]).ljust(25))
                            print(row[-1])
                        cursor.connection.commit()
                        print("SQL query executed successfully.")
                    except sqlite3.Error as e:
                        print(f"Error executing SQL query: {e}")
                
                    cursor.connection.commit()
                    cursor.connection.close()
                    
            else:
                print(f"Command '{args[0]}' is not available for standard users.")
        else:
            print(f"You must be logged in to use the command '{args[0]}'. Use 'login' to log in as a user first.")

        print()




# Make sure the script can only be run as a standalone program
if __name__ == "__main__":
    main()
else:
    print("Booker cannot be imported as a module.")
