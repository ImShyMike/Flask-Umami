from flask import Flask

from flask_umami import Umami

app = Flask(__name__)

umami = Umami(
    app,
    umami_url="https://umami.example.com",
    umami_id="website-umami-id",
)


@app.route("/")
def home():
    return "Hello, World!"

if __name__ == "__main__":
    app.run()
