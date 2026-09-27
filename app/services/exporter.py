"""
Project Exporter Service
Packages converted TypeScript files and original static assets into in-memory ZIP archives
or writes directly to a target directory.
"""
import io
import os
import zipfile
from typing import Dict, Any, List

class ProjectExporter:
    @staticmethod
    def create_zip_archive(
        files: List[Dict[str, Any]],
        converted_map: Dict[str, str],
        tsconfig_content: str,
        updated_package_json: str
    ) -> bytes:
        """
        Creates an in-memory ZIP archive of the converted TypeScript project.
        """
        zip_buffer = io.BytesIO()
        has_tsconfig = False
        has_package_json = False

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for f in files:
                rel_path = f["path"]
                
                # Check if this file was converted
                if f["is_convertible"] and rel_path in converted_map:
                    target_path = f.get("target_path", rel_path)
                    content = converted_map[rel_path]
                    zip_file.writestr(target_path, content.encode("utf-8"))
                elif rel_path.lower().endswith("package.json"):
                    has_package_json = True
                    content = updated_package_json if updated_package_json else f.get("content", "")
                    zip_file.writestr(rel_path, content.encode("utf-8"))
                elif rel_path.lower().endswith("tsconfig.json"):
                    has_tsconfig = True
                    content = f.get("content", tsconfig_content)
                    zip_file.writestr(rel_path, content.encode("utf-8"))
                else:
                    # Non-convertible file (css, html, json, etc.)
                    # If it has content in memory, write it
                    if f.get("content") is not None:
                        zip_file.writestr(rel_path, f["content"].encode("utf-8"))
                    elif f.get("abs_path") and os.path.exists(f["abs_path"]):
                        try:
                            with open(f["abs_path"], "rb") as raw_f:
                                zip_file.writestr(rel_path, raw_f.read())
                        except Exception:
                            pass

            # Inject tsconfig.json if not present
            if not has_tsconfig and tsconfig_content:
                zip_file.writestr("tsconfig.json", tsconfig_content.encode("utf-8"))

            # Inject package.json if not present
            if not has_package_json and updated_package_json:
                zip_file.writestr("package.json", updated_package_json.encode("utf-8"))

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    @staticmethod
    def export_to_directory(
        files: List[Dict[str, Any]],
        converted_map: Dict[str, str],
        tsconfig_content: str,
        updated_package_json: str,
        output_dir: str
    ) -> Dict[str, Any]:
        """
        Exports the converted TypeScript project directly to a local filesystem directory.
        """
        os.makedirs(output_dir, exist_ok=True)
        has_tsconfig = False
        has_package_json = False
        written_count = 0

        for f in files:
            rel_path = f["path"]
            if f["is_convertible"] and rel_path in converted_map:
                target_path = f.get("target_path", rel_path)
                out_path = os.path.join(output_dir, target_path)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with open(out_path, "w", encoding="utf-8") as out_f:
                    out_f.write(converted_map[rel_path])
                written_count += 1
            elif rel_path.lower().endswith("package.json"):
                has_package_json = True
                out_path = os.path.join(output_dir, rel_path)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with open(out_path, "w", encoding="utf-8") as out_f:
                    out_f.write(updated_package_json if updated_package_json else f.get("content", "{}"))
                written_count += 1
            elif rel_path.lower().endswith("tsconfig.json"):
                has_tsconfig = True
                out_path = os.path.join(output_dir, rel_path)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with open(out_path, "w", encoding="utf-8") as out_f:
                    out_f.write(f.get("content", tsconfig_content))
                written_count += 1
            else:
                out_path = os.path.join(output_dir, rel_path)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                if f.get("content") is not None:
                    with open(out_path, "w", encoding="utf-8") as out_f:
                        out_f.write(f["content"])
                    written_count += 1
                elif f.get("abs_path") and os.path.exists(f["abs_path"]):
                    try:
                        with open(f["abs_path"], "rb") as in_f, open(out_path, "wb") as out_f:
                            out_f.write(in_f.read())
                        written_count += 1
                    except Exception:
                        pass

        if not has_tsconfig and tsconfig_content:
            with open(os.path.join(output_dir, "tsconfig.json"), "w", encoding="utf-8") as out_f:
                out_f.write(tsconfig_content)
            written_count += 1

        if not has_package_json and updated_package_json:
            with open(os.path.join(output_dir, "package.json"), "w", encoding="utf-8") as out_f:
                out_f.write(updated_package_json)
            written_count += 1

        return {
            "success": True,
            "output_dir": os.path.abspath(output_dir),
            "files_written": written_count
        }
