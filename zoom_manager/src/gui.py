"""
GUI module for Zoom to Drive Recording Manager
Provides a modern, user-friendly interface for managing Zoom recordings
"""

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QLineEdit, QPushButton,
                            QCheckBox, QProgressBar, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from cryptography.fernet import Fernet
import json
from pathlib import Path
import asyncio
from transfer_manager import TransferManager

class TransferWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.transfer_manager = None

    def run(self):
        try:
            # Create event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Initialize transfer manager
            self.transfer_manager = TransferManager(self.config)
            self.transfer_manager.progress_signal = self.progress
            
            # Run the transfer
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
        self.setMinimumSize(600, 400)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Credentials section
        creds_group = QWidget()
        creds_layout = QVBoxLayout(creds_group)
        
        # Environment file selection
        env_layout = QHBoxLayout()
        self.env_path = QLineEdit()
        self.env_path.setPlaceholderText("Select .env file...")
        env_button = QPushButton("Browse")
        env_button.clicked.connect(self.select_env_file)
        env_layout.addWidget(QLabel("Environment File:"))
        env_layout.addWidget(self.env_path)
        env_layout.addWidget(env_button)
        
        # Search parameters
        self.meeting_name = QLineEdit()
        self.meeting_name.setPlaceholderText("Meeting Name")
        self.user_email = QLineEdit()
        self.user_email.setPlaceholderText("User Email")
        self.days = QLineEdit()
        self.days.setPlaceholderText("Days to Search (default: 7)")
        
        # Options
        self.debug_mode = QCheckBox("Debug Mode")
        self.cleanup = QCheckBox("Clean up local files after upload")
        self.cleanup.setChecked(True)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        
        # Start button
        self.start_button = QPushButton("Start Transfer")
        self.start_button.clicked.connect(self.start_transfer)
        
        # Add widgets to layout
        creds_layout.addLayout(env_layout)
        creds_layout.addWidget(QLabel("Meeting Name:"))
        creds_layout.addWidget(self.meeting_name)
        creds_layout.addWidget(QLabel("User Email:"))
        creds_layout.addWidget(self.user_email)
        creds_layout.addWidget(QLabel("Days to Search:"))
        creds_layout.addWidget(self.days)
        creds_layout.addWidget(self.debug_mode)
        creds_layout.addWidget(self.cleanup)
        
        layout.addWidget(creds_group)
        layout.addWidget(self.progress)
        layout.addWidget(self.start_button)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Worker thread
        self.worker = None

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
            
            self.statusBar().showMessage("Environment file encrypted successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to encrypt environment file: {str(e)}")

    def start_transfer(self):
        if not self.validate_inputs():
            return
            
        self.progress.setVisible(True)
        self.start_button.setEnabled(False)
        self.statusBar().showMessage("Transfer in progress...")
        
        config = {
            'meeting_name': self.meeting_name.text(),
            'user_email': self.user_email.text(),
            'days': int(self.days.text() or 7),
            'debug_mode': self.debug_mode.isChecked(),
            'cleanup': self.cleanup.isChecked(),
            'env_file': self.env_path.text()
        }
        
        self.worker = TransferWorker(config)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.transfer_finished)
        self.worker.error.connect(self.transfer_error)
        self.worker.start()

    def validate_inputs(self):
        if not self.meeting_name.text():
            QMessageBox.warning(self, "Warning", "Please enter a meeting name")
            return False
        if not self.user_email.text():
            QMessageBox.warning(self, "Warning", "Please enter a user email")
            return False
        if not self.env_path.text():
            QMessageBox.warning(self, "Warning", "Please select an environment file")
            return False
        return True

    def update_progress(self, value):
        self.progress.setValue(value)

    def transfer_finished(self):
        self.progress.setVisible(False)
        self.start_button.setEnabled(True)
        self.statusBar().showMessage("Transfer completed successfully")
        QMessageBox.information(self, "Success", "Transfer completed successfully!")

    def transfer_error(self, error_msg):
        self.progress.setVisible(False)
        self.start_button.setEnabled(True)
        self.statusBar().showMessage("Transfer failed")
        QMessageBox.critical(self, "Error", f"Transfer failed: {error_msg}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 