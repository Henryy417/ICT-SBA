"""
This file contains:
 - CalendarView: a Tkinter/ttk Frame that displays a month grid and bookings per day
 - fetch_bookings(db_path, start=None, end=None): helper to extract bookings from the project's SQLite database
 - a small demo runner that loads bookings from data.db (if present) or uses sample data

Note: This is a calendar demo with no other funtionalities except displaying bookings.
"""

import tkinter as tk
from tkinter import ttk
import calendar
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
import sqlite3
from pathlib import Path


DB_DATETIME_FMT = '%Y-%m-%d %H:%M'


def _to_str_dt(value: Union[str, datetime]) -> str:
    if isinstance(value, datetime):
        return value.strftime(DB_DATETIME_FMT)
    if isinstance(value, str):
        # Normalize common representations: if only date is provided, append midnight
        try:
            # if already contains time
            datetime.strptime(value, DB_DATETIME_FMT)
            return value
        except Exception:
            try:
                # try date-only
                dt = datetime.strptime(value, '%Y-%m-%d')
                return dt.strftime(DB_DATETIME_FMT)
            except Exception:
                raise ValueError(f"Invalid datetime string: {value}. Expected 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM'.")
    raise TypeError('start/end must be str or datetime')


def fetch_bookings(db_path: Union[str, Path], start: Optional[Union[str, datetime]] = None, end: Optional[Union[str, datetime]] = None) -> List[Dict]:
    """Fetch bookings from SQLite database and return as list of booking dicts.

    If start and end are provided, only bookings that overlap the interval [start, end] are returned.
    Overlap condition used: NOT (booking_end < start OR booking_start > end)

    Returns list sorted by start time and mapped to keys expected by CalendarView:
        { 'id', 'title', 'start', 'end', 'room', 'user' }
    """
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    params = []
    where_clause = ''

    if start is not None and end is not None:
        s = _to_str_dt(start)
        e = _to_str_dt(end)
        # we want bookings that overlap [s, e]
        where_clause = 'WHERE NOT (end < ? OR start > ?)'
        params = [s, e]
    elif start is not None:
        s = _to_str_dt(start)
        where_clause = 'WHERE end >= ?'
        params = [s]
    elif end is not None:
        e = _to_str_dt(end)
        where_clause = 'WHERE start <= ?'
        params = [e]

    query = f"SELECT id, roomID, username, start, end, usage FROM bookings {where_clause} ORDER BY start ASC"

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        rows = cur.execute(query, params).fetchall()
    finally:
        conn.close()

    bookings = []
    for row in rows:
        bid, roomid, username, start_s, end_s, usage = row
        # Attempt to normalize times to 'YYYY-MM-DD HH:MM'
        try:
            dt_start = datetime.strptime(start_s, DB_DATETIME_FMT)
            start_norm = dt_start.strftime(DB_DATETIME_FMT)
        except Exception:
            try:
                dt_start = datetime.strptime(start_s, '%Y-%m-%d')
                start_norm = dt_start.strftime(DB_DATETIME_FMT)
            except Exception:
                start_norm = start_s

        try:
            dt_end = datetime.strptime(end_s, DB_DATETIME_FMT)
            end_norm = dt_end.strftime(DB_DATETIME_FMT)
        except Exception:
            try:
                dt_end = datetime.strptime(end_s, '%Y-%m-%d')
                end_norm = dt_end.strftime(DB_DATETIME_FMT)
            except Exception:
                end_norm = end_s

        bookings.append({
            'id': bid,
            'title': usage,
            'start': start_norm,
            'end': end_norm,
            'room': roomid,
            'user': username,
        })

    return bookings


