# Deployment Guide

This guide provides step-by-step instructions to deploy the TasteFinder AI recommendation system. 

The application uses a decoupled architecture:
1. **Backend**: FastAPI web server (Python) deployed on **Railway**.
2. **Frontend**: Vite + React SPA (JavaScript) deployed on **Vercel**.

---

## 📋 Prerequisites
- A [GitHub](https://github.com) account with the repository pushed.
- A [Railway](https://railway.app) account.
- A [Vercel](https://vercel.com) account.
- Your LLM API key (e.g., Groq API Key or OpenAI API Key).

---

## 1. Backend Deployment (Railway)

Railway is used to host the FastAPI Python server. It automatically detects the Python runtime from the `requirements.txt` and uses the provided `Procfile` to run the server.

### Steps to Deploy:
1. Log in to [Railway](https://railway.app/) and click **New Project**.
2. Select **Deploy from GitHub repo** and choose your repository.
3. Once the service is created, click on it and navigate to the **Variables** tab.
4. Add the following environment variables:
   - `GROQ_API_KEY`: Your Groq API key (or `OPENAI_API_KEY` if utilizing OpenAI models).
   - `ALLOWED_ORIGINS`: Comma-separated list of allowed origins (e.g., `https://your-frontend.vercel.app`). Defaults to `*` if left blank.
   - *Railway automatically manages the `PORT` variable for the application.*
5. Navigate to the **Settings** tab.
6. Scroll down to the **Networking** section and click **Generate Domain** (or set up a custom domain). 
7. Copy the generated domain URL (e.g., `https://milestone-zomato-production.up.railway.app`). **You will need this for the frontend configuration.**

> [!NOTE]
> The backend server uses the [Procfile](file:///Users/ayushisharma/Milestone_Zomato/Procfile) in the root directory which specifies the web process command:
> `web: uvicorn src.api:app --host 0.0.0.0 --port $PORT`
> Railway reads this file automatically to run the FastAPI app.

---

## 2. Frontend Deployment (Vercel)

Vercel is used to build and host the Vite + React frontend application.

### Steps to Deploy:
1. Log in to [Vercel](https://vercel.com/) and click **Add New** > **Project**.
2. Import your GitHub repository.
3. In the **Configure Project** screen, adjust the following settings:
   - **Framework Preset**: Select `Vite`.
   - **Root Directory**: Click *Edit* and select the `frontend` folder. (This tells Vercel to run the build within the subdirectory).
   - **Build and Output Settings**: Leave as default (`Build Command: npm run build`, `Output Directory: dist`).
4. Expand the **Environment Variables** section and add the following variable:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: The public URL of your Railway backend (e.g., `https://milestone-zomato-production.up.railway.app`). *Make sure there is no trailing slash.*
5. Click **Deploy**.
6. Once the build completes, Vercel will provide you with a production URL for your frontend application.

---

## 🔒 Security & CORS Notes
- In [src/api.py](file:///Users/ayushisharma/Milestone_Zomato/src/api.py), CORS is configured with `allow_origins=["*"]` by default. This makes testing easy across any dynamic preview deployments on Vercel.
- **For production deployments**, it is recommended to restrict `allow_origins` in [src/api.py](file:///Users/ayushisharma/Milestone_Zomato/src/api.py) specifically to your frontend's Vercel domain to secure the API.
