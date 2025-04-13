from flask import Flask, request, jsonify, render_template

# Define website routes
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')  # Render the HTML file


@app.route('/test', methods=['GET'])
def test():
    return jsonify("Test Success"), 200


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)