# Flask-Umami

[pypi_url]: https://pypi.org/project/Flask-Umami

[![License](https://img.shields.io/pypi/l/Flask-Umami)](https://github.com/ImShyMike/Flask-Umami/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/Flask-Umami)][pypi_url]
[![Python Version](https://img.shields.io/pypi/pyversions/Flask-Umami)][pypi_url]
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/Flask-Umami)][pypi_url]

[Flask-Umami][pypi_url] is an extension for [Flask](https://flask.palletsprojects.com) that simplifies the integration of the web analytics platform [Umami](https://umami.is) into any Flask project.

## Quickstart

### Install

`pip install Flask-Umami`

### Minimal Example

```python
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
```

(Check out the [examples folder](https://github.com/ImShyMike/Flask-Umami/tree/main/examples) for a more in-depth example)

## Disclaimer

Flask-Umami is **not affiliated with Umami** in any way. It simply provides a simple way to integrate Umami's HTML snippet into websites developed using Flask.
