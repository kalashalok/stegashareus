# Stegashaurus 🦕

> **Covert, Loss-Resistant Seed Phrase Storage in Plain Sight**

**Stegashaurus** is an open-source, anti-forensic steganography desktop application designed to hide sensitive cryptographic payloads—such as 24-word Bitcoin BIP-39 seed phrases—inside standard JPEG images. 

Unlike traditional steganography tools that break when an image is uploaded to social media or messaging apps, Stegashaurus uses **spatial macro-block encoding** and **heavy Reed-Solomon error correction** to ensure hidden data can survive lossy chat app re-compression (e.g., Discord, WhatsApp) while maintaining full plausible deniability.

---

## 💡 Why Stegashaurus?

Storing seed phrases on paper, metal plates, or unencrypted local files leaves them vulnerable to physical theft, targeted searches, and social engineering. 

While encrypting files helps, the presence of an encrypted container itself signals to an attacker that valuable data exists (**the target problem**). Stegashaurus solves this by making your backup look like a completely normal, uninteresting photograph.

---

## 🛠️ What Problem It Solves

1. **Destructive Chat Compression:** Standard steganography embeds data in fine image details (like EXIF metadata or single-pixel LSBs) that are wiped instantly by image processing pipelines. Stegashaurus embeds data across large spatial pixel regions ($32 \times 32$ macro-tiles) to survive automated re-encoding.
2. **Predictable Randomness:** Uses an **AES-256-CTR CSPRNG** seeded via **PBKDF2-HMAC-SHA256 (600k iterations)** to randomize tile layout, preventing statistical detection and key prediction.
3. **Plausible Deniability:** The application maintains uniform extraction behavior. Attempting to extract data from a normal, plain JPEG yields the **exact same error message** as entering the wrong passphrase on an actual encrypted stego image. An observer cannot prove a file contains hidden data.

---

## 🎯 Practical Applications

* **Emergency Recovery:** Store a backup of your 24-word seed phrase in plain sight within a family photo sent over messaging apps or stored in cloud galleries.
* **Borders & Asset Protection:** Cross high-risk checkpoints or travel without carrying physical metal/paper seed backups or obvious encrypted containers.
* **Coercion Resistance:** Because a non-stego image and a wrong passphrase produce identical outputs, you retain complete deniability under inspection.

---

## 🚦 Project Status

*This repository is currently an active submission for the Bitcoin Open Source Hackathon. The implementation is in active development.*

### Tech Stack
* **Language / GUI:** Python 3, PyQt6
* **Cryptography:** AES-256-GCM, PBKDF2-HMAC-SHA256
* **Steganography Engine:** OpenCV, NumPy, Reed-Solomon (ECC)
* **Target OS:** Linux Mint / Debian / Ubuntu (`.deb` package release planned)

---

## 📜 License
MIT License
