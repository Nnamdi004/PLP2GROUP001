#!/usr/bin/env python3
"""
Class Attendance Marking System

A terminal-based application to track student attendance using SQLite database.
Developed by Nnamdi, Kenny, Kuda, Agnes, Christian, Joseph, and Gedeon
"""

import os
import datetime
import sqlite3
from typing import Dict, List, Optional, Tuple


class AttendanceSystem:
    """Main class for the attendance system."""

    def __init__(self, db_file: str = "attendance.db"):
        """Initialize the attendance system with a database file."""
        self.db_file = db_file
        self.conn = None
        self.cursor = None
        self.initialize_database()

    def initialize_database(self) -> None:
        """Initialize the SQLite database and create tables if they don't exist."""
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.cursor = self.conn.cursor()
            
            # Create students table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            ''')
            
            # Create attendance table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES students (id),
                    UNIQUE(student_id, date)
                )
            ''')
            
            self.conn.commit()
            print("Database initialized successfully.")
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            if self.conn:
                self.conn.rollback()
                
    def close_connection(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def add_student(self, name: str) -> bool:
        """Add a new student to the system."""
        try:
            self.cursor.execute("INSERT INTO students (name) VALUES (?)", (name,))
            self.conn.commit()
            print(f"{name} has been added to the attendance list.")
            return True
        except sqlite3.IntegrityError:
            print(f"{name} already exists in the system.")
            return False
        except sqlite3.Error as e:
            print(f"Error adding student: {e}")
            self.conn.rollback()
            return False

    def get_students(self) -> List[Tuple[int, str]]:
        """Get all students from the database."""
        try:
            self.cursor.execute("SELECT id, name FROM students ORDER BY name")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error retrieving students: {e}")
            return []

    def mark_attendance(self, date: Optional[str] = None) -> None:
        """Mark attendance for students for a specific date."""
        students = self.get_students()
        
        if not students:
            print("No students in the system. Please add students first.")
            return

        if date is None:
            date = datetime.datetime.now().strftime("%Y-%m-%d")

        print(f"\nMarking attendance for {date}")
        print("Current Attendance List:")
        
        # Display all students with their current status for the day
        for i, (student_id, student_name) in enumerate(students, 1):
            try:
                self.cursor.execute(
                    "SELECT status FROM attendance WHERE student_id = ? AND date = ?", 
                    (student_id, date)
                )
                result = self.cursor.fetchone()
                status = result[0] if result else "Absent"
                print(f"{i}. {student_name}: {status}")
            except sqlite3.Error as e:
                print(f"Error retrieving attendance for {student_name}: {e}")
                status = "Unknown"
                print(f"{i}. {student_name}: {status}")
        
        print("\nSelect a student to mark as Present (Enter number or type 'done' to finish)")
        
        while True:
            choice = input("> ").strip().lower()
            
            if choice == 'done':
                break
                
            try:
                student_idx = int(choice) - 1
                if 0 <= student_idx < len(students):
                    student_id, student_name = students[student_idx]
                    
                    # Check if there's already an attendance record for this student on this date
                    self.cursor.execute(
                        "SELECT id FROM attendance WHERE student_id = ? AND date = ?", 
                        (student_id, date)
                    )
                    result = self.cursor.fetchone()
                    
                    if result:
                        # Update existing record
                        self.cursor.execute(
                            "UPDATE attendance SET status = ? WHERE student_id = ? AND date = ?", 
                            ("Present", student_id, date)
                        )
                    else:
                        # Insert new record
                        self.cursor.execute(
                            "INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)", 
                            (student_id, date, "Present")
                        )
                    
                    self.conn.commit()
                    print(f"{student_name} is now marked as Present.")
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a number or 'done'.")
            except sqlite3.Error as e:
                print(f"Database error: {e}")
                self.conn.rollback()

    def view_attendance(self, date: Optional[str] = None) -> None:
        """View attendance records, optionally filtered by date."""
        students = self.get_students()
        
        if not students:
            print("No students in the system.")
            return
            
        if date:
            print(f"\nClass Attendance for {date}:")
            for student_id, student_name in students:
                try:
                    self.cursor.execute(
                        "SELECT status FROM attendance WHERE student_id = ? AND date = ?", 
                        (student_id, date)
                    )
                    result = self.cursor.fetchone()
                    status = result[0] if result else "Absent"
                    print(f"{student_name}: {status}")
                except sqlite3.Error as e:
                    print(f"Error retrieving attendance for {student_name}: {e}")
        else:
            # Get all unique dates from attendance records
            try:
                self.cursor.execute("SELECT DISTINCT date FROM attendance ORDER BY date")
                dates = [row[0] for row in self.cursor.fetchall()]
                
                if not dates:
                    print("No attendance records found.")
                    return
                    
                print("\nAttendance Records:")
                print(f"{'Student':<20}", end="")
                
                for date in dates:
                    print(f"{date:<12}", end="")
                print()
                
                # Print a separator line
                print("-" * (20 + 12 * len(dates)))
                
                # Print each student's attendance
                for student_id, student_name in students:
                    print(f"{student_name:<20}", end="")
                    
                    for date in dates:
                        self.cursor.execute(
                            "SELECT status FROM attendance WHERE student_id = ? AND date = ?", 
                            (student_id, date)
                        )
                        result = self.cursor.fetchone()
                        status = result[0] if result else "Absent"
                        print(f"{status:<12}", end="")
                    print()
            except sqlite3.Error as e:
                print(f"Database error: {e}")

    def generate_report(self) -> None:
        """Generate attendance report showing present percentages."""
        students = self.get_students()
        
        if not students:
            print("No students in the system.")
            return
            
        try:
            # Get all unique dates from attendance records
            self.cursor.execute("SELECT DISTINCT date FROM attendance")
            dates = self.cursor.fetchall()
            
            if not dates:
                print("No attendance records found.")
                return
                
            total_days = len(dates)
            
            print("\nAttendance Report:")
            print(f"{'Student':<20} {'Present %':<10} {'Absent %':<10} {'Total Days':<10}")
            print("-" * 50)
            
            for student_id, student_name in students:
                # Count days present
                self.cursor.execute(
                    "SELECT COUNT(*) FROM attendance WHERE student_id = ? AND status = ?", 
                    (student_id, "Present")
                )
                present_days = self.cursor.fetchone()[0]
                
                present_percent = (present_days / total_days) * 100 if total_days > 0 else 0
                absent_percent = 100 - present_percent
                
                print(f"{student_name:<20} {present_percent:<10.2f} {absent_percent:<10.2f} {total_days:<10}")
        except sqlite3.Error as e:
            print(f"Database error: {e}")


def display_menu() -> None:
    """Display the main menu options."""
    print("\n" + "=" * 50)
    print("CLASS ATTENDANCE MARKING SYSTEM")
    print("=" * 50)
    print("1. Add a Student")
    print("2. Mark Attendance")
    print("3. View Attendance")
    print("4. Generate Report")
    print("5. Exit")
    print("=" * 50)


def main() -> None:
    """Main function to run the attendance system."""
    system = AttendanceSystem()
    
    print("Welcome to the Class Attendance Management System.")
    print("This application helps you track student attendance with ease.")
    
    try:
        while True:
            display_menu()
            choice = input("Enter your choice (1/2/3/4/5): ").strip()
            
            if choice == "1":
                name = input("Enter the student's name: ").strip()
                if name:
                    system.add_student(name)
                else:
                    print("Invalid name. Please try again.")
                    
            elif choice == "2":
                date_input = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()
                date = date_input if date_input else None
                system.mark_attendance(date)
                
            elif choice == "3":
                date_input = input("Enter date (YYYY-MM-DD) or press Enter for all dates: ").strip()
                date = date_input if date_input else None
                system.view_attendance(date)
                
            elif choice == "4":
                system.generate_report()
                
            elif choice == "5":
                print("Thank you for using the Attendance Management System. Goodbye!")
                break
                
            else:
                print("Invalid choice. Please try again.")
    finally:
        # Ensure database connection is closed properly
        system.close_connection()


if __name__ == "__main__":
    main()

