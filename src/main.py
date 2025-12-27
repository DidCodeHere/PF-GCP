import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from .scraper import Scraper
from .analyzer import PropertyAnalyzer
import os

app = typer.Typer()
console = Console()

@app.command()
def search(
    location: str = typer.Option(..., prompt="Where do you want to invest? (e.g. Manchester)", help="City or Town name"),
    radius: float = typer.Option(5.0, prompt="Search radius (miles)?", help="Radius in miles"),
    max_price: int = typer.Option(100000, help="Maximum price"),
    limit: int = typer.Option(10, help="Number of results to show")
):
    """
    Search for investment properties under a certain price.
    """
    console.print(f"[bold green]Starting Property Finder...[/bold green]")
    console.print(f"Target: [cyan]{location}[/cyan] (+{radius}m) | Max: [gold1]£{max_price:,}[/gold1]")

    scraper = Scraper()
    analyzer = PropertyAnalyzer()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        
        task1 = progress.add_task(description="Scraping Rightmove...", total=None)
        properties = scraper.search_rightmove(location, radius, max_price)
        
        if not properties:
            progress.stop()
            console.print("[bold red]No properties found or scraping failed.[/bold red]")
            return

        task2 = progress.add_task(description="Analyzing Investment Potential...", total=None)
        analyzed_props = analyzer.analyze(properties)
        
    # Display Results
    table = Table(title=f"Top Investment Opportunities in {location}")
    table.add_column("Score", style="magenta", justify="center")
    table.add_column("Price", style="green")
    table.add_column("Address")
    table.add_column("Type/Title")
    table.add_column("AI Summary", style="italic")
    
    for prop in analyzed_props[:limit]:
        score_str = f"{prop.investment_score:.1f}"
        table.add_row(
            score_str,
            f"£{prop.price:,.0f}",
            prop.address,
            prop.title,
            prop.ai_summary
        )

    console.print(table)
    
    # Save CSV option
    if typer.confirm("Do you want to save these results to a CSV?"):
        import pandas as pd
        df = pd.DataFrame([vars(p) for p in analyzed_props])
        filename = f"investment_opps_{location}_{max_price}.csv"
        df.to_csv(filename, index=False)
        console.print(f"[bold green]Saved to {filename}[/bold green]")

if __name__ == "__main__":
    app()
