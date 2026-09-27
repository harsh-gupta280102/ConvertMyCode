"""
PyConvert Configuration & Built-in Prompt System
"""
import os
from pydantic import BaseModel
from typing import Dict, Any, List

DEFAULT_PORT = 8000
DEFAULT_HOST = "127.0.0.1"

# Supported Gemini models for JS -> TS conversion (official Google AI Studio models)
AVAILABLE_MODELS = [
    {
        "id": "gemini-3.6-flash",
        "name": "Gemini 3.6 Flash",
        "badge": "Recommended & Fastest",
        "description": "Latest next-generation coding and reasoning model."
    },
    {
        "id": "gemini-3.5-flash-lite",
        "name": "Gemini 3.5 Flash Lite",
        "badge": "Ultra Fast & Cost-effective",
        "description": "High-throughput and lightweight model for rapid transformation."
    },
    {
        "id": "gemini-3.6-pro",
        "name": "Gemini 3.6 Pro",
        "badge": "Deep Reasoning",
        "description": "Highest reasoning quality for complex codebases & deep generics."
    },
    {
        "id": "gemini-2.0-flash",
        "name": "Gemini 2.0 Flash (Auto-mapped)",
        "badge": "Auto-mapped",
        "description": "Legacy alias automatically routed to Gemini 3.6 Flash."
    },
    {
        "id": "gemini-1.5-flash",
        "name": "Gemini 1.5 Flash (Auto-mapped)",
        "badge": "Auto-mapped",
        "description": "Legacy alias automatically routed to Gemini 3.6 Flash."
    }
]

# System Instructions tailored for JavaScript to TypeScript conversion
SYSTEM_INSTRUCTION = """You are an expert TypeScript and React compiler, architect, and developer.
Your mission is to convert JavaScript code (.js, .jsx, .mjs, .cjs) into clean, modern, strongly-typed TypeScript (.ts, .tsx).

Strict Conversion Rules:
1. Preserve all runtime logic, JSX component hierarchy, event handlers, and algorithms exactly.
2. Infer precise and accurate TypeScript types, interfaces, generics, and return types.
3. For React JSX / Components (.jsx -> .tsx or React .js -> .tsx):
   - Define explicit TypeScript interfaces or types for all Component Props (e.g. `interface ButtonProps { ... }`).
   - Strongly type Component functions: `export const Button: React.FC<ButtonProps> = ...` or `export function Button({ ... }: ButtonProps): JSX.Element`.
   - Strongly type all Hooks (`useState<T>`, `useRef<T>`, `useMemo<T>`, `useCallback`, `useContext`).
   - Type all Event handlers (e.g., `React.MouseEvent<HTMLButtonElement>`, `React.ChangeEvent<HTMLInputElement>`, `React.FormEvent`).
   - Import necessary React types (`import React, { FC, ReactNode, useState, useEffect } from 'react'`).
4. For Node.js / Express / Backend:
   - Convert CommonJS (`require`, `module.exports`) to ESM (`import`, `export`).
   - Type Express `Request`, `Response`, `NextFunction`, middleware, and database models.
5. For async functions: Ensure correct `Promise<T>` return types.
6. Output Format:
   - Output ONLY the converted TypeScript / TSX code inside a single ```tsx (or ```typescript) code block.
   - Do NOT include any introductory or concluding conversational text.
   - The returned code must be syntactically valid TypeScript / TSX ready to compile with zero syntax errors.
"""

PROMPT_TEMPLATES: Dict[str, str] = {
    "standard": """Convert the following JavaScript file into TypeScript ({target_extension}).

File Path: {file_path}
Project Context: {project_summary}

JavaScript Source Code:
```{source_lang}
{code}
```

Output ONLY the complete converted TypeScript code in a ```{target_lang} code block.""",

    "strict": """Convert the following JavaScript file into strict, high-fidelity TypeScript ({target_extension}).
Enforce strict TypeScript rules:
- Explicit interfaces for all object structures, function parameters, and return types.
- Avoid 'any'. Use precise generics, union types, or unknown.

File Path: {file_path}
Project Context: {project_summary}

JavaScript Source Code:
```{source_lang}
{code}
```

Output ONLY the complete converted TypeScript code in a ```{target_lang} code block.""",

    "react": """Convert the following React JSX/JS component into React TypeScript ({target_extension}).
Requirements:
- Define comprehensive Props interfaces for all components.
- Strongly type all React Hooks (`useState<T>`, `useRef<T>`, etc.) and custom hooks.
- Type all DOM events (`React.MouseEvent`, `React.ChangeEvent`, etc.).
- Ensure all JSX elements, children (`React.ReactNode`), and CSS classes are fully preserved.

File Path: {file_path}
Project Context: {project_summary}

React JSX Code:
```{source_lang}
{code}
```

Output ONLY the complete converted React TSX code in a ```tsx code block.""",

    "node_backend": """Convert the following Node.js / Express JavaScript file into TypeScript ({target_extension}).
Requirements:
- Convert CommonJS to ESM `import`/`export` syntax.
- Type Express route handlers, middleware, request/response objects.
- Declare interfaces for all database models and API payloads.

File Path: {file_path}
Project Context: {project_summary}

Node.js Code:
```{source_lang}
{code}
```

Output ONLY the complete converted TypeScript code in a ```{target_lang} code block."""
}

