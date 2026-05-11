"""Flask CLI commands."""
import click

from app.db_bootstrap import run_seed
from app.extensions import db


def register_cli(app):
    @app.cli.command("seed-db")
    def seed_db():
        """Create default roles, admin user, sample category/department."""
        click.echo("Seeding database...")
        run_seed()
        click.echo("Done. If new, login: admin / admin123 — change password immediately.")

    @app.cli.command("create-all")
    def create_all():
        """Create tables (development shortcut; prefer migrations)."""
        db.create_all()
        click.echo("Tables created.")
