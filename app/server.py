"""
PyConvert FastAPI Server
REST API for folder ingestion, visual tree representation, Gemini AI conversion,
tsconfig generation, and project exporting.
"""
import os
import asyncio
import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pyconvert")
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Response, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import AVAILABLE_MODELS
from app.services.gemini_service import GeminiService
from app.services.project_scanner import ProjectScanner
from app.services.analyzer import ProjectAnalyzer
from app.services.exporter import ProjectExporter
from app.services.sample_projects import SAMPLE_PROJECTS

app = FastAPI(
    title="PyConvert - JS to TS Gemini Studio",
    description="Python-powered JavaScript to TypeScript Project Converter with Gemini AI",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request / Response Models
class ValidateKeyRequest(BaseModel):
    api_key: str
    model: str = "gemini-2.5-flash"

class ScanPathRequest(BaseModel):
    folder_path: str

class ConvertFileRequest(BaseModel):
    api_key: str
    file_path: str
    code: str
    target_extension: str
    model: str = "gemini-2.5-flash"
    strictness: str = "strict"
    project_summary: str = ""
    custom_instructions: Optional[str] = None

class BatchConvertRequest(BaseModel):
    api_key: str
    model: str = "gemini-2.5-flash"
    strictness: str = "strict"
    project_summary: str = ""
    custom_instructions: Optional[str] = None
    files: List[Dict[str, Any]]
    concurrency: int = 3

class ExportZipRequest(BaseModel):
    files: List[Dict[str, Any]]
    converted_map: Dict[str, str]
    tsconfig: Optional[str] = None
    package_json: Optional[str] = None

class ExportDiskRequest(BaseModel):
    files: List[Dict[str, Any]]
    converted_map: Dict[str, str]
    tsconfig: Optional[str] = None
    package_json: Optional[str] = None
    output_dir: str

# API Endpoints
@app.get("/api/models")
async def get_models():
    """Returns available Gemini models"""
    return {
        "models": AVAILABLE_MODELS,
        "default": "gemini-2.5-flash"
    }

@app.post("/api/validate-key")
async def validate_key(req: ValidateKeyRequest):
    """Validates the user's Gemini API key"""
    result = GeminiService.test_api_key(req.api_key, req.model)
    return result

@app.post("/api/scan-path")
async def scan_local_path(req: ScanPathRequest):
    """Scans a local directory on the filesystem and returns the project tree"""
    try:
        project_data = ProjectScanner.scan_directory(req.folder_path)
        analysis = ProjectAnalyzer.analyze_project(project_data["files"])
        recommended_tsconfig = ProjectAnalyzer.generate_tsconfig(analysis)
        
        return {
            "success": True,
            "project": project_data,
            "analysis": analysis,
            "tsconfig": recommended_tsconfig
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/samples")
async def get_samples():
    """Lists available built-in sample JavaScript projects"""
    samples = []
    for s_id, s_data in SAMPLE_PROJECTS.items():
        samples.append({
            "id": s_id,
            "name": s_data["name"],
            "description": s_data["description"],
            "icon": s_data.get("icon", "folder"),
            "file_count": len(s_data["files"])
        })
    return {"samples": samples}

@app.post("/api/load-sample/{sample_id}")
async def load_sample(sample_id: str):
    """Loads a built-in sample project into the studio workspace"""
    if sample_id not in SAMPLE_PROJECTS:
        raise HTTPException(status_code=404, detail="Sample project not found")

    sample = SAMPLE_PROJECTS[sample_id]
    files_flat = []
    stats = {
        "total_files": 0,
        "convertible_files": 0,
        "total_lines": 0,
        "convertible_lines": 0,
        "estimated_tokens": 0
    }

    # Build flat file list & tree
    for item in sample["files"]:
        rel_path = item["path"].replace("\\", "/")
        name = os.path.basename(rel_path)
        _, ext = os.path.splitext(name)
        ext = ext.lower()
        is_convertible = ext in {".js": ".ts", ".jsx": ".tsx", ".mjs": ".mts", ".cjs": ".cts"}
        target_ext = {".js": ".ts", ".jsx": ".tsx", ".mjs": ".mts", ".cjs": ".cts"}.get(ext, ext)
        target_path = rel_path[:-len(ext)] + target_ext if is_convertible else rel_path
        content = item["content"]
        lines = len(content.splitlines())

        file_obj = {
            "name": name,
            "path": rel_path,
            "abs_path": None,
            "type": "file",
            "extension": ext,
            "is_convertible": is_convertible,
            "target_extension": target_ext,
            "target_path": target_path,
            "size": len(content.encode("utf-8")),
            "lines": lines,
            "content": content,
            "status": "pending" if is_convertible else "skipped"
        }
        files_flat.append(file_obj)

        stats["total_files"] += 1
        stats["total_lines"] += lines
        if is_convertible:
            stats["convertible_files"] += 1
            stats["convertible_lines"] += lines
            stats["estimated_tokens"] += int(len(content) / 3.5) + (lines * 3)

    # Build simple tree
    tree = {"name": sample["name"], "path": ".", "type": "directory", "children": []}
    
    # Organize into tree hierarchy
    for f in files_flat:
        parts = f["path"].split("/")
        current_level = tree["children"]
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                current_level.append(f)
            else:
                found_dir = next((c for c in current_level if c.get("type") == "directory" and c.get("name") == part), None)
                if not found_dir:
                    found_dir = {
                        "name": part,
                        "path": "/".join(parts[:i+1]),
                        "type": "directory",
                        "children": []
                    }
                    current_level.append(found_dir)
                current_level = found_dir["children"]

    analysis = ProjectAnalyzer.analyze_project(files_flat)
    tsconfig = ProjectAnalyzer.generate_tsconfig(analysis)

    return {
        "success": True,
        "project": {
            "root_name": sample["name"],
            "root_path": f"[Sample: {sample['name']}]",
            "tree": tree,
            "files": files_flat,
            "stats": stats
        },
        "analysis": analysis,
        "tsconfig": tsconfig
    }

@app.post("/api/convert-file")
async def convert_file(req: ConvertFileRequest):
    """Converts a single JavaScript file to TypeScript via Gemini API"""
    logger.info(f"[/api/convert-file] Converting {req.file_path} ({len(req.code)} chars) with {req.model}")
    result = GeminiService.convert_file(
        api_key=req.api_key,
        code=req.code,
        file_path=req.file_path,
        target_extension=req.target_extension,
        model=req.model,
        strictness=req.strictness,
        project_summary=req.project_summary,
        custom_instructions=req.custom_instructions
    )
    logger.info(f"[/api/convert-file] Result for {req.file_path}: success={result.get('success')}, code_len={len(result.get('converted_code', ''))}, error={result.get('error')}")
    return result

@app.post("/api/batch-convert")
async def batch_convert(req: BatchConvertRequest):
    """
    Converts a batch of files concurrently with a bounded semaphore
    to respect Gemini API rate limits.
    """
    if not req.api_key or not req.api_key.strip():
        raise HTTPException(status_code=400, detail="Gemini API Key is required")

    sem = asyncio.Semaphore(max(1, min(req.concurrency, 5)))
    results: Dict[str, Any] = {}

    async def _convert_worker(file_info: Dict[str, Any]):
        path = file_info["path"]
        code = file_info.get("content", "")
        target_ext = file_info.get("target_extension", ".ts")
        
        async with sem:
            # Run sync conversion in thread pool to avoid blocking async loop
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(
                None,
                GeminiService.convert_file,
                req.api_key,
                code,
                path,
                target_ext,
                req.model,
                req.strictness,
                req.project_summary,
                req.custom_instructions
            )
            results[path] = res

    convertible_files = [f for f in req.files if f.get("is_convertible")]
    await asyncio.gather(*[_convert_worker(f) for f in convertible_files])

    return {
        "success": True,
        "total_processed": len(convertible_files),
        "results": results
    }

@app.post("/api/analyze-project")
async def analyze_project_endpoint(files: List[Dict[str, Any]]):
    """Analyzes files and produces tsconfig and updated package.json"""
    analysis = ProjectAnalyzer.analyze_project(files)
    tsconfig = ProjectAnalyzer.generate_tsconfig(analysis)
    
    # Find existing package.json if any
    pkg_file = next((f for f in files if f.get("path", "").lower().endswith("package.json")), None)
    pkg_content = pkg_file.get("content", "") if pkg_file else ""
    updated_pkg = ProjectAnalyzer.update_package_json(pkg_content, analysis)

    return {
        "analysis": analysis,
        "tsconfig": tsconfig,
        "updated_package_json": updated_pkg
    }

@app.post("/api/export-zip")
async def export_zip(req: ExportZipRequest):
    """Creates and returns a ZIP file of the converted project"""
    analysis = ProjectAnalyzer.analyze_project(req.files)
    tsconfig = req.tsconfig or ProjectAnalyzer.generate_tsconfig(analysis)
    
    pkg_file = next((f for f in req.files if f.get("path", "").lower().endswith("package.json")), None)
    pkg_content = pkg_file.get("content", "") if pkg_file else ""
    updated_pkg = req.package_json or ProjectAnalyzer.update_package_json(pkg_content, analysis)

    zip_bytes = ProjectExporter.create_zip_archive(
        files=req.files,
        converted_map=req.converted_map,
        tsconfig_content=tsconfig,
        updated_package_json=updated_pkg
    )

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=typescript-project.zip"}
    )

@app.post("/api/export-disk")
async def export_disk(req: ExportDiskRequest):
    """Writes the converted project to a local target directory"""
    analysis = ProjectAnalyzer.analyze_project(req.files)
    tsconfig = req.tsconfig or ProjectAnalyzer.generate_tsconfig(analysis)
    
    pkg_file = next((f for f in req.files if f.get("path", "").lower().endswith("package.json")), None)
    pkg_content = pkg_file.get("content", "") if pkg_file else ""
    updated_pkg = req.package_json or ProjectAnalyzer.update_package_json(pkg_content, analysis)

    result = ProjectExporter.export_to_directory(
        files=req.files,
        converted_map=req.converted_map,
        tsconfig_content=tsconfig,
        updated_package_json=updated_pkg,
        output_dir=req.output_dir
    )
    return result

# Serve Static UI files
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def serve_index():
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse("<h1>PyConvert is starting... static files loading</h1>")
