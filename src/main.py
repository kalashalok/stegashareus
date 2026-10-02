import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout,
    QHBoxLayout, QLineEdit, QPushButton, QFileDialog,
    QProgressBar, QMessageBox, QTextEdit, QCheckBox
)
from PyQt6.QtCore import QThread, pyqtSignal

import core


class EmbedWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, src_img, payload_text, passphrase, out_img):
        super().__init__()
        self.src_img = src_img
        self.payload_text = payload_text
        self.passphrase = passphrase
        self.out_img = out_img

    def run(self):
        try:
            core.embed_data(self.src_img, self.payload_text, self.passphrase, self.out_img)
            self.finished.emit(True, "Seed phrase embedded into spatial macro-blocks successfully!")
        except Exception as e:
            self.finished.emit(False, str(e))


class ExtractWorker(QThread):
    finished = pyqtSignal(bool, str, str)

    def __init__(self, stego_img, passphrase):
        super().__init__()
        self.stego_img = stego_img
        self.passphrase = passphrase

    def run(self):
        try:
            extracted_text = core.extract_data(self.stego_img, self.passphrase)
            self.finished.emit(True, extracted_text, "Extraction complete!")
        except core.StegoError as se:
            self.finished.emit(False, "", str(se))
        except Exception:
            self.finished.emit(False, "", "Error: Could not extract any valid data with that passphrase")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spatial Steganography Tool (Seed Phrase Edition)")
        self.setGeometry(100, 100, 600, 520)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.init_embed_tab()
        self.init_extract_tab()

    def init_embed_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Cover Image Selection
        h1 = QHBoxLayout()
        self.embed_img_input = QLineEdit()
        self.embed_img_input.setPlaceholderText("Select Cover JPEG Image...")
        btn_browse_img = QPushButton("Browse")
        btn_browse_img.clicked.connect(lambda: self.browse_file(self.embed_img_input, "JPEG Images (*.jpg *.jpeg)"))
        h1.addWidget(self.embed_img_input)
        h1.addWidget(btn_browse_img)
        layout.addLayout(h1)

        # Seed Phrase Input
        self.payload_input = QTextEdit()
        self.payload_input.setPlaceholderText("Enter 24-Word Seed Phrase or Short Text Payload...")
        self.payload_input.setMaximumHeight(100)
        layout.addWidget(self.payload_input)

        # Output File Destination Selection
        h3 = QHBoxLayout()
        self.embed_out_input = QLineEdit()
        self.embed_out_input.setPlaceholderText("Select Output Stego Image Destination (e.g., stego_image.jpg)...")
        btn_browse_out = QPushButton("Browse")
        btn_browse_out.clicked.connect(lambda: self.save_file(self.embed_out_input, "JPEG Images (*.jpg)"))
        h3.addWidget(self.embed_out_input)
        h3.addWidget(btn_browse_out)
        layout.addLayout(h3)

        # Passphrase Input & Visibility Toggle
        h_pass = QHBoxLayout()
        self.embed_pass = QLineEdit()
        self.embed_pass.setPlaceholderText("Enter Encryption Passphrase")
        self.embed_pass.setEchoMode(QLineEdit.EchoMode.Password)
        
        chk_show_pass = QCheckBox("Show Passphrase")
        chk_show_pass.toggled.connect(lambda checked: self.toggle_pass_visibility(self.embed_pass, checked))
        
        h_pass.addWidget(self.embed_pass)
        h_pass.addWidget(chk_show_pass)
        layout.addLayout(h_pass)

        # Progress Bar (Hidden by default until active)
        self.embed_progress = QProgressBar()
        self.embed_progress.setTextVisible(False)
        self.embed_progress.setVisible(False)
        layout.addWidget(self.embed_progress)

        btn_embed = QPushButton("Embed & Encrypt Data")
        btn_embed.clicked.connect(self.run_embed)
        layout.addWidget(btn_embed)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Embed Seed Phrase")

    def init_extract_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Target Image Selection
        h1 = QHBoxLayout()
        self.ext_img_input = QLineEdit()
        self.ext_img_input.setPlaceholderText("Select Target JPEG Image...")
        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(lambda: self.browse_file(self.ext_img_input, "JPEG Images (*.jpg *.jpeg)"))
        h1.addWidget(self.ext_img_input)
        h1.addWidget(btn_browse)
        layout.addLayout(h1)

        # Passphrase Input & Visibility Toggle
        h_pass = QHBoxLayout()
        self.ext_pass = QLineEdit()
        self.ext_pass.setPlaceholderText("Enter Decryption Passphrase")
        self.ext_pass.setEchoMode(QLineEdit.EchoMode.Password)

        chk_show_pass = QCheckBox("Show Passphrase")
        chk_show_pass.toggled.connect(lambda checked: self.toggle_pass_visibility(self.ext_pass, checked))

        h_pass.addWidget(self.ext_pass)
        h_pass.addWidget(chk_show_pass)
        layout.addLayout(h_pass)

        # Progress Bar (Hidden by default until active)
        self.ext_progress = QProgressBar()
        self.ext_progress.setTextVisible(False)
        self.ext_progress.setVisible(False)
        layout.addWidget(self.ext_progress)

        btn_extract = QPushButton("Decrypt & Extract Seed Phrase")
        btn_extract.clicked.connect(self.run_extract)
        layout.addWidget(btn_extract)

        self.ext_output_preview = QTextEdit()
        self.ext_output_preview.setReadOnly(True)
        self.ext_output_preview.setPlaceholderText("Extracted seed phrase will appear here...")
        layout.addWidget(self.ext_output_preview)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Extract Seed Phrase")

    def toggle_pass_visibility(self, line_edit, checked):
        if checked:
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def browse_file(self, target_widget, file_filter):
        filename, _ = QFileDialog.getOpenFileName(self, "Select File", "", file_filter)
        if filename:
            target_widget.setText(filename)

    def save_file(self, target_widget, file_filter):
        filename, _ = QFileDialog.getSaveFileName(self, "Save File As", "stego_output.jpg", file_filter)
        if filename:
            target_widget.setText(filename)

    def run_embed(self):
        src = self.embed_img_input.text().strip()
        payload = self.payload_input.toPlainText().strip()
        out = self.embed_out_input.text().strip()
        pwd = self.embed_pass.text()

        if not (src and payload and out and pwd):
            QMessageBox.warning(self, "Input Error", "All fields and passphrase are required.")
            return

        self.embed_progress.setVisible(True)
        self.embed_progress.setRange(0, 0)
        self.worker = EmbedWorker(src, payload, pwd, out)
        self.worker.finished.connect(self.on_embed_finished)
        self.worker.start()

    def on_embed_finished(self, success, message):
        self.embed_progress.setVisible(False)
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", f"Embedding failed: {message}")

    def run_extract(self):
        src = self.ext_img_input.text().strip()
        pwd = self.ext_pass.text()

        if not (src and pwd):
            QMessageBox.warning(self, "Input Error", "Image file and passphrase are required.")
            return

        self.ext_progress.setVisible(True)
        self.ext_progress.setRange(0, 0)
        self.worker = ExtractWorker(src, pwd)
        self.worker.finished.connect(self.on_extract_finished)
        self.worker.start()

    def on_extract_finished(self, success, text, message):
        self.ext_progress.setVisible(False)
        if success:
            self.ext_output_preview.setText(text)
            QMessageBox.information(self, "Status", "Extraction process complete.")
        else:
            self.ext_output_preview.clear()
            QMessageBox.critical(self, "Extraction Error", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
