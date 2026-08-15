"""Routes package — registers all blueprints."""
from .health import bp as health_bp
from .servers import bp as servers_bp
from .workloads import bp as workloads_bp
from .allocations import bp as allocations_bp


def register_blueprints(app):
    app.register_blueprint(health_bp)
    app.register_blueprint(servers_bp)
    app.register_blueprint(workloads_bp)
    app.register_blueprint(allocations_bp)
