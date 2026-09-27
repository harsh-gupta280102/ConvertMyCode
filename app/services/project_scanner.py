"""
Project Scanner Service
Scans local or in-memory project structures, generates visual tree hierarchies,
and analyzes project metadata and metrics.
"""
import os
import mimetypes
from typing import Dict, Any, List, Optional

import re

IGNORE_DIRS = {
    "node_modules", ".git", "dist", "build", ".next", ".nuxt",
    ".cache", "coverage", "__pycache__", ".venv", "venv", ".idea", ".vscode"
}

IGNORE_FILES = {
    ".DS_Store", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Thumbs.db"
}

# Only JavaScript / React extensions are converted to TypeScript
CONVERTIBLE_EXTENSIONS = {
    ".js": ".ts",
    ".jsx": ".tsx",
    ".mjs": ".mts",
    ".cjs": ".cts"
}

class ProjectScanner:
    @staticmethod
    def scan_directory(dir_path: str) -> Dict[str, Any]:
        """
        Recursively scans a local folder path and constructs a structured tree.
        """
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            raise ValueError(f"Directory not found: {dir_path}")

        root_name = os.path.basename(os.path.abspath(dir_path))
        files_flat: List[Dict[str, Any]] = []
        stats = {
            "total_files": 0,
            "convertible_files": 0,
            "static_files": 0,
            "total_lines": 0,
            "convertible_lines": 0,
            "estimated_tokens": 0
        }

        tree = ProjectScanner._scan_node(
            dir_path=dir_path,
            rel_path="",
            files_flat=files_flat,
            stats=stats
        )

        return {
            "root_name": root_name,
            "root_path": os.path.abspath(dir_path),
            "tree": tree,
            "files": files_flat,
            "stats": stats
        }

    @staticmethod
    def _scan_node(
        dir_path: str,
        rel_path: str,
        files_flat: List[Dict[str, Any]],
        stats: Dict[str, int]
    ) -> Dict[str, Any]:
        node_name = os.path.basename(dir_path)
        children: List[Dict[str, Any]] = []

        try:
            entries = sorted(os.scandir(dir_path), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return {"name": node_name, "type": "directory", "children": [], "error": "Permission Denied"}

        for entry in entries:
            if entry.name in IGNORE_DIRS or entry.name in IGNORE_FILES:
                continue

            entry_rel_path = os.path.join(rel_path, entry.name).replace("\\", "/")

            if entry.is_dir():
                sub_tree = ProjectScanner._scan_node(
                    dir_path=entry.path,
                    rel_path=entry_rel_path,
                    files_flat=files_flat,
                    stats=stats
                )
                children.append(sub_tree)
            elif entry.is_file():
                file_info = ProjectScanner._process_file(entry.path, entry_rel_path)
                children.append(file_info)
                files_flat.append(file_info)

                # Stats update
                stats["total_files"] += 1
                stats["total_lines"] += file_info["lines"]
                if file_info["is_convertible"]:
                    stats["convertible_files"] += 1
                    stats["convertible_lines"] += file_info["lines"]
                    stats["estimated_tokens"] += int(file_info["size"] / 3.5) + (file_info["lines"] * 3)
                else:
                    stats["static_files"] += 1

        return {
            "name": node_name,
            "path": rel_path or ".",
            "type": "directory",
            "children": children
        }

    @staticmethod
    def _process_file(abs_path: str, rel_path: str) -> Dict[str, Any]:
        _, ext = os.path.splitext(abs_path)
        ext = ext.lower()

        is_convertible = ext in CONVERTIBLE_EXTENSIONS
        lines = 0
        size = 0
        content = ""

        try:
            size = os.path.getsize(abs_path)
            # Only read text files into memory if size < 2MB
            if size < 2 * 1024 * 1024:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                    lines = len(content.splitlines())
        except Exception:
            lines = 0

        # Detect if .js contains React / JSX syntax (strict detection)
        is_jsx = False
        if ext == ".jsx":
            is_jsx = True
        elif ext == ".js" and is_convertible:
            has_react_import = bool(
                re.search(r'import\s+React', content) or
                re.search(r'from\s+[\'"]react[\'"]', content) or
                re.search(r'require\s*\(\s*[\'"]react[\'"]\s*\)', content)
            )
            if has_react_import:
                is_jsx = True
            else:
                jsx_signals = sum([
                    bool(re.search(r'<\s*[A-Z][A-Za-z0-9]*[\s/>]', content)),
                    bool(re.search(r'className\s*=', content)),
                    bool(re.search(r'<>|</>|<React\.Fragment', content)),
                    bool(re.search(r'use(State|Effect|Ref|Memo|Callback|Context|Reducer)\s*\(', content))
                ])
                is_jsx = jsx_signals >= 2

        target_ext = ".tsx" if is_jsx else CONVERTIBLE_EXTENSIONS.get(ext, ext)
        target_rel_path = ProjectScanner._get_target_rel_path(rel_path, ext, target_ext) if is_convertible else rel_path

        return {
            "name": os.path.basename(abs_path),
            "path": rel_path,
            "abs_path": abs_path,
            "type": "file",
            "extension": ext,
            "is_convertible": is_convertible,
            "is_jsx": is_jsx,
            "target_extension": target_ext,
            "target_path": target_rel_path,
            "size": size,
            "lines": lines,
            "content": content,
            "status": "pending" if is_convertible else "unmodified"
        }

    @staticmethod
    def _get_target_rel_path(rel_path: str, original_ext: str, target_ext: str) -> str:
        if original_ext in CONVERTIBLE_EXTENSIONS:
            return rel_path[:-len(original_ext)] + target_ext
        return rel_path

