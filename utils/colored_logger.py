"""
Colored console output utility for Flask application
"""
from colorama import init, Fore, Back, Style
import datetime

# Initialize colorama for Windows compatibility
init(autoreset=True)

class ColoredLogger:
    """Utility class for colored console output"""
    
    @staticmethod
    def success(message):
        """Print success message in green"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"{Fore.GREEN}✓ [{timestamp}] {message}{Style.RESET_ALL}")
    
    @staticmethod
    def info(message):
        """Print info message in blue"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"{Fore.CYAN}ℹ [{timestamp}] {message}{Style.RESET_ALL}")
    
    @staticmethod
    def warning(message):
        """Print warning message in yellow"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"{Fore.YELLOW}⚠ [{timestamp}] {message}{Style.RESET_ALL}")
    
    @staticmethod
    def error(message):
        """Print error message in red"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"{Fore.RED}✗ [{timestamp}] {message}{Style.RESET_ALL}")
    
    @staticmethod
    def header(message):
        """Print header message with background"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"{Back.BLUE}{Fore.WHITE} [{timestamp}] {message} {Style.RESET_ALL}")
    
    @staticmethod
    def database(message):
        """Print database message in magenta"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"{Fore.MAGENTA}🗄 [{timestamp}] {message}{Style.RESET_ALL}")
    
    @staticmethod
    def server(message):
        """Print server message in bright green"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"{Fore.LIGHTGREEN_EX}🚀 [{timestamp}] {message}{Style.RESET_ALL}")
    
    @staticmethod
    def ngrok(message):
        """Print ngrok message in bright cyan"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"{Fore.LIGHTCYAN_EX}🌐 [{timestamp}] {message}{Style.RESET_ALL}")

# Create a global logger instance
logger = ColoredLogger()