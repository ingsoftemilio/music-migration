# app.py
from __future__ import annotations

import os
import typer
from dotenv import load_dotenv

from core.enums import ServiceName
from core.registry import ServiceRegistry
from core.transfer_engine import TransferEngine
from core.matching import pick_best_match_fuzzy  # change to pick_best_match_simple if you prefer

from services.spotify_service import SpotifyService
from services.deezer_service import DeezerService

app = typer.Typer(no_args_is_help=True)


def build_registry() -> ServiceRegistry:
    # Loads .env from repo root (same folder where you run `python app.py ...`)
    load_dotenv()

    registry = ServiceRegistry()
    registry.register(SpotifyService())
    registry.register(DeezerService())
    return registry


@app.command("deezer-me")
def deezer_me() -> None:
    """
    Quick sanity check: verifies DEEZER_ACCESS_TOKEN and prints your Deezer user info.
    """
    load_dotenv()
    token = os.getenv("DEEZER_ACCESS_TOKEN")

    if not token:
        typer.echo("Missing DEEZER_ACCESS_TOKEN in .env")
        raise typer.Exit(code=1)

    dz = DeezerService()
    dz.ensure_authenticated()

    # DeezerService stores the user id internally; this call also confirms API works.
    me = dz._get("/user/me")  # small shortcut for now; we can expose a public method later
    typer.echo(f"Connected to Deezer id={me.get('id')}  name={me.get('name')}")


@app.command("transfer-playlist")
def transfer_playlist(
    source: ServiceName = typer.Option(..., "--from", help="Source service: spotify|deezer"),
    dest: ServiceName = typer.Option(..., "--to", help="Destination service: spotify|deezer"),
    playlist_id: str = typer.Option(..., "--id", help="Playlist ID (service-specific)"),
    new_name: str | None = typer.Option(None, "--name", help="Optional new playlist name in destination"),
) -> None:
    """
    Transfers a playlist from one service to another.
    """
    if source == dest:
        raise typer.BadParameter("Source and destination must be different.")

    registry = build_registry()
    src_service = registry.get(source)
    dst_service = registry.get(dest)

    engine = TransferEngine(
        source=src_service,
        dest=dst_service,
        pick_best_match=pick_best_match_fuzzy,
    )

    result = engine.transfer_playlist(source_playlist_id=playlist_id, new_playlist_name=new_name)
    typer.echo(result.summary())


if __name__ == "__main__":
    app()