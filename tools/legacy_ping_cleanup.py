"""Disable only the three known, obsolete Autarco ping/TCP push automations.

The original diagnostic package uses list items starting with an id. Preserve
all other YAML bytes, including templates, comments, secrets and notifications.
This deliberately avoids parsing/rewriting the complete HA YAML configuration.
"""

from pathlib import Path
import os
import re
import stat
import tempfile

LEGACY_IDS = frozenset({
    "autarco_logger_offline_push",
    "autarco_modbus_local_push",
    "autarco_connection_recovered_push",
})
ID_LINE = re.compile(r"^(?P<indent> *)-\s+id:\s*(?P<quote>['\"]?)(?P<id>[a-z_]+)(?P=quote)\s*(?:#.*)?$")
SCALAR = re.compile(r":\s*[|>][+\-0-9]*\s*(?:#.*)?$")


def disable_legacy_notifications(content: bytes) -> tuple[bytes, tuple[str, ...]]:
    """Set initial_state false on exact known automation list entries."""
    text = content.decode("utf-8")
    lines = text.splitlines(keepends=True)
    changed = []
    replacements = []
    scalar_indent = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))
        if scalar_indent is not None:
            if not stripped or indent > scalar_indent:
                continue
            scalar_indent = None
        if SCALAR.search(line.rstrip("\r\n")):
            scalar_indent = indent
            continue
        match = ID_LINE.fullmatch(line.rstrip("\r\n"))
        if not match or match["id"] not in LEGACY_IDS:
            continue
        # For packages, the enclosing mapping must actually be automation.
        # Root list entries are the standard automations.yaml representation.
        if indent:
            parent = next((previous.strip() for previous in reversed(lines[:index])
                           if previous.strip() and not previous.lstrip().startswith("#")
                           and len(previous) - len(previous.lstrip(" ")) < indent), "")
            if parent != "automation:":
                continue
        end = index + 1
        while end < len(lines):
            following = lines[end]
            if following.strip() and not following.lstrip().startswith("#"):
                following_indent = len(following) - len(following.lstrip(" "))
                if following_indent <= indent:
                    break
            end += 1
        newline = "\r\n" if line.endswith("\r\n") else "\n"
        key = " " * (indent + 2) + "initial_state:"
        existing = [i for i in range(index + 1, end) if lines[i].startswith(key)]
        if len(existing) > 1:
            raise ValueError(f"Dubbele initial_state bij {match['id']}; bestand niet gewijzigd")
        desired = key + " false" + newline
        if existing:
            at = existing[0]
            current = lines[at]
            if current.partition("#")[0].strip() == "initial_state: false":
                continue
            # Preserve any inline comment on the old initial_state line.
            comment = current.partition("#")[2].rstrip("\r\n")
            if comment:
                desired = key + " false  #" + comment + newline
            replacements.append((at, at + 1, [desired]))
        else:
            if not line.endswith(("\n", "\r")):
                replacements.append((index, index + 1, [line + newline, desired]))
            else:
                replacements.append((index + 1, index + 1, [desired]))
        changed.append(match["id"])
    for start, end, replacement in sorted(replacements, reverse=True):
        lines[start:end] = replacement
    return "".join(lines).encode("utf-8"), tuple(changed)


def plan_cleanup(config: Path) -> dict[Path, tuple[bytes, bytes, tuple[str, ...]]]:
    paths = {config / "automations.yaml"}
    paths.update(config.glob("autarco_diagnostics*.yaml"))
    packages = config / "packages"
    if packages.is_dir() and not packages.is_symlink():
        paths.update(packages.rglob("*.yaml"))
        paths.update(packages.rglob("*.yml"))
    changes = {}
    for file in sorted(paths):
        if not file.is_file() or file.is_symlink() or not file.resolve().is_relative_to(config.resolve()):
            continue
        before = file.read_bytes()
        # Skip unrelated files without decoding or touching their contents.
        if not any(identifier.encode() in before for identifier in LEGACY_IDS):
            continue
        after, identifiers = disable_legacy_notifications(before)
        if after != before:
            changes[file] = (before, after, identifiers)
    return changes


def replace_file(file: Path, expected: bytes, replacement: bytes) -> None:
    """Write atomically, retaining file mode and guarding concurrent edits."""
    if file.read_bytes() != expected:
        raise ValueError(f"Bestand tijdens deploy gewijzigd: {file.name}")
    mode = stat.S_IMODE(file.stat().st_mode)
    fd, staging = tempfile.mkstemp(prefix=".autarco-notifications-", dir=file.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(replacement)
        os.chmod(staging, mode)
        os.replace(staging, file)
    finally:
        if os.path.exists(staging):
            os.unlink(staging)
