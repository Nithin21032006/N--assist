# N-Assist Free Hosting & Deployment Guide

This guide outlines how to host your **N-Assist** student productivity assistant online for free. Depending on whether you want to use the local SQLite database or a production MySQL database, choose the platform that best fits your requirements.

---

## 🚀 Option 1: PythonAnywhere (Recommended for SQLite)
PythonAnywhere offers a **permanently free tier** with persistent filesystem storage. Since SQLite writes directly to a database file (`n_assist.db`), PythonAnywhere will preserve all your user tasks, statistics, and logs even when the server restarts or goes idle.

### Step-by-Step Setup:
1. **Create an Account**: Sign up for a free account at [pythonanywhere.com](https://www.pythonanywhere.com/).
2. **Upload Your Code**:
   * Go to the **Files** tab on PythonAnywhere.
   * Zip your local `N-assist` folder.
   * Upload the `.zip` file to your home directory `/home/<username>/`.
   * Open a **Bash Console** on PythonAnywhere and extract it:
     ```bash
     unzip N-assist.zip
     ```
3. **Configure the Virtual Environment**:
   * Inside the Bash Console, navigate to the project directory and create a virtual environment:
     ```bash
     cd N-assist
     virtualenv --python=python3.10 venv
     source venv/bin/activate
     pip install -r requirements.txt
     ```
4. **Configure Web Application**:
   * Navigate to the **Web** tab on the PythonAnywhere dashboard.
   * Click **Add a new web app**, select **Manual Configuration**, and pick **Python 3.10**.
   * Set the **Source code directory** path to: `/home/<username>/N-assist`
   * Set the **Working directory** path to: `/home/<username>/N-assist`
   * Set the **Virtualenv** path to: `/home/<username>/N-assist/venv`
5. **Configure WSGI Configuration File**:
   * Click the link to edit the **WSGI configuration file** (found under the Code section).
   * Delete everything inside, and replace it with:
     ```python
     import sys
     import os

     # Add your project directory to the sys.path
     project_home = '/home/<username>/N-assist'
     if project_home not in sys.path:
         sys.path.insert(0, project_home)

     # Load environment variables
     from dotenv import load_dotenv
     load_dotenv(os.path.join(project_home, '.env'))

     # Import the Flask app
     from app import app as application
     ```
     *(Make sure to replace `<username>` with your actual PythonAnywhere username!)*
6. **Set Environment Variables**:
   * In your files tab, create a `.env` file inside `/home/<username>/N-assist` and set your secrets.
7. **Reload Web App**:
   * Go to the **Web** tab and click **Reload**. Your site is now live at: `http://<username>.pythonanywhere.com`

---

## 🌐 Option 2: Render.com (Recommended for MySQL)
Render is a modern cloud hosting platform. However, because its free tier Web Services use **ephemeral disks**, any SQLite file database (`n_assist.db`) will be **wiped clean whenever the service restarts or goes idle** (approximately once a day). Render is best if you connect to an external production database.

### Step-by-Step Setup:
1. **Push to GitHub**:
   * Create a repository on GitHub (private or public).
   * Initialize git in your local project and push the code:
     ```bash
     git init
     git add .
     git commit -m "Initial commit"
     git branch -M main
     git remote add origin <your-github-repo-url>
     git push -u origin main
     ```
2. **Provision a Free MySQL Database**:
   * Sign up at [Aiven.io](https://aiven.io/) or [PlanetScale](https://planetscale.com/) to get a permanently free MySQL database connection URI.
3. **Deploy on Render**:
   * Sign up at [Render.com](https://render.com/).
   * Click **New +** -> **Web Service**.
   * Connect your GitHub account and select your `N-assist` repository.
   * Configure settings:
     * **Language**: `Python`
     * **Build Command**: `pip install -r requirements.txt`
     * **Start Command**: `gunicorn app:app` *(Note: Add `gunicorn` to your requirements.txt)*
4. **Configure Environment Variables**:
   * Go to the **Environment** tab on Render.
   * Click **Add Environment Variable** and enter:
     * `SECRET_KEY`: `<your_secret_key>`
     * `MYSQL_HOST`: `<your_database_host>`
     * `MYSQL_USER`: `<your_database_user>`
     * `MYSQL_PASSWORD`: `<your_database_password>`
     * `MYSQL_DB`: `<your_database_name>`
     * `MYSQL_PORT`: `3306`
5. **Deploy**: Click **Deploy Web Service**. Your app will be hosted at `https://n-assist.onrender.com` (or similar custom sub-domain).

---

## ⚡ Option 3: Expose Your Local Server Instantly (Free Tunneling)
If you want to demo your local server to friends, teachers, or mobile devices *instantly* without uploading code to the cloud, you can run a free secure tunnel.

### Using Localhost.run (Zero-installation)
If you have SSH installed on your system (default on modern Windows 10/11), you can expose your local port 5000:
1. Start your local Flask server (`python app.py`).
2. Open a separate PowerShell or command prompt and run:
   ```bash
   ssh -R 80:localhost:5000 nokey@localhost.run
   ```
3. It will print a public URL in the terminal (e.g. `https://n-assist-xxxx.lhr.life`). Anyone on the internet can click it to visit your running local site!

### Using Ngrok
1. Download ngrok from [ngrok.com](https://ngrok.com/).
2. Run your Flask app locally (`python app.py`).
3. Run the ngrok tunnel in your terminal:
   ```bash
   ngrok http 5000
   ```
4. Copy the secure forwarding URL (e.g., `https://xxxx-xx-xx.ngrok-free.app`) and share it!
