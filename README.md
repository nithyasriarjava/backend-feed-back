# Feedback Triage Assistant

An AI-powered Feedback Triage system that classifies customer feedback into categories using Gemini AI, analyzes sentiment, generates summaries, and allows authenticated users to manage their feedback.

---

# Features

- User Signup
- User Login (JWT Authentication)
- Protected Routes
- Submit Feedback
- AI-powered Feedback Classification
- Sentiment Analysis
- Automatic Summary Generation
- View User Feedback
- Delete Feedback
- Background Processing using FastAPI Background Tasks
- Secure Password Hashing (bcrypt)

---

# Tech Stack

## Frontend

- React.js
- React Router DOM
- Axios
- CSS
- Lucide React Icons

## Backend

- FastAPI
- SQLAlchemy
- MySQL
- JWT Authentication
- Passlib (bcrypt)
- Gemini API

---

# Project Structure

## Frontend

```
src
│
├── components
│   ├── Login
│   ├── Signup
│   ├── Dashboard
│   └── Feedback
│
├── context
│
├── hooks
│
├── services
│
└── App.js
```

## Backend

```
backend
│
├── main.py
├── models.py
├── schemas.py
├── database.py
├── gemini_service.py
└── requirements.txt
```

---

# API Endpoints

## Authentication

### Signup

```
POST /auth/signup
```

Request

```json
{
    "email":"user@gmail.com",
    "password":"123456"
}
```

Response

```json
{
    "token":"JWT_TOKEN"
}
```

---

### Login

```
POST /auth/login
```

Request

```json
{
    "email":"user@gmail.com",
    "password":"123456"
}
```

Response

```json
{
    "message":"Login successful",
    "token":"JWT_TOKEN"
}
```

---

## Feedback

### Create Feedback

```
POST /feedback
```

Authorization

```
Bearer JWT_TOKEN
```

Request

```json
{
    "text":"Application crashes while opening settings."
}
```

Response

```json
{
    "id":1,
    "text":"Application crashes while opening settings.",
    "status":"pending"
}
```

---

### Get Feedback

```
GET /feedback
```

Authorization

```
Bearer JWT_TOKEN
```

---

### Delete Feedback

```
DELETE /feedback/{id}
```

Authorization

```
Bearer JWT_TOKEN
```

---

# AI Processing

After feedback is submitted:

- Gemini API analyzes the feedback.
- Detects Category.
- Detects Sentiment.
- Generates Summary.
- Updates the database automatically using Background Tasks.

---

# Authentication

- JWT Token Authentication
- Password Hashing using bcrypt
- Protected Feedback APIs
- Authorization Header Validation

---

# Database

## Users

| Field | Type |
|--------|------|
| id | BIGINT |
| email | VARCHAR |
| password | VARCHAR |
| created_at | TIMESTAMP |

---

## Feedback

| Field | Type |
|--------|------|
| id | BIGINT |
| user_email | VARCHAR |
| text | TEXT |
| category | ENUM |
| sentiment | ENUM |
| summary | VARCHAR |
| status | ENUM |
| error_message | TEXT |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |

---

# Setup

## Backend

Clone the repository

```bash
git clone <repository-url>
```

Go to backend

```bash
cd backend
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run server

```bash
uvicorn main:app --reload
```

---

## Frontend

Go to frontend

```bash
cd frontend
```

Install packages

```bash
npm install
```

Start project

```bash
npm start
```

---

# Environment Variables

Create a `.env` file.

```
JWT_SECRET=your_secret_key
DATABASE_URL=your_database_url
GEMINI_API_KEY=your_gemini_api_key
```

---

# Hosted Links

## Frontend

https://feed-back123.netlify.app

## Backend

https://backend-feed-back.onrender.com

---

# Design Trade-off

Instead of blocking the user interface while waiting for Gemini AI to process feedback, the application stores feedback immediately with a **pending** status and processes it in the background using **FastAPI Background Tasks**.

This approach improves user experience by making the application responsive and allows AI processing failures to be handled independently without affecting user requests.

---

# Future Improvements

- Refresh Token Authentication
- Email Verification
- Forgot Password
- Pagination
- Search & Filter
- Feedback Editing
- Admin Dashboard
- Role-based Authentication
- Docker Deployment

---

# Developed By

**Nithya Sri**

Frontend Developer | React | FastAPI | SQLAlchemy | MySQL