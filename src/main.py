import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from .scraper import Scraper
from .analyzer import PropertyAnalyzer
from .llm_analyzer import LLMAnalyzer
import os

app = typer.Typer()
console = Console()

@app.command()
def search(
    location: str = typer.Option(None, help="City or Town name"),
    radius: float = typer.Option(None, help="Radius in miles"),
    max_price: int = typer.Option(None, help="Maximum price"),
    limit: int = typer.Option(10, help="Number of results to show"),
    use_llm: bool = typer.Option(None, help="Use Local LLM for deeper analysis (slower)"),
    source: str = typer.Option("all", help="Source to scrape: 'rightmove', 'zoopla', 'auction', or 'all'"),
    exclude_land: bool = typer.Option(None, help="Strictly exclude land/plots from results"),
    csv: bool = typer.Option(False, help="Save results to CSV automatically")
):
    """
    Search for investment properties under a certain price.
    """
    console.print(f"[bold green]Starting Property Finder...[/bold green]")

    # Interactive Prompts if arguments are missing
    if location is None:
        location = typer.prompt("Where do you want to invest? (e.g. Manchester)")
    
    if radius is None:
        radius = float(typer.prompt("Search radius (miles)?", default=5.0))
        
    if max_price is None:
        max_price = int(typer.prompt("Maximum price?", default=100000))

    if exclude_land is None:
        exclude_land = typer.confirm("Do you want to exclude land/plots?", default=True)

    if use_llm is None:
        use_llm = typer.confirm("Use Local LLM for deeper analysis (slower)?", default=False)

    console.print(f"Target: [cyan]{location}[/cyan] (+{radius}m) | Max: [gold1]£{max_price:,}[/gold1] | Source: {source}")
    if exclude_land:
        console.print("[bold yellow]Excluding Land/Plots[/bold yellow]")

    scraper = Scraper()
    analyzer = PropertyAnalyzer()
    
    properties = []
    
    # Allowed radii for Rightmove/Zoopla
    allowed_radii = [0.0, 0.25, 0.5, 1.0, 3.0, 5.0, 10.0, 15.0, 20.0, 30.0, 40.0]
    
    # Find starting index for radius
    try:
        current_radius_idx = next(i for i, r in enumerate(allowed_radii) if r >= radius)
    except StopIteration:
        current_radius_idx = len(allowed_radii) - 1

    # Cache for sources that don't support radius or only need one-time scraping
    cached_auction_house_props = None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        
        while current_radius_idx < len(allowed_radii):
            current_radius = allowed_radii[current_radius_idx]
            progress.console.print(f"[dim]Searching with radius: {current_radius} miles...[/dim]")
            
            properties = [] # Reset properties for new search
            
            if source.lower() in ["rightmove", "all"]:
                task1 = progress.add_task(description=f"Scraping Rightmove ({current_radius}m)...", total=None)
                rm_props = scraper.search_rightmove(location, current_radius, max_price)
                properties.extend(rm_props)
                progress.remove_task(task1)
            
            if source.lower() in ["zoopla", "all"]:
                task_z = progress.add_task(description=f"Scraping Zoopla ({current_radius}m)...", total=None)
                zp_props = scraper.search_zoopla(location, current_radius, max_price)
                properties.extend(zp_props)
                progress.remove_task(task_z)

            if source.lower() in ["auction", "all"]:
                # Auction House (Keyword based, no radius parameter usually effective for this scraper)
                # Only scrape once to save time
                if cached_auction_house_props is None:
                    task_a = progress.add_task(description=f"Scraping Auction House...", total=None)
                    cached_auction_house_props = scraper.search_auction_house(location, current_radius, max_price)
                    progress.remove_task(task_a)
                
                if cached_auction_house_props:
                    properties.extend(cached_auction_house_props)

                # Pugh Auctions (Supports radius)
                task_p = progress.add_task(description=f"Scraping Pugh Auctions ({current_radius}m)...", total=None)
                pugh_props = scraper.search_pugh(location, current_radius, max_price)
                properties.extend(pugh_props)
                progress.remove_task(task_p)

                # SDL Auctions
                task_sdl = progress.add_task(description=f"Scraping SDL Auctions...", total=None)
                sdl_props = scraper.search_sdl_auctions(location, current_radius, max_price)
                properties.extend(sdl_props)
                progress.remove_task(task_sdl)

                # Allsop Auctions
                task_allsop = progress.add_task(description=f"Scraping Allsop Auctions...", total=None)
                allsop_props = scraper.search_allsop(location, current_radius, max_price)
                properties.extend(allsop_props)
                progress.remove_task(task_allsop)
            
            # Check if we have enough non-land properties
            non_land_count = sum(1 for p in properties if not analyzer.is_land(p))
            
            # If we are excluding land, we only care about non-land count
            # If we are NOT excluding land, we still want to ensure we found *some* houses if possible, 
            # but maybe we shouldn't force expansion if the user is okay with land.
            # However, the user complaint was "radius is not changing" when they wanted houses.
            # So let's keep the logic: if we found < 3 houses, expand.
            
            if non_land_count >= 3: # Threshold: at least 3 houses found
                break
            
            if current_radius >= 40.0:
                break
                
            progress.console.print(f"[yellow]Found only {non_land_count} houses. Expanding search radius...[/yellow]")
            current_radius_idx += 1
        
        if not properties:
            progress.stop()
            console.print("[bold red]No properties found or scraping failed.[/bold red]")
            return

        task2 = progress.add_task(description="Analyzing Investment Potential...", total=None)
        analyzed_props = analyzer.analyze(properties, exclude_land=exclude_land)

        if use_llm:
            llm = LLMAnalyzer()
            if llm.is_available():
                task3 = progress.add_task(description="Running Local LLM Analysis (Top 5)...", total=5)
                # Only analyze top 5 to save time
                for prop in analyzed_props[:5]:
                    result = llm.analyze_description(prop.description)
                    prop.llm_score = result['score']
                    prop.llm_reasoning = result['reasoning']
                    progress.advance(task3)
            else:
                console.print("[bold yellow]Warning: Ollama not detected. Skipping LLM analysis.[/bold yellow]")
        
    # Display Results
    table = Table(title=f"Top Investment Opportunities in {location}")
    table.add_column("Score", style="magenta", justify="center")
    table.add_column("Category", justify="center")
    if use_llm:
        table.add_column("LLM Score", style="cyan", justify="center")
    table.add_column("Price", style="green")
    table.add_column("Address")
    table.add_column("Type/Title")
    table.add_column("Link", style="blue")
    table.add_column("AI Summary", style="italic")
    
    for prop in analyzed_props[:limit]:
        score_str = f"{prop.investment_score:.1f}"
        
        # Category Styling
        cat_style = "white"
        if prop.category == "Distressed":
            cat_style = "bold red"
        elif prop.category == "Fixer Upper":
            cat_style = "bold yellow"
        elif prop.category == "Land":
            cat_style = "dim"
            
        row_data = [
            score_str,
            f"[{cat_style}]{prop.category}[/{cat_style}]",
            f"£{prop.price:,.0f}",
            prop.address,
            prop.title,
            prop.url,
            prop.ai_summary
        ]
        if use_llm:
            llm_str = f"{prop.llm_score:.1f}" if prop.llm_score else "-"
            row_data.insert(2, llm_str) # Insert after Category
            if prop.llm_reasoning:
                row_data[-1] = f"{prop.ai_summary}\n[cyan]LLM: {prop.llm_reasoning}[/cyan]"

        table.add_row(*row_data)

    console.print(table)
    
    # Save CSV option
    if csv or typer.confirm("Do you want to save these results to a CSV?"):
        import pandas as pd
        df = pd.DataFrame([vars(p) for p in analyzed_props])
        filename = f"investment_opps_{location}_{max_price}.csv"
        df.to_csv(filename, index=False)
        console.print(f"[bold green]Saved to {filename}[/bold green]")

if __name__ == "__main__":
    app()
