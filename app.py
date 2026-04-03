import os
import socket
import psycopg2
from flask import Flask, request, jsonify
import sys
print("=== APP STARTING ===", file=sys.stderr)
sys.stderr.flush()

app = Flask(__name__)

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print('DATABASE_URL not set')
        return None
    try:
        conn = psycopg2.connect(database_url, connect_timeout=10)
        print('Database connected successfully')
        return conn
    except Exception as e:
        print(f'Database connection FAILED: {str(e)}')
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
@app.route('/debug')
def debug():
    import os
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        return f"DATABASE_URL exists (starts with: {db_url[:20]}...)"
    else:
        return "DATABASE_URL not found"

@app.route('/health')
def health():
    conn = get_db_connection()
    if conn:
        db_status = "connected"
        conn.close()
    else:
        db_status = "disconnected"
    
    return {"status": "healthy", "database": db_status}


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
