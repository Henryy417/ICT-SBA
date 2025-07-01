# Global program functions
def displayerror(msg): # Error Message: User must solve this to receive expected results
    print(f"\33[31m{msg}\33[0m")

def displaysuccess(msg): # Success Message: User receives expected results
    print(f"\33[32m{msg}\33[0m")

def displaywarning(msg): # Warning Message: User may want to solve this to receive better results
    print(f"\33[33m{msg}\33[0m")

def displayinfo(msg): # Information Message: User may want to know this but nothing is wrong nor actions needed
    print(f"\33[34m{msg}\33[0m")

def main():
    # Import necessary modules
    from shlex import split
    from getpass import getpass
    from hashlib import sha3_512
    from datetime import datetime
    import sqlite3
    import os

    # Program information
    info = "Booker v1.0"
    copyright = "Copyright (c) 2025 Chen Hang Tsz Henry"

    # Customizable program information
    databasepath = os.path.realpath(os.path.dirname(__file__))+"/data.db"

    # Placeholder for user authentication
    currentuser = None  # Placeholder for current user
    isadmin = False  # Placeholder for admin status

    # Command definitions
    commands = {
        # Commands usable before login
        "help": {"help": "Show help message."},
        "man": {"args": {"command": {"format": "text"}}, "help": "Show manual for a specific command."},
        "exit": {"help": "Exit Booker."},
        "ver": {"help": "Show current version info."},
        "cls": {"help": "Clear the screen."},
        "login": {"args": {"username": {"format": "text"}}, "help": "Log in as a user."},
        # Commands usable as admins
        "reg": {
            "args": {"username": {"format": "text"}},
            "help": "Register a new user.",
            "use_requirement": "admin"
        },
        "dereg": {
            "args": {"username": {"format": "csv"}},
            "help": "Deregister users.",
            "use_requirement": "admin"
        },
        "cpx": {
            "args": {"username": {"format": "text"}},
            "help": "Change the password of a user. Defaults to the current user if no username is provided.",
            "use_requirement": "admin"
        },
        "users": {
            "help": "List all users.",
            "use_requirement": "admin"
        },
        "build": {
            "args": {"roomIDs": {"format": "csv"}},
            "help": "Create new rooms with specified IDs.",
            "use_requirement": "admin"
        },
        "destroy": {
            "args": {"roomIDs": {"format": "csv"}},
            "help": "Delete rooms with specified IDs.",
            "use_requirement": "admin"
        },
        "sql": {
            "args": {"query": {"format": "text"}},
            "help": "Execute a raw SQL query. The SQL query must be quoted. Be careful with this command as it can modify the database.",
            "use_requirement": "admin"
        },
        # Commands usable as standard users
        "cp": {
            "help": "Change the password of the current user.",
            "use_requirement": "user"
        },
        "rooms": {
            "help": "List all rooms.",
            "use_requirement": "user"
        },
        "search": {
            "args": {
                "roomIDs": {"format": "csv", "wildcard": True, "default": "*"},
                "usernames": {"format": "csv", "wildcard": True, "default": "*"},
                "start": {"format": "time", "wildcard": True, "default": "now"},
                "end": {"format": "time", "wildcard": True, "default": "*"}
            },
            "help": "List bookings of the specified rooms booked by specified users within a given time.",
            "use_requirement": "user"
        },
        "show": {
            "args": {"bookingIDs": {"format": "csv", "wildcard": True, "default": "*"}},
            "help": "Show bookings of specified booking IDs.",
            "use_requirement": "user"
        },
        "book": {
            "args": {
                "roomIDs": {"format": "csv"},
                "start": {"format": "time"},
                "end": {"format": "time"}
            },
            "help": "Make a reservation for specified rooms at a given time.",
            "use_requirement": "user"
        },
        "cancel": {
            "args": {"bookingIDs": {"format": "csv"}},
            "help": "Cancel bookings by booking IDs. Standard users can only cancel their own bookings.",
            "use_requirement": "user"
        },
        "clear": {
            "args": {
                "roomIDs": {"format": "csv", "wildcard": True},
                "usernames": {"format": "csv", "wildcard": True},
                "start": {"format": "time", "wildcard": True},
                "end": {"format": "time", "wildcard": True}
            },
            "help": "Cancel bookings to make available the specified rooms booked by specified users within a given time. Standard users can only clear their own bookings.",
            "use_requirement": "user"
        }
    }

    # List of available commands based on user status
    available_commands = {}

    def update_available_commands():
        for cmd, details in commands.items():
            if not ('use_requirement' in details and (details['use_requirement'] == "admin" and not isadmin or details['use_requirement'] == "user" and currentuser is None)):
                available_commands[cmd] = details
    
    update_available_commands() # Update available commands based on current user status

    # Print program information
    print(info)
    print(copyright)
    displayinfo("Type 'help' for a list of commands.")

    # Initialize database and create necessary tables if they do not exist
    cursor = sqlite3.connect(databasepath).cursor()

    if cursor.execute("SELECT type FROM sqlite_master WHERE type='table' AND name='users'").fetchone() is None:

        # Create users table if it does not exist
        cursor.execute(
            "CREATE TABLE users (username TEXT PRIMARY KEY, pwhash BLOB NOT NULL, isadmin BOOLEAN NOT NULL DEFAULT 0)"
        )
        cursor.execute("INSERT INTO users (username, pwhash, isadmin) VALUES (?, ?, ?)", ("admin", sha3_512(b"admin").digest(), 1))

        displayinfo("Initialization: Created 'users' table and added default admin user.")
    
    if cursor.execute("SELECT type FROM sqlite_master WHERE type='table' AND name='rooms'").fetchone() is None:

       # Create rooms table if it does not exist
       cursor.execute(
           "CREATE TABLE rooms (id TEXT PRIMARY KEY)"
       )

       displayinfo("Initialization: Created 'rooms' table.")

    if cursor.execute("SELECT type FROM sqlite_master WHERE type='table' AND name='bookings'").fetchone() is None:

        # Create bookings table if it does not exist
        cursor.execute(
            "CREATE TABLE bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, roomID TEXT, username TEXT, start TEXT NOT NULL, end TEXT NOT NULL, FOREIGN KEY (username) REFERENCES users(username), FOREIGN KEY (roomID) REFERENCES rooms(id))"
        )

        # Create indexes
        cursor.execute("CREATE INDEX idx_bookings_room_user ON bookings (roomID, username)")
        cursor.execute("CREATE INDEX idx_bookings_user ON bookings (username)")
        cursor.execute("CREATE INDEX idx_bookings_time ON bookings (start)")

        displayinfo("Initialization: Created 'bookings' table.")

    cursor.connection.commit()
    cursor.connection.close()

    print()

    # Main loop for command input
    while True:
        # Split input into arguments
        try:
            args = split(input((('\33[31m'+currentuser+'\33[0m' if isadmin else currentuser) if currentuser is not None else "") + "> "))
        except ValueError:
            displayerror("Invalid input. Looks like you forget a closing quote somewhere, or escape characters are not used properly.\nQuotes and backslashes, when used literally, should be escaped with a backslash (\\).")
            print()
            continue
        
        # Ignore empty input
        if len(args) == 0:
            continue

        # Check if command exists
        if args[0] not in available_commands:
            possiblecmds = []
            for cmd in available_commands:
                if cmd.startswith(args[0]):
                        possiblecmds.append(cmd)
            if len(possiblecmds) == 0:
                displayerror(f"Command or abbreviation '{args[0]}' not found. Type 'help' for a list of commands.")
                print()
                continue
            elif len(possiblecmds) == 1:
                args[0] = possiblecmds[0]
                displayinfo(f"Command abbreviation interpreted as '{possiblecmds[0]}'.")
            else:
                displayerror(f"Command abbreviation '{args[0]}' is ambiguous. Which of the following commands did you mean: {', '.join(possiblecmds)}?")
                print()
                continue

        # Check required number of arguments and fill defaults if necessary
        if len(args)-1 < (len(available_commands[args[0]]['args']) if 'args' in available_commands[args[0]] else 0):
            defaults_available = True
            for _ in range(len(args)-1, len(available_commands[args[0]]['args'])):
                if 'default' not in list(available_commands[args[0]]['args'].values())[_]:
                    defaults_available = False
                    break
            if defaults_available:
                for i in range(len(args)-1, len(available_commands[args[0]]['args'])):
                    args.append(list(available_commands[args[0]]['args'].values())[i]["default"])
                displayinfo(f"Default values filled. Actually running: {args[0]} {' '.join(args[1:])}")
            else:
                displayerror(f"Command '{args[0]}' uses {len(available_commands[args[0]]['args']) if 'args' in available_commands[args[0]] else 0} argument(s). Got {len(args)-1}. Default values are not provided for missing arguments.")
                print()
                continue
        elif len(args)-1 > (len(available_commands[args[0]]['args']) if 'args' in available_commands[args[0]] else 0):
            displaywarning(f"Command '{args[0]}' requires only {len(available_commands[args[0]]['args']) if 'args' in available_commands[args[0]] else 0} argument(s). Got {len(args)-1}.")
        
        print()

        # Handle commands
        if args[0] == "help":

            print("Use 'man' to receive more information about a specific command.")
            print("Command abbreviations are allowed. Enter the first few letters of a command. Note that the parser tries to see the input as a complete command before seeking a possible abbreviation.")
            print("After entering a command, add a space then the arguments if arguments are required.\n")
            print("Arguments are separated by spaces. If an argument contains spaces, it must be quoted with single or double quotes.")
            print("Default values of arguments, if exist, will be filled when not enough arguments are provided.")

            print()

            if currentuser is not None:
                print("Arguments of \33[3mcsv\33[0m values, commonly seen if more than one value is allowed in an argument (e.g. IDs), are separated by commas without spaces. e.g. 'room1,room2,room3'.")
                print("Arguments of \33[3mtime\33[0m values must be in the format 'YYYY-MM-DD HH:MM'. e.g. '2008-04-17 12:00'. Additionally, 'now' can be used to refer to current time.")
                print("Wildcard '*' usually means \33[3mall\33[0m. For some time input, it can be used to remove respective time constraints according to context. e.g. Using '*' as start time and '2008-04-17' as end time means every record until '2008-04-17'.")
            else:
                print("More commands are available after login.")

            print()

            print("Command".ljust(25)+"Description".ljust(25))
            print("---".ljust(25)+"---".ljust(25))

            for cmd, details in available_commands.items():
                    print(cmd.ljust(25)+details['help'].ljust(25))

        elif args[0] == "man":

            if args[1] in available_commands:
                print("Usage:")
                syntax_text = args[1]+" "
                if 'args' in available_commands[args[1]]:
                    for arg, prop in available_commands[args[1]]["args"].items():
                        syntax_text += f"[{prop['format']}{"|*" if 'wildcard' in prop else ''}: {arg}{"="+str(prop.get('default')) if 'default' in prop else ''}] "
                print(syntax_text.strip())
                print("\nDescription:")
                print(available_commands[args[1]]['help'])

            else:
                displayerror(f"No manual entry for command '{args[1]}'.")

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
                update_available_commands()
                displaysuccess(f"Logged in as '{currentuser}'.")
            else:
                displayerror("Invalid username or password.")

        elif currentuser is not None:
            if args[0] == "cp":

                if (new_password := getpass("New Password: ")) == getpass("Confirm New Password: "):
                    new_pwhash = sha3_512(new_password.encode()).digest()

                    cursor = sqlite3.connect(databasepath).cursor()
                    cursor.execute("UPDATE users SET pwhash=? WHERE username=?", (new_pwhash, currentuser))
                    cursor.connection.commit()
                    cursor.connection.close()

                    displaysuccess("Password changed successfully.")
                else:
                    displayerror("Passwords do not match. Please try again.")

            elif args[0] == "rooms":

                cursor = sqlite3.connect(databasepath).cursor()
                rooms = cursor.execute("SELECT id FROM rooms").fetchall()
                cursor.connection.commit()
                cursor.connection.close()

                if rooms:
                    displaysuccess("Rooms found:")
                    for room in rooms:
                        print(room[0])
                else:
                    displaywarning("No rooms found. Please create rooms using the 'build' command.")

            elif args[0] == "search":

                room_ids = args[1].split(',')
                user_ids = args[2].split(',')
                start = args[3]
                end = args[4]

                cursor = sqlite3.connect(databasepath).cursor()

                params = []
                if room_ids[0] != '*':
                    room_ids = [room for room in room_ids if cursor.execute("SELECT id FROM rooms WHERE id=?", [room]).fetchone() is not None or displaywarning(f"Room '{room}' does not exist and is skipped.")]
                    params.extend(room_ids)
                if user_ids[0] != '*':
                    user_ids = [user for user in user_ids if cursor.execute("SELECT username FROM users WHERE username=?", [user]).fetchone() is not None or displaywarning(f"User '{user}' does not exist and is skipped.")]
                    params.extend(user_ids)
                if start != '*':
                    if start == 'now':
                        start = datetime.now().strftime('%Y-%m-%d %H:%M')
                        displayinfo(f"Using current time {start} as start time.")
                    params.append(start)
                if end != '*':
                    if end == 'now':
                        end = datetime.now().strftime('%Y-%m-%d %H:%M')
                        displayinfo(f"Using current time {end} as end time.")
                    params.append(end)
                
                if cursor.execute("SELECT strftime('%F %R', ?) IS NOT NULL AND strftime('%F %R', ?) IS NOT NULL", (start, end)).fetchone()[0] == 1:
                    if cursor.execute("SELECT substr(timediff(strftime('%F %R', ?), strftime('%F %R', ?)),1,1)", (end, start)).fetchone()[0] == "+":

                        query = f"SELECT * FROM bookings WHERE {'roomID IN ('+','.join('?' for _ in room_ids)+')' if not room_ids or room_ids[0] != '*' else "TRUE"} AND {'username IN ('+','.join('?' for _ in user_ids)+')' if not user_ids or user_ids[0] != '*' else "TRUE"} AND {"substr(timediff(?, end),1,1) = '-'" if start != '*' else "TRUE"} AND {"substr(timediff(start, ?),1,1) = '-'" if end != '*' else "TRUE"}"
                
                        bookings = cursor.execute(query, params).fetchall()
                        cursor.connection.commit()
                        cursor.connection.close()

                        if bookings:
                            displaysuccess("Bookings found:")
                            print("Booking ID".ljust(25)+"Room ID".ljust(25)+"User".ljust(25)+"Start Time".ljust(25)+"End Time".ljust(25))
                            print("---".ljust(25)+"---".ljust(25)+"---".ljust(25)+"---".ljust(25)+"---".ljust(25))
                            for booking in bookings:
                                print(str(booking[0]).ljust(25)+booking[1].ljust(25)+booking[2].ljust(25)+booking[3].ljust(25)+booking[4].ljust(25))
                        else:
                            displaysuccess("No bookings found. The time slot is free.")
                    else:
                        displayerror("Time input is invalid. The end time must be after the start time.")
                else:
                    displayerror("Invalid time format. Please use 'YYYY-MM-DD HH:MM' or 'now'.")

            elif args[0] == "show":

                booking_ids = args[1].split(',')
                bookings = []

                cursor = sqlite3.connect(databasepath).cursor()
                if booking_ids[0] == '*':
                    bookings = cursor.execute("SELECT * FROM bookings").fetchall()
                else:
                    for booking_id in booking_ids:
                        booking = cursor.execute("SELECT * FROM bookings WHERE id=?", [booking_id]).fetchone()
                        if booking is None:
                            displaywarning(f"Booking ID '{booking_id}' does not exist and is skipped.")
                            continue
                        bookings.append(booking)
                cursor.connection.commit()
                cursor.connection.close()

                if bookings:
                    displaysuccess("Bookings found:")
                    print("Booking ID".ljust(25)+"Room ID".ljust(25)+"User".ljust(25)+"Start Time".ljust(25)+"End Time".ljust(25))
                    print("---".ljust(25)+"---".ljust(25)+"---".ljust(25)+"---".ljust(25)+"---".ljust(25))
                    for booking in bookings:
                        print(str(booking[0]).ljust(25)+booking[1].ljust(25)+booking[2].ljust(25)+booking[3].ljust(25)+booking[4].ljust(25))
                else:
                    displayerror("No bookings found.")

            elif args[0] == "book":

                room_ids = args[1].split(',')
                start = args[2]
                end = args[3]
                actual_room_ids = []

                cursor = sqlite3.connect(databasepath).cursor()

                if start == 'now':
                    start = datetime.now().strftime('%Y-%m-%d %H:%M')
                    displayinfo(f"Using current time {start} as start time.")
                if end == 'now':
                    end = datetime.now().strftime('%Y-%m-%d %H:%M')
                    displayinfo(f"Using current time {end} as end time.")

                if cursor.execute("SELECT strftime('%F %R', ?) IS NOT NULL AND strftime('%F %R', ?) IS NOT NULL", (start, end)).fetchone()[0] == 1:
                    if cursor.execute("SELECT substr(timediff(strftime('%F %R', ?), strftime('%F %R', ?)),1,1)", (end, start)).fetchone()[0] == "+":

                        for room_id in room_ids:
                            if cursor.execute("SELECT id FROM rooms WHERE id=?", [room_id]).fetchone() is None:
                                displaywarning(f"Room '{room_id}' does not exist and is skipped.")
                                continue
                            
                            booked = cursor.execute(f"SELECT id FROM bookings WHERE roomID = {room_id} AND substr(timediff(?, end),1,1) = '-' AND substr(timediff(start, ?),1,1) = '-'", (start, end)).fetchone()

                            if booked is not None:
                                displaywarning(f"Time slot is already booked (Booking ID: {booked[0]}) for room {room_id} and is skipped.")
                                continue

                            actual_room_ids.append(room_id)
                            cursor.execute("INSERT INTO bookings (roomID, username, start, end) VALUES (?, ?, strftime('%F %R', ?), strftime('%F %R', ?))", (room_id, currentuser, start, end))

                        if actual_room_ids:
                            displaysuccess(f"Booking(s) for the following room(s) created successfully:")
                            print("\t".join(actual_room_ids))

                        else:
                            displayerror("No bookings were created. Please check the time slot and room IDs.")
                    else:
                        displayerror("Time input is invalid. The end time must be after the start time.")
                else:
                    displayerror("Invalid time format. Please use 'YYYY-MM-DD HH:MM' or 'now'.")

                cursor.connection.commit()
                cursor.connection.close()

            elif args[0] == "cancel":

                booking_ids = args[1].split(',')
                actual_booking_ids = []

                cursor = sqlite3.connect(databasepath).cursor()

                for booking_id in booking_ids:
                    booking = cursor.execute("SELECT username FROM bookings WHERE id=?", [booking_id]).fetchone()
                    if booking is None:
                        displaywarning(f"Booking ID '{booking_id}' does not exist and is skipped.")
                        continue
                    if booking[0] != currentuser and not isadmin:
                        displaywarning(f"You can only cancel your own bookings as a standard user. Booking ID '{booking_id}' is skipped.")
                        continue
                    actual_booking_ids.append(booking_id)
                    cursor.execute("DELETE FROM bookings WHERE id=?", [booking_id])

                cursor.connection.commit()
                cursor.connection.close()

                if actual_booking_ids:
                    displaysuccess(f"The following bookings are cancelled successfully:")
                    print("\t".join(actual_booking_ids))
                else:
                    displayerror("No bookings were cancelled.")

            elif args[0] == "clear":

                room_ids = args[1].split(',')
                user_ids = args[2].split(',')
                start = args[3]
                end = args[4]

                if "*" not in (room_ids, user_ids, start, end) or input("You are using wildcard '*' in one or more arguments. This will cancel bookings massively. Are you sure you want to proceed? Enter 'yes' to confirm: ").lower() == "yes":

                    actual_booking_ids = []

                    cursor = sqlite3.connect(databasepath).cursor()

                    params = []
                    if room_ids[0] != '*':
                        room_ids = [room for room in room_ids if cursor.execute("SELECT id FROM rooms WHERE id=?", [room]).fetchone() is not None or displaywarning(f"Room '{room}' does not exist and is skipped.")]
                        params.extend(room_ids)
                    if user_ids[0] != '*':
                        user_ids = [user for user in user_ids if cursor.execute("SELECT username FROM users WHERE username=?", [user]).fetchone() is not None or displaywarning(f"User '{user}' does not exist and is skipped.")]
                        params.extend(user_ids)
                    if start != '*':
                        if start == 'now':
                            start = datetime.now().strftime('%Y-%m-%d %H:%M')
                            displayinfo(f"Using current time {start} as start time.")
                        params.append(start)
                    if end != '*':
                        if end == 'now':
                            end = datetime.now().strftime('%Y-%m-%d %H:%M')
                            displayinfo(f"Using current time {end} as end time.")
                        params.append(end)

                    if cursor.execute("SELECT strftime('%F %R', ?) IS NOT NULL AND strftime('%F %R', ?) IS NOT NULL", (start, end)).fetchone()[0] == 1:
                        if cursor.execute("SELECT substr(timediff(strftime('%F %R', ?), strftime('%F %R', ?)),1,1)", (end, start)).fetchone()[0] != "+":

                            query = f"SELECT id, username FROM bookings WHERE {'roomID IN ('+','.join('?' for _ in room_ids)+')' if not room_ids or room_ids[0] != '*' else "TRUE"} AND {'username IN ('+','.join('?' for _ in user_ids)+')' if not user_ids or user_ids[0] != '*' else "TRUE"} AND {"substr(timediff(?, end),1,1) = '-'" if start != '*' else "TRUE"} AND {"substr(timediff(start, ?),1,1) = '-'" if end != '*' else "TRUE"}"

                            bookings = cursor.execute(query, params).fetchall()

                            if bookings:
                                for booking in bookings:
                                    if booking[1] != currentuser and not isadmin:
                                        displaywarning(f"You can only clear your own bookings as a standard user. Booking ID '{booking[0]}' is skipped.")
                                        continue
                                    actual_booking_ids.append(booking[0])
                                    cursor.execute("DELETE FROM bookings WHERE id=?", [booking[0]])

                            if actual_booking_ids:
                                displaysuccess(f"The following bookings are cleared successfully:")
                                print("\t".join(actual_booking_ids))
                            else:
                                displayerror("No bookings were cleared.")

                            cursor.connection.commit()
                            cursor.connection.close()
                        else:
                            displayerror("Time input is invalid. The end time must be after the start time.")
                    else:
                        displayerror("Invalid time format. Please use 'YYYY-MM-DD HH:MM' or 'now'.")
                else:
                    displayerror("Clearing bookings cancelled.")
                
            elif isadmin:

                if args[0] == "reg":
                    
                    cursor = sqlite3.connect(databasepath).cursor()

                    if cursor.execute("SELECT username FROM users WHERE username=?", [args[1]]).fetchone() is None:
                        pwhash = sha3_512(getpass("Password: ").encode()).digest()
                        cursor.execute("INSERT INTO users (username, pwhash) VALUES (?, ?)", (args[1], pwhash))
                        displaysuccess(f"User '{args[1]}' registered successfully.")
                    else:
                        displayerror(f"User '{args[1]}' already exists. Please choose a different username.")

                    cursor.connection.commit()
                    cursor.connection.close()                

                elif args[0] == "dereg":

                    if input(f"Are you sure you want to deregister the users? Their bookings will be as well cancelled. Enter 'yes' to confirm: ").lower() == "yes":
                        usernames = args[1].split(',')
                        actual_usernames = []

                        cursor = sqlite3.connect(databasepath).cursor()
                        cursor.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints

                        for username in usernames:
                            if cursor.execute("SELECT username FROM users WHERE username=?", [username]).fetchone() is None:
                                displaywarning(f"User '{username}' does not exist and is skipped.")
                                continue
                            elif username == currentuser:
                                displaywarning(f"You cannot deregister yourself. Please log in as another user first. Your username is skipped.")
                                continue
                            actual_usernames.append(username)
                            cursor.execute("DELETE FROM bookings WHERE username=?", [username])
                            cursor.execute("DELETE FROM users WHERE username=?", [username])
                            
                        cursor.connection.commit()
                        cursor.connection.close()

                        if actual_usernames:
                            displaysuccess(f"The following users are deregistered successfully:")
                            print("\t".join(actual_usernames))
                        else:
                            displayerror("No users were deregistered.")
                    else:
                        displayerror("Deregistration cancelled.")
                
                elif args[0] == "cpx":

                    cursor = sqlite3.connect(databasepath).cursor()

                    if cursor.execute("SELECT username FROM users WHERE username=?", [args[1]]).fetchone() is not None:
                        new_password = getpass("New Password: ")
                        confirm_password = getpass("Confirm New Password: ")
                        if new_password == confirm_password:
                            new_pwhash = sha3_512(new_password.encode()).digest()
                            cursor.execute("UPDATE users SET pwhash=? WHERE username=?", (new_pwhash, args[1]))
                            displaysuccess(f"Password for user '{args[1]}' changed successfully.")
                        else:    
                            displayerror("Passwords do not match. Please try again.")
                    else:
                        displayerror(f"User '{args[1]}' does not exist.")
                    
                    cursor.connection.commit()
                    cursor.connection.close()

                elif args[0] == "users":

                    cursor = sqlite3.connect(databasepath).cursor()
                    users = cursor.execute("SELECT * FROM users").fetchall()
                    cursor.connection.commit()
                    cursor.connection.close()

                    if users:
                        displaysuccess("Users found:")
                        print("Username".ljust(25)+"Admin")
                        print("---".ljust(25)+"---".ljust(25))
                        for user in users:
                            print(user[0].ljust(25)+("Yes" if user[1] else "No").ljust(25))
                    else:
                        displaywarning("No users found. Please register users using the 'reg' command.")

                elif args[0] == "build":

                    room_ids = args[1].split(',')
                    actual_room_ids = []

                    cursor = sqlite3.connect(databasepath).cursor()
                    
                    for room_id in room_ids:
                        if cursor.execute("SELECT id FROM rooms WHERE id=?", [room_id]).fetchone() is not None:
                            displaywarning(f"Room '{room_id}' already exists and is skipped.")
                            continue
                        actual_room_ids.append(room_id)
                        cursor.execute("INSERT INTO rooms (id) VALUES (?)", [room_id])

                    cursor.connection.commit()
                    cursor.connection.close()

                    if actual_room_ids:
                        displaysuccess(f"The following rooms are created successfully:")
                        print("\t".join(actual_room_ids))
                    else:
                        displayerror("No rooms were created.")

                elif args[0] == "destroy":

                    if input(f"Are you sure you want to delete the rooms? Their bookings will be as well cancelled. Enter 'yes' to confirm: ").lower() == "yes":
                        room_ids = args[1].split(',')
                        actual_room_ids = []

                        cursor = sqlite3.connect(databasepath).cursor()
                        cursor.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints

                        for room_id in room_ids:
                            if cursor.execute("SELECT id FROM rooms WHERE id=?", [room_id]).fetchone() is None:
                                displaywarning(f"Room '{room_id}' does not exist and is skipped.")
                                continue
                            actual_room_ids.append(room_id)
                            cursor.execute("DELETE FROM bookings WHERE roomID=?", [room_id])
                            cursor.execute("DELETE FROM rooms WHERE id=?", [room_id])

                        cursor.connection.commit()
                        cursor.connection.close()

                        if actual_room_ids:
                            displaysuccess(f"The following rooms are deleted successfully:")
                            print("\t".join(actual_room_ids))
                        else:
                            displayerror("No rooms were deleted.")
                    else:
                        displayerror("Deletion cancelled.")
                
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
                        displaysuccess("SQL query executed successfully.")
                    except sqlite3.Error as e:
                        displayerror(f"Error executing SQL query:\n{e}")
                
                    cursor.connection.commit()
                    cursor.connection.close()
                    
            else:
                displayerror(f"Command '{args[0]}' is not available for standard users.")
        else:
            displayerror(f"You must be logged in to use the command '{args[0]}'. Use 'login' to log in as a user first.")

        print()



# Make sure the script can only be run as a standalone program
if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        exit(0)
    except KeyboardInterrupt:
        displayerror("Program terminated due to user keyboard interrupt (Ctrl+C).")
        exit(1)
    except:
        from os import path
        from datetime import datetime
        from traceback import format_exc, print_exc

        displayerror(f"Program terminated due to unexpectedly error.\nError info:\n{format_exc()}")
        with open(path.realpath(path.dirname(__file__))+"/error.log", "a") as f:
            f.write(str(datetime.now())+"\n")
            print_exc(file=f)
            f.write("\n\n\n")

        exit(1)
else:
    displayerror("Booker cannot be imported as a module.")
    exit(1)
