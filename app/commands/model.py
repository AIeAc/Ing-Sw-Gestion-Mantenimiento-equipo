import click
from flask import current_app

from app.ml.training import train_and_save_model
from app.repositories.risks import list_historical_training_rows


@click.command("entrenar-modelo-riesgo")
@click.option(
    "--muestras",
    default=1600,
    show_default=True,
    type=click.IntRange(min=200, max=100000),
    help="Cantidad de escenarios simulados que complementan el historial real.",
)
@click.option(
    "--semilla",
    default=42,
    show_default=True,
    type=int,
    help="Semilla para reproducir la división y el entrenamiento.",
)
def train_risk_model_command(muestras, semilla):
    """Entrena, compara y guarda el modelo predictivo local."""
    historical_rows = list_historical_training_rows()
    artifact = train_and_save_model(
        current_app.config["RISK_MODEL_PATH"],
        sample_count=muestras,
        random_state=semilla,
        historical_rows=historical_rows,
    )
    click.echo(
        "Casos usados: "
        f"{artifact['dataset']['historical_samples']} históricos + "
        f"{artifact['dataset']['synthetic_samples']} simulados"
    )
    click.echo(f"Modelo seleccionado: {artifact['selected_model']}")
    for name, metrics in artifact["evaluations"].items():
        click.echo(
            f"- {name}: F1={metrics['f1']:.3f}, "
            f"recall={metrics['recall']:.3f}, "
            f"precision={metrics['precision']:.3f}"
        )
    if not artifact["accepted"]:
        raise click.ClickException(
            "El modelo no cumplió los criterios mínimos; revisa el conjunto de datos."
        )
    click.echo(f"Modelo guardado en: {current_app.config['RISK_MODEL_PATH']}")


def init_app(app):
    app.cli.add_command(train_risk_model_command)
