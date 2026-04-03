import os
import sys
import psycopg2
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# HTML template with CSS design
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Railway Flask App</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .card {
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        
        .status {
            display: inline-block;
            background: #10b981;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-bottom: 20px;
        }
        
        .endpoints {
            background: #f3f4f6;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .endpoints h3 {
            color: #374151;
            margin-bottom: 15px;
        }
        
        .endpoint {
            background: white;
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 8px;
            font-family: monospace;
            border-left: 4px solid #667eea;
        }
        
        .method {
            display: inline-block;
            font-weight: bold;
            margin-right: 10px;
        }
        
        .get { color: #10b981; }
        .post { color: #f59e0b; }
        .delete { color: #ef4444; }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }
        
        th {
            background: #f3f4f6;
            color: #374151;
            font-weight: 600;
        }
        
        tr:hover {
            background: #f9fafb;
        }
        
        .add-item {
            margin: 20px 0;
            display: flex;
            gap: 10px;
        }
        
        input {
            flex: 1;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            font-size: 1em;
        }
        
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
        }
        
        button:hover {
            background: #5a67d8;
        }
        
        .delete-btn {
            background: #ef4444;
            padding: 6px 12px;
            font-size: 0.9em;
        }
        
        .delete-btn:hover {
            background: #dc2626;
        }
        
        .footer {
            text-align: center;
            margin-top: 20px;
            color: white;
        }
        
        .footer a {
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="status">✅ ONLINE</div>
            <h1>🚀 Railway Flask App</h1>
            <div class="subtitle">PostgreSQL Database Connected</div>
            
            <div class="endpoints">
                <h3>📡 API Endpoints</h3>
                <div class="endpoint">
                    <span class="method get">GET</span> /items - View all items
                </div>
                <div class="endpoint">
                    <span class="method post">POST</span> /items - Add new item (JSON: {"name": "item"})
                </div>
                <div class="endpoint">
                    <span class="method delete">DELETE</span> /items/&lt;id&gt; - Delete an item
                </div>
                <div class="endpoint">
                    <span class="method get">GET</span> /health - Check app status
                </div>
            </div>
            
            <h3>📝 Add New Item</h3>
            <div class="add-item">
                <input type="text" id="itemName" placeholder="Enter item name..." onkeypress="if(event.key==='Enter') addItem()">
                <button onclick="addItem()">➕ Add Item</button>
            </div>
            
            <h3>📋 Items List</h3>
            <div id="itemsTable">
                <table>
                    <thead>
                        <tr><th>ID</th><th>Name</th><th>Created At</th><th>Action</th></tr>
                    </thead>
                    <tbody id="itemsBody">
                    </tbody>
                </table>
            </div>
        </div>
        <div class="footer">
            <p>Deployed on Railway | PostgreSQL Database | Flask Framework</p>
        </div>
    </div>
    
    <script>
        async function loadItems() {
            const response = await fetch('/items');
            const items = await response.json();
            const tbody = document.getElementById('itemsBody');
            tbody.innerHTML = '';
            items.forEach(item => {
                const row = tbody.insertRow();
                row.insertCell(0).textContent = item.id;
                row.insertCell(1).textContent = item.name;
                row.insertCell(2).textContent = new Date(item.created_at).toLocaleString();
                const deleteCell = row.insertCell(3);
                const deleteBtn = document.createElement('button');
                deleteBtn.textContent = 'Delete';
                deleteBtn.className = 'delete-btn';
                deleteBtn.onclick = () => deleteItem(item.id);
                deleteCell.appendChild(deleteBtn);
            });
        }
        
        async function addItem() {
            const input = document.getElementById('itemName');
            const name = input.value.trim();
            if (!name) return;
            
            await fetch('/items', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: name})
            });
            input.value = '';
            loadItems();
        }
        
        async function deleteItem(id) {
            await fetch('/items/' + id, {method: 'DELETE'});
            loadItems();
        }
        
        loadItems();
    </script>
</body>
</html>
'''

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print('DATABASE_URL not set', file=sys.stderr)
        return None
    try:
        conn = psycopg2.connect(database_url, connect_timeout=10)
        print('Database connected successfully', file=sys.stderr)
        return conn
    except Exception as e:
        print(f'Database connection FAILED: {str(e)}', file=sys.stderr)
        return None

def init_db():
    conn = get_db_connection()
    if not conn:
        print('DATABASE_URL not set; skipping DB initialization.', file=sys.stderr)
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
    print('Database table ready', file=sys.stderr)

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    conn = get_db_connection()
    if conn:
        db_status = "connected"
        conn.close()
    else:
        db_status = "disconnected"
    return {"status": "healthy", "database": db_status}

@app.route('/items', methods=['GET'])
def get_items():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database not configured'}), 503
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

@app.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database not configured'}), 503
    cur = conn.cursor()
    cur.execute('INSERT INTO items (name) VALUES (%s) RETURNING id', (data['name'],))
    item_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'id': item_id, 'name': data['name'], 'message': 'Created'}), 201

@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database not configured'}), 503
    cur = conn.cursor()
    cur.execute('DELETE FROM items WHERE id = %s RETURNING id', (item_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if deleted:
        return jsonify({'message': 'Deleted'})
    else:
        return jsonify({'error': 'Not found'}), 404

# Initialize database
with app.app_context():
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)