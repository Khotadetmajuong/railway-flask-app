import os
import socket
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)

# This function creates a connection to the database
def get_db_connection():
    # Railway automatically provides DATABASE_URL - we just use it
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        # No database configured; return None so callers can handle gracefully
        return None
    try:
        # Add timeout to prevent hanging (5 seconds)
        return psycopg2.connect(database_url, connect_timeout=5)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Create the items table if it doesn't exist
def init_db():
    conn = get_db_connection()
    if not conn:
        print('DATABASE_URL not set; skipping DB initialization.')
        return
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

# Home route - simple welcome message
@app.route('/')
def home():
    return '''
    <h1>Railway Flask App</h1>
    <p>Your app is running successfully!</p>
    <p>Try these endpoints:</p>
    <ul>
        <li><a href="/items">GET /items</a> - View all items</li>
        <li>POST /items - Add a new item (use Postman or curl)</li>
    </ul>
    '''

@app.route('/health')
def health():
    return {"status": "healthy"}


# GET all items
@app.route('/items', methods=['GET'])
def get_items():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database not configured. Set DATABASE_URL.'}), 503
    cur = conn.cursor()
    cur.execute('SELECT id, name, created_at FROM items ORDER BY id DESC')
    items = []
    for row in cur.fetchall():
        items.append({
            'id': row[0],
            'name': row[1],
            'created_at': row[2].isoformat() if row[2] else None
        })
    cur.close()
    conn.close()
    return jsonify(items)

# POST a new item
@app.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()
    
    # Validate that name was provided
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database not configured. Set DATABASE_URL.'}), 503
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO items (name) VALUES (%s) RETURNING id',
        (data['name'],)
    )
    item_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({
        'id': item_id,
        'name': data['name'],
        'message': 'Item created successfully'
    }), 201

# DELETE an item by ID
@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database not configured. Set DATABASE_URL.'}), 503
    cur = conn.cursor()
    cur.execute('DELETE FROM items WHERE id = %s RETURNING id', (item_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if deleted:
        return jsonify({'message': 'Item deleted successfully'})
    else:
        return jsonify({'error': 'Item not found'}), 404

# Run the app
if __name__ == '__main__':
    init_db()  # Create table if it doesn't exist
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
