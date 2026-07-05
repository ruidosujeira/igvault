"""Beautiful CLI for igvault using Typer + Rich."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich import box

from . import __version__
from .config import DEFAULT_LIMIT, DOWNLOAD_BASE
from .core import (
    download_reels,
    fetch_profile_reels,
    bulk_cooldown,
    human_sleep,
    get_reel_video_url,
    download_reel,
)

app = typer.Typer(
    name="igvault",
    help="igvault — Baixe Reels públicos do Instagram de forma simples, confiável e anti-ban.",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

console = Console()


def _strip_at(username: str) -> str:
    return username.strip().lstrip("@")


@app.command("reels", help="Baixa Reels públicos de um perfil.")
@app.command("profile", help="Alias para 'reels' — baixa Reels de um perfil.")
def reels(
    username: str = typer.Argument(..., help="Nome do usuário (ex: @nasa ou nasa)"),
    limit: int = typer.Option(DEFAULT_LIMIT, "--limit", "-l", min=1, max=50, help="Quantidade máxima de reels"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Simula sem baixar nada (teste rápido)"),
):
    """Baixa Reels de @username e salva em ./downloads/@username/reels/"""
    clean = _strip_at(username)
    if not clean:
        console.print("[red]Erro:[/red] username inválido.")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            f"[bold cyan]igvault[/bold cyan]  •  [bold]@{clean}[/bold]  •  limit=[yellow]{limit}[/yellow]"
            + ("  [dim](DRY-RUN)[/dim]" if dry_run else ""),
            title="[bold]🔍 Buscando Reels[/bold]",
            border_style="cyan",
        )
    )

    # Discovery
    with console.status("[bold green]Procurando reels públicos...", spinner="dots"):
        shortcodes = fetch_profile_reels(clean, limit=limit)
        shortcodes = shortcodes[:limit]

    if not shortcodes:
        console.print(
            Panel(
                "[yellow]Nenhum reel encontrado.[/yellow]\n"
                "• O perfil pode ser privado\n"
                "• Instagram pode estar bloqueando temporariamente\n"
                "• Tente novamente em alguns minutos ou com outro perfil",
                title="[red]Sem resultados[/red]",
                border_style="yellow",
            )
        )
        raise typer.Exit(0)

    console.print(f"[green]✓[/green] Encontrados [bold]{len(shortcodes)}[/bold] reels candidatos.\n")

    if dry_run:
        table = Table(title="Dry-Run: Reels que seriam baixados", box=box.SIMPLE)
        table.add_column("#", style="dim")
        table.add_column("Shortcode", style="cyan")
        table.add_column("Destino esperado")
        for i, sc in enumerate(shortcodes, 1):
            dest = str(DOWNLOAD_BASE / f"@{clean}" / "reels" / f"{sc}.mp4")
            table.add_row(str(i), sc, dest)
        console.print(table)
        console.print(Panel("[bold green]Dry-run concluído com sucesso.[/bold green] Nenhum arquivo baixado.", border_style="green"))
        return

    # Real download with progress
    target_dir = DOWNLOAD_BASE / f"@{clean}" / "reels"
    target_dir.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    skipped = 0
    errors = 0
    files: list[str] = []

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    )

    task = progress.add_task(f"Baixando reels de @{clean}", total=len(shortcodes))

    with progress:
        for idx, sc in enumerate(shortcodes):
            progress.update(task, description=f"Reel [cyan]{sc}[/cyan] ({idx+1}/{len(shortcodes)})")

            # Human delay
            if idx > 0:
                human_sleep()

            # Manual loop for nice per-item Rich progress (uses same core functions)
            video_url = get_reel_video_url(sc)
            if not video_url:
                errors += 1
                progress.console.print(f"  [red]✗[/red] {sc} — URL não encontrada")
                progress.advance(task)
                continue

            dest = target_dir / f"{sc}.mp4"
            if dest.exists():
                skipped += 1
                files.append(str(dest))
                progress.console.print(f"  [yellow]↻[/yellow] {sc} — já existe")
                progress.advance(task)
                continue

            ok, err = download_reel(video_url, dest, referer="https://www.instagram.com/")
            if ok:
                downloaded += 1
                files.append(str(dest))
                progress.console.print(f"  [green]✔[/green] {sc} salvo")
            else:
                errors += 1
                progress.console.print(f"  [red]✗[/red] {sc} — {err or 'erro'}")

            progress.advance(task)

    # Summary
    summary = (
        f"[bold green]Baixados:[/bold green] {downloaded}   "
        f"[yellow]Pulados:[/yellow] {skipped}   "
        f"[red]Erros:[/red] {errors}\n"
        f"[dim]Pasta:[/dim] {target_dir}"
    )
    console.print(
        Panel(summary, title="[bold]✅ Concluído[/bold]", border_style="green" if downloaded > 0 else "yellow")
    )

    if files:
        t = Table(title="Arquivos", box=box.MINIMAL)
        t.add_column("Arquivo", style="green")
        for f in files[:8]:
            t.add_row(Path(f).name)
        if len(files) > 8:
            t.add_row(f"... +{len(files)-8} mais")
        console.print(t)


@app.command("bulk", help="Baixa reels de múltiplos perfis listados em um arquivo (um por linha).")
def bulk(
    file: Path = typer.Argument(..., exists=True, readable=True, help="Arquivo .txt com usernames (um por linha)"),
    limit: int = typer.Option(DEFAULT_LIMIT, "--limit", "-l", min=1, max=30, help="Limite por perfil"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Simula a operação"),
):
    """Processa vários perfis com cooldowns anti-ban entre eles."""
    try:
        lines = file.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        console.print(f"[red]Erro ao ler arquivo:[/red] {e}")
        raise typer.Exit(1)

    users = []
    for line in lines:
        u = _strip_at(line.strip())
        if u and not u.startswith("#"):
            users.append(u)

    if not users:
        console.print("[yellow]Nenhum usuário válido encontrado no arquivo.[/yellow]")
        raise typer.Exit(0)

    console.print(
        Panel.fit(
            f"[bold]Bulk mode[/bold] — {len(users)} perfis • limit={limit} por perfil"
            + (" [dim](DRY-RUN)[/dim]" if dry_run else ""),
            border_style="magenta",
        )
    )

    total_dl = 0
    total_err = 0

    for i, user in enumerate(users):
        if i > 0:
            cd = bulk_cooldown()
            console.print(f"[dim]⏳ Cooldown entre perfis: {cd:.1f}s[/dim]")

        console.rule(f"@{user}")
        res = download_reels(user, limit=limit, dry_run=dry_run)
        total_dl += res.get("downloaded", 0)
        total_err += res.get("errors", 0)

        console.print(
            f"  [green]{res.get('downloaded', 0)}[/green] baixados • "
            f"[red]{res.get('errors', 0)}[/red] erros"
        )

    console.print(
        Panel(
            f"Total baixados: [bold green]{total_dl}[/bold green]\n"
            f"Erros totais: [red]{total_err}[/red]",
            title="📦 Bulk finalizado",
            border_style="magenta",
        )
    )


@app.command("help", hidden=True)
def help_cmd():
    """Mostra ajuda estendida."""
    console.print(app)


@app.callback()
def main(
    version: bool = typer.Option(None, "--version", "-v", is_eager=True, help="Mostra a versão"),
):
    if version:
        console.print(f"[bold cyan]igvault[/bold cyan] v{__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()
