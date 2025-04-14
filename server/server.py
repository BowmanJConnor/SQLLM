from flask import Flask, request, jsonify, render_template
from llm_io import Llama4MaverickIO
from db import db, User

# Define website routes
app = Flask(__name__)
llm = None

# Initialize database with SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://sqllm_user:sqllm_pass@localhost:5432/sqllm_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


@app.route('/')
def home():
    return render_template('index.html')  # Render the HTML file

@app.route('/test', methods=['GET'])
def test():
    return jsonify("Test Success"), 200

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    print(f"Received Data on /ask: {data}")
    if llm != None and "input" in data:
        return llm.ask(data["input"])
    else:
        return jsonify({"error": "Bad Request"}), 400

@app.route('/list_users', methods=['GET'])
def list_users():
    try:
        users = User.query.all()
        response = []
        for user in users:
            response.append(f"ID: {user.id}, Name: {user.name}, Age: {user.age}")
        return jsonify(response), 200
    except:
        return jsonify({"error": "Database Error"}), 400
    

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="SQLLM Server")
    parser.add_argument("api_key", help="API Key file for OpenRouter")
    args = parser.parse_args()

    llm = Llama4MaverickIO(args.api_key)

    app.run(host="127.0.0.1", port=5000, debug=True)