# 🎬 FlaskCinema

> A **lightweight, beautiful, zero-configuration** personal movie library.  
> Point it at your movie folder and instantly browse & stream your collection from any web browser.

---

## ✨ Features

- 🧹 **Automatic Meta-Tag Cleaning**  
  Strips messy release tags like `YTS`, `BluRay`, `x264`, `10bit`, etc. for clean, professional titles.

- 📂 **Recursive Directory Browsing**  
  Full folder tree support with breadcrumb navigation.

- ⚡ **Smart Streaming Engine**  
  Implements **HTTP 206 Partial Content** for instant seeking without full downloads.

- 🪟 **Modern Glassmorphism UI**  
  Sleek blurred-glass interface optimized for desktop, tablet, and mobile.

- 🔒 **Security-Focused**  
  Built-in protection against path traversal attacks.

---

## 🚀 Quick Start

### Clone the repository
```bash
[git clone https://github.com/yourusername/FlaskCinema.git](https://github.com/gavithgethmin01/Movie_Stream.git)
cd FlaskCinema
Install dependencies
bash
Copy code
pip install flask
Configure your library
Open app.py and update the MOVIES_ROOT variable:

python
Copy code
MOVIES_ROOT = r"C:\Users\Name\Videos"
Launch the app
bash
Copy code
python app.py
Access your library
Local: http://localhost:5000

Network: http://<your-ip>:5000

Stream your movies from any device on the same network 🎥

🛠️ Technical Breakdown
Backend: Flask (Python)

Frontend: HTML5, CSS3 (Flexbox / Grid), Vanilla JavaScript

Streaming: HTTP 206 Partial Content

Path Handling: pathlib (cross-platform: Windows / Linux)

📝 Supported Formats
All browser-native formats, including:

.mp4

.mkv

.webm

.avi

.mov

🤝 Contributing
Contributions are welcome 🙌
Fork the repo, improve it, and submit a pull request.

Planned Features
🔍 Search functionality

💬 Automatic subtitle detection

🎨 Theme customization

⚠️ Disclaimer
This project is intended for personal use only.
Make sure you own the rights to the media you stream.

⭐ Support the Project
If you like FlaskCinema, drop a ⭐ on GitHub.
It helps the project grow and stay alive ❤️

