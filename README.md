# OpenCore Legacy Patcher-Mod (OCLP-Mod)

[![CI Build](https://github.com)](https://github.com)

**OpenCore Legacy Patcher-Mod** is a customized distribution built on top of the advanced [bOOtOx OpenCore Legacy Patcher layout](https://github.com). This fork utilizes optimized automated build pipelines and integrated `opencore.pkg` workflows to deliver a streamlined patcher experience for unsupported Mac hardware.

---

## ✨ Features & Enhancements

Unlike the standard upstream branch, **OCLP-Mod** benefits from:
* **Pre-Built Package Workflows:** Uses bOOtOx's structural layout to bundle required `opencore.pkg` and native binary payload files smoothly.
* **Failure-Free Compiles:** Out-of-the-box support for automated building via GitHub Actions with no hidden signature roadblocks.
* **Custom Branding:** Formatted explicitly under the *OpenCore Legacy Patcher-Mod* naming scheme.

---

## 🚀 Getting Started & Downloads

### Downloading the Pre-Built App
1. Go to the **Actions** tab of this repository.
2. Select the latest successful workflow run from the sidebar.
3. Scroll down to the **Artifacts** section at the bottom of the page to download your compiled zip file bundle.

### Running from Source Locally
If you want to run the project in a developer environment directly on your Mac:

```bash
# Clone your fork
git clone https://github.com
cd OpenCore-Legacy-Patcher-Mod

# Install required framework libraries
pip3 install -r requirements.txt

# Launch the app interface
python3 OpenCore-Patcher-GUI.command
```

---

## 📝 Credits & Disclaimers

* **Credits:** A massive thank you to **bOOtOx** for compiling the foundational fixed layout, and to the **Dortania** team for the original groundbreaking [OpenCore Legacy Patcher](https://github.com) project.
* **Disclaimer:** This project is an independent community modification. Use at your own risk. Always back up your data before altering core system drivers.

