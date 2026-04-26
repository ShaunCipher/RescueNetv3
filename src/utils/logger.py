"""
Centralized logging utility for RescueNet.
Provides unified logging methods for timing, errors, and status messages.
"""
from time import perf_counter


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
    
    def set_terminal(self, terminal):
        """Set or update the terminal widget."""
        self._terminal = terminal
    
    def log(self, message):
        """
        Basic log message.
        
        Args:
            message: The message to log
        """
        if self._terminal is not None:
            self._terminal.insert("end", f"\n> {message}")
            self._terminal.see("end")
    
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
            self.log(f"{message} in {elapsed:.{precision}f} seconds.")
        else:
            self.log(message)
    
    def log_error(self, message, error=None):
        """
        Log error message.
        
        Args:
            message: The error message to log
            error: Optional exception object to include
        """
        if error is not None:
            self.log(f"ERROR: {message}: {error}")
        else:
            self.log(f"ERROR: {message}")
    
    def log_status(self, message):
        """
        Log status/info message.
        
        Args:
            message: The status message to log
        """
        self.log(message)
    
    def log_warning(self, message):
        """
        Log warning message.
        
        Args:
            message: The warning message to log
        """
        self.log(f"WARNING: {message}")
    
    def log_success(self, message):
        """
        Log success message.
        
        Args:
            message: The success message to log
        """
        self.log(f"SUCCESS: {message}")


# Singleton instance for global access
_logger = Logger()


def get_logger():
    """Get the global logger instance."""
    return _logger


def set_global_terminal(terminal):
    """Set the global terminal for all logging."""
    _logger.set_terminal(terminal)