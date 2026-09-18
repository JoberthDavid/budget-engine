from flask import Flask

from app.adapters.composition_engine import CompositionEngineAdapter
from app.api.health import bp as health_bp
from app.api.routes import bp as budget_bp, configure
from app.application.calculate_budget import CalculateBudget


def create_app() -> Flask:
    app = Flask(__name__)

    composition_engine = CompositionEngineAdapter()
    calculate_budget = CalculateBudget(composition_engine)
    configure(calculate_budget)

    app.register_blueprint(health_bp)
    app.register_blueprint(budget_bp)
    return app
