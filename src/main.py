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

# Program information
INFO = "Booker v2.0"

# Customizable program information
DB_PATH = Path(__file__).resolve().parent/"data.db"

def main():
    ## Initialization ##
    # Functional imports and mofications
    from getpass import getpass as inputpw
    from hashlib import sha3_512 as hash
    from os import system as sysexec, name as sysname
    from re import compile as regex_compile, PatternError as RegexCompileError
    from enum import Enum
    import sqlite3

    # Functional Functions
    def update_available_commands():
        global available_commands
        available_commands = []
        for cmd, details in commands.items():
            if 'use_requirement' not in details or (details['use_requirement'] == "admin" and isadmin or details['use_requirement'] == "user" and currentuser is not None):
                available_commands.append(cmd)

    def is_valid_time_interval(start: str, end: str, allow_equal: bool = False) -> bool:
        start_dt = datetime.strptime(start, '%Y-%m-%d %H:%M')
        end_dt = datetime.strptime(end, '%Y-%m-%d %H:%M')
        if allow_equal:
            return start_dt <= end_dt
        else:
            return start_dt < end_dt

    # Functional Functions for SQL: NO INPUT VALIDATION!
    def sql_is_in_time_interval(interval_start: str, interval_end: str, target_start: str, target_end: str) -> bool:
        interval_start_dt = datetime.strptime(interval_start, '%Y-%m-%d %H:%M')
        interval_end_dt = datetime.strptime(interval_end, '%Y-%m-%d %H:%M')
        target_start_dt = datetime.strptime(target_start, '%Y-%m-%d %H:%M')
        target_end_dt = datetime.strptime(target_end, '%Y-%m-%d %H:%M')
        return not(interval_start_dt >= target_end_dt or interval_end_dt <= target_start_dt)

    def sql_regex_match(pattern: str, value: str = "") -> bool:
        return regex_compile(pattern).match(value) is not None

    # Placeholder for user authentication
    currentuser = None  # Placeholder for current user
    isadmin = False  # Placeholder for admin status

    # Command special flag characters
    class MetaChar(Enum):
        asterisk = '*'
        now = 'now'
    
    # Command definitions
    commands = {
        # Commands usable before login
        "help": {"help": "Show help message."},
        "man": {"args": {"command": {"format": "text"}}, "help": "Show manual for a specific command."},
        "exit": {"help": "Exit Booker."},
        "version": {"help": "Show current version info."},
        "cls": {"help": "Clear the screen."},
        "login": {"args": {"username": {"format": "text"}}, "help": "Log in as a user."},
        # Commands usable as admins
        "reg": {
            "args": {"username": {"format": "text"}},
            "help": "Register a new user or change the password of an existing user.",
            "use_requirement": "admin"
        },
        "dereg": {
            "args": {"usernames": {"format": "csv"}},
            "help": "Deregister users.",
            "use_requirement": "admin"
        },
        "auth": {
            "args": {"usernames": {"format": "csv"}},
            "help": "Make user an administrator.",
            "use_requirement": "admin"
        },
        "deauth": {
            "args": {"usernames": {"format": "csv"}},
            "help": "Make user a standard user.",
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
                "roomIDs": {"format": "csv", "default": MetaChar.asterisk, "special_chars": [MetaChar.asterisk]},
                "usernames": {"format": "csv", "default": MetaChar.asterisk, "special_chars": [MetaChar.asterisk]},
                "start": {"format": "time", "default": MetaChar.now, "special_chars": [MetaChar.now, MetaChar.asterisk]},
                "end": {"format": "time", "default": MetaChar.asterisk, "special_chars": [MetaChar.now, MetaChar.asterisk]},
                "usage": {"format": "regex", "default": ""}
            },
            "help": "List bookings of the specified rooms booked by specified users within a given time. Usage can be filtered using a regular expression.",
            "use_requirement": "user"
        },
        "show": {
            "args": {"bookingIDs": {"format": "csv", "default": MetaChar.asterisk, "special_chars": [MetaChar.asterisk]}},
            "help": "Show bookings of specified booking IDs.",
            "use_requirement": "user"
        },
        "book": {
            "args": {
                "roomIDs": {"format": "csv"},
                "start": {"format": "time", "default": MetaChar.now, "special_chars": [MetaChar.now]},
                "end": {"format": "time", "special_chars": [MetaChar.now]},
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
                "roomIDs": {"format": "csv", "special_chars": [MetaChar.asterisk]},
                "usernames": {"format": "csv", "special_chars": [MetaChar.asterisk]},
                "start": {"format": "time", "special_chars": [MetaChar.now, MetaChar.asterisk]},
                "end": {"format": "time", "special_chars": [MetaChar.now, MetaChar.asterisk]},
                "usage": {"format": "regex", "default": ""}
            },
            "help": "Cancel bookings to make available the specified rooms booked by specified users within a given time. Usage can be filtered using a regular expression. Standard users can only clear their own future bookings.",
            "use_requirement": "user"
        }
    }

    update_available_commands() # Initialize available_commands variable & update available commands based on current user status

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
        connection.execute("INSERT INTO users (username, pwhash, isadmin) VALUES (?, ?, ?)", ("admin", hash(b"admin").digest(), 1))
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
        # Note: Modification to the bookings table should, at all times, be done with foreign key constraints enabled to maintain data consistency and integrity.
        connection.execute(
            "CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, roomID TEXT, username TEXT, start TEXT NOT NULL, end TEXT NOT NULL, usage TEXT NOT NULL, FOREIGN KEY (username) REFERENCES users(username), FOREIGN KEY (roomID) REFERENCES rooms(id))"
        )

        # Create indexes for bookings table to improve performance
        connection.execute("CREATE INDEX IF NOT EXISTS idx_bookings_room_user ON bookings (roomID, username)") # Optimizing searches through both room and room & user
        connection.execute("CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings (username)") # Optimizing searches through user
        connection.execute("CREATE INDEX IF NOT EXISTS idx_bookings_time ON bookings (start)") # Optimizing searches through time
        connection.commit()

        displayinfo("Initialization: Created 'bookings' table.")

    print() # Print a newline for better readability

    ## Main loop ##
    while True:

        # End database access
        connection.commit() # Commit any previous changes to the database and avoid database lock issues
        connection.close() # Close previous connection to avoid resource usage

        # Input & Authorization #
        raw = input((('\33[91m'+currentuser+'\33[0m' if isadmin else currentuser) if currentuser is not None else "") + "> ").strip()

        # Re-initialize database access
        connection = sqlite3.connect(DB_PATH) # Initialize database connection for command execution
        connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints

        # Check if user still exists if logged in
        if currentuser is not None:
            result_isadmin = connection.execute("SELECT isadmin FROM users WHERE username = ?", [currentuser]).fetchone()
            if result_isadmin is None:
                currentuser = None
                isadmin = False
                update_available_commands()
                displayerror("Administrators have removed your account. You are now logged out.")
                print()
                continue
            elif result_isadmin[0] != isadmin:
                isadmin = result_isadmin[0] == 1
                update_available_commands()
                displayinfo("Administrators have promoted you to an administrator." if result_isadmin[0] == 1 else "Administrators have demoted you to a standard user.")
                print()

        current_submission_time = datetime.now().strftime('%Y-%m-%d %H:%M') # Get current time for submission

        # Parser #
        # Ignore empty input
        if len(raw) == 0:
            continue

        # Parse the input valid command and arguments
        cmd = None
        args = {}

        positional_args = []

        unfilled_named_args = []

        index = 0

        in_quote = False
        escaped = False

        current_word = ''
        current_is_quoted = None

        parse_error_loop_exit = False
        while index < len(raw) + 1:
            if index == len(raw) or raw[index] == ' ' and not in_quote:
                if current_is_quoted:
                    if unfilled_named_args:
                        args[unfilled_named_args.pop(0)] = current_word
                    else:
                        positional_args.append(current_word)
                    current_is_quoted = False
                else:
                    if cmd is None:
                        if current_word not in available_commands:
                            possible_cmds = []
                            for available_cmd in available_commands:
                                if available_cmd.startswith(current_word):
                                    possible_cmds.append(available_cmd)
                            if len(possible_cmds) == 1:
                                cmd = possible_cmds[0]
                            elif len(possible_cmds) > 1:
                                displayerror(f"Ambiguous command abbreviation '{current_word}'. Which command did you mean: {', '.join(possible_cmds)}?")
                                parse_error_loop_exit = True
                                break
                            else:
                                displayerror(f"Unknown command or abbreviation '{current_word}'. Type 'help' for a list of commands.")
                                parse_error_loop_exit = True
                                break
                        else:
                            cmd = current_word
                    elif current_word.startswith('--'):
                        argname = current_word[2:]
                        if 'args' not in commands[cmd] or argname not in commands[cmd]['args']:
                            displayerror(f"Unknown argument '{argname}' for command '{cmd}'.")
                            parse_error_loop_exit = True
                            break
                        unfilled_named_args.append(current_word[2:])
                    elif unfilled_named_args:
                        args[argname := unfilled_named_args.pop(0)] = MetaChar(current_word) if current_word in MetaChar else current_word
                    else:
                        positional_args.append(MetaChar(current_word) if current_word in MetaChar else current_word)
                in_quote = False
                escaped = False
                current_word = ''
                current_is_quoted = None    
            elif not escaped:
                if raw[index] == in_quote:
                    in_quote = False
                elif (quote := raw[index]) in ('"', '\'') and not in_quote:
                    in_quote = quote
                    current_is_quoted = True
                elif raw[index] == '\\' and in_quote != '\'' and index + 1 < len(raw) and raw[index + 1] in ('"', '\'', '\\'):
                    escaped = True
                else:
                    current_word += raw[index]
            else:
                current_word += raw[index]
                escaped = False
            index += 1
        if parse_error_loop_exit:
            print() # Print a newline for better readability
            continue
        if unfilled_named_args:
            for arg in unfilled_named_args:
                args[arg] = ''

        # Fill positional arguments and check for required arguments plus filling defaults
        if 'args' in commands[cmd]:
            for arg in commands[cmd]['args']:
                if arg not in args:
                    if positional_args:
                        value = positional_args.pop(0)
                        args[arg] = value
                    else:
                        if 'default' in commands[cmd]['args'][arg]:
                            args[arg] = commands[cmd]['args'][arg]['default']
                        else:
                            displayerror(f"Missing required argument '{arg}' for command '{cmd}'.")
                            parse_error_loop_exit = True
                            break
            if parse_error_loop_exit:
                print() # Print a newline for better readability
                continue
        if len(positional_args) > 0:
            displayerror(f"Too many positional arguments for command '{cmd}'. Expected {len(commands[cmd]['args']) if 'args' in commands[cmd] else 0}, got {len(args) + len(positional_args)}.")
            print()
            continue

        # Validate argument values
        for arg in args:
            # Convert MetaChar to its value
            if isinstance(args[arg], MetaChar):
                if 'special_chars' not in commands[cmd]['args'][arg] or args[arg] not in commands[cmd]['args'][arg]['special_chars']:
                    args[arg] = args[arg].value
                    
            if not isinstance(args[arg], MetaChar):
                if commands[cmd]['args'][arg]['format'] == 'csv':
                    args[arg] = args[arg].split(',')
                    if '' in args[arg]:
                        displayerror(f"CSV argument '{arg}' cannot be empty.")
                        parse_error_loop_exit = True
                        break
                elif commands[cmd]['args'][arg]['format'] == 'time':
                    try:
                        datetime.strptime(args[arg], '%Y-%m-%d %H:%M')
                    except ValueError:
                        displayerror(f"Time argument '{arg}' is not a valid time input.")
                        parse_error_loop_exit = True
                elif commands[cmd]['args'][arg]['format'] == 'regex':
                    try:
                        regex_compile(args[arg])
                    except RegexCompileError:
                        displayerror(f"Regular expression argument '{arg}' is not a valid regex pattern.")
                        parse_error_loop_exit = True
                elif commands[cmd]['args'][arg]['format'] == 'text':
                    if not args[arg]:
                        displayerror(f"Text argument '{arg}' cannot be empty.")
                        parse_error_loop_exit = True
            
            # Globally applied meta characters explanation
            if args[arg] == MetaChar.now:
                args[arg] = current_submission_time
        if parse_error_loop_exit:
            print() # Print a newline for better readability
            continue

        # Display what is being executed
        execution_line = cmd
        for argname, value in args.items():
            execution_line += f' --{argname} '
            if isinstance(value, MetaChar):
                execution_line += f'{value.value}'
            elif isinstance(value, list):
                execution_line += ','.join(value)
            else:
                execution_line += f'"{value}"'
        displayinfo(f"Executing: {execution_line}")

        print() # Print a newline for better readability

        # Command Handlers #

        command_notice = False

        # Commands that can be used before login
        if cmd == "help":

            print("Use 'man' to receive more information about a specific command.")
            print("Each word is separated by a space. If you want to use spaces in a single word, please quote the argument with single or double quotes. Escaping characters is not allowed in single quotes.")
            print("If you want to use characters that are not ASCII printable characters, please also quote them.")
            print("Command abbreviations are allowed. Enter the first few letters of a command. Note that the parser tries to see the input as a complete command before seeking a possible abbreviation.")
            print("After entering a command, add a space then the arguments if arguments are required.\n")
            print("Arguments can be either named or positional. For named arguments, input double hyphen '--' followed the argument name in the same word, and then the argument value as another. Quote the word if you want to have '--' at the beginning literally. For positional arguments, input the value directly as a word. They will be taken as the the first unfilled argument in the command.")
            print("Default values of arguments, if exist, will be filled when not enough arguments are provided.")

            print() # Print a newline for better readability

            if currentuser is not None:
                print("Arguments of \33[3mcsv\33[0m values, commonly seen if more than one value is allowed in an argument (e.g. IDs), are separated by commas without spaces. Values cannot be empty. e.g. 'room1,room2,room3'.")
                print("Arguments of \33[3mtime\33[0m values must be in the format 'YYYY-MM-DD HH:MM'. e.g. '2008-04-17 12:00'. Additionally, 'now' can be used to refer to current time.")
                print("Arguments of \33[3mregex\33[0m values must be a valid regular expression. Matching is done from the beginning of the target text (invisible '^' has been prepended). e.g. '.' to match everything, or 'room\\d+$' to match room IDs that start with 'room' followed by one or more digits.")
                print("Arguments of \33[3mtext\33[0m values can be any text that is not empty without special formatting.")
                print("Wildcard '*' can often be used. It usually means \33[3mall\33[0m. For some time input, it can be used to remove respective time constraints according to context. e.g. Using '*' as start time and '2008-04-17' as end time means every record until '2008-04-17'.")
            else:
                print("More commands are available after login.")

            print() # Print a newline for better readability

            display_table(
                ["Command", "Description"],
                [15, 0],
                *[[cmd, details['help']] for cmd, details in commands.items() if cmd in available_commands]  # Filter out commands that are not available to the current user
            )

        elif cmd == "man":

            if args["command"] in available_commands:
                print("Usage:")
                syntax_text = args["command"]
                if 'args' in commands[args["command"]]:
                    syntax_text += ' '
                    for arg, prop in commands[args["command"]]["args"].items():
                        syntax_text += f"[{arg}({prop['format']}{('|' + '|'.join(prop['substitutions'])) if 'substitutions' in prop else ''}){('="' + prop['default'] + '"') if 'default' in prop else ''}] " # Syntax for each argument
                print(syntax_text.strip())
                print("\nDescription:")
                print(commands[args["command"]]['help'])
            else:
                displayerror(f"No manual entry for command '{args["command"]}'.")

        elif cmd == "exit":

            # End database access
            connection.commit() # Commit any previous changes to the database and avoid database lock issues
            connection.close() # Close previous connection to avoid resource usage

            raise SystemExit(0)

        elif cmd == "version":

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
                displayerror("No license file is found. This may indicate an illegal distribution.\nThis program is originally released under the MIT License by Chen Hang Tsz Henry. Please refer to the source code repository for more information.")

        elif cmd == "cls":

            sysexec("cls" if sysname == "nt" else "clear") # Compatible with older Windows without PowerShell

        elif cmd == "login":

            pwhash = hash(inputpw("Password: ").encode()).digest()

            result_user = connection.execute("SELECT isadmin FROM users WHERE username=? AND pwhash=?", (args["username"], pwhash)).fetchone()

            if result_user is not None:
                currentuser = args["username"]
                isadmin = result_user[0] == 1
                update_available_commands()
                displaysuccess(f"Logged in as '{currentuser}'.")
            else:
                displayerror("Invalid username or password.")

        # Commands that can be used only after login
        elif currentuser is not None:
            if cmd == "cp":

                if (new_password := inputpw("New Password: ")) == inputpw("Confirm New Password: "):
                    new_pwhash = hash(new_password.encode()).digest()

                    connection.execute("UPDATE users SET pwhash=? WHERE username=?", (new_pwhash, currentuser))

                    displaysuccess("Password changed successfully.")
                else:
                    displayerror("Passwords do not match. Please try again.")

            elif cmd == "rooms":

                result_rooms = connection.execute("SELECT id, description FROM rooms ORDER BY id").fetchall()

                if result_rooms:
                    displaysuccess("Rooms found:")
                    display_table(
                        ["ID", "Description"],
                        [10, 0],
                        *result_rooms
                    )
                else:
                    displaywarning("No rooms found. Please create rooms using the 'build' command.")

            elif cmd == "search":

                # Meta characters transformation
                if args["start"] == MetaChar.asterisk:
                    actual_start = datetime.min.strftime('%Y-%m-%d %H:%M')
                else:
                    actual_start = args["start"]
                if args["end"] == MetaChar.asterisk:
                    actual_end = datetime.max.strftime('%Y-%m-%d %H:%M')
                else:
                    actual_end = args["end"]

                # Input consistency checks
                if not is_valid_time_interval(actual_start, actual_end):
                    displayerror("Time input is inconsistent. The end time must be later than the start time.")
                    print()
                    continue

                # Constructing query parameters with non-fatal dynamic input validity check using stored data
                params = []
                command_notice = False
                if args["roomIDs"] != MetaChar.asterisk:
                    actual_room_ids = [room for room in args["roomIDs"] if connection.execute("SELECT 0 FROM rooms WHERE id=?", [room]).fetchone() is not None or (command_notice := True) and displaywarning(f"Room '{room}' does not exist and is skipped.")]
                    params.extend(actual_room_ids)
                else:
                    actual_room_ids = MetaChar.asterisk
                if args["usernames"] != MetaChar.asterisk:
                    actual_user_ids = [user for user in args["usernames"] if connection.execute("SELECT 0 FROM users WHERE username=?", [user]).fetchone() is not None or (command_notice := True) and displaywarning(f"User '{user}' does not exist and is skipped.")]
                    params.extend(actual_user_ids)
                else:
                    actual_user_ids = MetaChar.asterisk
                params.append(actual_start)
                params.append(actual_end)
                params.append(args["usage"])
                
                print() if command_notice else None # Print a newline if there was a in-command notice

                connection.create_function("in_interval", 4, sql_is_in_time_interval)
                connection.create_function("regex", 2, sql_regex_match)

                query = f"SELECT * FROM bookings WHERE {'roomID IN (' + ','.join('?' for _ in actual_room_ids) + ')' if actual_room_ids != MetaChar.asterisk else "TRUE"} AND {'username IN ('+','.join('?' for _ in actual_user_ids)+')' if actual_user_ids != MetaChar.asterisk else "TRUE"} AND in_interval(?, ?, start, end) AND regex(?, usage) ORDER BY strftime('%F %R', start), roomID"

                result_bookings = connection.execute(query, params).fetchall()

                if result_bookings:
                    displaysuccess("Bookings found:")
                    display_table(
                        ["ID", "Room ID", "User", "Start Time", "End Time", "Usage"],
                        [10, 10, 20, 20, 20, 0],
                        *result_bookings
                    )
                else:
                    displaysuccess("No bookings found. The time slot is free.")

            elif cmd == "show":

                # Fetching results with non-fatal dynamic input validity check using stored data
                if '*' not in args["bookingIDs"]:
                    result_bookings = connection.execute("SELECT * FROM bookings WHERE id IN (" + ','.join('?' for _ in args["bookingIDs"]) + ")", args["bookingIDs"]).fetchall()
                else:
                    result_bookings = []
                    for booking_id in args["bookingIDs"]:
                        booking = connection.execute("SELECT * FROM bookings WHERE id=?", [booking_id]).fetchone()
                        if booking is None:
                            displaywarning(f"Booking ID '{booking_id}' does not exist and is skipped.")
                            command_notice = True
                            continue
                        result_bookings.append(booking)

                print() if command_notice else None # Print a newline if there was a in-command notice

                if result_bookings:
                    displaysuccess("Bookings found:")
                    display_table(
                        ["ID", "Room ID", "User", "Start Time", "End Time", "Usage"],
                        [10, 10, 20, 20, 20, 0],
                        *result_bookings
                    )
                else:
                    displayerror("No bookings found.")

            elif cmd == "book":
                
                connection.execute("BEGIN EXCLUSIVE") # Start an exclusive transaction to prevent other users from modifying the database after validative searching
                connection.create_function("in_interval", 4, sql_is_in_time_interval)

                # Input consistency checks
                if not is_valid_time_interval(args["start"], args["end"]):
                    displayerror("Time input is inconsistent. The end time must be later than the start time.")
                    print()
                    continue

                # Dynamic input validity check using stored data
                if not isadmin and not is_valid_time_interval(current_submission_time, args["start"], allow_equal=True):
                    displayerror("Standard user cannot set start time in the past. Please use a future time or 'now'.")
                    print()
                    continue

                # Doing actions with non-fatal dynamic input validity check using stored data
                result_bookings = []
                for room_id in args["roomIDs"]:
                    if connection.execute("SELECT 0 FROM rooms WHERE id=?", [room_id]).fetchone() is None:
                        displaywarning(f"Room '{room_id}' does not exist and is skipped.")
                        command_notice = True
                        continue
                    if (result_bookedbooking := connection.execute(f"SELECT id FROM bookings WHERE roomID = ? AND in_interval(?, ?, start, end)", (room_id, args["start"], args["end"])).fetchone()) is not None:
                        displaywarning(f"Time slot is occupied (Booking ID: {result_bookedbooking[0]}) for room {room_id} and is skipped.")
                        command_notice = True
                        continue

                    connection.execute("INSERT INTO bookings (roomID, username, start, end, usage) VALUES (?, ?, strftime('%F %R', ?), strftime('%F %R', ?), ?)", (room_id, currentuser, args["start"], args["end"], args["usage"]))
                    connection.commit() # Commit the addition to the database before fetching the booking record
                    result_bookings.append(connection.execute("SELECT * FROM bookings WHERE ID = (SELECT seq FROM sqlite_sequence WHERE name = 'bookings')").fetchone()) # Fetch the newly added booking

                print() if command_notice else None # Print a newline if there was a in-command notice

                if result_bookings:
                    displaysuccess("Booking(s) below created successfully:")
                    display_table(
                        ["ID", "Room ID", "User", "Start Time", "End Time", "Usage"],
                        [10, 10, 20, 20, 20, 0],
                        *result_bookings
                    )
                else:
                    displayerror("No bookings were created.")

            elif cmd == "modify":

                # No exclusive lock as even if the booking is deleted or modified on the fly, data integrity and consistency are still maintained, without any errors occurring.

                # Doing actions with non-fatal dynamic input validity check using stored data
                result_bookings = []
                for booking_id in args["bookingIDs"]:
                    result_booking = connection.execute("SELECT username, start FROM bookings WHERE id=?", [booking_id]).fetchone()
                    if result_booking is None:
                        displaywarning(f"Booking ID '{booking_id}' does not exist and is skipped.")
                        command_notice = True
                        continue
                    if result_booking[0] != currentuser and not isadmin:
                        displaywarning(f"You can only modify your own bookings as a standard user. Booking ID '{booking_id}' is skipped.")
                        command_notice = True
                        continue
                    if not isadmin and not is_valid_time_interval(current_submission_time, result_booking[1], allow_equal=True):
                        displaywarning(f"Booking ID '{booking_id}' is in the past and cannot be modified by a standard user.")
                        command_notice = True
                        continue

                    connection.execute("UPDATE bookings SET usage=? WHERE id=?", (args["usage"], booking_id))
                    connection.commit() # Commit the modification to the database before fetching the booking record
                    result_bookings.append(connection.execute("SELECT * FROM bookings WHERE id=?", [booking_id]).fetchone()) # Fetch the modified booking

                print() if command_notice else None # Print a newline if there was a in-command notice

                if result_bookings:
                    displaysuccess("The following bookings are modified as below successfully:")
                    display_table(
                        ["ID", "Room ID", "User", "Start Time", "End Time", "Usage"],
                        [10, 10, 20, 20, 20, 0],
                        *result_bookings
                    )
                else:
                    displayerror("No bookings were modified.")

            elif cmd == "cancel":

                # No exclusive lock as even if the user is deleted or the password is changed on the fly, data integrity and consistency are still maintained, without any errors occurring.

                # Doing actions with non-fatal dynamic input validity check using stored data
                result_bookings = []
                for booking_id in args["bookingIDs"]:
                    result_booking = connection.execute("SELECT username, start FROM bookings WHERE id=?", [booking_id]).fetchone()
                    if result_booking is None:
                        displaywarning(f"Booking ID '{booking_id}' does not exist and is skipped.")
                        command_notice = True
                        continue
                    if result_booking[0] != currentuser and not isadmin:
                        displaywarning(f"You can only cancel your own bookings as a standard user. Booking ID '{booking_id}' is skipped.")
                        command_notice = True
                        continue
                    if not isadmin and not is_valid_time_interval(current_submission_time, result_booking[1], allow_equal=True):
                        displaywarning(f"Booking ID '{booking_id}' is in the past and cannot be cancelled by a standard user.")
                        command_notice = True
                        continue

                    result_bookings.append(connection.execute("SELECT * FROM bookings WHERE id=?", [booking_id]).fetchone()) # Fetch the booking before deletion
                    connection.execute("DELETE FROM bookings WHERE id=?", [booking_id])

                print() if command_notice else None # Print a newline if there was a in-command notice

                if result_bookings:
                    displaysuccess("The following bookings are cancelled successfully:")
                    display_table(
                        ["ID", "Room ID", "User", "Start Time", "End Time", "Usage"],
                        [10, 10, 20, 20, 20, 0],
                        *result_bookings
                    )
                else:
                    displayerror("No bookings were cancelled.")

            elif cmd == "clear":

                if ('*' not in args["roomIDs"] and '*' not in args["usernames"] and '*' not in args["start"] and '*' not in args["end"]) or input("You are using wildcard '*' in one or more arguments. This will cancel bookings massively. Are you sure you want to proceed? Enter 'yes' to confirm: ").lower() == "yes":

                    # Meta characters transformation
                    if args["start"] == MetaChar.asterisk:
                        actual_start = datetime.min.strftime('%Y-%m-%d %H:%M')
                    else:
                        actual_start = args["start"]
                    if args["end"] == MetaChar.asterisk:
                        actual_end = datetime.max.strftime('%Y-%m-%d %H:%M')
                    else:
                        actual_end = args["end"]

                    # Input consistency checks
                    if not is_valid_time_interval(actual_start, actual_end):
                        displayerror("Time input is inconsistent. The end time must be later than the start time.")
                        print()
                        continue

                    # Constructing query parameters with non-fatal dynamic input validity check using stored data
                    params = []
                    command_notice = False
                    if args["roomIDs"] != MetaChar.asterisk:
                        actual_room_ids = [room for room in args["roomIDs"] if connection.execute("SELECT 0 FROM rooms WHERE id=?", [room]).fetchone() is not None or (command_notice := True) and displaywarning(f"Room '{room}' does not exist and is skipped.")]
                        params.extend(actual_room_ids)
                    else:
                        actual_room_ids = MetaChar.asterisk
                    if args["usernames"] != MetaChar.asterisk:
                        actual_usernames = [user for user in args["usernames"] if connection.execute("SELECT 0 FROM users WHERE username=?", [user]).fetchone() is not None or (command_notice := True) and displaywarning(f"User '{user}' does not exist and is skipped.")]
                        params.extend(actual_usernames)
                    else:
                        actual_usernames = MetaChar.asterisk
                    params.append(actual_start)
                    params.append(actual_end)
                    params.append(args["usage"])

                    print() if command_notice else None # Print a newline if there was a in-command notice

                    connection.create_function("in_interval", 4, sql_is_in_time_interval)
                    connection.create_function("regex", 2, sql_regex_match)

                    query = f"SELECT * FROM bookings WHERE {'roomID IN ('+','.join('?' for _ in actual_room_ids)+')' if actual_room_ids != MetaChar.asterisk else 'TRUE'} AND {'username IN ('+','.join('?' for _ in actual_usernames)+')' if actual_usernames != MetaChar.asterisk else 'TRUE'} AND in_interval(?, ?, start, end) AND regex(?, usage)"

                    bookings = connection.execute(query, params).fetchall()

                    # Doing actions with non-fatal dynamic input validity check using stored data
                    result_bookings = []
                    for booking in bookings:
                        if booking[2] != currentuser and not isadmin:
                            displaywarning(f"You can only clear your own bookings as a standard user. Booking ID '{booking[0]}' is skipped.")
                            command_notice = True
                            continue
                        result_bookings.append(booking)

                        connection.execute("DELETE FROM bookings WHERE id=?", [booking[0]])

                    print() if command_notice else None # Print a newline if there was a in-command notice

                    if result_bookings:
                        displaysuccess("The following bookings are cancelled successfully:")
                        display_table(
                            ["ID", "Room ID", "User", "Start Time", "End Time", "Usage"],
                            [10, 10, 20, 20, 20, 0],
                            *result_bookings
                        )
                    else:
                        displayerror("No bookings were cancelled.")

                else:
                    displayerror("Clearing bookings cancelled.")
                
            elif isadmin:

                if cmd == "reg":

                    # No exclusive lock as even if the user is deleted or the password is changed on the fly, data integrity and consistency are still maintained, without any errors occurring.

                    # Non-fatal dynamic input validity check using stored data
                    if connection.execute("SELECT username FROM users WHERE username=?", [args["username"]]).fetchone() is not None:
                        displayinfo(f"User '{args['username']}' already exists. Changing password.")
                        command_notice = True

                    print() if command_notice else None # Print a newline if there was a in-command notice

                    pwhash = hash(inputpw("Password: ").encode()).digest()
                    connection.execute("INSERT OR REPLACE INTO users (username, pwhash) VALUES (?, ?)", (args["username"], pwhash))
                    displaysuccess(f"User '{args['username']}' registered or updated successfully.")

                elif cmd == "dereg":

                    if input("Are you sure you want to deregister the users? Their bookings will be as well cancelled. Enter 'yes' to confirm: ").lower() == "yes":

                        # No exclusive lock as even if the user is deleted or the password is changed on the fly, data integrity and consistency are still maintained, without any errors occurring.

                        # Doing actions with non-fatal dynamic input validity check using stored data
                        result_usernames = []
                        result_bookings = []
                        for username in args["usernames"]:
                            if connection.execute("SELECT username FROM users WHERE username=?", [username]).fetchone() is None:
                                displaywarning(f"User '{username}' does not exist and is skipped.")
                                command_notice = True
                                continue
                            if username == currentuser:
                                displaywarning("You cannot deregister yourself. Please log in as another admin first. Your username is skipped.")
                                command_notice = True
                                continue

                            result_usernames.append([username])
                            result_bookings.extend(connection.execute("SELECT * FROM bookings WHERE username=?", [username]).fetchall()) # Fetch the bookings before deletion
                            connection.execute("DELETE FROM bookings WHERE username=?", [username])
                            connection.execute("DELETE FROM users WHERE username=?", [username])

                        print() if command_notice else None # Print a newline if there was a in-command notice

                        if result_usernames:
                            displaysuccess("The following users are deregistered and logged out successfully:")
                            display_table(
                                ["Username"],
                                [20],
                                *result_usernames
                            )
                            if result_bookings:
                                print() # Print a newline for better readability
                                displaysuccess("The following bookings are cancelled due to user deregistration:")
                                display_table(
                                    ["ID", "Room ID", "User", "Start Time", "End Time", "Usage"],
                                    [10, 10, 20, 20, 20, 0],
                                    *result_bookings
                                )
                        else:
                            displayerror("No users were deregistered.")

                    else:
                        displayerror("Deregistration cancelled.")

                elif cmd == "auth":

                    # No exclusive lock as even if the user is authorized or deauthorized on the fly, data integrity and consistency are still maintained, without any errors occurring.

                    # Doing actions with non-fatal dynamic input validity check using stored data
                    result_usernames = []
                    for username in args["usernames"]:
                        if connection.execute("SELECT username FROM users WHERE username=?", [username]).fetchone() is None:
                            displaywarning(f"User '{username}' does not exist and is skipped.")
                            command_notice = True
                            continue

                        result_usernames.append([username])
                        connection.execute("UPDATE users SET isadmin = 1 WHERE username=?", [username])

                    print() if command_notice else None # Print a newline if there was a in-command notice

                    if result_usernames:
                        displaysuccess("The following users are authorized successfully:")
                        display_table(
                            ["Username"],
                            [20],
                            *result_usernames
                        )
                    else:
                        displayerror("No users were authorized.")

                elif cmd == "deauth":

                    # No exclusive lock as even if the user is authorized or deauthorized on the fly, data integrity and consistency are still maintained, without any errors occurring.

                    # Doing actions with non-fatal dynamic input validity check using stored data
                    result_usernames = []
                    for username in args["usernames"]:
                        if connection.execute("SELECT username FROM users WHERE username=?", [username]).fetchone() is None:
                            displaywarning(f"User '{username}' does not exist and is skipped.")
                            command_notice = True
                            continue
                        if username == currentuser:
                            displaywarning("You cannot deauthorize yourself. Please log in as another admin first. Your username is skipped.")
                            command_notice = True
                            continue

                        result_usernames.append([username])
                        connection.execute("UPDATE users SET isadmin = 0 WHERE username=?", [username])

                    print() if command_notice else None # Print a newline if there was a in-command notice

                    if result_usernames:
                        displaysuccess("The following users are deauthorized successfully:")
                        display_table(
                            ["Username"],
                            [20],
                            *result_usernames
                        )
                    else:
                        displayerror("No users were deauthorized.")

                elif cmd == "users":

                    result_users = connection.execute("SELECT * FROM users ORDER BY username").fetchall()

                    if result_users:
                        displaysuccess("Users found:")
                        display_table(
                            ["Admin", "Username"],
                            [5, 0],
                            *[[bool(user[1]), user[0]] for user in result_users]
                        )
                    else:
                        displaywarning("No users found. Please register users using the 'reg' command.")

                elif cmd == "build":

                    # No exclusive lock as even if the user is deleted or the password is changed on the fly, data integrity and consistency are still maintained, without any errors occurring.

                    # Doing actions with non-fatal dynamic input validity check using stored data
                    result_room_ids = []
                    for room_id in args["roomIDs"]:
                        if connection.execute("SELECT id FROM rooms WHERE id=?", [room_id]).fetchone() is not None:
                            displayinfo(f"Room '{room_id}' already exists, changing description.")
                            command_notice = True

                        result_room_ids.append([room_id])
                        connection.execute("INSERT OR REPLACE INTO rooms (id, description) VALUES (?, ?)", [room_id, args["description"]])

                    connection.commit()
                    connection.close()

                    print() if command_notice else None # Print a newline if there was a in-command notice

                    if result_room_ids:
                        displaysuccess("The following rooms are created or updated successfully:")
                        display_table(
                            ["Room ID"],
                            [10],
                            *result_room_ids
                        )
                    else:
                        displayerror("No rooms were created.")

                elif cmd == "destroy":

                    if input("Are you sure you want to delete the rooms? Their bookings will be as well cancelled. Enter 'yes' to confirm: ").lower() == "yes":

                        # No exclusive lock as even if the user is deleted or the password is changed on the fly, data integrity and consistency are still maintained, without any errors occurring.

                        # Doing actions with non-fatal dynamic input validity check using stored data
                        result_room_ids = []
                        for room_id in args["roomIDs"]:
                            if connection.execute("SELECT id FROM rooms WHERE id=?", [room_id]).fetchone() is None:
                                displaywarning(f"Room '{room_id}' does not exist and is skipped.")
                                command_notice = True
                                continue

                            result_room_ids.append([room_id])
                            connection.execute("DELETE FROM bookings WHERE roomID=?", [room_id])
                            connection.execute("DELETE FROM rooms WHERE id=?", [room_id])

                        print() if command_notice else None # Print a newline if there was a in-command notice

                        if result_room_ids:
                            displaysuccess("The following rooms are deleted successfully:")
                            display_table(
                                ["Room ID"],
                                [10],
                                *result_room_ids
                            )
                        else:
                            displayerror("No rooms were deleted.")

                    else:
                        displayerror("Deletion cancelled.")
                
                elif cmd == "sql":
                    
                    try:
                        result = connection.execute(args["query"]).fetchall()
                    except sqlite3.Error as e:
                        displayerror(f"Error executing SQL query:\n{e}")
                    else:
                        displaysuccess("SQL query executed successfully:")
                        display_table(
                            [description[0] for description in connection.description],
                            [25 for _ in range(len(connection.description))],
                            *result
                        )

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
    except:
        from datetime import datetime
        from traceback import format_exc

        displayerror(f"Program terminated due to unexpectedly error.\nError info:\n{format_exc()}")
        print() # Print a newline for better readability
        with open(Path(__file__).resolve().parent/"error.log", "a") as f:
            f.write(str(datetime.now())+"\n"+format_exc()+"\n\n\n")
    finally:
        # Rollback of any uncommitted changes in the current cycle to the database will be done automatically on exit
        raise SystemExit(1) # Exit the program with a non-zero exit code to indicate an error

else:
    displayerror("Booker cannot be imported as a module.")
    print() # Print a newline for better readability
    raise SystemExit(1)
