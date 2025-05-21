# Barter Platform - EffectiveMobile Task

A Django-based platform for exchanging goods between users with both web interface and REST API.

Demo : https://effective-mobile.duckdns.org/  \
Api documentation: https://effective-mobile.duckdns.org/api/docs  \
*The demo is hosted on AWS EC2 instance*

## Features

- User authentication (login/registration)
- Create, edit, and delete product listings
- Send and manage trade proposals
- Search and filter listings
- REST API for programmatic access
- Swagger API documentation

## Technology Stack

- Backend: Django 4.2, Django REST Framework
- Frontend: HTML 5, CSS, Bootstrap, Django templates
- Deployment: AWS EC2, Nginx, Gunicorn

## Prerequisites

- Python 3.8+
- Git

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/hamidullaorifov/EffectiveMobileTask.git
cd EffectiveMobileTask
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
### 4. Configure Environment Variables
Create a .env file in the project root:
```dotenv
SECRET_KEY=your-django-secret-key
```

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Run Development Server
```bash
python manage.py runserver
```
The application will be available at http://localhost:8000
### 7. (Optional) Generate data
Instead of manually creating data open your browser and paste http://localhost:8000/generate url \
It generates dummy data
## API Documentation
After running the server, access the API documentation at: \

Swagger UI: http://localhost:8000/api/docs/
