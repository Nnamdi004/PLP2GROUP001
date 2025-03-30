#!/usr/bin/env python3
"""
Automatic Class Attendance Marking System

A terminal-based application to track student attendance using SQLite database.
Features automatic initialization with class data and manual/auto attendance options.
Developed by Nnamdi, Kenny, Kuda, Agnes, Christian, Joseph, and Gedeon
"""

import os
import datetime
import sqlite3
import random
from typing import Dict, List, Optional, Tuple


class AttendanceSystem:
    """Main class for the attendance system."""

    def __init__(self, db_file: str = "attendance.db"):
        """Initialize the attendance system with a database file."""
        self.db_file = db_file
        self.conn = None
        self.cursor = None
        self.initialize_database()
        
        # Check if we need to populate initial data
        self.check_and_initialize_class_data()

    def initialize_database(self) -> None:
        """Initialize the SQLite database and create tables if they don't exist."""
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.cursor = self.conn.cursor()
            
            # Create classes table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            ''')
            
            # Create students table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    class_id INTEGER NOT NULL,
                    FOREIGN KEY (class_id) REFERENCES classes (id),
                    UNIQUE(name, class_id)
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
    
    def check_and_initialize_class_data(self) -> None:
        """Check if Kenya class exists, if not create it with 20 students."""
        try:
            # Check if Kenya class exists
            self.cursor.execute("SELECT id FROM classes WHERE name = ?", ("Kenya",))
            result = self.cursor.fetchone()
            
            if result is None:
                # Create Kenya class
                self.cursor.execute("INSERT INTO classes (name) VALUES (?)", ("Kenya",))
                class_id = self.cursor.lastrowid
                
                # Add 20 predefined students
                student_names = [
                    "Alice", "Michael", "Sarah", "David", "Jessica", 
                    "James", "Emily", "Robert", "Olivia", "Daniel", 
                    "Sophia", "Ethan", "Isabella", "Benjamin", "Chloe", 
                    "Matthew", "Ava", "Christopher", "Mia", "William"
                ]
                
                for name in student_names:
                    self.cursor.execute(
                        "INSERT INTO students (name, class_id) VALUES (?, ?)",
                        (name, class_id)
                    )
                
                self.conn.commit()
                print("Kenya class initialized with 20 students.")
        except sqlite3.Error as e:
            print(f"Error initializing class data: {e}")
            self.conn.rollback()
                
    def close_connection(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def get_classes(self) -> List[Tuple[int, str]]:
        """Get all classes from the database."""
        try:
            self.cursor.execute("SELECT id, name FROM classes ORDER BY name")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error retrieving classes: {e}")
            return []

    def add_student(self, name: str, class_id: int) -> bool:
        """Add a new student to the system."""
        try:
            self.cursor.execute(
                "INSERT INTO students (name, class_id) VALUES (?, ?)", 
                (name, class_id)
            )
            self.conn.commit()
            print(f"{name} has been added to the attendance list.")
            return True
        except sqlite3.IntegrityError:
            print(f"{name} already exists in this class.")
            return False
        except sqlite3.Error as e:
            print(f"Error adding student: {e}")
            self.conn.rollback()
            return False

    def get_students(self, class_id: int) -> List[Tuple[int, str]]:
        """Get all students from a specific class."""
        try:
            self.cursor.execute(
                "SELECT id, name FROM students WHERE class_id = ? ORDER BY name", 
                (class_id,)
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error retrieving students: {e}")
            return []

    def mark_attendance_manually(self, class_id: int, date: Optional[str] = None) -> None:
        """Mark attendance manually for students in a class for a specific date."""
        students = self.get_students(class_id)
        
        if not students:
            print("No students in this class. Please add students first.")
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
    
    def mark_attendance_automatically(self, class_id: int, date: Optional[str] = None,
                                     absent_rate: float = 0.2) -> None:
        """
        Mark attendance automatically for students in a class.
        
        Args:
            class_id: The ID of the class
            date: The date for attendance (default: today)
            absent_rate: Percentage of students to mark as absent (default: 20%)
        """
        students = self.get_students(class_id)
        
        if not students:
            print("No students in this class. Please add students first.")
            return

        if date is None:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
            
        # Get class name for display
        self.cursor.execute("SELECT name FROM classes WHERE id = ?", (class_id,))
        class_name = self.cursor.fetchone()[0]
            
        print(f"\nAutomatically marking attendance for class '{class_name}' on {date}")
        
        # Determine which students will be absent
        num_absent = max(1, int(len(students) * absent_rate))
        absent_indices = random.sample(range(len(students)), num_absent)
        absent_students = [students[i] for i in absent_indices]
        
        try:
            # First mark all as present
            for student_id, student_name in students:
                status = "Absent" if (student_id, student_name) in absent_students else "Present"
                
                # Check if there's already an attendance record
                self.cursor.execute(
                    "SELECT id FROM attendance WHERE student_id = ? AND date = ?", 
                    (student_id, date)
                )
                result = self.cursor.fetchone()
                
                if result:
                    # Update existing record
                    self.cursor.execute(
                        "UPDATE attendance SET status = ? WHERE student_id = ? AND date = ?", 
                        (status, student_id, date)
                    )
                else:
                    # Insert new record
                    self.cursor.execute(
                        "INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)", 
                        (student_id, date, status)
                    )
            
            self.conn.commit()
            print(f"Attendance marked automatically. {len(students) - num_absent} present, {num_absent} absent.")
            
            # Show the attendance that was marked
            print("\nAttendance Summary:")
            for student_id, student_name in students:
                self.cursor.execute(
                    "SELECT status FROM attendance WHERE student_id = ? AND date = ?", 
                    (student_id, date)
                )
                status = self.cursor.fetchone()[0]
                print(f"{student_name}: {status}")
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()

    def view_attendance(self, class_id: int, date: Optional[str] = None) -> None:
        """View attendance records for a class, optionally filtered by date."""
        students = self.get_students(class_id)
        
        if not students:
            print("No students in this class.")
            return
            
        # Get class name for display
        self.cursor.execute("SELECT name FROM classes WHERE id = ?", (class_id,))
        class_name = self.cursor.fetchone()[0]
            
        if date:
            print(f"\nClass Attendance for '{class_name}' on {date}:")
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
            # Get all unique dates from attendance records for this class
            try:
                self.cursor.execute("""
                    SELECT DISTINCT a.date 
                    FROM attendance a
                    JOIN students s ON a.student_id = s.id
                    WHERE s.class_id = ?
                    ORDER BY a.date
                """, (class_id,))
                dates = [row[0] for row in self.cursor.fetchall()]
                
                if not dates:
                    print("No attendance records found for this class.")
                    return
                    
                print(f"\nAttendance Records for '{class_name}':")
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

    def generate_report(self, class_id: int) -> None:
        """Generate attendance report showing present percentages for a class."""
        students = self.get_students(class_id)
        
        if not students:
            print("No students in this class.")
            return
            
        # Get class name for display
        self.cursor.execute("SELECT name FROM classes WHERE id = ?", (class_id,))
        class_name = self.cursor.fetchone()[0]
            
        try:
            # Get all unique dates from attendance records for this class
            self.cursor.execute("""
                SELECT DISTINCT a.date 
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE s.class_id = ?
            """, (class_id,))
            dates = self.cursor.fetchall()
            
            if not dates:
                print("No attendance records found for this class.")
                return
                
            total_days = len(dates)
            
            print(f"\nAttendance Report for '{class_name}':")
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
    print("AUTOMATIC CLASS ATTENDANCE MARKING SYSTEM")
    print("=" * 50)
    print("1. Add a Student")
    print("2. Mark Attendance Manually")
    print("3. Mark Attendance Automatically")
    print("4. View Attendance")
    print("5. Generate Report")
    print("6. Exit")
    print("=" * 50)


def main() -> None:
    """Main function to run the attendance system."""
    system = AttendanceSystem()
    
    print("Welcome to the Automatic Class Attendance Management System.")
    print("This application helps you track student attendance with ease.")
    
    try:
        # Get Kenya class ID (should be 1 if it's the first class)
        system.cursor.execute("SELECT id FROM classes WHERE name = ?", ("Kenya",))
        result = system.cursor.fetchone()
        
        if result is None:
            print("Error: Kenya class not found in database.")
            return
            
        kenya_class_id = result[0]
        
        while True:
            display_menu()
            choice = input("Enter your choice (1/2/3/4/5/6): ").strip()
            
            if choice == "1":
                name = input("Enter the student's name: ").strip()
                if name:
                    system.add_student(name, kenya_class_id)
                else:
                    print("Invalid name. Please try again.")
                    
            elif choice == "2":
                date_input = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()
                date = date_input if date_input else None
                system.mark_attendance_manually(kenya_class_id, date)
                
            elif choice == "3":
                date_input = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()
                date = date_input if date_input else None
                
                try:
                    absent_rate = float(input("Enter absent rate (0-1, default 0.2): ").strip() or "0.2")
                    if not 0 <= absent_rate <= 1:
                        print("Absent rate must be between 0 and 1. Using default 0.2.")
                        absent_rate = 0.2
                except ValueError:
                    print("Invalid input. Using default absent rate of 0.2.")
                    absent_rate = 0.2
                    
                system.mark_attendance_automatically(kenya_class_id, date, absent_rate)
                
            elif choice == "4":
                date_input = input("Enter date (YYYY-MM-DD) or press Enter for all dates: ").strip()
                date = date_input if date_input else None
                system.view_attendance(kenya_class_id, date)
                
            elif choice == "5":
                system.generate_report(kenya_class_id)
                
            elif choice == "6":
                print("Thank you for using the Automatic Attendance Management System. Goodbye!")
                break
                
            else:
                print("Invalid choice. Please try again.")
    finally:
        # Ensure database connection is closed properly
        system.close_connection()


if __name__ == "__main__":
    main()
