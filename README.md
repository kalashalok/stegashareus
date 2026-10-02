# Stegashaurus 🦕

**Covert, Loss-Resistant Seed Phrase Storage in Plain Sight**  
*Submitted as an open-source project for the Bitcoin Open Source Hackathon.*

---

## 📽️ Demo Video
[https://drive.google.com/file/d/1C3ARVHtvL419wF8rcBAvzRb4032TMSQv/view?usp=sharing] 

* Kindly download the video for better quality.

---

## 👥 Team Members
* **Alok** (Solo Contributor)

---

## 💡 What Problem It Solves

Storing cryptographic seed phrases (such as 24-word BIP-39 lists) on paper, metal plates, or unencrypted text files leaves users vulnerable to physical theft, targeted searches, and social engineering.

While standard file encryption protects payload contents, the existence of an encrypted file container alerts an attacker that valuable assets exist. Traditional steganography tools attempt to hide data within fine image details (such as LSB modifications or EXIF metadata), but these are instantly wiped when processed by messaging app pipelines (e.g., WhatsApp, Signal, Discord).

**Stegashaurus** solves this by embedding encrypted data directly across spatial macro-blocks ($8 \times 8$ pixel regions) using robust error correction, enabling hidden payloads to survive lossy social media re-compression while maintaining full plausible deniability.

---

## 🛠️ Architecture & Technical Approach

### 1. Cryptographic Framing & Security
* **Key Derivation:** Uses `PBKDF2-HMAC-SHA256` with 100,000 iterations and a unique salt to derive an AES-256 key alongside a deterministic CSPRNG seed.
* **Payload Encryption:** Payload text is encrypted using `AES-256-GCM` with a 96-bit random nonce for authenticated privacy and integrity.
* **Plausible Deniability:** The extraction engine uses uniform execution paths. Attempting to extract data from a standard JPEG or using an incorrect passphrase produces identical error outputs ("*Error: Could not extract any valid data with that passphrase*"), rendering stego images indistinguishable from plain photos under interrogation.

### 2. Loss-Resilient Spatial QIM Engine
* **Spatial Macro-Block Encoding:** Data is encoded into the mean luminance ($Y$-channel in YCrCb color space) of $8 \times 8$ macro-blocks rather than individual pixels.
* **Fixed-Step Quantization Index Modulation (QIM):** Uses a deterministic micro-step ($\Delta = 4.0$) to modulate luminance averages into even/odd parity grids.
* **Reed-Solomon Error Correction (ECC):** Incorporates 32 parity bytes of Reed-Solomon encoding, allowing full payload recovery even if up to 16 bytes of spatial data are corrupted during lossy compression.
* **Deterministic CSPRNG Shuffling:** An `AES-256-CTR` CSPRNG deterministically shuffles block access patterns using a passphrase-derived seed, preventing localized data cluster detection.
* **Automatic Pre-Resizing Guard:** Automatically resizes incoming high-resolution images ($\le 1600\text{px}$) prior to embedding to eliminate app-side spatial downsampling.

---

## ⚖️ Engineering Trade-Offs & Known Limitations

An honest evaluation of engineering trade-offs made during development:

### 1. Reverting from Passphrase-Keyed Offsets to Fixed-Step QIM
* **The Trade-Off:** During prototyping, an experimental implementation using passphrase-keyed pseudorandom block offsets ($r_i$) was developed to eliminate the statistical modulo signature detectable under statistical steganalysis.
* **The Finding:** While keyed offsets successfully masked the steganalysis signature, they drastically reduced compression tolerance. Under aggressive JPEG re-encoding on Signal and WhatsApp, variable decision margins caused bit error rates that exceeded Reed-Solomon correction thresholds.
* **The Resolution:** For the production submission, fixed-step QIM ($\Delta = 4.0$) was chosen to ensure reliable real-world performance over messaging platforms. The modulo signature trade-off is documented as a known characteristic of high-resilience spatial steganography.

### 2. Platform Pipeline Constraints
* **Grid Alignment Sensitivity:** Spatial QIM relies on standard $8 \times 8$ block alignment. Platform transformations that introduce pixel-level canvas cropping or padding can desynchronize the extraction grid.
* **High-Frequency & Clipped Textures:** Images with extreme high-frequency noise (e.g., dense grass) or clipped luminance values ($0$ or $255$) can suffer localized bit shifts during aggressive JPEG quantization. Natural, well-lit photographs provide the highest survival rates.

### 3. Future Work
* Transitioning from spatial domain embedding to **2D-DCT (Discrete Cosine Transform) frequency domain modulation** to achieve grid-shift invariant alignment.

---

## ⚙️ Installation & Clean-Machine Setup

Follow these instructions to install and run Stegashaurus on a fresh Debian/Ubuntu/Linux Mint system.

## Installation

### Option 1: 1-Click Installation (Debian / Ubuntu / Linux Mint)

Download the latest `.deb` package from the [Releases](https://github.com/kalashalok/stegashaurus/releases) page and install it using `apt`:

```bash
sudo apt update
sudo apt install ./robust-stego-app.deb
stegashaurus
```


### Option B: Build & Run from Source (Cross-Platform: Windows, macOS, Linux)
Prerequisites

 * Python 3.10+

 * OpenCV & System Qt6 libraries

```bash
# 1. Clone the repository
git clone https://github.com/kalashalok/stegashaurus.git
cd stegashaurus

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the PyQt6 application GUI
python3 src/gui.py
```
## 🧪 How to Exercise (Happy Path Test)

1. **Launch the Application:** Open Stegashaurus using `stegashaurus` or `python3 src/gui.py`.
2. **Embed Payload:**
   * Select a standard photo (`.jpg`).
   * Enter your 24-word BIP-39 seed phrase in the payload field.
   * Enter a strong passphrase and click **Embed & Save**.
3. **Transmit Over Messaging Apps:**
   * Send the output JPEG image over **WhatsApp** or **Signal** (standard photo attachment).
   * Download the received photo on the destination device.
4. **Extract Payload:**
   * Load the downloaded image into Stegashaurus under the **Extract** tab.
   * Enter the passphrase used during embedding and click **Extract Data**.
   * The seed phrase will decrypt and display cleanly.

---

## 🛠️ Tech Stack & Dependencies

* **Language / GUI:** Python 3, PyQt6
* **Cryptography:** `cryptography` (AES-256-GCM, PBKDF2-HMAC-SHA256)
* **Image Engine:** `opencv-python`, `numpy`
* **Error Correction:** `reedsolo` (Reed-Solomon ECC)
* **Packaging:** Debian `.deb` build tools (`dpkg-deb`)
