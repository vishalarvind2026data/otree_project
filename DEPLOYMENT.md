# oTree Online Deployment & Participant Distribution Guide

This guide explains how to host your **oTree Modal Shift & Carbon Taxation** project live on the internet so participants anywhere can access the experiment using their smartphones, tablets, or computers.

---

## 1. How Participant Links Work

Once your project is live (at a domain like `https://my-experiment.onrender.com` or `https://my-tunnel.trycloudflare.com`), you have three ways to share links with participants:

### Option 1: Public Open Room Link (Recommended for Surveys, WhatsApp, Email, MTurk)
* **URL:** `https://<YOUR_DOMAIN>/room/online_open`
* **How it works:** Participants click the link, see a clean "Welcome" page, and click **Start**. They enter the experiment immediately without needing a participant code or password.
* **Setup in Admin:** In your Admin Panel (`https://<YOUR_DOMAIN>/admin`), click **Rooms** > **Public Online Session** and click **Create Session** (select `Modal Shift & Carbon Taxation` and your desired participant capacity).

### Option 2: Pre-Assigned Lab Room Link (For Controlled Cohorts)
* **URL:** `https://<YOUR_DOMAIN>/room/lab_session?participant_label=P001`
* **How it works:** Participants are pre-assigned IDs (`P001` to `P060` in `_rooms/lab_session.txt`). You can send each participant their unique link, or have them visit `/room/lab_session` and enter their code.

### Option 3: Admin Session Links (Ad-Hoc Batches)
* In the Admin Panel, go to **Sessions** > **Create New Session**.
* Select **Modal Shift & Carbon Taxation**, set the number of participants (e.g., 30), and click **Create**.
* oTree generates:
  - **Single Session-Wide Link:** `https://<YOUR_DOMAIN>/join/<session_code>` (first 30 people to click are assigned seats).
  - **Individual Links:** e.g., `https://<YOUR_DOMAIN>/InitializeParticipant/<code_1>`, `https://<YOUR_DOMAIN>/InitializeParticipant/<code_2>`, etc.

---

## 2. Choosing Your Hosting Method

| Method | Setup Time | Cost | Best For | Requires Laptop On? |
| :--- | :--- | :--- | :--- | :--- |
| **Method A: Instant Tunnel** (`localtunnel` / `cloudflared`) | **60 seconds** | **Free** | Immediate pilot testing, live demos, small cohorts | Yes |
| **Method B: Render.com Cloud** | **10 minutes** | **Free / Low Cost** | 24/7 internet hosting, class-wide or public survey | No |
| **Method C: Heroku + oTree Hub** | **15 minutes** | **Standard Eco Dynos (~$5-$7)** | Official academic standard, multi-day large-scale cohorts | No |

---

## Method A: Instant Public Link in 60 Seconds (Zero Cloud Setup)

If you want a public HTTPS link **right now** to test with friends or participants across the internet without setting up cloud servers or databases:

### Step 1: Make sure your local server is running
In your terminal, start the server:
```bash
./run_dev.sh
# Server is now running at http://localhost:8000
```

### Step 2: Open a public secure tunnel
In a second terminal window in your project folder, run:
```bash
./share_live_tunnel.sh
```
*(Or manually run: `npx --yes localtunnel --port 8000`)*

Localtunnel will output a public HTTPS URL:
```text
your url is: https://bright-falcon-22.loca.lt
```

### Step 3: Send to participants
Your live links are immediately:
* Participant Open Link: `https://bright-falcon-22.loca.lt/room/online_open`
* Admin Dashboard: `https://bright-falcon-22.loca.lt/admin` (Username: `admin`, Password: `admin`)

> [!NOTE]
> All participant responses, latencies, and choices are saved in real-time to your local database (`db.sqlite3`), and you can monitor live session progress and graphs on your screen at `/AdminReport/<session_code>`.

---

## Method B: 24/7 Cloud Hosting on Render.com (Recommended)

Render offers managed web hosting with a PostgreSQL database.

