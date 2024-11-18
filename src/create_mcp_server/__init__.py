import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import click
from packaging.version import parse

MIN_UV_VERSION = '0.4.10'

def check_uv_version(required_version: str) -> str | None:
    """Check if uv is installed and has minimum version"""
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True, check=True)
        version = result.stdout.strip()
        match = re.match(r"uv (\d+\.\d+\.\d+)", version)
        if match:
            version_num = match.group(1)
            if parse(version_num) >= parse(required_version):
                return version
        return None
    except subprocess.CalledProcessError:
        click.echo("❌ Error: Failed to check uv version.", err=True)
        sys.exit(1)
    except FileNotFoundError:
        return None


def ensure_uv_installed() -> None:
    """Ensure uv is installed at minimum version"""
    if check_uv_version(MIN_UV_VERSION) is None:
        click.echo(f"❌ Error: uv >= {MIN_UV_VERSION} is required but not installed.", err=True)
        click.echo("To install, visit: https://github.com/astral-sh/uv", err=True)
        sys.exit(1)


def get_claude_config_path() -> Path | None:
    """Get the Claude config directory based on platform"""
    if sys.platform == "win32":
        path = Path(Path.home(), "AppData", "Roaming", "Claude")
    elif sys.platform == "darwin":
        path = Path(Path.home(), "Library", "Application Support", "Claude")
    else:
        return None

    if path.exists():
        return path
    return None

def has_claude_app() -> bool:
    return get_claude_config_path() is not None

def update_claude_config(project_name: str, project_path: Path) -> bool:
    """Add the project to the Claude config if possible"""
    config_dir = get_claude_config_path()
    if not config_dir:
        return False

    config_file = config_dir / "claude_desktop_config.json"
    if not config_file.exists():
        return False

    try:
        config = json.loads(config_file.read_text())
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        if project_name in config["mcpServers"]:
            click.echo(f"⚠️ Warning: {project_name} already exists in Claude.app configuration", err=True)
            click.echo(f"Settings file location: {config_file}", err=True)
            return False

        config["mcpServers"][project_name] = {
            "command": "uv",
            "args": ["--directory", str(project_path), "run", project_name],
        }

        config_file.write_text(json.dumps(config, indent=2))
        click.echo(f"✅ Added {project_name} to Claude.app configuration")
        click.echo(f"Settings file location: {config_file}")
        return True
    except Exception:
        click.echo("❌ Failed to update Claude.app configuration", err=True)
        click.echo(f"Settings file location: {config_file}", err=True)
        return False


def copy_template(path: Path, name: str) -> None:
    """Copy template files into src/<project_name>"""
    template_dir = Path(__file__).parent / "template"
    src_dir = next((path / "src").glob("*/__init__.py"), None)
    if src_dir is None:
        click.echo("❌ Error: Could not find __init__.py in src directory", err=True)
        sys.exit(1)
    target_dir = src_dir.parent
    try:
        shutil.copytree(template_dir, target_dir, dirs_exist_ok=True)
    except Exception as e:
        click.echo(f"❌ Error: Failed to copy template files: {e}", err=True)
        sys.exit(1)

def create_project(path: Path, name: str, use_claude: bool = True) -> None:
    """Create a new project using uv"""
    path.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            ["uv", "init", "--name", name, "--package", "--app", "--quiet"], cwd=path, check=True
        )
    except subprocess.CalledProcessError:
        click.echo("❌ Error: Failed to initialize project.", err=True)
        sys.exit(1)

    # Add mcp dependency using uv add
    try:
        subprocess.run(["uv", "add", "mcp"], cwd=path, check=True)
    except subprocess.CalledProcessError:
        click.echo("❌ Error: Failed to add mcp dependency.", err=True)
        sys.exit(1)

    copy_template(path, name)

    # Check if Claude.app is available
    if use_claude and has_claude_app() and click.confirm("\nClaude.app detected. Would you like to install the server into Claude.app now?", default=True):
        update_claude_config(name, path)

    relpath = path.relative_to(Path.cwd())
    click.echo(f"✅ Created project {name} in {relpath}")
    click.echo("ℹ️ To install dependencies run:")
    click.echo(f"   cd {relpath}")
    click.echo("   uv sync --dev --all-extras")


def check_package_name(name: str) -> bool:
    """Check if the package name is valid according to pyproject.toml spec"""
    if not name:
        click.echo("❌ Project name cannot be empty", err=True)
        return False
    if " " in name:
        click.echo("❌ Project name must not contain spaces", err=True)
        return False
    if not all(c.isascii() and (c.isalnum() or c in "_-.") for c in name):
        click.echo("❌ Project name must consist of ASCII letters, digits, underscores, hyphens, and periods", err=True)
        return False
    if name.startswith(("_", "-", ".")) or name.endswith(("_", "-", ".")):
        click.echo("❌ Project name must not start or end with an underscore, hyphen, or period", err=True)
        return False
    return True


@click.command()
@click.option(
    "--path",
    type=click.Path(path_type=Path),
    help="Directory to create project in",
)
@click.option(
    "--name",
    type=str,
    help="Project name",
)
@click.option(
    "--claudeapp/--no-claudeapp",
    default=True,
    help="Enable/disable Claude.app integration",
)
def main(path: Path | None, name: str | None, claudeapp: bool) -> int:
    """Create a new MCP server project"""
    ensure_uv_installed()

    click.echo("Creating a new MCP server project using uv.")
    click.echo("This will set up a Python project with MCP dependency.")
    click.echo("\nLet's begin!\n")

    name = click.prompt("Project name (required)", type=str) if name is None else name

    if name is None:
        click.echo("❌ Error: Project name cannot be empty", err=True)
        return 1

    if not check_package_name(name):
        return 1

    project_path = (Path.cwd() / name) if path is None else path

    # Ask the user if the path is correct if not specified on command line
    if path is None:
        click.echo(f"Project will be created at: {project_path}")
        if not click.confirm("Is this correct?", default=True):
            project_path = Path(click.prompt("Enter the correct path", type=click.Path(path_type=Path)))

    if project_path is None:
        click.echo("❌ Error: Invalid path. Project creation aborted.", err=True)
        return 1

    create_project(project_path, name, claudeapp)

    return 0