from flask import Flask

from flask_umami import Umami, UmamiConfig

app = Flask(__name__)

umami = Umami(
    app,
    umami_url="https://umami.example.com",
    umami_id="website-umami-id",
    config={
        "/custom": UmamiConfig( # This gets priority over the matches below
            host_url="https://custom.example.com",
            auto_track=False,
            domains=["custom.example.com"],
            tag="custom-umami-script",
            exclude_search=True,
            exclude_hash=True,
            do_not_track=True,
        ),
        ".*": UmamiConfig( # Falls back to this if no match is found
            host_url="https://example.com",
            domains=["example.com"],
            tag="umami-script",
        )
    },
    ignore_routes=["/admin"],
    ignore_status_codes=[404],
    use_bs4=True,
    create_head_if_not_exists=True,
)


@app.route("/") # Example of a default route
def home():
    return "Hello, World!"


@app.route("/admin") # Example of an ignored route
def admin():
    return "Admin page"

@app.route("/custom") # Example of route with custom configuration
def custom():
    return "Test page"

@app.route("/toggle") # Example of a route that toggles the tag
def toggle():
    umami.toggle()
    return f"Umami tag is now {'enabled' if umami.enabled else 'disabled'}"


if __name__ == "__main__":
    app.run()
