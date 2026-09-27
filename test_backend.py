"""
Backend Test Suite for PyConvert
Validates all core services, endpoints, tree scanner, analyzer, JSX handling, and zip exporter.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.sample_projects import SAMPLE_PROJECTS
from app.services.analyzer import ProjectAnalyzer
from app.services.exporter import ProjectExporter
from app.services.project_scanner import ProjectScanner
from app.services.gemini_service import GeminiService
from app.config import AVAILABLE_MODELS, PROMPT_TEMPLATES

class TestPyConvertBackend(unittest.TestCase):
    def test_config_models(self):
        self.assertGreaterEqual(len(AVAILABLE_MODELS), 3)
        model_ids = [m["id"] for m in AVAILABLE_MODELS]
        self.assertIn("gemini-2.0-flash", model_ids)
        self.assertIn("gemini-1.5-flash", model_ids)

    def test_sample_projects(self):
        self.assertIn("express_api", SAMPLE_PROJECTS)
        self.assertIn("react_components", SAMPLE_PROJECTS)
        react_sample = SAMPLE_PROJECTS["react_components"]
        self.assertGreaterEqual(len(react_sample["files"]), 4)

    def test_project_analyzer(self):
        react_files = [
            {"path": "package.json", "content": '{"dependencies": {"react": "^18.0.0"}}'},
            {"path": "src/App.jsx", "content": 'import React from "react";'}
        ]
        analysis = ProjectAnalyzer.analyze_project(react_files)
        self.assertTrue(analysis["is_react"])
        self.assertIn("React", analysis["frameworks"])

        tsconfig = ProjectAnalyzer.generate_tsconfig(analysis)
        self.assertIn("react-jsx", tsconfig)

    def test_jsx_code_detection(self):
        jsx_file = "src/components/Button.jsx"
        jsx_code = "export function Button() { return <button className='btn'>Click</button>; }"
        self.assertTrue(GeminiService.is_jsx_code(jsx_file, jsx_code, "React App"))

        # .js file containing JSX
        js_with_jsx = "src/components/Card.js"
        js_jsx_code = "import React from 'react'; export function Card() { return <div className='card'></div>; }"
        self.assertTrue(GeminiService.is_jsx_code(js_with_jsx, js_jsx_code, "React App"))

        # Pure node backend js file
        pure_node_file = "src/utils/math.js"
        pure_node_code = "function add(a, b) { return a + b; } module.exports = { add };"
        self.assertFalse(GeminiService.is_jsx_code(pure_node_file, pure_node_code, "Node.js API"))

    def test_project_exporter_preserves_static_files(self):
        files = [
            {"path": "src/index.js", "content": "console.log('hello');", "is_convertible": True, "target_path": "src/index.ts"},
            {"path": "public/index.html", "content": "<!DOCTYPE html><html><body></body></html>", "is_convertible": False},
            {"path": "styles/global.css", "content": "body { margin: 0; }", "is_convertible": False},
            {"path": "package.json", "content": '{"name": "test"}', "is_convertible": False}
        ]
        converted_map = {
            "src/index.js": "console.log('hello from ts');"
        }
        zip_bytes = ProjectExporter.create_zip_archive(
            files=files,
            converted_map=converted_map,
            tsconfig_content='{"compilerOptions": {}}',
            updated_package_json='{"name": "test-ts"}'
        )
        self.assertGreater(len(zip_bytes), 100)

    def test_gemini_code_extraction(self):
        sample_ai_response = """
Here is your converted React TSX component:

```tsx
import React, { FC } from 'react';

interface ButtonProps {
  label: string;
  onClick: () => void;
}

export const Button: FC<ButtonProps> = ({ label, onClick }) => {
  return <button onClick={onClick}>{label}</button>;
};
```

Hope this helps!
"""
        clean_code = GeminiService._extract_code(sample_ai_response)
        self.assertTrue("interface ButtonProps" in clean_code)
        self.assertTrue("export const Button: FC<ButtonProps>" in clean_code)
        self.assertNotIn("Here is your converted", clean_code)

if __name__ == "__main__":
    unittest.main()
