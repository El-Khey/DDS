from pathlib import Path

from flask import Flask

from src.server.database.connexion import init_app, init_db
from src.server.routes.api import enregistrer_routes_api
from src.server.routes.pages import enregistrer_routes_pages


BASE_DIR = Path(__file__).resolve().parent
CLIENT_DIR = BASE_DIR.parent / "client"


def create_app(test_config=None):
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=str(CLIENT_DIR / "pages"),
        static_folder=str(CLIENT_DIR / "public"),
        static_url_path="/public",
    )
    app.config.from_mapping(
        DATABASE=BASE_DIR / "instance" / "refuge_climatique.sqlite",
    )
    # Le JSON garde l'ordre des éléments du XML au lieu d'être trié.
    app.json.sort_keys = False
    if test_config:
        app.config.update(test_config)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    init_app(app)

    with app.app_context():
        init_db()

    enregistrer_routes_pages(app)
    enregistrer_routes_api(app)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
