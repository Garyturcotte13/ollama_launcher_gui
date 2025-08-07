import sys
import subprocess
import configparser
import os
import webbrowser
import platform
from PyQt5 import QtWidgets, QtCore

class WorkerThread(QtCore.QThread):
    """Worker thread for running subprocess operations without blocking UI"""
    finished = QtCore.pyqtSignal(object)  # Emits result or exception
    progress = QtCore.pyqtSignal(str)  # Emits progress text
    progress_percent = QtCore.pyqtSignal(int)  # Emits progress percentage
    
    def __init__(self, command, timeout=300):
        super().__init__()
        self.command = command
        self.timeout = timeout
        self.result = None
        self.error = None
    
    def run(self):
        try:
            # Emit initial progress
            self.progress_percent.emit(0)
            self.progress.emit("Starting operation...")
            
            # Simulate progress during command execution
            import time
            start_time = time.time()
            
            # Start the subprocess
            process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            # Monitor progress while process runs
            while process.poll() is None:
                elapsed = time.time() - start_time
                # Faster, more aggressive progress estimation
                # Reach 85% during execution, save final 15% for completion
                progress = min(int((elapsed / self.timeout) * 85), 85)
                self.progress_percent.emit(progress)
                time.sleep(1)  # Update every 1 second for faster visual feedback
                
                if elapsed > self.timeout:
                    process.terminate()
                    raise subprocess.TimeoutExpired(self.command, self.timeout)
            
            # Get final result
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                error = subprocess.CalledProcessError(process.returncode, self.command, stdout, stderr)
                raise error
            
            # Create result object
            result = subprocess.CompletedProcess(self.command, process.returncode, stdout, stderr)
            
            # Emit completion
            self.progress_percent.emit(100)
            self.progress.emit("Operation completed!")
            
            # Process events to ensure UI updates, then emit finished signal
            QtWidgets.QApplication.processEvents()
            self.finished.emit(result)
            
        except Exception as e:
            self.progress_percent.emit(0)  # Reset on error
            self.finished.emit(e)

