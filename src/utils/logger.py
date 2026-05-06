"""
Centralized logging utility for RescueNet.
Provides unified logging methods for timing, errors, and status messages.
"""
from time import perf_counter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import tkinter as tk
from tkinter import filedialog


class Logger:
    """Centralized logger for RescueNet application."""
    
    def __init__(self, terminal=None):
        """
        Initialize the logger.
        
        Args:
            terminal: Optional terminal widget (e.g., TerminalPanel.text_area)
        """
        self._terminal = terminal
        self._start_time = None
        self.messages = []  # Store messages for history
        self._statement_counter = 0  # Track iteration count for statements
    
    def set_terminal(self, terminal):
        """Set or update the terminal widget."""
        self._terminal = terminal
    
    def _format_message(self, message):
        """
        Format a message with iteration count.
        
        Args:
            message: The message to format
            
        Returns:
            Formatted message with iteration count
        """
        self._statement_counter += 1
        return f"[{self._statement_counter}]: {message}"
    
    def log(self, message):
        """
        Basic log message.
        
        Args:
            message: The message to log
        """
        full_message = self._format_message(message)
        if self._terminal is not None:
            self._terminal.insert("end", f"\n{full_message}")
            self._terminal.see("end")
        self.messages.append(full_message)
    
    def log_perf(self, message, start_time=None, precision=2):
        """
        Log performance/timing message.
        
        Args:
            message: The message to log
            start_time: Optional start time from perf_counter(). 
                       If provided, calculates elapsed time.
            precision: Decimal places for timing (default 2)
        """
        if start_time is not None:
            elapsed = perf_counter() - start_time
            message = f"{message} in {elapsed:.{precision}f} seconds."
        full_message = self._format_message(message)
        if self._terminal is not None:
            self._terminal.insert("end", f"\n{full_message}")
            self._terminal.see("end")
        self.messages.append(full_message)
    
    def log_error(self, message, error=None):
        """
        Log error message.
        
        Args:
            message: The error message to log
            error: Optional exception object to include
        """
        if error is not None:
            message = f"ERROR: {message}: {error}"
        else:
            message = f"ERROR: {message}"
        full_message = self._format_message(message)
        if self._terminal is not None:
            self._terminal.insert("end", f"\n{full_message}")
            self._terminal.see("end")
        self.messages.append(full_message)
    
    def log_status(self, message):
        """
        Log status/info message.
        
        Args:
            message: The status message to log
        """
        full_message = self._format_message(message)
        if self._terminal is not None:
            self._terminal.insert("end", f"\n{full_message}")
            self._terminal.see("end")
        self.messages.append(full_message)
    
    def log_warning(self, message):
        """
        Log warning message.
        
        Args:
            message: The warning message to log
        """
        message = f"WARNING: {message}"
        full_message = self._format_message(message)
        if self._terminal is not None:
            self._terminal.insert("end", f"\n{full_message}")
            self._terminal.see("end")
        self.messages.append(full_message)
    
    def log_success(self, message):
        """
        Log success message.
        
        Args:
            message: The success message to log
        """
        message = f"SUCCESS: {message}"
        full_message = self._format_message(message)
        if self._terminal is not None:
            self._terminal.insert("end", f"\n{full_message}")
            self._terminal.see("end")
        self.messages.append(full_message)
    
    def export_history_to_pdf(self, filename="terminal_history.pdf"):
        """
        Export the logged messages to a PDF file.
        
        Args:
            filename: The name of the PDF file to create
        """
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        story.append(Paragraph("Terminal Message History", styles['Heading1']))
        story.append(Spacer(1, 12))
        
        for msg in self.messages:
            story.append(Paragraph(msg, styles['Normal']))
            story.append(Spacer(1, 6))
        
        doc.build(story)


# Singleton instance for global access
_logger = Logger()


def get_logger():
    """Get the global logger instance."""
    return _logger


def set_global_terminal(terminal):
    """Set the global terminal for all logging."""
    _logger.set_terminal(terminal)