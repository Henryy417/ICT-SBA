# Global imports
from pathlib import Path
from datetime import datetime

# Global program functions
def displayerror(msg: str): # Error Message: User must solve this to receive expected results
    print(f"\33[91m{msg}\33[0m")

def displaysuccess(msg: str): # Success Message: User receives expected results
    print(f"\33[92m{msg}\33[0m")

def displaywarning(msg: str): # Warning Message: User may want to solve this to receive better results
    print(f"\33[93m{msg}\33[0m")

def displayinfo(msg: str): # Information Message: User may want to know this but nothing is wrong nor actions needed
    print(f"\33[94m{msg}\33[0m")

def display_table(headers: list[str], widths: list[int], *rows: list):
    line_buffer = ""
    for header, width in zip(headers, widths):
        line_buffer += header.ljust(width)
    print(line_buffer)

    line_buffer = ""
    for width in widths:
        line_buffer += '---'.ljust(width)
    print(line_buffer)

    for row in rows:
        line_buffer = ""
        for item, width in zip(row, widths):
            line_buffer += str(item).ljust(width)
        print(line_buffer)

def main():
    ## Initialization ##
    # Functional imports
    from shlex import split, join
    from getpass import getpass
    from hashlib import sha3_512
    from os import system as sysexec, name as sysname
    from re import compile as regex_compile, error as regex_error
    import sqlite3

    # Functional Functions
    def update_available_commands():
        for cmd, details in commands.items():
            if not ('use_requirement' in details and (details['use_requirement'] == "admin" and not isadmin or details['use_requirement'] == "user" and currentuser is None)):
                available_commands[cmd] = details

    def is_valid_time_interval(start: str, end: str, allow_equal: bool = False, allow_wildcard = False) -> bool:
        if allow_wildcard and (start == '*' or end == '*'):
            return True
        try:
            start_dt = datetime.strptime(start, '%Y-%m-%d %H:%M')
            end_dt = datetime.strptime(end, '%Y-%m-%d %H:%M')
            return start_dt < end_dt if not allow_equal else start_dt <= end_dt
        except ValueError:
            return False

    def is_in_time_interval(interval_start: str, interval_end: str, target_start: str, target_end: str) -> bool: # NO INPUT VALIDATION! USE is_valid_time_interval() BEFORE THIS FUNCTION!
        interval_start_dt = datetime.strptime(interval_start, '%Y-%m-%d %H:%M') if interval_start != '*' else datetime.min
        interval_end_dt = datetime.strptime(interval_end, '%Y-%m-%d %H:%M') if interval_end != '*' else datetime.max
        target_start_dt = datetime.strptime(target_start, '%Y-%m-%d %H:%M')
        target_end_dt = datetime.strptime(target_end, '%Y-%m-%d %H:%M')
        return not(interval_start_dt >= target_end_dt or interval_end_dt <= target_start_dt)
        
    def regex_match(pattern: str, value: str = "") -> bool | None:
        try:
            regex = regex_compile(pattern)
        except regex_error:
            return None # Return None if the regex pattern is invalid
        return regex.match(value) is not None

    # Program information
    INFO = "Booker v1.0"

    # Customizable program information
    DB_PATH = Path(__file__).resolve().parent/"data.db"

    # Placeholder for user authentication
    currentuser = None  # Placeholder for current user
    isadmin = False  # Placeholder for admin status

    # Command definitions
    commands = {
        # Commands usable before login
        "help": {"help": "Show help message."},
        "man": {"args": {"command": {"format": "text"}}, "help": "Show manual for a specific command."},
        "exit": {"help": "Exit Booker."},
        "version": {"help": "Show current version info."},
        "cls": {"help": "Clear the screen."},
        "login": {"args": {"username": {"format": "text"}}, "help": "Log in as a user."},
        "gui": {"help": "Start the GUI version of Booker."},
        # Commands usable as admins
        "reg": {
            "args": {"username": {"format": "text"}},
            "help": "Register a new user or change the password of an existing user.",
            "use_requirement": "admin"
        },
        "dereg": {
            "args": {"username": {"format": "csv"}},
            "help": "Deregister users.",
            "use_requirement": "admin"
        },
        "users": {
            "help": "List all users.",
            "use_requirement": "admin"
        },
        "build": {
            "args": {"roomIDs": {"format": "csv"}, "description": {"format": "text", "default": "Classroom"}},
            "help": "Create new rooms or change the description of existing rooms with specified IDs.",
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
                "end": {"format": "time", "wildcard": True, "default": "*"},
                "usage": {"format": "text", "default": "."}
            },
            "help": "List bookings of the specified rooms booked by specified users within a given time. Usage can be filtered using a regular expression.",
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
                "end": {"format": "time"},
                "usage": {"format": "text"}
            },
            "help": "Make a reservation for specified rooms at a given time.",
            "use_requirement": "user"
        },
        "modify": {
            "args": {"bookingIDs": {"format": "csv"}, "Description": {"format": "text"}},
            "help": "Modify the description of bookings by booking IDs. Standard users can only modify their own future bookings.",
            "use_requirement": "user"
        },
        "cancel": {
            "args": {"bookingIDs": {"format": "csv"}},
            "help": "Cancel bookings by booking IDs. Standard users can only cancel their own future bookings.",
            "use_requirement": "user"
        },
        "clear": {
            "args": {
                "roomIDs": {"format": "csv", "wildcard": True},
                "usernames": {"format": "csv", "wildcard": True},
                "start": {"format": "time", "wildcard": True},
                "end": {"format": "time", "wildcard": True},
                "usage": {"format": "text"}
            },
            "help": "Cancel bookings to make available the specified rooms booked by specified users within a given time. Usage can be filtered using a regular expression. Standard users can only clear their own future bookings.",
            "use_requirement": "user"
        }
    }

    available_commands = {} # List of available commands based on user status
    update_available_commands() # Update available commands based on current user status

    # Print program information
    print(INFO)
    print("Type 'help' for a list of commands.")

    # Initialize database and create necessary tables if they do not exist
    connection = sqlite3.connect(DB_PATH)
    
    if connection.execute("SELECT type FROM sqlite_master WHERE type='table' AND name='users'").fetchone() is None:

        # Create users table with prevention of external between-command transaction
        connection.execute(
            "CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, pwhash BLOB NOT NULL, isadmin BOOLEAN NOT NULL DEFAULT 0)"
        )
        connection.execute("INSERT INTO users (username, pwhash, isadmin) VALUES (?, ?, ?)", ("admin", sha3_512(b"admin").digest(), 1))
        connection.commit()

        displayinfo("Initialization: Created 'users' table and added default admin user.")

    if connection.execute("SELECT type FROM sqlite_master WHERE type='table' AND name='rooms'").fetchone() is None:

       # Create rooms table with prevention of external between-command transaction
       connection.execute(
           "CREATE TABLE IF NOT EXISTS rooms (id TEXT PRIMARY KEY, description TEXT NOT NULL)"
       )
       connection.commit()

       displayinfo("Initialization: Created 'rooms' table.")

    if connection.execute("SELECT type FROM sqlite_master WHERE type='table' AND name='bookings'").fetchone() is None:

        # Create bookings table with prevention of external between-command transaction
        connection.execute(
            "CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, roomID TEXT, username TEXT, start TEXT NOT NULL, end TEXT NOT NULL, usage TEXT NOT NULL, FOREIGN KEY (username) REFERENCES users(username), FOREIGN KEY (roomID) REFERENCES rooms(id))"
        )

        # Create indexes for bookings table to improve performance
        connection.execute("CREATE INDEX IF NOT EXISTS idx_bookings_room_user ON bookings (roomID, username)") # Optimizing searches through both room and room&user
        connection.execute("CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings (username)") # Optimizing searches through user
        connection.execute("CREATE INDEX IF NOT EXISTS idx_bookings_time ON bookings (start)") # Optimizing searches through time
        connection.commit()

        displayinfo("Initialization: Created 'bookings' table.")

    connection.close()

    print() # Print a newline for better readability

    ## Main loop ##
    while True:

        # Parser #

        parser_notice = False

        # Split input into arguments
        try:
            args = split(input((('\33[31m'+currentuser+'\33[0m' if isadmin else currentuser) if currentuser is not None else "") + "> "))
        except ValueError:
            displayerror("Invalid input. Looks like you forget a closing quote somewhere, or escape characters are not used properly.\nQuotes and backslashes, when used literally, should be escaped with a backslash (\\).")
            print() # Print a newline for better readability
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
                print() # Print a newline for better readability
                continue
            elif len(possiblecmds) == 1:
                args[0] = possiblecmds[0]
                displayinfo(f"Command abbreviation interpreted as '{possiblecmds[0]}'.")
                parser_notice = True
            else:
                displayerror(f"Command abbreviation '{args[0]}' is ambiguous. Which of the following commands did you mean: {', '.join(possiblecmds)}?")
                print() # Print a newline for better readability
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
                displayinfo(f"Default values filled. Actually running: {join(args)}")
                parser_notice = True
            else:
                displayerror(f"Command '{args[0]}' uses {len(available_commands[args[0]]['args']) if 'args' in available_commands[args[0]] else 0} argument(s). Got {len(args)-1}. Default values are not provided for missing arguments.")
                print() # Print a newline for better readability
                continue
        elif len(args)-1 > (len(available_commands[args[0]]['args']) if 'args' in available_commands[args[0]] else 0):
            displaywarning(f"Command '{args[0]}' requires only {len(available_commands[args[0]]['args']) if 'args' in available_commands[args[0]] else 0} argument(s). Got {len(args)-1}.")
            parser_notice = True

        print() if parser_notice else None # Print a newline if there was a parser notice

        # Command Handlers #

        command_notice = False

        # Commands that can be used before login
        if args[0] == "help":

            print("Use 'man' to receive more information about a specific command.")
            print("Command abbreviations are allowed. Enter the first few letters of a command. Note that the parser tries to see the input as a complete command before seeking a possible abbreviation.")
            print("After entering a command, add a space then the arguments if arguments are required.\n")
            print("Arguments are separated by spaces. If an argument contains spaces, it must be quoted with single or double quotes.")
            print("Default values of arguments, if exist, will be filled when not enough arguments are provided.")

            print() # Print a newline for better readability

            if currentuser is not None:
                print("Arguments of \33[3mcsv\33[0m values, commonly seen if more than one value is allowed in an argument (e.g. IDs), are separated by commas without spaces. e.g. 'room1,room2,room3'.")
                print("Arguments of \33[3mtime\33[0m values must be in the format 'YYYY-MM-DD HH:MM'. e.g. '2008-04-17 12:00'. Additionally, 'now' can be used to refer to current time.")
                print("Wildcard '*' usually means \33[3mall\33[0m. For some time input, it can be used to remove respective time constraints according to context. e.g. Using '*' as start time and '2008-04-17' as end time means every record until '2008-04-17'.")
            else:
                print("More commands are available after login.")

            print() # Print a newline for better readability

            display_table(
                ["Command", "Description"],
                [15, 0],
                *[(cmd, details['help']) for cmd, details in available_commands.items()]
            )

        elif args[0] == "man":

            if args[1] in available_commands:
                print("Usage:")
                syntax_text = args[1]+" "
                if 'args' in available_commands[args[1]]:
                    for arg, prop in available_commands[args[1]]["args"].items():
                        syntax_text += f"[{prop['format']}{"|*" if 'wildcard' in prop else ''}: {arg}{"="+str(prop.get('default')) if 'default' in prop else ''}] " # Syntax for each argument
                print(syntax_text.strip())
                print("\nDescription:")
                print(available_commands[args[1]]['help'])
            else:
                displayerror(f"No manual entry for command '{args[1]}'.")

        elif args[0] == "exit":

            raise SystemExit(0)

        elif args[0] == "version":

            print(INFO)
            
            print() # Print a newline for better readability

            # Search for license file in the same directory and the parent directory as this script
            if (Path(__file__).resolve().parent/"LICENSE").exists():
                with open(Path(__file__).resolve().parent/"LICENSE", "r") as license_file:
                    print(license_file.read())
            elif (Path(__file__).resolve().parent.parent/"LICENSE").exists():
                with open(Path(__file__).resolve().parent.parent/"LICENSE", "r") as license_file:
                    print(license_file.read())
            else:
                displayerror("No license file is found. This may indicate an illegal distribution.")
                displayerror("This program is originally released under the MIT License by Chen Hang Tsz Henry. Please refer to the source code repository for more information.")

        elif args[0] == "cls":

            sysexec("cls" if sysname == "nt" else "clear") # Compatible with older Windows without PowerShell

        elif args[0] == "login":

            pwhash = sha3_512(getpass("Password: ").encode()).digest()

            connection = sqlite3.connect(DB_PATH)
            result = connection.execute("SELECT isadmin FROM users WHERE username=? AND pwhash=?", (args[1], pwhash)).fetchone()
            connection.commit()
            connection.close()

            if result is not None:
                currentuser = args[1]
                isadmin = result[0] == 1
                update_available_commands()
                displaysuccess(f"Logged in as '{currentuser}'.")
            else:
                displayerror("Invalid username or password.")

        # Commands that can be used only after login
        elif currentuser is not None:
            if args[0] == "cp":

                if (new_password := getpass("New Password: ")) == getpass("Confirm New Password: "):
                    new_pwhash = sha3_512(new_password.encode()).digest()

                    connection = sqlite3.connect(DB_PATH)
                    connection.execute("UPDATE users SET pwhash=? WHERE username=?", (new_pwhash, currentuser))
                    connection.commit()
                    connection.close()

                    displaysuccess("Password changed successfully.")
                else:
                    displayerror("Passwords do not match. Please try again.")

            elif args[0] == "rooms":

                connection = sqlite3.connect(DB_PATH)
                rooms = connection.execute("SELECT id, description FROM rooms ORDER BY id").fetchall()
                connection.commit()
                connection.close()

                if rooms:
                    displaysuccess("Rooms found:")
                    display_table(
                        ["ID", "Description"],
                        [10, 0],
                        *rooms
                    )
                else:
                    displaywarning("No rooms found. Please create rooms using the 'build' command.")

            elif args[0] == "search":

                room_ids = args[1].split(',')
                user_ids = args[2].split(',')
                start = args[3]
                end = args[4]
                usage = args[5]

                connection = sqlite3.connect(DB_PATH)

                params = []
                if room_ids[0] != '*':
                    room_ids = [room for room in room_ids if connection.execute("SELECT id FROM rooms WHERE id=?", [room]).fetchone() is not None or displaywarning(f"Room '{room}' does not exist and is skipped.") and (command_notice := True)]
                    params.extend(room_ids)
                if user_ids[0] != '*':
                    user_ids = [user for user in user_ids if connection.execute("SELECT username FROM users WHERE username=?", [user]).fetchone() is not None or displaywarning(f"User '{user}' does not exist and is skipped.") and (command_notice := True)]
                    params.extend(user_ids)
                now = datetime.now().strftime('%Y-%m-%d %H:%M')
                if start != '*':
                    if start == 'now':
                        start = now
                        displayinfo(f"Using current time {start} as start time.")
                        command_notice = True
                params.append(start)
                if end != '*':
                    if end == 'now':
                        end = now
                        displayinfo(f"Using current time {end} as end time.")
                        command_notice = True
                params.append(end)
                params.append(usage)

                if is_valid_time_interval(start, end, allow_wildcard=True):
                    if regex_match(usage) is not None:

                        connection.create_function("in_interval", 4, is_in_time_interval)
                        connection.create_function("regex", 2, regex_match)
                        
                        query = f"SELECT * FROM bookings WHERE {'roomID IN ('+','.join('?' for _ in room_ids)+')' if not room_ids or room_ids[0] != '*' else "TRUE"} AND {'username IN ('+','.join('?' for _ in user_ids)+')' if not user_ids or user_ids[0] != '*' else "TRUE"} AND in_interval(?, ?, start, end) AND regex(?, usage) ORDER BY strftime('%F %R', start), roomID"

                        bookings = connection.execute(query, params).fetchall()

                        print() if command_notice else None # Print a newline if there was a in-command notice

                        if bookings:
                            displaysuccess("Bookings found:")
                            display_table(
                                ["Booking ID", "Room ID", "User", "Start Time", "End Time", "Usage"],
                                [10, 10, 20, 20, 20, 0],
                                *bookings
                            )
                        else:
                            displaysuccess("No bookings found. The time slot is free.")

                    else:
                        displayerror("Usage input is invalid. Please use a valid regular expression for usage filtering.")
                else:
                    displayerror("Invalid time input. Either the end time is not later than the start time, or the time format is incorrect. Refer to the manual for more information.")

                connection.commit()
                connection.close()

            elif args[0] == "show":

                booking_ids = args[1].split(',')
                bookings = []

                connection = sqlite3.connect(DB_PATH)

                if booking_ids[0] == '*':
                    bookings = connection.execute("SELECT * FROM bookings").fetchall()
                else:
                    for booking_id in booking_ids:
                        booking = connection.execute("SELECT * FROM bookings WHERE id=?", [booking_id]).fetchone()
                        if booking is None:
                            displaywarning(f"Booking ID '{booking_id}' does not exist and is skipped.")
                            command_notice = True
                            continue
                        bookings.append(booking)

                connection.commit()
                connection.close()

                print() if command_notice else None # Print a newline if there was a in-command notice

                if bookings:
                    displaysuccess("Bookings found:")
                    display_table(
                        ["Booking ID", "Room ID", "User", "Start Time", "End Time", "Usage"],
                        [10, 10, 20, 20, 20, 0],
                        *bookings
                    )
                else:
                    displayerror("No bookings found.")

            elif args[0] == "book":

                room_ids = args[1].split(',')
                start = args[2]
                end = args[3]
                usage = args[4]
                actual_room_ids = []

                connection = sqlite3.connect(DB_PATH)
                connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
                connection.execute("BEGIN EXCLUSIVE")

                now = datetime.now().strftime('%Y-%m-%d %H:%M')
                if start == 'now':
                    start = now
                    displayinfo(f"Using current time {start} as start time.")
                    command_notice = True
                if end == 'now':
                    end = now
                    displayinfo(f"Using current time {end} as end time.")
                    command_notice = True

                if isadmin or is_valid_time_interval(now, start, allow_equal=True):
                    if is_valid_time_interval(start, end):
                        if len(usage) > 0:

                            connection.create_function("in_interval", 4, is_in_time_interval)

                            for room_id in room_ids:
                                if connection.execute("SELECT id FROM rooms WHERE id=?", [room_id]).fetchone() is None:
                                    displaywarning(f"Room '{room_id}' does not exist and is skipped.")
                                    command_notice = True
                                    continue

                                booked = connection.execute(f"SELECT id FROM bookings WHERE roomID = ? AND in_interval(?, ?, start, end)", (room_id, start, end)).fetchone()

                                if booked is not None:
                                    displaywarning(f"Time slot is occupied (Booking ID: {booked[0]}) for room {room_id} and is skipped.")
                                    command_notice = True
                                    continue

                                actual_room_ids.append(room_id)
                                connection.execute("INSERT INTO bookings (roomID, username, start, end, usage) VALUES (?, ?, strftime('%F %R', ?), strftime('%F %R', ?), ?)", (room_id, currentuser, start, end, usage))

                            print() if command_notice else None # Print a newline if there was a in-command notice

                            if actual_room_ids:
                                displaysuccess(f"Booking(s) for the following room(s) created successfully:")
                                display_table(
                                    ["Room ID"],
                                    [10],
                                    *[[room_id] for room_id in actual_room_ids]
                                )
                            else:
                                displayerror("No bookings were created. Please check the time slot and room IDs.")
                            
                        else:
                            displayerror("Usage cannot be empty. Please provide a description of the booking.")
                    else:
                        displayerror("Invalid time input. Either the end time is not later than the start time, or the time format is incorrect. Refer to the manual for more information.")
                else:
                    displayerror("Standard user cannot set start time in the past. Please use a future time or 'now'.")

                connection.commit()
                connection.close()

            elif args[0] == "modify":

                booking_ids = args[1].split(',')
                usage = args[2]
                actual_booking_ids = []

                if len(usage) != 0:

                    connection = sqlite3.connect(DB_PATH)
                    # No exclusive lock as even if the user is deleted or the password is changed on the fly, data integrity and consistency are still maintained, without any errors occurring.

                    for booking_id in booking_ids:
                        booking = connection.execute("SELECT username, start FROM bookings WHERE id=?", [booking_id]).fetchone()
                        if booking is None:
                            displaywarning(f"Booking ID '{booking_id}' does not exist and is skipped.")
                            command_notice = True
                            continue
                        if booking[0] != currentuser and not isadmin:
                            displaywarning(f"You can only modify your own bookings as a standard user. Booking ID '{booking_id}' is skipped.")
                            command_notice = True
                            continue
                        if not (isadmin or is_valid_time_interval(datetime.now().strftime('%Y-%m-%d %H:%M'), booking[1], allow_equal=True)):
                            displaywarning(f"Booking ID '{booking_id}' is in the past and cannot be modified by a standard user.")
                            command_notice = True
                            continue
                        actual_booking_ids.append(booking_id)
                        connection.execute("UPDATE bookings SET usage=? WHERE id=?", (usage, booking_id))

                    print() if command_notice else None # Print a newline if there was a in-command notice

                    if actual_booking_ids:
                        displaysuccess(f"The following bookings are modified successfully:")
                        display_table(
                            ["Booking ID"],
                            [10],
                            *[[booking_id] for booking_id in actual_booking_ids]
                        )
                    else:
                        displayerror("No bookings were modified. Please check the booking IDs.")

                    connection.commit()
                    connection.close()

                else:
                    displayerror("Usage cannot be empty. Please provide a description of the booking.")

            elif args[0] == "cancel":

                booking_ids = args[1].split(',')
                actual_booking_ids = []

                connection = sqlite3.connect(DB_PATH)
                # No exclusive lock as even if the user is deleted or the password is changed on the fly, data integrity and consistency are still maintained, without any errors occurring.

                for booking_id in booking_ids:
                    booking = connection.execute("SELECT username, start FROM bookings WHERE id=?", [booking_id]).fetchone()
                    if booking is None:
                        displaywarning(f"Booking ID '{booking_id}' does not exist and is skipped.")
                        command_notice = True
                        continue
                    if booking[0] != currentuser and not isadmin:
                        displaywarning(f"You can only cancel your own bookings as a standard user. Booking ID '{booking_id}' is skipped.")
                        command_notice = True
                        continue
                    if not (isadmin or is_valid_time_interval(datetime.now().strftime('%Y-%m-%d %H:%M'), booking[1], allow_equal=True)):
                        displaywarning(f"Booking ID '{booking_id}' is in the past and cannot be cancelled by a standard user.")
                        command_notice = True
                        continue
                    actual_booking_ids.append(booking_id)
                    connection.execute("DELETE FROM bookings WHERE id=?", [booking_id])

                connection.commit()
                connection.close()

                print() if command_notice else None # Print a newline if there was a in-command notice

                if actual_booking_ids:
                    displaysuccess(f"The following bookings are cancelled successfully:")
                    display_table(
                        ["Booking ID"],
                        [10],
                        *[[booking_id] for booking_id in actual_booking_ids]
                    )
                else:
                    displayerror("No bookings were cancelled.")

            elif args[0] == "clear":

                room_ids = args[1].split(',')
                user_ids = args[2].split(',')
                start = args[3]
                end = args[4]
                usage = args[5]

                if "*" not in (room_ids, user_ids, start, end) or input("You are using wildcard '*' in one or more arguments. This will cancel bookings massively. Are you sure you want to proceed? Enter 'yes' to confirm: ").lower() == "yes":

                    actual_booking_ids = []

                    connection = sqlite3.connect(DB_PATH)
                    # No exclusive lock as even if the user is deleted or the password is changed on the fly, data integrity and consistency are still maintained, without any errors occurring.

                    params = []
                    if room_ids[0] != '*':
                        room_ids = [room for room in room_ids if connection.execute("SELECT id FROM rooms WHERE id=?", [room]).fetchone() is not None or displaywarning(f"Room '{room}' does not exist and is skipped.") and (command_notice := True)]
                        params.extend(room_ids)
                    if user_ids[0] != '*':
                        user_ids = [user for user in user_ids if connection.execute("SELECT username FROM users WHERE username=?", [user]).fetchone() is not None or displaywarning(f"User '{user}' does not exist and is skipped.") and (command_notice := True)]
                        params.extend(user_ids)
                    now = datetime.now().strftime('%Y-%m-%d %H:%M')
                    if start != '*':
                        if start == 'now':
                            start = now
                            displayinfo(f"Using current time {start} as start time.")
                            command_notice = True
                        params.append(start)
                    if end != '*':
                        if end == 'now':
                            end = now
                            displayinfo(f"Using current time {end} as end time.")
                            command_notice = True
                        params.append(end)
                    params.append(usage)

                    if isadmin or is_valid_time_interval(now, start, allow_equal=True):
                        if is_valid_time_interval(start, end, allow_wildcard=True):
                            if regex_match(usage) is not None:

                                connection.create_function("in_interval", 4, is_in_time_interval)
                                connection.create_function("regex", 2, regex_match)

                                query = f"SELECT id, username FROM bookings WHERE {'roomID IN ('+','.join('?' for _ in room_ids)+')' if not room_ids or room_ids[0] != '*' else "TRUE"} AND {'username IN ('+','.join('?' for _ in user_ids)+')' if not user_ids or user_ids[0] != '*' else "TRUE"} AND {'in_interval(?, ?, start, end)' if start != '*' and end != '*' else "TRUE"} AND regex(?, usage)"

                                bookings = connection.execute(query, params).fetchall()

                                if bookings:
                                    for booking in bookings:
                                        if booking[1] != currentuser and not isadmin:
                                            displaywarning(f"You can only clear your own bookings as a standard user. Booking ID '{booking[0]}' is skipped.")
                                            command_notice = True
                                            continue
                                        actual_booking_ids.append(str(booking[0]))
                                        connection.execute("DELETE FROM bookings WHERE id=?", [booking[0]])

                                print() if command_notice else None # Print a newline if there was a in-command notice

                                if actual_booking_ids:
                                    displaysuccess(f"The following bookings are cleared successfully:")
                                    display_table(
                                        ["Booking ID"],
                                        [10],
                                        *[[booking_id] for booking_id in actual_booking_ids]
                                    )
                                else:
                                    displayerror("No bookings were cleared.")

                            else:
                                displayerror("Usage input is invalid. Please use a valid regular expression for usage filtering.")
                        else:
                            displayerror("Invalid time input. Either the end time is not later than the start time, or the time format is incorrect. Refer to the manual for more information.")
                    else:
                        displayerror("Clearing past bookings is not allowed for a standard user. Please use a future time or 'now' as start time.")

                    connection.commit()
                    connection.close()

                else:
                    displayerror("Clearing bookings cancelled.")
                
            elif isadmin:

                if args[0] == "reg":

                    connection = sqlite3.connect(DB_PATH)
                    # No exclusive lock as even if the user is deleted or the password is changed on the fly, data integrity and consistency are still maintained, without any errors occurring.

                    if connection.execute("SELECT username FROM users WHERE username=?", [args[1]]).fetchone() is not None:
                        displayinfo(f"User '{args[1]}' already exists. Changing password.")
                        command_notice = True

                    print() if command_notice else None # Print a newline if there was a in-command notice

                    pwhash = sha3_512(getpass("Password: ").encode()).digest()
                    connection.execute("INSERT OR REPLACE users (username, pwhash) VALUES (?, ?)", (args[1], pwhash))
                    displaysuccess(f"User '{args[1]}' registered successfully.")

                    connection.commit()
                    connection.close()

                elif args[0] == "dereg":

                    if input(f"Are you sure you want to deregister the users? Their bookings will be as well cancelled. Enter 'yes' to confirm: ").lower() == "yes":

                        usernames = args[1].split(',')
                        actual_usernames = []

                        connection = sqlite3.connect(DB_PATH)
                        connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
                        # No exclusive lock as even if the user is deleted or the password is changed on the fly, data integrity and consistency are still maintained, without any errors occurring.

                        for username in usernames:
                            if connection .execute("SELECT username FROM users WHERE username=?", [username]).fetchone() is None:
                                displaywarning(f"User '{username}' does not exist and is skipped.")
                                command_notice = True
                                continue
                            elif username == currentuser:
                                displaywarning(f"You cannot deregister yourself. Please log in as another user first. Your username is skipped.")
                                command_notice = True
                                continue
                            actual_usernames.append(username)
                            connection.execute("DELETE FROM bookings WHERE username=?", [username])
                            connection.execute("DELETE FROM users WHERE username=?", [username])

                        connection.commit()
                        connection.close()

                        print() if command_notice else None # Print a newline if there was a in-command notice

                        if actual_usernames:
                            displaysuccess(f"The following users are deregistered successfully:")
                            display_table(
                                ["Username"],
                                [20],
                                *[[username] for username in actual_usernames]
                            )
                        else:
                            displayerror("No users were deregistered.")

                    else:
                        displayerror("Deregistration cancelled.")

                elif args[0] == "users":

                    connection = sqlite3.connect(DB_PATH)
                    users = connection.execute("SELECT * FROM users ORDER BY username").fetchall()
                    connection.commit()
                    connection.close()

                    if users:
                        displaysuccess("Users found:")
                        display_table(
                            ["Admin", "Username"],
                            [5, 0],
                            *[("Yes" if user[1] else "No", user[0]) for user in users]
                        )
                    else:
                        displaywarning("No users found. Please register users using the 'reg' command.")

                elif args[0] == "build":

                    room_ids = args[1].split(',')
                    description = args[2]
                    actual_room_ids = []

                    connection = sqlite3.connect(DB_PATH)
                    # No exclusive lock as even if the user is deleted or the password is changed on the fly, data integrity and consistency are still maintained, without any errors occurring.

                    for room_id in room_ids:
                        if connection.execute("SELECT id FROM rooms WHERE id=?", [room_id]).fetchone() is not None:
                            displayinfo(f"Room '{room_id}' already exists, changing description.")
                            command_notice = True
    
                        actual_room_ids.append(room_id)
                        connection.execute("INSERT OR REPLACE INTO rooms (id, description) VALUES (?, ?)", [room_id, description])

                    connection.commit()
                    connection.close()

                    print() if command_notice else None # Print a newline if there was a in-command notice

                    if actual_room_ids:
                        displaysuccess(f"The following rooms are created successfully:")
                        display_table(
                            ["Room ID"],
                            [10],
                            *[[room_id] for room_id in actual_room_ids]
                        )
                    else:
                        displayerror("No rooms were created.")

                elif args[0] == "destroy":

                    if input(f"Are you sure you want to delete the rooms? Their bookings will be as well cancelled. Enter 'yes' to confirm: ").lower() == "yes":

                        room_ids = args[1].split(',')
                        actual_room_ids = []

                        connection = sqlite3.connect(DB_PATH)
                        connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
                        # No exclusive lock as even if the user is deleted or the password is changed on the fly, data integrity and consistency are still maintained, without any errors occurring.

                        for room_id in room_ids:
                            if connection.execute("SELECT id FROM rooms WHERE id=?", [room_id]).fetchone() is None:
                                displaywarning(f"Room '{room_id}' does not exist and is skipped.")
                                command_notice = True
                                continue
                            actual_room_ids.append(room_id)
                            connection.execute("DELETE FROM bookings WHERE roomID=?", [room_id])
                            connection.execute("DELETE FROM rooms WHERE id=?", [room_id])

                        connection.commit()
                        connection.close()

                        print() if command_notice else None # Print a newline if there was a in-command notice

                        if actual_room_ids:
                            displaysuccess(f"The following rooms are deleted successfully:")
                            display_table(
                                ["Room ID"],
                                [10],
                                *[[room_id] for room_id in actual_room_ids]
                            )
                        else:
                            displayerror("No rooms were deleted.")

                    else:
                        displayerror("Deletion cancelled.")
                
                elif args[0] == "sql":

                    connection = sqlite3.connect(DB_PATH)
                    connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
                    
                    cursor = connection.cursor()
                    try:
                        result = cursor.execute(args[1]).fetchall()
                    except sqlite3.Error as e:
                        displayerror(f"Error executing SQL query:\n{e}")
                    else:
                        displaysuccess("SQL query executed successfully:")
                        display_table(
                            [description[0] for description in cursor.description],
                            [25 for _ in range(len(cursor.description))],
                            *result
                        )

                    connection.commit()
                    connection.close()

        print() # Print a newline for better readability



## Making sure the script can only be run as a standalone program & Global error handling ##
if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise # Allow SystemExit to propagate normally
    except KeyboardInterrupt:
        displayerror("Program terminated due to user keyboard interrupt (Ctrl+C).")
        print() # Print a newline for better readability
        raise SystemExit(1)
    except:
        from datetime import datetime
        from traceback import format_exc

        displayerror(f"Program terminated due to unexpectedly error.\nError info:\n{format_exc()}")
        print() # Print a newline for better readability
        with open(Path(__file__).resolve().parent/"error.log", "a") as f:
            f.write(str(datetime.now())+"\n"+format_exc()+"\n\n\n")

        raise SystemExit(1)
else:
    displayerror("Booker cannot be imported as a module.")
    print() # Print a newline for better readability
    raise SystemExit(1)
