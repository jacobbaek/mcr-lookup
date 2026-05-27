# mcr-lookup

A CLI tool for querying Microsoft Container Registry (MCR) image metadata.

## Requirements

- Python 3
- `requests` library

```
pip install requests
```

## Usage

```
mcrlookup.py catalog [--table]
mcrlookup.py tags <repo> [--table]
mcrlookup.py manifest <repo> <tag> [--table]
mcrlookup.py created <repo> <tag> [--table]
```

### Commands

| Command | Description |
|---------|-------------|
| `catalog` | List all repositories in MCR |
| `tags` | List available tags for a repository |
| `manifest` | Show manifest details (layers, platforms) for a specific image tag |
| `created` | Show the creation timestamp of an image (resolves amd64/linux by default) |

### Options

- `--table` : Display output in a formatted table instead of raw JSON.

## Examples

List tags for a repository:

```
python mcrlookup.py tags aks/eviction-autoscaler --table
```

Check when an image was created:

```
python mcrlookup.py created aks/eviction-autoscaler 1.0.0 --table
```

View manifest platforms:

```
python mcrlookup.py manifest aks/eviction-autoscaler 1.0.0 --table
```
