"""
Project Analyzer Service
Analyzes dependencies and project files to detect frameworks (React, Express, Node, etc.)
and generates tailored tsconfig.json and updated package.json.
"""
import json
from typing import Dict, Any, List, Optional

class ProjectAnalyzer:
    @staticmethod
    def analyze_project(files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes the files flat list to determine frameworks, libraries, and project type.
        """
        frameworks = []
        is_react = False
        is_node = False
        is_vite = False
        is_next = False
        has_package_json = False
        package_json_content: Optional[Dict[str, Any]] = None

        # Look for package.json
        for f in files:
            path_lower = f["path"].lower()
            if path_lower.endswith("package.json"):
                has_package_json = True
                try:
                    package_json_content = json.loads(f.get("content", "{}"))
                    deps = {
                        **package_json_content.get("dependencies", {}),
                        **package_json_content.get("devDependencies", {})
                    }
                    if "react" in deps:
                        is_react = True
                        frameworks.append("React")
                    if "next" in deps:
                        is_next = True
                        frameworks.append("Next.js")
                    if "express" in deps or "koa" in deps or "fastify" in deps:
                        is_node = True
                        frameworks.append("Express/Node")
                    if "vite" in deps:
                        is_vite = True
                        frameworks.append("Vite")
                except Exception:
                    pass

            if f["path"].endswith((".jsx", ".tsx")):
                is_react = True
                if "React" not in frameworks:
                    frameworks.append("React")

        if not frameworks:
            frameworks.append("Vanilla JavaScript / Node.js")

        project_type = "React / Vite" if (is_react and is_vite) else ("React App" if is_react else ("Node.js API" if is_node else "Modern JavaScript"))

        summary = f"{project_type} project using {', '.join(frameworks)}."

        return {
            "project_type": project_type,
            "frameworks": frameworks,
            "is_react": is_react,
            "is_node": is_node,
            "is_vite": is_vite,
            "is_next": is_next,
            "summary": summary,
            "package_json_content": package_json_content
        }

    @staticmethod
    def generate_tsconfig(analysis: Dict[str, Any]) -> str:
        """
        Generates a recommended tsconfig.json based on project analysis.
        """
        is_react = analysis.get("is_react", False)
        is_node = analysis.get("is_node", False)
        is_vite = analysis.get("is_vite", False)

        compiler_options: Dict[str, Any] = {
            "target": "ES2022",
            "module": "ESNext" if (is_react or is_vite) else "NodeNext",
            "moduleResolution": "bundler" if (is_react or is_vite) else "NodeNext",
            "esModuleInterop": True,
            "forceConsistentCasingInFileNames": True,
            "strict": True,
            "skipLibCheck": True,
            "resolveJsonModule": True,
            "isolatedModules": True,
            "noEmit": True if (is_react or is_vite) else False
        }

        if is_react:
            compiler_options["jsx"] = "react-jsx"
            compiler_options["lib"] = ["DOM", "DOM.Iterable", "ESNext"]
        else:
            compiler_options["lib"] = ["ESNext"]
            if is_node:
                compiler_options["outDir"] = "./dist"
                compiler_options["rootDir"] = "./src"

        tsconfig = {
            "compilerOptions": compiler_options,
            "include": ["src/**/*", "**/*.ts", "**/*.tsx"],
            "exclude": ["node_modules", "dist", "build"]
        }

        return json.dumps(tsconfig, indent=2)

    @staticmethod
    def update_package_json(raw_package_json: str, analysis: Dict[str, Any]) -> str:
        """
        Enhances existing package.json with TypeScript devDependencies and build scripts.
        """
        try:
            pkg = json.loads(raw_package_json) if raw_package_json else {}
        except Exception:
            pkg = {"name": "converted-ts-project", "version": "1.0.0"}

        dev_deps = pkg.get("devDependencies", {})
        dev_deps["typescript"] = "^5.4.0"

        if analysis.get("is_react"):
            dev_deps["@types/react"] = "^18.3.0"
            dev_deps["@types/react-dom"] = "^18.3.0"
        
        if analysis.get("is_node") or not analysis.get("is_react"):
            dev_deps["@types/node"] = "^20.12.0"
            dev_deps["ts-node"] = "^10.9.2"

        pkg["devDependencies"] = dev_deps

        # Update scripts
        scripts = pkg.get("scripts", {})
        if "type-check" not in scripts:
            scripts["type-check"] = "tsc --noEmit"
        if "build" not in scripts:
            scripts["build"] = "tsc"
        pkg["scripts"] = scripts

        return json.dumps(pkg, indent=2)
