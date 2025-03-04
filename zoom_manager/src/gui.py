"""
GUI module for Zoom to Drive Recording Manager
Changes:
- Enhanced UI with modern styling
- Added detailed status updates
- Added debug drive configuration
- Improved error handling and feedback
"""

import sys
import os
import traceback
from pathlib import Path
from datetime import datetime

# Add src directory to Python path
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Basic error handling before any other imports
def basic_error_handler():
    try:
        # Create log directory first
        log_dir = Path.home() / '.zoom_drive' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'app.log'
        
        # Write basic error info to file
        with open(log_file, 'a') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Startup attempt at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Python version: {sys.version}\n")
            f.write(f"Current directory: {os.getcwd()}\n")
            f.write(f"Executable path: {sys.executable}\n")
            f.write(f"sys.path: {sys.path}\n")
            f.write(f"{'='*50}\n")
    except Exception as e:
        # If we can't write to log file, try to show a basic error dialog
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Startup Error")
            msg.setInformativeText(str(e))
            msg.exec()
        except:
            print(f"Critical error during startup: {str(e)}", file=sys.stderr)

# Call basic error handler before any other imports
basic_error_handler()

# Now try to import everything else
try:
    import logging
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                QHBoxLayout, QLabel, QLineEdit, QPushButton,
                                QCheckBox, QProgressBar, QFileDialog, QMessageBox,
                                QGroupBox)
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
    from PyQt6.QtGui import QPalette, QColor, QFont
    from cryptography.fernet import Fernet
    import json
    import asyncio
    from transfer_manager import TransferManager, TransferStatus
except Exception as e:
    with open(Path.home() / '.zoom_drive' / 'logs' / 'app.log', 'a') as f:
        f.write(f"Import error: {str(e)}\n")
        f.write(traceback.format_exc())
    raise

