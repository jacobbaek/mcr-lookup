#!/usr/bin/env python3
import sys
import requests
import json

BASE = "https://mcr.microsoft.com/v2"
TIMEOUT = 10


def print_table(headers, rows):
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, col in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(col)))

    print(" | ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers))))
    print("-+-".join("-" * w for w in col_widths))

    for row in rows:
        print(" | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row))))


def catalog(table=False):
    r = requests.get(f"{BASE}/_catalog", timeout=TIMEOUT)

    if r.status_code != 200:
        print("❌ MCR does NOT allow full catalog listing via API")
        return

    data = r.json()

    if table:
        rows = [[repo] for repo in data.get("repositories", [])]
        print_table(["REPOSITORY"], rows)
    else:
        print(json.dumps(data, indent=2))


def tags(repo, table=False):
    r = requests.get(f"{BASE}/{repo}/tags/list", timeout=TIMEOUT)

    if r.status_code == 404:
        print(f"❌ repository not found: {repo}")
        return

    if r.status_code != 200:
        print(f"❌ tags fetch failed: {r.status_code}")
        return

    data = r.json()

    if table:
        rows = [[t] for t in data.get("tags", [])]
        print_table(["TAG"], rows)
    else:
        print(json.dumps(data, indent=2))


def get_image_manifest(repo, tag):
    headers = {
        "Accept": ",".join([
            "application/vnd.oci.image.index.v1+json",
            "application/vnd.docker.distribution.manifest.list.v2+json",
            "application/vnd.oci.image.manifest.v1+json",
            "application/vnd.docker.distribution.manifest.v2+json"
        ])
    }

    r = requests.get(f"{BASE}/{repo}/manifests/{tag}", headers=headers, timeout=TIMEOUT)

    if r.status_code == 404:
        print(f"❌ manifest not found: {repo}:{tag}")
        return None

    if r.status_code != 200:
        print(f"❌ manifest fetch failed: {r.status_code}")
        return None

    data = r.json()

    if "manifests" in data:
        for m in data["manifests"]:
            p = m.get("platform", {})
            if p.get("architecture") == "amd64" and p.get("os") == "linux":
                digest = m["digest"]

                r2 = requests.get(
                    f"{BASE}/{repo}/manifests/{digest}",
                    headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"},
                    timeout=TIMEOUT
                )

                if r2.status_code != 200:
                    print(f"❌ sub-manifest fetch failed: {r2.status_code}")
                    return None

                return r2.json()

        print("❌ no amd64/linux manifest found")
        return None

    return data


def manifest(repo, tag, table=False):
    headers = {
        "Accept": ",".join([
            "application/vnd.oci.image.index.v1+json",
            "application/vnd.docker.distribution.manifest.list.v2+json",
            "application/vnd.oci.image.manifest.v1+json",
            "application/vnd.docker.distribution.manifest.v2+json"
        ])
    }

    r = requests.get(f"{BASE}/{repo}/manifests/{tag}", headers=headers, timeout=TIMEOUT)

    if r.status_code == 404:
        print(f"❌ manifest not found: {repo}:{tag}")
        return

    if r.status_code != 200:
        print(f"❌ manifest fetch failed: {r.status_code}")
        return

    if not table:
        print(json.dumps(r.json(), indent=2))
        return

    data = r.json()

    # multi-arch
    if "manifests" in data:
        rows = []
        for m in data["manifests"]:
            p = m.get("platform", {})
            rows.append([
                p.get("os", ""),
                p.get("architecture", ""),
                m.get("digest", "")[:20]
            ])
        print_table(["OS", "ARCH", "DIGEST"], rows)

    # single image
    elif "layers" in data:
        rows = []
        for l in data["layers"]:
            rows.append([
                l.get("mediaType", "").split(".")[-1],
                str(l.get("size", "")),
                l.get("digest", "")[:20]
            ])
        print_table(["TYPE", "SIZE", "DIGEST"], rows)


def created(repo, tag, table=False):
    manifest = get_image_manifest(repo, tag)

    if not manifest:
        return

    config_digest = manifest.get("config", {}).get("digest")

    if not config_digest:
        print("❌ config digest not found")
        return

    blob_resp = requests.get(f"{BASE}/{repo}/blobs/{config_digest}", timeout=TIMEOUT)

    if blob_resp.status_code != 200:
        print(f"❌ blob fetch failed: {blob_resp.status_code}")
        return

    blob = blob_resp.json()
    created_time = blob.get("created", "N/A")

    if table:
        print_table(["REPO", "TAG", "CREATED"], [[repo, tag, created_time]])
    else:
        print(json.dumps({
            "repo": repo,
            "tag": tag,
            "created": created_time
        }, indent=2))


def usage():
    print("""
Usage:
  mcrlookup.py catalog [--table]
  mcrlookup.py tags <repo> [--table]
  mcrlookup.py manifest <repo> <tag> [--table]
  mcrlookup.py created <repo> <tag> [--table]

Examples:
  mcrlookup.py created aks/eviction-autoscaler 1.0.0 --table
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    cmd = sys.argv[1]
    table = "--table" in sys.argv

    if cmd == "catalog":
        catalog(table)

    elif cmd == "tags" and len(sys.argv) >= 3:
        tags(sys.argv[2], table)

    elif cmd == "manifest" and len(sys.argv) >= 4:
        manifest(sys.argv[2], sys.argv[3], table)

    elif cmd == "created" and len(sys.argv) >= 4:
        created(sys.argv[2], sys.argv[3], table)

    else:
        usage()