class CalendarView(ttk.Frame):
    """
    A simple calendar view widget for Tkinter that shows a month grid and displays bookings per day.

    Usage:
        cv = CalendarView(parent)
        cv.pack(fill='both', expand=True)
        cv.set_bookings(bookings_list)

    Bookings format (list of dicts):
        [
            {
                'id': 1,
                'title': 'Lecture',
                'start': '2025-10-31 09:00',  # ISO-like string or datetime
                'end': '2025-10-31 10:30',
                'room': 'room101',
                'user': 'alice'
            },
            ...
        ]

    The widget shows month navigation and a popup with day details when a day is clicked.
    """

    def __init__(self, master, bookings: Optional[List[Dict[str, Any]]] = None, **kwargs):
        super().__init__(master, **kwargs)
        self._today = datetime.today().date()
        self._year = self._today.year
        self._month = self._today.month
        self._bookings_raw: List[Dict[str, Any]] = bookings or []
        self._bookings_by_date = {}

        self._build_ui()
        self.set_bookings(self._bookings_raw)

    def _build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill='x')

        self.prev_btn = ttk.Button(header, text='◀', width=3, command=self._on_prev)
        self.prev_btn.pack(side='left')

        self.title_var = tk.StringVar()
        self.title_lbl = ttk.Label(header, textvariable=self.title_var, anchor='center', font=('Segoe UI', 12, 'bold'))
        self.title_lbl.pack(side='left', expand=True)

        self.next_btn = ttk.Button(header, text='▶', width=3, command=self._on_next)
        self.next_btn.pack(side='right')

        # Weekday headings
        self.grid_frame = ttk.Frame(self)
        self.grid_frame.pack(fill='both', expand=True, padx=6, pady=6)

        weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for c, wd in enumerate(weekdays):
            lbl = ttk.Label(self.grid_frame, text=wd, anchor='center')
            lbl.grid(row=0, column=c, sticky='nsew', padx=2, pady=2)

        # Day cells (6 rows x 7 cols)
        self.day_cells = []
        for r in range(1, 7):
            row_cells = []
            for c in range(7):
                cell = ttk.Frame(self.grid_frame, relief='groove', borderwidth=1)
                cell.grid(row=r, column=c, sticky='nsew', padx=2, pady=2)
                cell.rowconfigure(0, weight=0)
                cell.rowconfigure(1, weight=1)
                # Day number
                day_lbl = ttk.Label(cell, text='', anchor='nw')
                day_lbl.grid(row=0, column=0, sticky='nw', padx=4, pady=2)
                # Bookings container
                booking_container = tk.Frame(cell, bg='white')
                booking_container.grid(row=1, column=0, sticky='nsew', padx=2, pady=2)
                booking_container.columnconfigure(0, weight=1)

                row_cells.append({'frame': cell, 'day_lbl': day_lbl, 'bookings': booking_container})
            self.day_cells.append(row_cells)

        # Make grid expand evenly
        for c in range(7):
            self.grid_frame.columnconfigure(c, weight=1)
        for r in range(1, 7):
            self.grid_frame.rowconfigure(r, weight=1)

    def _on_prev(self):
        if self._month == 1:
            self._month = 12
            self._year -= 1
        else:
            self._month -= 1
        self._render_month()

    def _on_next(self):
        if self._month == 12:
            self._month = 1
            self._year += 1
        else:
            self._month += 1
        self._render_month()

    def set_bookings(self, bookings: List[Dict[str, Any]]):
        """Set and index bookings. Accepts datetime objects or strings for start/end."""
        normalized = []
        for b in bookings:
            bb = dict(b)
            # Normalize start/end
            for k in ('start', 'end'):
                if k in bb and not isinstance(bb[k], datetime):
                    # Accept 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD'
                    try:
                        bb[k] = datetime.strptime(bb[k], '%Y-%m-%d %H:%M')
                    except Exception:
                        try:
                            bb[k] = datetime.strptime(bb[k], '%Y-%m-%d')
                        except Exception:
                            raise ValueError(f"Invalid date format for booking {b}")
            normalized.append(bb)

        self._bookings_raw = normalized
        self._index_bookings()
        self._render_month()

    def _index_bookings(self):
        """Build a mapping from date -> list[booking]"""
        by_date = {}
        for b in self._bookings_raw:
            # place booking on each date that the booking touches
            start_date = b['start'].date()
            end_date = b.get('end', b['start']).date()
            cur = start_date
            while cur <= end_date:
                by_date.setdefault(cur, []).append(b)
                cur += timedelta(days=1)
        # Sort each day's bookings by start time
        for d, bl in by_date.items():
            bl.sort(key=lambda x: x['start'])
        self._bookings_by_date = by_date

    def _render_month(self):
        cal = calendar.Calendar(firstweekday=0)  # Monday = 0
        month_days = cal.monthdayscalendar(self._year, self._month)
        self.title_var.set(f"{calendar.month_name[self._month]} {self._year}")

        # Fill the 6x7 grid
        for r in range(6):
            week = month_days[r] if r < len(month_days) else [0] * 7
            for c in range(7):
                daynum = week[c]
                cell = self.day_cells[r][c]
                day_lbl = cell['day_lbl']
                bookings_frame = cell['bookings']
                # Clear previous booking widgets
                for widget in bookings_frame.winfo_children():
                    widget.destroy()

                if daynum == 0:
                    day_lbl.config(text='')
                    # mark as disabled
                    cell['frame'].configure(style='Disabled.TFrame')
                else:
                    dt = datetime(year=self._year, month=self._month, day=daynum).date()
                    day_lbl.config(text=str(daynum))
                    # highlight today
                    if dt == self._today:
                        day_lbl.config(foreground='blue')
                    else:
                        day_lbl.config(foreground='black')

                    # add up to 3 booking labels
                    bookings = self._bookings_by_date.get(dt, [])
                    for i, b in enumerate(bookings[:3]):
                        text = f"{b.get('start').strftime('%H:%M') if 'start' in b else ''} {b.get('title','(No title)')}"
                        lbl = tk.Label(bookings_frame, text=text, anchor='w', bg='white', fg='black')
                        lbl.pack(fill='x', padx=2, pady=1)
                        # bind click to show details
                        lbl.bind('<Button-1>', lambda e, _d=dt: self._show_day_popup(_d))

                    if len(bookings) > 3:
                        more_lbl = tk.Label(bookings_frame, text=f"+{len(bookings)-3} more", anchor='w', bg='white', fg='gray')
                        more_lbl.pack(fill='x', padx=2, pady=1)
                        more_lbl.bind('<Button-1>', lambda e, _d=dt: self._show_day_popup(_d))

                    # whole cell click
                    cell['frame'].bind('<Button-1>', lambda e, _d=dt: self._show_day_popup(_d))

    def _show_day_popup(self, date_obj):
        bookings = self._bookings_by_date.get(date_obj, [])
        popup = tk.Toplevel(self)
        popup.title(date_obj.strftime('%A, %Y-%m-%d'))
        popup.geometry('400x300')

        header = ttk.Label(popup, text=date_obj.strftime('%A, %B %d, %Y'), font=('Segoe UI', 11, 'bold'))
        header.pack(pady=6)

        canvas = tk.Canvas(popup)
        scrollbar = ttk.Scrollbar(popup, orient='vertical', command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            '<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        if not bookings:
            ttk.Label(scroll_frame, text='No bookings', foreground='gray').pack(padx=8, pady=8)
        else:
            for b in bookings:
                frame = ttk.Frame(scroll_frame, relief='ridge', borderwidth=1)
                frame.pack(fill='x', padx=8, pady=6)
                title = ttk.Label(frame, text=b.get('title', '(No title)'), font=('Segoe UI', 10, 'bold'))
                title.pack(anchor='w', padx=6, pady=(4, 0))
                meta = f"{b.get('start').strftime('%Y-%m-%d %H:%M') if 'start' in b else ''} — {b.get('end').strftime('%Y-%m-%d %H:%M') if 'end' in b else ''}"
                ttk.Label(frame, text=meta, foreground='gray').pack(anchor='w', padx=6, pady=(0, 4))
                if 'room' in b:
                    ttk.Label(frame, text=f"Room: {b.get('room')}").pack(anchor='w', padx=6, pady=(0, 4))
                if 'user' in b:
                    ttk.Label(frame, text=f"Booked by: {b.get('user')}").pack(anchor='w', padx=6, pady=(0, 6))

        ttk.Button(popup, text='Close', command=popup.destroy).pack(pady=6)


# Demo runner / convenience functions
def make_sample_bookings():
    today = datetime.today()
    return [
        {'id': 1, 'title': 'Morning Meeting', 'start': (today).strftime('%Y-%m-%d 09:00'), 'end': (today).strftime('%Y-%m-%d 10:00'), 'room': 'A1', 'user': 'alice'},
        {'id': 2, 'title': 'Project Discussion', 'start': (today + timedelta(days=1)).strftime('%Y-%m-%d 11:00'), 'end': (today + timedelta(days=1)).strftime('%Y-%m-%d 12:00'), 'room': 'B2', 'user': 'bob'},
        {'id': 3, 'title': 'Workshop', 'start': (today + timedelta(days=3)).strftime('%Y-%m-%d 13:00'), 'end': (today + timedelta(days=3)).strftime('%Y-%m-%d 16:00'), 'room': 'Lab', 'user': 'carol'},
        {'id': 4, 'title': 'Multi-day Event', 'start': (today + timedelta(days=5)).strftime('%Y-%m-%d 10:00'), 'end': (today + timedelta(days=7)).strftime('%Y-%m-%d 16:00'), 'room': 'Hall', 'user': 'dave'},
    ]


def load_bookings_from_db_or_sample():
    """Try to load bookings from data.db in the same folder; fall back to samples."""
    root = Path(__file__).resolve().parent
    dbfile = root / 'data.db'
    if dbfile.exists():
        try:
            bookings = fetch_bookings(dbfile)
            if bookings:
                return bookings
        except Exception as e:
            print(f"Warning: failed to load bookings from DB ({e}), falling back to sample data.")
    return make_sample_bookings()


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Bookings Calendar Demo')
    root.geometry('900x600')

    cv = CalendarView(root)
    cv.pack(fill='both', expand=True)

    bookings = load_bookings_from_db_or_sample()
    cv.set_bookings(bookings)

    root.mainloop()
