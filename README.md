# Stegashareus 🦕

**Covert, Loss-Resistant Seed Phrase Storage in Plain Sight**  
*Submitted as an open-source project for the Boss Battle Hackathon.*

---

## 📽️ Demo Video
[https://drive.google.com/file/d/1C3ARVHtvL419wF8rcBAvzRb4032TMSQv/view?usp=sharing] 

* Kindly download the video for better quality.

---

## 👥 Team Members
* **Alok** (Solo Contributor)

---

## 💡 Why Stegashareus? (Problem & Solution)

### The Problem: Your Life Savings in a "Transparent Safe"

Bitcoin gives individuals complete financial sovereignty, but managing seed phrases (24-word BIP-39 lists) remains a critical single point of failure. Traditional backup methods create distinct, identifiable targets:

* **Paper & Metal Backups:** Leaving a steel plate or paper seed backup in your home is the digital equivalent of putting your entire life savings inside a safe with a transparent door, placed right in your living room with a sign that says *"Valuable items inside, please break in."*
* **Standard File Encryption:** Encrypting a file on your computer or cloud storage protects the contents, but the encrypted container itself signals to an observer or intruder that high-value assets exist. 
* **Physical & Political Vulnerability:** History repeatedly shows that during geopolitical turmoil, banking collapses, or sudden forced displacement, people are forced to flee with nothing but the clothes on their backs. Carrying physical seed plates through checkpoints, borders, or hostile territory invites confiscation, extortion, or physical coercion.

Relying on memory alone is fragile. Relying on conspicuous physical backups leaves you exposed.

---

### The Solution: Plausible Deniability & Loss-Resistant Steganography

**Stegashareus** transforms ordinary digital photos into covert, resilient vaults for your critical cryptographic keys.

#### 1. Hide in Plain Sight (Plausible Deniability)
Instead of creating a suspicious encrypted archive, Stegashareus embeds your encrypted seed phrase directly into the spatial pixel matrix ($8 \times 8$ macro-blocks) of a standard JPEG. To any observer, inspector, or automated system, your backup looks like an ordinary vacation photo or family portrait sitting peacefully in your photo album.

#### 2. Decentralized, Borderless Cloud Backups
Because Stegashareus uses custom spatial embedding combined with Reed-Solomon Error Correction (ECC), your stego-images survive the lossy JPEG re-compression applied by messaging platforms and cloud storage pipelines (WhatsApp, Signal, Telegram, Discord, Google Photos etc.). You can upload a photo to a public channel or message it to yourself as a passive, redundant backup available anywhere in the world.

#### 3. Absolute Uniformity Against Interrogation
Extracting data requires both the image and the correct passphrase. The extraction engine executes identical logic across all runs: attempting to extract data from a plain, unaltered JPEG or using an incorrect passphrase returns an identical, generic error output (`"Error: Could not extract any valid data with that passphrase"`). There are no mathematical artifacts or structural cues left behind to prove a payload even exists.

> **In a world where digital assets grow more valuable by the day, storing them carelessly carries catastrophic risk. Stegashareus ensures your sovereignty remains truly private, portable, and undeniable.**

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

Follow these instructions to install and run Stegashareus on a fresh Debian/Ubuntu/Linux Mint system.

## Installation

### Option 1: 1-Click Installation (Debian / Ubuntu / Linux Mint)

Download the latest `.deb` package from the [Releases](https://github.com/kalashalok/stegashareus/releases) page and install it using `apt`:

```bash
sudo apt update
sudo apt install ./robust-stego-app.deb
stegashareus
```


### Option B: Build & Run from Source (Cross-Platform: Windows, macOS, Linux)
Prerequisites

 * Python 3.10+

 * OpenCV & System Qt6 libraries

```bash
# 1. Clone the repository
git clone https://github.com/kalashalok/stegashareus.git
cd stegashareus

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the PyQt6 application GUI
python3 src/main.py
```
## 🧪 How to Exercise (Happy Path Test)

1. **Launch the Application:** Open Stegashareus using `stegashareus` or `python3 src/main.py`.
2. **Embed Payload:**
   * Select a standard photo (`.jpg`).
   * Enter your 24-word BIP-39 seed phrase in the payload field.
   * Enter a strong passphrase and click **Embed & Save**.
3. **Transmit Over Messaging Apps:**
   * Send the output JPEG image over **WhatsApp** or **Signal** (standard photo attachment).
   * Download the received photo on the destination device.
4. **Extract Payload:**
   * Load the downloaded image into Stegashareus under the **Extract** tab.
   * Enter the passphrase used during embedding and click **Extract Data**.
   * The seed phrase will decrypt and display cleanly.

---

## 🛠️ Tech Stack & Dependencies

* **Language / GUI:** Python 3, PyQt6
* **Cryptography:** `cryptography` (AES-256-GCM, PBKDF2-HMAC-SHA256)
* **Image Engine:** `opencv-python`, `numpy`
* **Error Correction:** `reedsolo` (Reed-Solomon ECC)
* **Packaging:** Debian `.deb` build tools (`dpkg-deb`)
