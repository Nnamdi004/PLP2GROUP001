#!/usr/bin/env python3
"""
Test script for the Automatic Class Attendance Marking System with SQLite database.
Run this to verify the basic functionality of the system.
"""

import os
import unittest
from unittest.mock import patch
import io
import sys
import sqlite3
import tempfile

# Import the main module
from attendance_system import AttendanceSystem

class TestAttendanceSystem(unittest.TestCase):
    """Test cases for the Automatic Attendance System."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary database file for testing
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.system = AttendanceSystem(self.db_path)
        
        # Get the Kenya class ID
        self.system.cursor.execute("SELECT id FROM classes WHERE name = ?", ("Kenya",))
        self.kenya_class_id = self.system.cursor.fetchone()[0]

    def tearDown(self):
        """Clean up after tests."""
        # Close the database connection
        self.system.close_connection()
        
        # Close and remove the temporary file
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_initialization(self):
        """Test that the system initializes with the Kenya class and students."""
        # Check that Kenya class exists
        self.system.cursor.execute("SELECT id FROM classes WHERE name = ?", ("Kenya",))
        result = self.system.cursor.fetchone()
        self.assertIsNotNone(result)
        
        # Check that 20 students exist in Kenya class
        self.system.cursor.execute("SELECT COUNT(*) FROM students WHERE class_id = ?", (self.kenya_class_id,))
        count = self.system.cursor.fetchone()[0]
        self.assertEqual(count, 20)
        
        # Check that some specific students exist
        students = ["Alice", "Michael", "William", "Sophia"]
        for student in students:
            self.system.cursor.execute(
                "SELECT id FROM students WHERE name = ? AND class_id = ?", 
                (student, self.kenya_class_id)
            )
            result = self.system.cursor.fetchone()
            self.assertIsNotNone(result)

    def test_add_student(self):
        """Test adding a new student."""
        # Add a new student
        result = self.system.add_student("NewStudent", self.kenya_class_id)
        self.assertTrue(result)
        
        # Verify the student was added
        students = self.system.get_students(self.kenya_class_id)
        student_names = [name for _, name in students]
        self.assertIn("NewStudent", student_names)
        
        # Try adding the same student again
        result = self.system.add_student("NewStudent", self.kenya_class_id)
        self.assertFalse(result)

    def test_manual_attendance(self):
        """Test manually marking attendance."""
        # Get a student's ID
        students = self.system.get_students(self.kenya_class_id)
        student_id, student_name = students[0]  # Get the first student
        
        # Simulate marking attendance for the first student
        with patch('builtins.input', side_effect=['1', 'done']):
            self.system.mark_attendance_manually(self.kenya_class_id, "2025-03-29")
        
        # Verify the student's attendance was marked
        self.system.cursor.execute(
            "SELECT status FROM attendance WHERE student_id = ? AND date = ?",
            (student_id, "2025-03-29")
        )
        result = self.system.cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "Present")

    def test_automatic_attendance(self):
        """Test automatically marking attendance."""
        # Mark attendance automatically
        self.system.mark_attendance_automatically(self.kenya_class_id, "2025-03-30", 0.2)
        
        # Check that all students have attendance records
        students = self.system.get_students(self.kenya_class_id)
        
        for student_id, _ in students:
            self.system.cursor.execute(
                "SELECT status FROM attendance WHERE student_id = ? AND date = ?",
                (student_id, "2025-03-30")
            )
            result = self.system.cursor.fetchone()
            self.assertIsNotNone(result)
            self.assertIn(result[0], ["Present", "Absent"])
        
        # Count the number of present and absent students
        self.system.cursor.execute("""
            SELECT status, COUNT(*) 
            FROM attendance 
            WHERE date = ? AND student_id IN (
                SELECT id FROM students WHERE class_id = ?
            )
            GROUP BY status
        """, ("2025-03-30", self.kenya_class_id))
        
        status_counts = dict(self.system.cursor.fetchall())
        total_students = len(students)
        
        # Check approximately 80% present, 20% absent (with some flexibility)
        self.assertIn("Present", status_counts)
        self.assertIn("Absent", status_counts)
        
        present_rate = status_counts["Present"] / total_students
        self.assertTrue(0.7 <= present_rate <= 0.9)  # Allow some flexibility

    def test_view_attendance(self):
        """Test viewing attendance records."""
        # First, mark attendance automatically
        self.system.mark_attendance_automatically(self.kenya_class_id, "2025-03-29", 0.2)
        
        # Capture output for view_attendance
        with patch('sys.stdout', new=io.StringIO()) as fake_output:
            self.system.view_attendance(self.kenya_class_id, "2025-03-29")
            output = fake_output.getvalue()
            
        # Check if the output contains student names and statuses
        students = self.system.get_students(self.kenya_class_id)
        for _, student_name in students[:5]:  # Check just a few students
            self.assertIn(student_name, output)
        
        self.assertIn("Present", output)  # There should be some students present
        self.assertIn("Absent", output)   # There should be some students absent

    def test_generate_report(self):
        """Test generating attendance report."""
        # Mark attendance for two days
        self.system.mark_attendance_automatically(self.kenya_class_id, "2025-03-29", 0.2)
        self.system.mark_attendance_automatically(self.kenya_class_id, "2025-03-30", 0.3)
        
        # Capture output for generate_report
        with patch('sys.stdout', new=io.StringIO()) as fake_output:
            self.system.generate_report(self.kenya_class_id)
            output = fake_output.getvalue()
            
        # Check if the report contains expected data
        students = self.system.get_students(self.kenya_class_id)
        for _, student_name in students[:5]:  # Check just a few students
            self.assertIn(student_name, output)
        
        self.assertIn("Present %", output)
        self.assertIn("Absent %", output)
        self.assertIn("Total Days", output)


if __name__ == "__main__":
    unittest.main()
