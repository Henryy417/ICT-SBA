# Booker v1.0 Documentation

## Overview
Booker is a command-line room booking system for managing users, rooms, and bookings. It supports user authentication, admin operations, and flexible search and management of bookings.

## Features
- User and admin authentication
- Register/deregister users
- Change password
- Create, update, and delete rooms
- Book, modify, cancel, and clear bookings
- Search and show bookings with flexible filters
- Raw SQL query execution

## Getting Started
1. To use it on your computer, run the script as a standalone program:
    ```bash
    python main.py
    ```
2. If you want a single executable:
    Use `pyinstaller` in the **root directory of this repository** to compile the Python source code into an executable:
    ```bash
    pyinstaller Booker.spec
    ```
    Then run the generated executable in the `dist` folder.
    > Note: The option for icons in `Booker.spec` is set to `icon=['assets\\Booker.ico']`, which only works on Windows. Edit it accordingly if you are using a different OS.
3. If you want to make Booker a back-end shell:
    Compile the source file like in (2). Manage Booker's standard input/output/error streams in your front-end app. If you are using Python, you may need the `subprocess` module.

## Command Reference
These are the currently available commands in Booker:
### Pre-login Commands
| Command   | Description                       |
|-----------|-----------------------------------|
| help      | Show help message                 |
| man       | Show manual for a command         |
| exit      | Exit Booker                       |
| version   | Show version info                 |
| cls       | Clear the screen                  |
| login     | Log in as a user                  |

### Admin Commands (after login)
| Command     | Description                                 |
|-------------|---------------------------------------------|
| reg         | Register a new user                         |
| dereg       | Deregister users                            |
| cpx         | Change password for a user                  |
| users       | List all users                              |
| build       | Create new rooms                            |
| refurnish   | Update room descriptions                    |
| destroy     | Delete rooms                                |
| sql         | Execute raw SQL query                       |

### User Commands (after login)
| Command   | Description                                   |
|-----------|-----------------------------------------------|
| cp        | Change password for current user              |
| rooms     | List all rooms                                |
| search    | List bookings with filters                    |
| show      | Show bookings by ID                           |
| book      | Make a reservation                            |
| modify    | Modify booking description                    |
| cancel    | Cancel bookings                               |
| clear     | Cancel bookings with filters                  |

## Arguments & Formats
- **csv**: Comma-separated values (e.g., `room1,room2`)
- **time**: Format `YYYY-MM-DD HH:MM` or `now` (other unspecified formats may be supported by SQLite, but not guaranteed)
- **text**: Free text without special formatting
> Note: Some arguments accept a wildcard (`*`) for flexible matching.

## Error Handling
- Errors, warnings, and info messages are color-coded.
- All errors are logged to `error.log`.

## Database
- Use SQLite on `data.db`.
- Tables `users`, `rooms` and `bookings` are used and created automatically on first run.

## Data Storage
If you run Booker from Python script, the files will be stored in the same directory as the script.

If you run it as an executable, the files will be stored in the `_internal` directory next to the executable.

## Example Usage: Setting up Booker
```bash
> l admin
Command abbreviation interpreted as 'login'.

Password:
Logged in as 'admin'.

admin> bu room1 "Conference Room"   
Command abbreviation interpreted as 'build'.

The following rooms are created successfully:
room1

admin> bo room1 "2025-07-14 09:00" "2025-07-14 10:00" Meeting
Command abbreviation interpreted as 'book'.

Booking(s) for the following room(s) created successfully:
room1

admin> se room1 * now * Meeting
Command abbreviation interpreted as 'search'.

Using current time 2025-07-13 23:09 as start time.

Bookings found:
Booking ID     Room ID   User                     Start Time               End Time                 Usage
---            ---       ---                      ---                      ---                      ---
1              room1     admin                    2025-07-14 09:00         2025-07-14 10:00         Meeting
```
> Note: The default user is `admin` with password `admin`, created automatically on first run.

## License
Copyright (c) 2025 Chen Hang Tsz Henry