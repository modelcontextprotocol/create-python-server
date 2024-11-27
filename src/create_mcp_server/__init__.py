import json
import re
import subprocess
import sys
from pathlib import Path

import click
import toml
from packaging.version import parse

MIN_UV_VERSION = "0.4.10"


class PyProject:
    def __init__(self, path: Path):
        self.data = toml.load(path)

    @property
    def name(self) -> str:
        return self.data["project"]["name"]

    @property
    def first_binary(self) -> str | None:
        scripts = self.data["project"].get("scripts", {})
        return next(iter(scripts.keys()), None)


def check_uv_version(required_version: str) -> str | None:
    """Check if uv is installed and has minimum version"""
    try:
        result = subprocess.run(
            ["uv", "--version"], capture_output=True, text=True, check=True
        )
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
        click.echo(
            f"❌ Error: uv >= {MIN_UV_VERSION} is required but not installed.", err=True
        )
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
            click.echo(
                f"⚠️ Warning: {project_name} already exists in Claude.app configuration",
                err=True,
            )
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


def get_package_directory(path: Path) -> Path:
    """Find the package directory under src/"""
    src_dir = next((path / "src").glob("*/__init__.py"), None)
    if src_dir is None:
        click.echo("❌ Error: Could not find __init__.py in src directory", err=True)
        sys.exit(1)
    return src_dir.parent


def copy_template(
    path: Path, name: str, description: str, version: str = "0.1.0"
) -> None:
    """Copy template files into src/<project_name>"""
    template_dir = Path(__file__).parent / "template"

    target_dir = get_package_directory(path)

    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(template_dir)))

    files = [
        ("__init__.py.jinja2", "__init__.py", target_dir),
        ("server.py.jinja2", "server.py", target_dir),
        ("README.md.jinja2", "README.md", path),
        ("test_server.py.jinja2", "test_server.py", target_dir),
    ]

    pyproject = PyProject(path / "pyproject.toml")
    bin_name = pyproject.first_binary

    template_vars = {
        "binary_name": bin_name,
        "server_name": name,
        "server_version": version,
        "server_description": description,
        "server_directory": str(path.resolve()),
    }

    try:
        for template_file, output_file, output_dir in files:
            template = env.get_template(template_file)
            rendered = template.render(**template_vars)

            out_path = output_dir / output_file
            out_path.write_text(rendered)

    except Exception as e:
        click.echo(f"❌ Error: Failed to template and write files: {e}", err=True)
        sys.exit(1)


def create_project(
    path: Path, name: str, description: str, version: str, use_claude: bool = True
) -> None:
    """Create a new project using uv"""
    path.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            ["uv", "init", "--name", name, "--package", "--app", "--quiet"],
            cwd=path,
            check=True,
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

    copy_template(path, name, description, version)

    # Check if Claude.app is available
    if (
        use_claude
        and has_claude_app()
        and click.confirm(
            "\nClaude.app detected. Would you like to install the server into Claude.app now?",
            default=True,
        )
    ):
        update_claude_config(name, path)

    relpath = path.relative_to(Path.cwd())
    click.echo(f"✅ Created project {name} in {relpath}")
    click.echo("ℹ️ To install dependencies run:")
    click.echo(f"   cd {relpath}")
    click.echo("   uv sync --dev --all-extras")


def update_pyproject_settings(
    project_path: Path, version: str, description: str
) -> None:
    """Update project version and description in pyproject.toml"""
    import toml

    pyproject_path = project_path / "pyproject.toml"

    if not pyproject_path.exists():
        click.echo("❌ Error: pyproject.toml not found", err=True)
        sys.exit(1)

    try:
        pyproject = toml.load(pyproject_path)

        if version is not None:
            pyproject["project"]["version"] = version

        if description is not None:
            pyproject["project"]["description"] = description

        pyproject_path.write_text(toml.dumps(pyproject))

    except Exception as e:
        click.echo(f"❌ Error updating pyproject.toml: {e}", err=True)
        sys.exit(1)


def check_package_name(name: str) -> bool:
    """Check if the package name is valid according to pyproject.toml spec"""
    if not name:
        click.echo("❌ Project name cannot be empty", err=True)
        return False
    if " " in name:
        click.echo("❌ Project name must not contain spaces", err=True)
        return False
    if not all(c.isascii() and (c.isalnum() or c in "_-.") for c in name):
        click.echo(
            "❌ Project name must consist of ASCII letters, digits, underscores, hyphens, and periods",
            err=True,
        )
        return False
    if name.startswith(("_", "-", ".")) or name.endswith(("_", "-", ".")):
        click.echo(
            "❌ Project name must not start or end with an underscore, hyphen, or period",
            err=True,
        )
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
    "--version",
    type=str,
    help="Server version",
)
@click.option(
    "--description",
    type=str,
    help="Project description",
)
@click.option(
    "--claudeapp/--no-claudeapp",
    default=True,
    help="Enable/disable Claude.app integration",
)
def main(
    path: Path | None,
    name: str | None,
    version: str | None,
    description: str | None,
    claudeapp: bool,
) -> int:
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

    description = (
        click.prompt("Project description", type=str, default="A MCP server project")
        if description is None
        else description
    )

    assert isinstance(description, str)

    # Validate version if not supplied on command line
    if version is None:
        version = click.prompt("Project version", default="0.1.0", type=str)
        assert isinstance(version, str)
        try:
            parse(version)  # Validate semver format
        except Exception:
            click.echo(
                "❌ Error: Version must be a valid semantic version (e.g. 1.0.0)",
                err=True,
            )
            return 1

    project_path = (Path.cwd() / name) if path is None else path

    # Ask the user if the path is correct if not specified on command line
    if path is None:
        click.echo(f"Project will be created at: {project_path}")
        if not click.confirm("Is this correct?", default=True):
            project_path = Path(
                click.prompt("Enter the correct path", type=click.Path(path_type=Path))
            )

    if project_path is None:
        click.echo("❌ Error: Invalid path. Project creation aborted.", err=True)
        return 1

    project_path = project_path.resolve()

    create_project(project_path, name, description, version, claudeapp)
    update_pyproject_settings(project_path, version, description)

    return 0
