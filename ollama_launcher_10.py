import sys
import subprocess
import configparser
import os
import webbrowser
from PyQt5 import QtWidgets

class OllamaLauncher(QtWidgets.QMainWindow):
    CONFIG_FILE = ".ollama_launcher_config"
    
    def __init__(self):
        super().__init__()
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
            """
            self.setStyleSheet(dark_style)
        else:
            # Light mode (default)
            self.setStyleSheet("")

    def show_about_dialog(self):
        QtWidgets.QMessageBox.about(
            self, 
            "About Ollama Launcher", 
            "Ollama Launcher GUI\nVersion 0.0.9\nBy Gary Robert Turcotte\n2025\nReleased under GPL 3.0"
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
            try:
                # Show progress message
                progress_msg = QtWidgets.QMessageBox(self)
                progress_msg.setWindowTitle("Updating Ollama")
                progress_msg.setText("Updating Ollama, please wait...")
                progress_msg.setStandardButtons(QtWidgets.QMessageBox.NoButton)
                if self.dark_mode:
                    progress_msg.setStyleSheet(self.styleSheet())
                progress_msg.show()
                
                # Process events to show the message
                QtWidgets.QApplication.processEvents()
                
                # Run the update command
                result = subprocess.run(
                    ["ollama", "update"],
                    capture_output=True, text=True, timeout=300, encoding='utf-8', errors='ignore'  # 5 minute timeout
                )
                
                progress_msg.close()
                
                if result.returncode == 0:
                    QtWidgets.QMessageBox.information(
                        self,
                        "Update Complete",
                        "Ollama has been updated successfully!\n\n"
                        f"Output: {result.stdout.strip() if result.stdout.strip() else 'Update completed.'}"
                    )
                else:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Update Warning",
                        f"Update completed with warnings:\n\n{result.stderr.strip() if result.stderr.strip() else 'No error details available.'}"
                    )
                    
            except subprocess.TimeoutExpired:
                progress_msg.close()
                QtWidgets.QMessageBox.critical(
                    self,
                    "Update Timeout",
                    "The update process timed out. Please try again or update manually."
                )
            except Exception as e:
                progress_msg.close()
                QtWidgets.QMessageBox.critical(
                    self,
                    "Update Error",
                    f"Failed to update Ollama:\n{e}\n\n"
                    "You may need to update Ollama manually."
                )

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
            ("wizard-coder:7b", "WizardCoder 7B - Code generation specialist"),
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
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore'
            )
            lines = result.stdout.strip().splitlines()
            if len(lines) < 2:
                return []
            llms = [line.split()[0] for line in lines[1:] if line.strip()]
            return llms
        except Exception:
            return []

    def launch_llm(self, llm_name):
        try:
            subprocess.Popen(
                ['start', 'cmd', '/k', f'ollama run {llm_name}'],
                shell=True
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to launch {llm_name}:\n{e}")

    def remove_llm(self, llm_name, dialog):
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Remove",
            f"Are you sure you want to remove {llm_name}?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                subprocess.run(
                    ["ollama", "rm", llm_name],
                    capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore'
                )
                QtWidgets.QMessageBox.information(self, "Removed", f"{llm_name} removed.")
                dialog.close()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to remove {llm_name}:\n{e}")

    def reinstall_llm(self, llm_name, dialog):
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Reinstall",
            f"Are you sure you want to reinstall {llm_name}?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                # First remove the LLM
                subprocess.run(
                    ["ollama", "rm", llm_name],
                    capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore'
                )

                # Then pull and install it again
                subprocess.run(
                    ["ollama", "pull", llm_name],
                    capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore'
                )
                QtWidgets.QMessageBox.information(self, "Reinstalled", f"{llm_name} reinstalled.")
                dialog.close()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to reinstall {llm_name}:\n{e}")

    def install_llm(self, llm_name, dialog):
        try:
            subprocess.run(
                ["ollama", "pull", llm_name],
                capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore'
            )
            QtWidgets.QMessageBox.information(self, "Installed", f"{llm_name} installed.")
            dialog.close()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to install {llm_name}:\n{e}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = OllamaLauncher()
    window.show()
    sys.exit(app.exec_())