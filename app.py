from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Flask app is running on Render!"

if __name__ == "__main__":
    # Use the port Render provides, default to 8080 for local testing
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
