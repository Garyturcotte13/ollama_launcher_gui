import sys
import subprocess
import configparser
import os
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

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # View menu
        view_menu = menu_bar.addMenu('View')
        dark_mode_action = view_menu.addAction('Toggle Dark Mode')
        dark_mode_action.triggered.connect(self.toggle_dark_mode)
        
        # Help menu
        help_menu = menu_bar.addMenu('Help')
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
            "Ollama Launcher GUI\nVersion 0.0.8\nBy Gary Robert Turcotte\n2025\nReleased under GPL 3.0"
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
        # Set the dialog size to 500x200 pixels
        dialog.resize(500, 200)
        dialog.setWindowTitle("Install New LLM")

        layout = QtWidgets.QVBoxLayout(dialog)

        # Apply theme to dialog
        if self.dark_mode:
            dialog.setStyleSheet(self.styleSheet())

        label = QtWidgets.QLabel("Enter the name of the LLM you want to install:")
        layout.addWidget(label)

        self.llm_name_edit = QtWidgets.QLineEdit()
        layout.addWidget(self.llm_name_edit)

        confirm_button = QtWidgets.QPushButton("Install")
        confirm_button.clicked.connect(lambda: self.install_llm(self.llm_name_edit.text(), dialog))
        layout.addWidget(confirm_button)

        dialog.exec_()

    def get_installed_llms(self):
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, check=True
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
                    capture_output=True, text=True, check=True
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
                    capture_output=True, text=True, check=True
                )

                # Then pull and install it again
                subprocess.run(
                    ["ollama", "pull", llm_name],
                    capture_output=True, text=True, check=True
                )
                QtWidgets.QMessageBox.information(self, "Reinstalled", f"{llm_name} reinstalled.")
                dialog.close()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to reinstall {llm_name}:\n{e}")

    def install_llm(self, llm_name, dialog):
        try:
            subprocess.run(
                ["ollama", "pull", llm_name],
                capture_output=True, text=True, check=True
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