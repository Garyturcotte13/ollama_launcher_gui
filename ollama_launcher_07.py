import sys
import subprocess
from PyQt5 import QtWidgets

class OllamaLauncher(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ollama LLM Launcher")
        # Set the main window size to 666x120 pixels
        self.resize(666, 120)
        self.layout = QtWidgets.QVBoxLayout(self)

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

    def show_installed_popup(self):
        dialog = QtWidgets.QDialog(self)
        # Set the dialog size to 500x500 pixels
        dialog.resize(500, 500)
        dialog.setWindowTitle("Run Installed LLMs")
        vbox = QtWidgets.QVBoxLayout(dialog)

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