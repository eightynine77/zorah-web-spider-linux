import os
import sys
import multiprocessing
import time
import engine  # <-- CRITICAL CHANGE: Importing engine.py

# --- LINUX/POSIX Imports (replaces msvcrt) ---
import tty
import termios
import select

# We need to set the path for 'auto-py-to-exe' to find the 'components'
# when running as a compiled .exe
if getattr(sys, 'frozen', False):
    # If running as a .exe, the path is relative to the .exe
    bundle_dir = sys._MEIPASS
    # <-- CRITICAL CHANGE: Pointing to the app object in engine.py
    engine.app.template_folder = os.path.join(bundle_dir, 'components')
    engine.app.static_folder = os.path.join(bundle_dir, 'components')

# This will hold our server process
server_process = None
status = "STOPPED"
error_msg = ""

# --- ANSI Color Codes (replaces os.system('color')) ---
C_GREEN = '\033[92m'  # Bright Green
C_RED = '\033[91m'    # Bright Red
C_RESET = '\033[0m'   # Reset color

def draw_menu():
    """Draws the TUI menu using simple print statements."""
    os.system('clear')  # Replaced 'cls' with 'clear'
    
    print("=========================================================")
    print("          ZORAH WEB SPIDER - CONTROL PANEL")
    print("=========================================================")
    print("\n")
    
    # Status
    if status == "RUNNING":
        # os.system('color 0A') # Removed
        print(f"  SERVER STATUS: {C_GREEN}RUNNING (http://127.0.0.1:8080){C_RESET}")
    else:
        # os.system('color 0C') # Removed
        print(f"  SERVER STATUS: {C_RED}STOPPED{C_RESET}")
    
    print("\n\n")
    print("  --- CONTROLS ---")
    print("  [ S ] Start Server")
    print("  [ T ] Stop Server")
    print("  [ Q ] Quit Program")
    print("\n")
    
    # Error message
    if error_msg:
        print(f"  {C_RED}MESSAGE: {error_msg}{C_RESET}")

# --- Linux/POSIX Keyboard Input (replaces msvcrt) ---

def kbhit():
    """Returns True if a key is pressed, False otherwise."""
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

def getch():
    """Gets a single character from stdin."""
    return sys.stdin.read(1)

def main_loop():
    """Main event loop for the TUI."""
    global server_process, status, error_msg
    
    draw_menu()
    
    while True:
        if kbhit():
            key = getch()
            error_msg = "" # Clear error on new keypress

            # --- [ S ] Start ---
            # Note: Changed from b's' (bytes) to 's' (string)
            if key == 's' or key == 'S':
                if not server_process or not server_process.is_alive():
                    try:
                        server_process = multiprocessing.Process(target=engine.start_server)
                        server_process.start()
                        status = "RUNNING"
                        error_msg = "Server started successfully. Opening browser..."
                        engine.open_browser(f"http://127.0.0.1:8080")
                    except Exception as e:
                        status = "STOPPED"
                        error_msg = f"Failed to start: {e}"
                else:
                    error_msg = "Server is already running."
                draw_menu()

            # --- [ T ] Stop ---
            elif key == 't' or key == 'T':
                if server_process and server_process.is_alive():
                    server_process.terminate()
                    server_process.join()
                    server_process = None
                    status = "STOPPED"
                    error_msg = "Server stopped successfully."
                else:
                    error_msg = "Server is not running."
                draw_menu()

            # --- [ Q ] Quit ---
            elif key == 'q' or key == 'Q':
                if server_process and server_process.is_alive():
                    print("Stopping server before quitting...")
                    server_process.terminate()
                    server_process.join()
                print(f"Exiting. Goodbye!{C_RESET}") # Add reset for safety
                break # Exit the loop
            else:
                pass 
                
        time.sleep(0.1) # Prevent high CPU usage

# This wrapper is required to safely initialize
def run_tui():
    multiprocessing.freeze_support() 
    
    # --- Set up terminal for non-blocking input ---
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    try:
        # Set terminal to cbreak mode (no echo, no buffering)
        tty.setcbreak(sys.stdin.fileno())
        main_loop()
    except KeyboardInterrupt:
        print(f"\nQuitting...{C_RESET}")
        if server_process and server_process.is_alive():
            server_process.terminate()
            server_process.join()
    finally:
        # --- ALWAYS restore terminal settings on exit ---
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    run_tui()