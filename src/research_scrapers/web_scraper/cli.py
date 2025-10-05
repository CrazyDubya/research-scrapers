"""Command-line interface for web scraper."""

import asyncio
import click
from pathlib import Path
from loguru import logger
import sys

from .scraper import WebScraper
from .config import ScraperConfig, get_preset


@click.group()
@click.option('--log-level', default='INFO', help='Logging level')
def cli(log_level: str):
    """Web Research Scraper CLI."""
    logger.remove()
    logger.add(sys.stderr, level=log_level)


@cli.command()
@click.argument('url')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file')
@click.option('--preset', '-p', help='Use preset configuration')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--format', '-f', default='json', help='Output format')
def scrape(url: str, config: str, preset: str, output: str, format: str):
    """Scrape a single URL."""
    
    # Load configuration
    if config:
        scraper_config = ScraperConfig.from_yaml(Path(config))
    elif preset:
        scraper_config = get_preset(preset)
    else:
        scraper_config = ScraperConfig()
    
    scraper_config.output_format = format
    
    async def run():
        scraper = WebScraper(scraper_config)
        try:
            result = await scraper.scrape_url(url)
            
            if output:
                scraper.save_results(result, Path(output))
            else:
                click.echo(result)
            
            # Print stats
            stats = scraper.get_stats()
            click.echo(f"\nStats: {stats}", err=True)
        
        finally:
            await scraper.close()
    
    asyncio.run(run())


@cli.command()
@click.argument('urls', nargs=-1, required=True)
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file')
@click.option('--preset', '-p', help='Use preset configuration')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--format', '-f', default='json', help='Output format')
def scrape_multiple(urls: tuple, config: str, preset: str, output: str, format: str):
    """Scrape multiple URLs."""
    
    # Load configuration
    if config:
        scraper_config = ScraperConfig.from_yaml(Path(config))
    elif preset:
        scraper_config = get_preset(preset)
    else:
        scraper_config = ScraperConfig()
    
    scraper_config.output_format = format
    
    async def run():
        scraper = WebScraper(scraper_config)
        try:
            results = await scraper.scrape_multiple(list(urls))
            
            if output:
                scraper.save_results(results, Path(output))
            else:
                for result in results:
                    click.echo(result)
            
            # Print stats
            stats = scraper.get_stats()
            click.echo(f"\nStats: {stats}", err=True)
        
        finally:
            await scraper.close()
    
    asyncio.run(run())


@cli.command()
@click.argument('url')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file')
@click.option('--preset', '-p', help='Use preset configuration')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--format', '-f', default='json', help='Output format')
@click.option('--max-pages', type=int, help='Maximum pages to scrape')
def scrape_paginated(url: str, config: str, preset: str, output: str, format: str, max_pages: int):
    """Scrape URL with pagination support."""
    
    # Load configuration
    if config:
        scraper_config = ScraperConfig.from_yaml(Path(config))
    elif preset:
        scraper_config = get_preset(preset)
    else:
        scraper_config = ScraperConfig()
    
    scraper_config.output_format = format
    scraper_config.pagination.enabled = True
    
    if max_pages:
        scraper_config.pagination.max_pages = max_pages
    
    async def run():
        scraper = WebScraper(scraper_config)
        try:
            results = await scraper.scrape_with_pagination(url)
            
            if output:
                scraper.save_results(results, Path(output))
            else:
                for result in results:
                    click.echo(result)
            
            # Print stats
            stats = scraper.get_stats()
            click.echo(f"\nScraped {len(results)} pages", err=True)
            click.echo(f"Stats: {stats}", err=True)
        
        finally:
            await scraper.close()
    
    asyncio.run(run())


@cli.command()
def list_presets():
    """List available configuration presets."""
    from .config import PRESETS
    
    click.echo("Available presets:")
    for name in PRESETS.keys():
        click.echo(f"  - {name}")


@cli.command()
@click.argument('preset')
@click.argument('output', type=click.Path())
def export_preset(preset: str, output: str):
    """Export a preset configuration to file."""
    config = get_preset(preset)
    
    output_path = Path(output)
    if output_path.suffix == '.yaml' or output_path.suffix == '.yml':
        config.to_yaml(output_path)
    elif output_path.suffix == '.json':
        config.to_json(output_path)
    else:
        click.echo("Output file must have .yaml, .yml, or .json extension", err=True)
        return
    
    click.echo(f"Exported {preset} preset to {output}")


if __name__ == '__main__':
    cli()