### Step 1: Push your project to GitHub
1. Create a private or public repository on [GitHub.com](https://github.com).
2. Initialize git and push your project:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of oTree Modal Shift project"
   git branch -M main
   git remote add origin https://github.com/vishalarvind2026data/otree_project.git
   git push -u origin main
   ```

### Step 2: Create a PostgreSQL Database on Render
1. Sign up / Log in to [Render.com](https://render.com).
2. Click **New +** > **PostgreSQL**.
3. Set:
   - **Name:** `otree-db`
   - **Database:** `otree`
   - **User:** `otree_user`
   - **Plan:** Free
4. Click **Create Database**.
5. Once created, copy the **Internal Database URL** (e.g., `postgres://otree_user:...@dpg-...:5432/otree`).

### Step 3: Create a Web Service on Render
1. On Render, click **New +** > **Web Service**.
2. Connect your GitHub repository.
3. Configure the settings:
   - **Name:** `otree-modal-shift`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `otree prodserver 0.0.0.0:$PORT`
   - **Plan:** Free
4. Scroll to **Environment Variables** and add:
   - `DATABASE_URL`: *(paste the Internal Database URL from Step 2)*
   - `OTREE_PRODUCTION`: `1`
   - `OTREE_AUTH_LEVEL`: `STUDY`
   - `OTREE_ADMIN_PASSWORD`: *(choose a strong password for your admin panel)*
   - `OTREE_SECRET_KEY`: *(paste any long random string)*
5. Click **Deploy Web Service**.

### Step 4: Initialize the Database
1. Once deployed, click the **Shell** tab on your Render Web Service dashboard.
2. Run:
   ```bash
   otree resetdb --noinput
   ```
3. Your app is now live at: `https://<your-service-name>.onrender.com`!

---

## Method C: Official oTree Hub & Heroku Deployment

oTree provides an official 1-click cloud launcher via [oTree Hub](https://www.otreehub.com).

### Step 1: Create Accounts
1. Sign up at [Heroku.com](https://www.heroku.com) and add a billing method (required for Heroku's $5/mo Eco Dyno plan).
2. Sign up at [oTree Hub](https://www.otreehub.com) using your email or GitHub.

### Step 2: Connect Heroku to oTree Hub
1. In oTree Hub, go to **Heroku Server Deployment**.
2. Connect your Heroku account via API token or OAuth.
3. Click **Create New App**. oTree Hub automatically provisions:
   - A Heroku Dyno configured with `Procfile` (`web: otree prodserver1of2`)
   - Heroku Postgres database addon
   - Heroku Data for Redis addon
   - Environment variables (`OTREE_PRODUCTION=1`, `OTREE_AUTH_LEVEL=STUDY`)

### Step 3: Upload and Deploy
1. Zip your project folder (or connect your GitHub repo to oTree Hub).
2. Click **Deploy Project**.
3. In oTree Hub, click **Reset Database** once the build finishes.
4. Your experiment is live at `https://<your-app-name>.herokuapp.com`.

---

## 3. Pre-Flight Checklist Before Sending Links to Real Participants

Before sharing your link on social media, Prolific, or with participants:

1. [ ] **Test with bots first:**
   - In your live Admin Panel, go to `/run_bots` or test a demo session with 3 participants to verify the flow is seamless.
2. [ ] **Verify Room is Activated:**
   - Go to `Admin` > `Rooms` > `Public Online Session (Open Link)`.
   - Click **Create Session** to ensure an active session is loaded in the room.
3. [ ] **Test on Mobile Device:**
   - Open `https://<YOUR_DOMAIN>/room/online_open` on your smartphone browser (iOS Safari and Android Chrome) to verify touch interactions and responsive layout.
4. [ ] **Check Live Session Monitoring:**
   - Visit `/AdminReport/<session_code>` while testing to confirm real-time updates for:
     - Section 1: Progress Tracker
     - Section 2: Financial Framing Overview
     - Section 3: Live Session Econometric Visualizations (Figures 1-4)
5. [ ] **Reset Database for Clean Data:**
   - When ready for the actual study, run `otree resetdb --noinput` to clear test runs and start with a pristine database.

---

## 4. Exporting Data After the Study

When participants finish:
1. Log into your Admin Panel at `https://<YOUR_DOMAIN>/admin`.
2. Click **Data** in the top navigation bar.
3. Download:
   - **All Apps (Excel or CSV):** Complete raw dataset including all variables and timestamps.
   - **Page Times (CSV):** Exact millisecond page deliberation latencies.
4. Or visit `/report?source=live` to view the comprehensive econometric findings and figures generated from your live participants.