# Set up logging
def setup_logging(debug_mode=False):
    log_dir = Path.home() / '.zoom_drive' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'app.log'
    
    level = logging.DEBUG if debug_mode else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class TransferWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.transfer_manager = None

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            self.transfer_manager = TransferManager(self.config)
            self.transfer_manager.progress_signal = self.progress
            self.transfer_manager.status_signal = self.status
            
            success = loop.run_until_complete(self.transfer_manager.run())
            
            if success:
                self.finished.emit()
            else:
                self.error.emit("Transfer failed")
                
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zoom to Drive Recording Manager")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Configuration section
        config_group = self.create_group_box("Configuration", "config")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(15)
        
        # Environment file selection with modern styling
        env_layout = QHBoxLayout()
        self.env_path = QLineEdit()
        self.env_path.setPlaceholderText("Select .env file...")
        env_button = QPushButton("Browse")
        env_button.setFixedWidth(100)
        env_button.clicked.connect(self.select_env_file)
        env_layout.addWidget(QLabel("Environment File:"))
        env_layout.addWidget(self.env_path)
        env_layout.addWidget(env_button)
        
        # Input fields with better spacing and styling
        self.meeting_name = self.create_input_field("Meeting Name:", "Enter meeting name to search for")
        self.user_email = self.create_input_field("User Email:", "Enter Zoom user email")
        self.days = self.create_input_field("Days to Search:", "Default: 7")
        
        config_layout.addLayout(env_layout)
        config_layout.addWidget(self.meeting_name)
        config_layout.addWidget(self.user_email)
        config_layout.addWidget(self.days)
        
        # Debug options with enhanced visibility
        debug_group = self.create_group_box("Debug Options", "debug")
        debug_layout = QVBoxLayout(debug_group)
        debug_layout.setSpacing(15)  # Add consistent spacing
        
        # Debug mode with better explanation
        debug_widget = QWidget()
        debug_layout_h = QHBoxLayout(debug_widget)
        self.debug_mode = QCheckBox("Debug Mode")
        debug_help = QLabel("(Enables detailed logging and simulation mode)")
        debug_help.setStyleSheet("color: #666; font-size: 11pt;")
        debug_layout_h.addWidget(self.debug_mode)
        debug_layout_h.addWidget(debug_help)
        debug_layout_h.addStretch()
        
        # Debug drive ID field
        self.debug_drive = QWidget()
        self.debug_drive.setProperty("debug_only", True)
        debug_drive_layout = QVBoxLayout(self.debug_drive)
        debug_drive_layout.setSpacing(5)
        debug_drive_layout.setContentsMargins(0, 0, 0, 0)
        debug_drive_label = QLabel("Debug Drive ID:")
        self.debug_drive_input = QLineEdit()
        self.debug_drive_input.setPlaceholderText("Enter Google Drive ID for testing (optional)")
        debug_drive_layout.addWidget(debug_drive_label)
        debug_drive_layout.addWidget(self.debug_drive_input)
        
        # Debug Shared Drive ID field
        self.debug_shared_drive = QWidget()
        self.debug_shared_drive.setProperty("debug_only", True)
        debug_shared_drive_layout = QVBoxLayout(self.debug_shared_drive)
        debug_shared_drive_layout.setSpacing(5)
        debug_shared_drive_layout.setContentsMargins(0, 0, 0, 0)
        debug_shared_drive_label = QLabel("Debug Shared Drive ID:")
        self.debug_shared_drive_input = QLineEdit()
        self.debug_shared_drive_input.setPlaceholderText("Enter Shared Drive ID for testing uploads (optional)")
        debug_shared_drive_layout.addWidget(debug_shared_drive_label)
        debug_shared_drive_layout.addWidget(self.debug_shared_drive_input)
        
        # Cleanup option
        self.cleanup = QCheckBox("Clean up local files after upload")
        self.cleanup.setChecked(True)
        
        debug_layout.addWidget(debug_widget)
        debug_layout.addWidget(self.debug_drive)
        debug_layout.addWidget(self.debug_shared_drive)
        debug_layout.addWidget(self.cleanup)
        
        # Status section
        status_group = self.create_group_box("Status", "status")
        status_layout = QVBoxLayout(status_group)
        
        # Status display
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 11pt;
                padding: 10px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 5px;
            }
        """)
        
        # Progress bar with modern styling
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 5px;
                text-align: center;
                background: rgba(255, 255, 255, 0.1);
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 5px;
            }
        """)
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress)
        
        # Start button with modern styling
        self.start_button = QPushButton("Start Transfer")
        self.start_button.setFixedHeight(40)
        self.start_button.clicked.connect(self.start_transfer)
        
        # Add all sections to main layout
        layout.addWidget(config_group)
        layout.addWidget(debug_group)
        layout.addWidget(status_group)
        layout.addWidget(self.start_button)
        
        # Connect debug mode toggle
        self.debug_mode.stateChanged.connect(self.toggle_debug_mode)
        
        # Initialize debug UI state
        self.toggle_debug_mode(False)

    def create_group_box(self, title, object_name):
        group = QGroupBox(title)
        group.setObjectName(object_name)
        return group

    def create_input_field(self, label_text, placeholder_text, visible_on_debug=False):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(label_text)
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder_text)
        
        layout.addWidget(label)
        layout.addWidget(input_field)
        
        if visible_on_debug:
            container.setVisible(False)
            container.setProperty("debug_only", True)
        
        return container

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QGroupBox {
                font-size: 14pt;
                font-weight: bold;
                border: 2px solid #34495e;
                border-radius: 8px;
                margin-top: 1em;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #ecf0f1;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #ecf0f1;
                font-size: 11pt;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #34495e;
                border-radius: 5px;
                background-color: #34495e;
                color: #ecf0f1;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2472a4;
            }
            QCheckBox {
                color: #ecf0f1;
                font-size: 11pt;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)

    def toggle_debug_mode(self, state):
        debug_widgets = self.findChildren(QWidget, "", Qt.FindChildOption.FindDirectChildrenOnly)
        for widget in debug_widgets:
            if widget.property("debug_only"):
                widget.setVisible(bool(state))
        
        if state:
            logger.debug("Debug mode enabled")
            self.status_label.setText("Debug mode enabled - Using simulation mode")
        else:
            logger.debug("Debug mode disabled")
            self.status_label.setText("Ready")

    def update_status(self, status):
        self.status_label.setText(status)
        logger.debug(f"Status updated: {status}")

    def select_env_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Environment File",
            "",
            "Environment Files (*.env);;All Files (*.*)"
        )
        if file_name:
            self.env_path.setText(file_name)
            self.encrypt_env_file(file_name)

    def encrypt_env_file(self, file_path):
        try:
            # Generate key if not exists
            key_path = Path.home() / '.zoom_drive' / 'key.key'
            key_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not key_path.exists():
                key = Fernet.generate_key()
                key_path.write_bytes(key)
            else:
                key = key_path.read_bytes()
            
            # Read and encrypt env file
            with open(file_path, 'rb') as f:
                env_data = f.read()
            
            f = Fernet(key)
            encrypted_data = f.encrypt(env_data)
            
            # Save encrypted data
            encrypted_path = Path(file_path).with_suffix('.env.encrypted')
            encrypted_path.write_bytes(encrypted_data)
            
            self.status_label.setText("Environment file encrypted successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to encrypt environment file: {str(e)}")

    def start_transfer(self):
        if not self.validate_inputs():
            return
            
        self.progress.setVisible(True)
        self.start_button.setEnabled(False)
        self.status_label.setText("Starting transfer...")
        
        config = {
            'meeting_name': self.meeting_name.findChild(QLineEdit).text(),
            'user_email': self.user_email.findChild(QLineEdit).text(),
            'days': int(self.days.findChild(QLineEdit).text() or 7),
            'debug_mode': self.debug_mode.isChecked(),
            'debug_drive_id': self.debug_drive_input.text() if self.debug_mode.isChecked() else None,
            'debug_shared_drive_id': self.debug_shared_drive_input.text() if self.debug_mode.isChecked() else None,
            'cleanup': self.cleanup.isChecked(),
            'env_file': self.env_path.text()
        }
        
        self.worker = TransferWorker(config)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.transfer_finished)
        self.worker.error.connect(self.transfer_error)
        self.worker.start()

    def validate_inputs(self):
        if not self.env_path.text():
            self.show_error("Please select an environment file")
            return False
        if not self.meeting_name.findChild(QLineEdit).text():
            self.show_error("Please enter a meeting name")
            return False
        if not self.user_email.findChild(QLineEdit).text():
            self.show_error("Please enter a user email")
            return False
        return True

    def show_error(self, message):
        QMessageBox.warning(self, "Input Error", message)

    def transfer_finished(self):
        self.progress.setVisible(False)
        self.start_button.setEnabled(True)
        self.status_label.setText("Transfer completed successfully")
        QMessageBox.information(self, "Success", "Transfer completed successfully!")

    def transfer_error(self, error_msg):
        self.progress.setVisible(False)
        self.start_button.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
        QMessageBox.critical(self, "Error", f"Transfer failed: {error_msg}")

def main():
    try:
        logger.info("Starting application...")
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        logger.info("Application window shown")
        sys.exit(app.exec())
    except Exception as e:
        logger.exception("Fatal error during application startup")
        # Show error dialog
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setText("Application Error")
        error_dialog.setInformativeText(str(e))
        error_dialog.setDetailedText(f"Log file: {Path.home() / '.zoom_drive' / 'logs' / 'app.log'}")
        error_dialog.exec()
        sys.exit(1)

if __name__ == "__main__":
    main() 