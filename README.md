# Railway Flask PostgreSQL App

A simple CRUD application deployed on Railway with PostgreSQL database.

## Local Development

1. Create virtual environment: `python -m venv venv`
2. Activate: `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Set DATABASE_URL environment variable (optional for local)
5. Run: `python app.py`

## API Endpoints

- `GET /` - Welcome page
- `GET /items` - List all items
- `POST /items` - Create new item (requires JSON: {"name": "item name"})
- `DELETE /items/<id>` - Delete an item

## Deployment

Automatically deploys to Railway when pushing to main branch.