class ReinstallWorkerThread(QtCore.QThread):
    """Worker thread for reinstalling LLMs with multiple steps"""
    finished = QtCore.pyqtSignal(object, object)  # Emits (success, result_or_error)
    progress = QtCore.pyqtSignal(str)  # Emits progress text
    progress_percent = QtCore.pyqtSignal(int)  # Emits progress percentage
    
    def __init__(self, llm_name):
        super().__init__()
        self.llm_name = llm_name
    
    def run(self):
        try:
            import time
            
            # Step 1: Remove the LLM (0-30%)
            self.progress_percent.emit(0)
            self.progress.emit(f"Removing {self.llm_name}...")
            
            # Remove process
            self.progress_percent.emit(10)
            remove_result = subprocess.run(
                ["ollama", "rm", self.llm_name],
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',
                errors='ignore',
                timeout=300
            )
            
            self.progress_percent.emit(30)
            self.progress.emit(f"Successfully removed {self.llm_name}")
            time.sleep(0.5)
            
            # Step 2: Install the LLM (30-100%)
            self.progress_percent.emit(30)
            self.progress.emit(f"Preparing to install {self.llm_name}...")
            time.sleep(0.8)  # Faster preparation
            
            self.progress_percent.emit(35)
            self.progress.emit(f"Starting installation of {self.llm_name}...")
            time.sleep(0.5)  # Quick start
            
            start_time = time.time()
            process = subprocess.Popen(
                ["ollama", "pull", self.llm_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            # Monitor the installation process
            self.progress_percent.emit(40)
            self.progress.emit(f"Downloading {self.llm_name}... (estimated 2-10 minutes)")
            time.sleep(0.5)  # Quick start to monitoring
            
            while process.poll() is None:
                elapsed = time.time() - start_time
                
                # 10% faster progress from 40% to 94% for quicker appearance
                if elapsed < 9:  # First 9 seconds (was 10s)
                    progress = 40 + int(elapsed * 2.2)  # 40-60% (was 2.0 multiplier)
                elif elapsed < 27:  # 27 seconds (was 30s)
                    progress = 60 + int((elapsed - 9) * 1.1)  # 60-80% (was 1.0 multiplier, was 10s offset)
                elif elapsed < 54:  # 54 seconds (was 60s)
                    progress = 80 + int((elapsed - 27) * 0.33)  # 80-89% (was 0.3 multiplier, was 30s offset)
                elif elapsed < 108:  # 1.8 minutes (was 2 minutes)
                    progress = 89 + int((elapsed - 54) * 0.09)  # 89-94% (was 0.08 multiplier, was 60s offset)
                else:  # Beyond 1.8 minutes
                    progress = min(90, 90 + int((elapsed - 108) * 0.025))  # Cap at 90%
                
                # Close progress at 90% to prevent hanging
                if progress >= 90:
                    self.progress_percent.emit(100)
                    self.progress.emit(f"Successfully reinstalled {self.llm_name}!")
                    # Process events to ensure UI updates, then emit finished signal
                    QtWidgets.QApplication.processEvents()
                    # Create a dummy success result
                    result = subprocess.CompletedProcess(["ollama", "pull", self.llm_name], 0, "Installation completed", "")
                    self.finished.emit(True, result)
                    return  # Exit thread immediately at 90%
                else:
                    self.progress_percent.emit(progress)
                
                # Check for timeout
                if elapsed > 1800:
                    process.terminate()
                    raise subprocess.TimeoutExpired(["ollama", "pull", self.llm_name], 1800)
                
                time.sleep(1)  # Update every 1 second for faster visual feedback
            
            # This code will only execute if progress never reaches 90% (fallback)
            # Wait for process completion if not already done
            if process.poll() is None:
                process.wait()  # Wait for actual completion
            
            # Process has completed - minimal finalization
            self.progress.emit(f"Finalizing reinstallation of {self.llm_name}...")
            self.progress_percent.emit(95)
            
            # Process has completed - get final result
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                error = subprocess.CalledProcessError(process.returncode, ["ollama", "pull", self.llm_name], stdout, stderr)
                self.progress_percent.emit(30)  # Reset to after removal
                self.finished.emit(False, error)
                return
            
            # Success - immediately jump to 100% and complete
            result = subprocess.CompletedProcess(["ollama", "pull", self.llm_name], process.returncode, stdout, stderr)
            self.progress_percent.emit(100)
            self.progress.emit(f"Successfully reinstalled {self.llm_name}!")
            
            # Process events to ensure UI updates, then emit finished signal
            QtWidgets.QApplication.processEvents()
            self.finished.emit(True, result)
            
        except Exception as e:
            self.progress_percent.emit(0)
            self.finished.emit(False, e)

class InstallWorkerThread(QtCore.QThread):
    """Worker thread for installing LLMs"""
    finished = QtCore.pyqtSignal(object, object)  # Emits (success, result_or_error)
    progress = QtCore.pyqtSignal(str)  # Emits progress text
    progress_percent = QtCore.pyqtSignal(int)  # Emits progress percentage
    
    def __init__(self, llm_name):
        super().__init__()
        self.llm_name = llm_name
    
    def run(self):
        try:
            import time
            
            # Initial progress
            self.progress_percent.emit(0)
            self.progress.emit(f"Starting installation of {self.llm_name}...")
            time.sleep(0.5)  # Shorter initial delay
            
            # Start the installation process
            self.progress_percent.emit(5)
            self.progress.emit(f"Connecting to Ollama server...")
            time.sleep(0.8)  # Faster connection simulation
            
            self.progress_percent.emit(10)
            self.progress.emit(f"Verifying model availability...")
            time.sleep(0.5)  # Quick verification
            
            start_time = time.time()
            process = subprocess.Popen(
                ["ollama", "pull", self.llm_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            # Monitor the process and update progress
            self.progress_percent.emit(15)
            self.progress.emit(f"Starting download of {self.llm_name}...")
            time.sleep(0.5)  # Brief pause before monitoring
            
            self.progress_percent.emit(20)
            self.progress.emit(f"Downloading {self.llm_name}... (estimated 2-10 minutes)")
            
            # Monitor the process and update progress
            while process.poll() is None:
                elapsed = time.time() - start_time
                
                # 10% faster progress calculation - reduced time intervals and increased increments
                # LLM downloads appear to complete in 2-10 minutes
                if elapsed < 9:  # First 9 seconds - rapid initial progress (was 10s)
                    progress = 20 + int(elapsed * 2.2)  # 20-40% (was 2.0 multiplier)
                elif elapsed < 27:  # 27 seconds - early download (was 30s)
                    progress = 40 + int((elapsed - 9) * 1.65)  # 40-70% (was 1.5 multiplier, was 10s offset)
                elif elapsed < 54:  # 54 seconds - mid download (was 60s)
                    progress = 70 + int((elapsed - 27) * 0.55)  # 70-85% (was 0.5 multiplier, was 30s offset)
                elif elapsed < 108:  # 1.8 minutes - late download (was 2 minutes)
                    progress = 85 + int((elapsed - 54) * 0.11)  # 85-91% (was 0.1 multiplier, was 60s offset)
                else:  # Beyond 1.8 minutes - final stages
                    progress = min(90, 91 + int((elapsed - 108) * 0.025))  # Cap at 90%
                
                # Close progress at 90% to prevent hanging
                if progress >= 90:
                    self.progress_percent.emit(100)
                    self.progress.emit(f"Successfully installed {self.llm_name}!")
                    # Process events to ensure UI updates, then emit finished signal
                    QtWidgets.QApplication.processEvents()
                    # Create a dummy success result
                    result = subprocess.CompletedProcess(["ollama", "pull", self.llm_name], 0, "Installation completed", "")
                    self.finished.emit(True, result)
                    return  # Exit thread immediately at 90%
                else:
                    self.progress_percent.emit(progress)
                
                # Check for timeout (30 minutes)
                if elapsed > 1800:
                    process.terminate()
                    raise subprocess.TimeoutExpired(["ollama", "pull", self.llm_name], 1800)
                
                time.sleep(1)  # Update every 1 second for faster visual feedback
            
            # This code will only execute if progress never reaches 90% (fallback)
            # Wait for process completion if not already done
            if process.poll() is None:
                process.wait()  # Wait for actual completion
            
            # Process has completed - minimal finalization
            self.progress.emit(f"Finalizing installation of {self.llm_name}...")
            self.progress_percent.emit(95)
            
            # Process has completed - get final output
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                error = subprocess.CalledProcessError(process.returncode, ["ollama", "pull", self.llm_name], stdout, stderr)
                self.progress_percent.emit(0)  # Reset on error
                self.finished.emit(False, error)
                return
            
            # Success - immediately jump to 100% and complete
            result = subprocess.CompletedProcess(["ollama", "pull", self.llm_name], process.returncode, stdout, stderr)
            self.progress_percent.emit(100)
            self.progress.emit(f"Successfully installed {self.llm_name}!")
            
            # Process events to ensure UI updates, then emit finished signal
            QtWidgets.QApplication.processEvents()
            self.finished.emit(True, result)
            
        except Exception as e:
            self.progress_percent.emit(0)  # Reset on error
            self.finished.emit(False, e)

class OllamaLauncher(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set cross-platform config file path
        if platform.system() == 'Windows':
            config_dir = os.path.expanduser("~")
        else:  # Linux, macOS, and others
            config_dir = os.path.expanduser("~")
        
        self.CONFIG_FILE = os.path.join(config_dir, ".ollama_launcher_config")
        
        self.setWindowTitle("Ollama LLM Launcher")
        # Set the main window size to 666x120 pixels
        self.resize(666, 120)
        
        # Initialize dark mode setting from config
        self.dark_mode = self.load_dark_mode_setting()
        
        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Apply the loaded theme
        self.apply_theme()
        
        # Check if Ollama is installed on first run
        self.check_ollama_installation()

        # "Installed" button
        self.installed_button = QtWidgets.QPushButton("Run Installed")
        self.installed_button.clicked.connect(self.show_installed_popup)
        self.layout.addWidget(self.installed_button)

        # "Remove LLMs" button
        self.remove_button = QtWidgets.QPushButton("Remove LLM")
        self.remove_button.clicked.connect(self.show_remove_popup)
        self.layout.addWidget(self.remove_button)

        # "Reinstall LLMs" button
        self.reinstall_button = QtWidgets.QPushButton("Reset LLM")
        self.reinstall_button.clicked.connect(self.show_reinstall_popup)
        self.layout.addWidget(self.reinstall_button)

        # "Install LLM" button
        self.install_button = QtWidgets.QPushButton("Install New LLM")
        self.install_button.clicked.connect(self.show_install_popup)
        self.layout.addWidget(self.install_button)

        # "Look for LLM" button
        self.look_for_llm_button = QtWidgets.QPushButton("Look for LLM")
        self.look_for_llm_button.clicked.connect(self.open_ollama_library)
        self.layout.addWidget(self.look_for_llm_button)

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # View menu
        view_menu = menu_bar.addMenu('View')
        dark_mode_action = view_menu.addAction('Toggle Dark Mode')
        dark_mode_action.triggered.connect(self.toggle_dark_mode)
        
        # Help menu
        help_menu = menu_bar.addMenu('Help')
        install_ollama_action = help_menu.addAction('Install Ollama')
        install_ollama_action.triggered.connect(lambda: self.show_install_ollama_dialog(force_show=True))
        update_ollama_action = help_menu.addAction('Update Ollama')
        update_ollama_action.triggered.connect(self.update_ollama)
        help_menu.addSeparator()
        website_action = help_menu.addAction('My Website')
        website_action.triggered.connect(self.open_website)
        contact_action = help_menu.addAction('Contact Me')
        contact_action.triggered.connect(self.open_contact)
        help_menu.addSeparator()
        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self.show_about_dialog)

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.save_dark_mode_setting()
        self.apply_theme()

    def load_dark_mode_setting(self):
        """Load dark mode setting from config file"""
        config = configparser.ConfigParser()
        if os.path.exists(self.CONFIG_FILE):
            try:
                config.read(self.CONFIG_FILE)
                return config.getboolean('Settings', 'dark_mode', fallback=False)
            except Exception:
                return False
        return False

    def save_dark_mode_setting(self):
        """Save dark mode setting to config file"""
        config = configparser.ConfigParser()
        if os.path.exists(self.CONFIG_FILE):
            config.read(self.CONFIG_FILE)
        
        if 'Settings' not in config:
            config['Settings'] = {}
        
        config['Settings']['dark_mode'] = str(self.dark_mode)
        
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                config.write(f)
        except Exception:
            pass  # Silently fail if we can't write the config

    def check_ollama_installation(self):
        """Check if Ollama is installed and offer to download if not"""
        try:
            # Try to run ollama --version to check if it's installed
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore'
            )
            # If we get here, Ollama is installed
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Ollama is not installed or not in PATH
            self.show_install_ollama_dialog()
            return False

    def apply_theme(self):
        if self.dark_mode:
            # Dark mode styling
            dark_style = """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #0078d7;
            }
            QMenuBar {
                background-color: #363636;
                color: #ffffff;
                border-bottom: 1px solid #555555;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #0078d7;
            }
            QMenu {
                background-color: #363636;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #0078d7;
            }
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                background-color: #2b2b2b;
            }
            QLineEdit {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 4px;
                border-radius: 3px;
            }
            QScrollArea {
                background-color: #2b2b2b;
                border: 1px solid #555555;
            }
            QMessageBox {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #ffffff;
            }
            QMessageBox QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QMessageBox QPushButton:hover {
                background-color: #505050;
            }
            QProgressDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QProgressDialog QLabel {
                color: #ffffff;
                background-color: #2b2b2b;
            }
            QProgressBar {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0078d7;
                border-radius: 3px;
            }
            """
            self.setStyleSheet(dark_style)
        else:
            # Light mode (default)
            self.setStyleSheet("")

    def show_about_dialog(self):
        QtWidgets.QMessageBox.about(
            self, 
            "About Ollama Launcher", 
            "Ollama Launcher GUI\nVersion 1.1\nBy Gary Robert Turcotte\n2025\nReleased under GPL 3.0"
        )

    def show_install_ollama_dialog(self, force_show=False):
        """Show dialog with options to install Ollama"""
        # Check if Ollama is installed only if not forced to show
        ollama_installed = False
        if not force_show:
            try:
                subprocess.run(
                    ["ollama", "--version"],
                    capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore'
                )
                ollama_installed = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                ollama_installed = False
        
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("Install Ollama")
        
        if force_show and not ollama_installed:
            # Check if it's actually installed when forced to show
            try:
                subprocess.run(
                    ["ollama", "--version"],
                    capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore'
                )
                ollama_installed = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                ollama_installed = False
        
        if ollama_installed and force_show:
            msg_box.setText("Ollama appears to be already installed on your system.")
            msg_box.setInformativeText("Would you like to visit the Ollama website anyway to check for updates or reinstall?")
        else:
            msg_box.setText("Ollama is not installed or not found in your system PATH.")
            msg_box.setInformativeText("Would you like to download Ollama from the official website?")
        
        # Add custom buttons
        download_button = msg_box.addButton("Download Ollama", QtWidgets.QMessageBox.ActionRole)
        cancel_button = msg_box.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
        
        # Apply theme to message box if in dark mode
        if self.dark_mode:
            msg_box.setStyleSheet(self.styleSheet())
        
        msg_box.exec_()
        
        if msg_box.clickedButton() == download_button:
            self.open_ollama_download_page()

    def open_ollama_download_page(self):
        """Open the Ollama download page in the default web browser"""
        try:
            webbrowser.open("https://ollama.com/download")
            QtWidgets.QMessageBox.information(
                self, 
                "Opening Browser", 
                "Opening the Ollama download page in your default web browser.\n\n"
                "After installing Ollama, restart this application to use it."
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to open web browser:\n{e}\n\n"
                "Please manually visit: https://ollama.com/download"
            )

    def open_website(self):
        """Open the TurkoKards website in the default web browser"""
        try:
            webbrowser.open("https://turkokards.com")
            QtWidgets.QMessageBox.information(
                self, 
                "Opening Website", 
                "Opening TurkoKards website in your default web browser."
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to open web browser:\n{e}\n\n"
                "Please manually visit: https://turkokards.com"
            )

    def open_contact(self):
        """Open email client with gary@turkokards.com"""
        try:
            webbrowser.open("mailto:gary@turkokards.com")
            QtWidgets.QMessageBox.information(
                self, 
                "Opening Email", 
                "Opening your default email client to contact gary@turkokards.com"
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to open email client:\n{e}\n\n"
                "Please manually email: gary@turkokards.com"
            )

    def open_ollama_library(self):
        """Open the Ollama library website in the default web browser"""
        try:
            webbrowser.open("https://ollama.com/library")
            QtWidgets.QMessageBox.information(
                self, 
                "Opening Ollama Library", 
                "Opening the Ollama model library in your default web browser.\n\n"
                "Browse available LLMs and copy the model name to install."
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to open web browser:\n{e}\n\n"
                "Please manually visit: https://ollama.com/library"
            )

    def update_ollama(self):
        """Update Ollama to the latest version"""
        # First check if Ollama is installed
        try:
            subprocess.run(
                ["ollama", "--version"],
                capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore'
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            QtWidgets.QMessageBox.warning(
                self,
                "Ollama Not Found",
                "Ollama is not installed or not found in your system PATH.\n\n"
                "Please install Ollama first using the 'Install Ollama' option."
            )
            return

        # Confirm the update
        reply = QtWidgets.QMessageBox.question(
            self,
            "Update Ollama",
            "This will update Ollama to the latest version.\n\n"
            "Do you want to continue?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            # Create progress dialog with percentage-based progress
            progress_dialog = QtWidgets.QProgressDialog("Updating Ollama, please wait...", None, 0, 100, self)
            progress_dialog.setWindowTitle("Updating Ollama")
            progress_dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            progress_dialog.setCancelButton(None)  # No cancel button
            progress_dialog.setMinimumDuration(0)  # Show immediately
            progress_dialog.setValue(0)  # Start at 0%
            if self.dark_mode:
                progress_dialog.setStyleSheet(self.styleSheet())
            progress_dialog.show()
            
            # Create and start worker thread
            self.worker = WorkerThread(["ollama", "update"], timeout=300)
            
            def on_progress_update(text):
                progress_dialog.setLabelText(text)
            
            def on_progress_percent_update(percent):
                progress_dialog.setValue(percent)
            
            def on_update_finished(result):
                # Immediately close progress dialog when update completes
                progress_dialog.close()
                
                if isinstance(result, Exception):
                    if isinstance(result, subprocess.TimeoutExpired):
                        QtWidgets.QMessageBox.critical(
                            self, "Update Timeout",
                            "The update process timed out. Please try again or update manually."
                        )
                    else:
                        QtWidgets.QMessageBox.critical(
                            self, "Update Error",
                            f"Failed to update Ollama:\n{result}\n\n"
                            "You may need to update Ollama manually."
                        )
                else:
                    if result.returncode == 0:
                        QtWidgets.QMessageBox.information(
                            self, "Update Complete",
                            "Ollama has been updated successfully!\n\n"
                            f"Output: {result.stdout.strip() if result.stdout.strip() else 'Update completed.'}"
                        )
                    else:
                        QtWidgets.QMessageBox.warning(
                            self, "Update Warning",
                            f"Update completed with warnings:\n\n{result.stderr.strip() if result.stderr.strip() else 'No error details available.'}"
                        )
            
            self.worker.progress.connect(on_progress_update)
            self.worker.progress_percent.connect(on_progress_percent_update)
            self.worker.finished.connect(on_update_finished)
            self.worker.start()

    def show_installed_popup(self):
        dialog = QtWidgets.QDialog(self)
        # Set the dialog size to 500x500 pixels
        dialog.resize(500, 500)
        dialog.setWindowTitle("Run Installed LLMs")
        vbox = QtWidgets.QVBoxLayout(dialog)

        # Apply theme to dialog
        if self.dark_mode:
            dialog.setStyleSheet(self.styleSheet())

        refresh_button = QtWidgets.QPushButton("Refresh LLM List")
        vbox.addWidget(refresh_button)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)

        def populate_llms():
            while scroll_layout.count():
                child = scroll_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            llms = self.get_installed_llms()
            if not llms:
                label = QtWidgets.QLabel("No LLMs found. Is Ollama installed?")
                scroll_layout.addWidget(label)
            else:
                for llm in llms:
                    btn = QtWidgets.QPushButton(f"Launch: {llm}")
                    btn.clicked.connect(lambda checked, name=llm: self.launch_llm(name))
                    scroll_layout.addWidget(btn)

        populate_llms()
        refresh_button.clicked.connect(populate_llms)

        scroll.setWidget(scroll_content)
        vbox.addWidget(scroll)
        dialog.exec_()

    def show_remove_popup(self):
        dialog = QtWidgets.QDialog(self)
        # Set the dialog size to 500x500 pixels
        dialog.resize(500, 500)
        dialog.setWindowTitle("Remove LLM")
        vbox = QtWidgets.QVBoxLayout(dialog)

        # Apply theme to dialog
        if self.dark_mode:
            dialog.setStyleSheet(self.styleSheet())

        refresh_button = QtWidgets.QPushButton("Refresh LLM List")
        vbox.addWidget(refresh_button)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)

        def populate_llms():
            while scroll_layout.count():
                child = scroll_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            llms = self.get_installed_llms()
            if not llms:
                label = QtWidgets.QLabel("No LLMs found. Is Ollama installed?")
                scroll_layout.addWidget(label)
            else:
                for llm in llms:
                    btn = QtWidgets.QPushButton(f"Remove: {llm}")
                    btn.clicked.connect(lambda checked, name=llm: self.remove_llm(name, dialog))
                    scroll_layout.addWidget(btn)

        populate_llms()
        refresh_button.clicked.connect(populate_llms)

        scroll.setWidget(scroll_content)
        vbox.addWidget(scroll)
        dialog.exec_()

    def show_reinstall_popup(self):
        dialog = QtWidgets.QDialog(self)
        # Set the dialog size to 500x500 pixels
        dialog.resize(500, 500)
        dialog.setWindowTitle("Reinstall LLMs")
        vbox = QtWidgets.QVBoxLayout(dialog)

        # Apply theme to dialog
        if self.dark_mode:
            dialog.setStyleSheet(self.styleSheet())

        refresh_button = QtWidgets.QPushButton("Refresh LLM List")
        vbox.addWidget(refresh_button)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)

        def populate_llms():
            while scroll_layout.count():
                child = scroll_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            llms = self.get_installed_llms()
            if not llms:
                label = QtWidgets.QLabel("No LLMs found. Is Ollama installed?")
                scroll_layout.addWidget(label)
            else:
                for llm in llms:
                    btn = QtWidgets.QPushButton(f"Reinstall: {llm}")
                    btn.clicked.connect(lambda checked, name=llm: self.reinstall_llm(name, dialog))
                    scroll_layout.addWidget(btn)

        populate_llms()
        refresh_button.clicked.connect(populate_llms)

        scroll.setWidget(scroll_content)
        vbox.addWidget(scroll)
        dialog.exec_()

    def show_install_popup(self):
        dialog = QtWidgets.QDialog(self)
        # Set the dialog size to 600x400 pixels
        dialog.resize(600, 400)
        dialog.setWindowTitle("Install New LLM")

        layout = QtWidgets.QVBoxLayout(dialog)

        # Apply theme to dialog
        if self.dark_mode:
            dialog.setStyleSheet(self.styleSheet())

        # Popular LLMs section
        popular_label = QtWidgets.QLabel("Popular LLMs (click to install):")
        layout.addWidget(popular_label)

        # Create scroll area for popular LLMs
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)

        # List of popular LLMs from ollama.com/library (smallest versions)
        popular_llms = [
            ("llama3.2:1b", "Meta Llama 3.2 1B - Latest compact Llama model"),
            ("llama3.1:8b", "Meta Llama 3.1 8B - Advanced reasoning"),
            ("llama3:8b", "Meta Llama 3 8B - General purpose"),
            ("llama2:7b", "Meta Llama 2 7B - Popular base model"),
            ("mistral:7b", "Mistral 7B - Fast and efficient"),
            ("mixtral:8x7b", "Mixtral 8x7B - Mixture of experts"),
            ("codellama:7b", "Code Llama 7B - Specialized for coding"),
            ("phi3:3.8b", "Microsoft Phi-3 3.8B - Compact and capable"),
            ("gemma:2b", "Google Gemma 2B - Lightweight"),
            ("qwen2:1.5b", "Alibaba Qwen2 1.5B - Multilingual model"),
            ("deepseek-coder:1.3b", "DeepSeek Coder 1.3B - Advanced coding model"),
            ("gpt-oss", "GPT-OSS - Open source GPT model"),
            ("nomic-embed-text", "Nomic Embed - Text embeddings"),
            ("all-minilm", "All MiniLM - Sentence embeddings"),
            ("neural-chat:7b", "Intel Neural Chat 7B - Conversational AI"),
            ("starling-lm:7b", "Starling LM 7B - RLHF trained model"),
            ("openchat:7b", "OpenChat 7B - Open source chat model"),
            ("vicuna:7b", "Vicuna 7B - Instruction following model"),
            ("orca-mini:3b", "Orca Mini 3B - Microsoft's compact model"),
            ("sqlcoder:7b", "SQLCoder 7B - SQL query generation")
        ]

        for llm_name, description in popular_llms:
            btn = QtWidgets.QPushButton(f"{llm_name} - {description}")
            btn.clicked.connect(lambda checked, name=llm_name: self.install_llm(name, dialog))
            scroll_layout.addWidget(btn)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Manual entry section
        manual_label = QtWidgets.QLabel("Or enter LLM name manually:")
        layout.addWidget(manual_label)

        self.llm_name_edit = QtWidgets.QLineEdit()
        self.llm_name_edit.setPlaceholderText("e.g., llama3:8b, mistral:7b-instruct")
        layout.addWidget(self.llm_name_edit)

        confirm_button = QtWidgets.QPushButton("Install Manual Entry")
        confirm_button.clicked.connect(lambda: self.install_llm(self.llm_name_edit.text(), dialog))
        layout.addWidget(confirm_button)

        dialog.exec_()

    def get_installed_llms(self):
        """Get list of installed LLMs with cross-platform subprocess handling"""
        try:
            # Use cross-platform subprocess settings
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, 
                text=True, 
                check=True, 
                encoding='utf-8', 
                errors='ignore',
                timeout=30  # Add timeout for better reliability
            )
            lines = result.stdout.strip().splitlines()
            if len(lines) < 2:
                return []
            llms = [line.split()[0] for line in lines[1:] if line.strip()]
            return llms
        except subprocess.TimeoutExpired:
            QtWidgets.QMessageBox.warning(
                self, "Timeout", 
                "Ollama list command timed out. Please check your Ollama installation."
            )
            return []
        except Exception as e:
            # More detailed error information for debugging
            QtWidgets.QMessageBox.warning(
                self, "Error", 
                f"Failed to get LLM list:\n{e}\n\nSystem: {platform.system()}"
            )
            return []

    def launch_llm(self, llm_name):
        """Launch LLM in a new terminal window across Windows, macOS, and Linux"""
        try:
            system = platform.system().lower()
            
            if system == 'windows':
                # Windows: Try different terminal options
                try:
                    # Try Windows Terminal first (modern Windows)
                    subprocess.Popen([
                        'wt.exe', 'cmd', '/k', f'ollama run {llm_name}'
                    ])
                except FileNotFoundError:
                    # Fallback to traditional cmd
                    subprocess.Popen([
                        'start', 'cmd', '/k', f'ollama run {llm_name}'
                    ], shell=True)
                    
            elif system == 'darwin':  # macOS
                # macOS: Use multiple approaches for better compatibility
                try:
                    # Try using osascript to open Terminal.app
                    subprocess.Popen([
                        'osascript', '-e',
                        f'tell application "Terminal" to do script "ollama run {llm_name}"'
                    ])
                except FileNotFoundError:
                    try:
                        # Alternative: Use open command with Terminal
                        script_content = f'#!/bin/bash\nollama run {llm_name}\necho "Press any key to close..."\nread -n 1'
                        subprocess.Popen([
                            'open', '-a', 'Terminal.app', '--args', 
                            'bash', '-c', script_content
                        ])
                    except FileNotFoundError:
                        # Final fallback for macOS
                        QtWidgets.QMessageBox.information(
                            self, "LLM Started", 
                            f"Starting {llm_name} in background.\nCheck your terminal for the ollama session."
                        )
                        subprocess.Popen(['ollama', 'run', llm_name])
                        
            elif system == 'linux':
                # Linux: Enhanced terminal detection with more options
                terminals = [
                    ('gnome-terminal', ['--', 'bash', '-c', f'ollama run {llm_name}; echo "Press Enter to close..."; read']),
                    ('konsole', ['-e', 'bash', '-c', f'ollama run {llm_name}; echo "Press Enter to close..."; read']),
                    ('xfce4-terminal', ['-e', 'bash', '-c', f'ollama run {llm_name}; echo "Press Enter to close..."; read']),
                    ('mate-terminal', ['-e', 'bash', '-c', f'ollama run {llm_name}; echo "Press Enter to close..."; read']),
                    ('lxterminal', ['-e', 'bash', '-c', f'ollama run {llm_name}; echo "Press Enter to close..."; read']),
                    ('xterm', ['-e', 'bash', '-c', f'ollama run {llm_name}; echo "Press Enter to close..."; read']),
                    ('x-terminal-emulator', ['-e', 'bash', '-c', f'ollama run {llm_name}; echo "Press Enter to close..."; read']),
                    ('terminator', ['-e', f'bash -c "ollama run {llm_name}; echo \\"Press Enter to close...\\"; read"']),
                    ('alacritty', ['-e', 'bash', '-c', f'ollama run {llm_name}; echo "Press Enter to close..."; read']),
                    ('kitty', ['-e', 'bash', '-c', f'ollama run {llm_name}; echo "Press Enter to close..."; read'])
                ]
                
                terminal_found = False
                for terminal, args in terminals:
                    try:
                        subprocess.Popen([terminal] + args)
                        terminal_found = True
                        break
                    except FileNotFoundError:
                        continue
                
                if not terminal_found:
                    # Final fallback for Linux
                    QtWidgets.QMessageBox.information(
                        self, "LLM Started", 
                        f"Starting {llm_name} in background.\nNo GUI terminal found. Check your terminal for the ollama session."
                    )
                    subprocess.Popen(['ollama', 'run', llm_name])
                    
            else:
                # Unknown/Other systems (BSD, etc.)
                QtWidgets.QMessageBox.information(
                    self, "LLM Started", 
                    f"Starting {llm_name} in background.\nPlatform: {platform.system()}.\nCheck your terminal for the ollama session."
                )
                subprocess.Popen(['ollama', 'run', llm_name])
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", 
                f"Failed to launch {llm_name}:\n{e}\n\nSystem: {platform.system()}\nPlatform: {platform.platform()}"
            )

    def remove_llm(self, llm_name, dialog):
        """Remove LLM with cross-platform subprocess handling"""
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Remove",
            f"Are you sure you want to remove {llm_name}?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                result = subprocess.run(
                    ["ollama", "rm", llm_name],
                    capture_output=True, 
                    text=True, 
                    check=True, 
                    encoding='utf-8', 
                    errors='ignore',
                    timeout=300  # 5 minute timeout
                )
                QtWidgets.QMessageBox.information(self, "Removed", f"{llm_name} removed successfully.")
                dialog.close()
            except subprocess.TimeoutExpired:
                QtWidgets.QMessageBox.critical(
                    self, "Timeout", 
                    f"Remove operation for {llm_name} timed out."
                )
            except subprocess.CalledProcessError as e:
                QtWidgets.QMessageBox.critical(
                    self, "Error", 
                    f"Failed to remove {llm_name}:\n{e.stderr if e.stderr else str(e)}\n\nSystem: {platform.system()}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Error", 
                    f"Failed to remove {llm_name}:\n{e}\n\nSystem: {platform.system()}"
                )

    def reinstall_llm(self, llm_name, dialog):
        """Reinstall LLM with cross-platform subprocess handling"""
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Reinstall",
            f"Are you sure you want to reinstall {llm_name}?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            # Create progress dialog with percentage-based progress
            progress_dialog = QtWidgets.QProgressDialog(f"Reinstalling {llm_name}, please wait...", None, 0, 100, self)
            progress_dialog.setWindowTitle("Reinstalling LLM")
            progress_dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            progress_dialog.setCancelButton(None)  # No cancel button
            progress_dialog.setMinimumDuration(0)  # Show immediately
            progress_dialog.setValue(0)  # Start at 0%
            if self.dark_mode:
                progress_dialog.setStyleSheet(self.styleSheet())
            progress_dialog.show()
            
            # Create and start worker thread
            self.reinstall_worker = ReinstallWorkerThread(llm_name)
            
            def on_progress_update(text):
                progress_dialog.setLabelText(text)
            
            def on_progress_percent_update(percent):
                progress_dialog.setValue(percent)
            
            def on_reinstall_finished(success, result):
                # Immediately close progress dialog when reinstall completes
                progress_dialog.close()
                
                if success:
                    QtWidgets.QMessageBox.information(self, "Reinstalled", f"{llm_name} reinstalled successfully.")
                    dialog.close()
                else:
                    if isinstance(result, subprocess.TimeoutExpired):
                        QtWidgets.QMessageBox.critical(
                            self, "Timeout", 
                            f"Reinstall operation for {llm_name} timed out."
                        )
                    elif isinstance(result, subprocess.CalledProcessError):
                        QtWidgets.QMessageBox.critical(
                            self, "Error", 
                            f"Failed to reinstall {llm_name}:\n{result.stderr if result.stderr else str(result)}\n\nSystem: {platform.system()}"
                        )
                    else:
                        QtWidgets.QMessageBox.critical(
                            self, "Error", 
                            f"Failed to reinstall {llm_name}:\n{result}\n\nSystem: {platform.system()}"
                        )
            
            self.reinstall_worker.progress.connect(on_progress_update)
            self.reinstall_worker.progress_percent.connect(on_progress_percent_update)
            self.reinstall_worker.finished.connect(on_reinstall_finished)
            self.reinstall_worker.start()

    def install_llm(self, llm_name, dialog):
        """Install LLM with cross-platform subprocess handling"""
        if not llm_name or not llm_name.strip():
            QtWidgets.QMessageBox.warning(self, "Invalid Input", "Please enter a valid LLM name.")
            return
            
        llm_name = llm_name.strip()
        
        # Create progress dialog with percentage-based progress
        progress_dialog = QtWidgets.QProgressDialog(
            f"Installing {llm_name}, please wait...\nThis may take several minutes for large models.", 
            None, 0, 100, self
        )
        progress_dialog.setWindowTitle("Installing LLM")
        progress_dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        progress_dialog.setCancelButton(None)  # No cancel button
        progress_dialog.setMinimumDuration(0)  # Show immediately
        progress_dialog.setValue(0)  # Start at 0%
        if self.dark_mode:
            progress_dialog.setStyleSheet(self.styleSheet())
        progress_dialog.show()
        
        # Create and start worker thread
        self.install_worker = InstallWorkerThread(llm_name)
        
        def on_progress_update(text):
            progress_dialog.setLabelText(text)
        
        def on_progress_percent_update(percent):
            progress_dialog.setValue(percent)
        
        def on_install_finished(success, result):
            # Immediately close progress dialog when installation completes
            progress_dialog.close()
            
            if success:
                output_text = result.stdout.strip() if result.stdout.strip() else 'Installation completed.'
                QtWidgets.QMessageBox.information(
                    self, "Installed", 
                    f"{llm_name} installed successfully!\n\nOutput: {output_text}"
                )
                dialog.close()
            else:
                if isinstance(result, subprocess.TimeoutExpired):
                    QtWidgets.QMessageBox.critical(
                        self, "Timeout", 
                        f"Installation of {llm_name} timed out.\nLarge models may take longer than expected."
                    )
                elif isinstance(result, subprocess.CalledProcessError):
                    error_msg = result.stderr.strip() if result.stderr and result.stderr.strip() else str(result)
                    QtWidgets.QMessageBox.critical(
                        self, "Installation Error", 
                        f"Failed to install {llm_name}:\n{error_msg}\n\nSystem: {platform.system()}\n\nPlease check:\n• Internet connection\n• LLM name spelling\n• Available disk space"
                    )
                else:
                    QtWidgets.QMessageBox.critical(
                        self, "Error", 
                        f"Failed to install {llm_name}:\n{result}\n\nSystem: {platform.system()}"
                    )
        
        self.install_worker.progress.connect(on_progress_update)
        self.install_worker.progress_percent.connect(on_progress_percent_update)
        self.install_worker.finished.connect(on_install_finished)
        self.install_worker.start()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = OllamaLauncher()
    window.show()
    sys.exit(app.exec_())