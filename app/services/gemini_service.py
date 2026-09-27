"""
Gemini Service for JavaScript to TypeScript Conversion
Direct API Integration with BYOK (Bring Your Own Key) support
"""
import re
import json
import requests
from typing import Dict, Any, Optional, Tuple
from app.config import SYSTEM_INSTRUCTION, PROMPT_TEMPLATES

# Map legacy or future aliases to active Google AI Studio models
MODEL_ALIASES = {
    "gemini-2.0-flash": "gemini-3.6-flash",
    "gemini-1.5-flash": "gemini-3.6-flash",
    "gemini-2.0-flash-lite": "gemini-3.5-flash-lite",
    "gemini-1.5-pro": "gemini-3.6-pro",
    "gemini-2.5-flash": "gemini-3.6-flash",
    "gemini-2.5-pro": "gemini-3.6-pro",
    "gemini-pro": "gemini-3.6-pro",
    "gemini-flash": "gemini-3.6-flash"
}

class GeminiService:
    _active_model_cache: Optional[str] = None

    @staticmethod
    def _normalize_model(model: str) -> str:
        model = (model or "gemini-3.6-flash").strip()
        return MODEL_ALIASES.get(model, model)

    @staticmethod
    def _resolve_working_model(api_key: str, failed_model: str, error_msg: str) -> Optional[str]:
        """
        Extracts Google's recommended replacement model from error messages or
        dynamically queries ModelService.ListModels to find an active model supporting generateContent.
        """
        # 1. Check if error message explicitly names a replacement model
        rec_match = re.search(r"models/(gemini-[\w.-]+)", error_msg)
        if rec_match:
            recommended = rec_match.group(1)
            if recommended != failed_model:
                return recommended

        # 2. Try standard active models in preference order
        for cand in ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.6-pro"]:
            if cand != failed_model:
                return cand

        # 3. Dynamic query to ModelService.ListModels
        try:
            list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key.strip()}"
            res = requests.get(list_url, timeout=10)
            if res.status_code == 200:
                models_data = res.json().get("models", [])
                for m in models_data:
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        m_name = m.get("name", "").replace("models/", "")
                        if m_name and m_name != failed_model:
                            return m_name
        except Exception:
            pass

        return "gemini-3.6-flash"

    @staticmethod
    def test_api_key(api_key: str, model: str = "gemini-3.6-flash") -> Dict[str, Any]:
        """
        Validates the provided Gemini API key by making a lightweight test query.
        """
        if not api_key or not api_key.strip():
            return {"valid": False, "error": "API key is required. Please paste your key from Google AI Studio."}

        target_model = GeminiService._normalize_model(model)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={api_key.strip()}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": "Respond with 'API_KEY_VALID' only."}]
            }],
            "generationConfig": {
                "maxOutputTokens": 10,
                "temperature": 0.0
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=12)
            
            # If model is deprecated or not found, resolve replacement
            if response.status_code != 200:
                err_text = response.text
                if "no longer available" in err_text or "not found for API version" in err_text or response.status_code == 404:
                    new_model = GeminiService._resolve_working_model(api_key, target_model, err_text)
                    if new_model and new_model != target_model:
                        target_model = new_model
                        retry_url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={api_key.strip()}"
                        retry_res = requests.post(retry_url, headers=headers, json=payload, timeout=12)
                        if retry_res.status_code == 200:
                            response = retry_res

            if response.status_code == 200:
                return {
                    "valid": True,
                    "model": target_model,
                    "message": f"Gemini API key is active and connected via {target_model}!"
                }

            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}: {response.text}")
            
            if "API key not valid" in error_msg:
                error_msg = "Invalid API Key. Please check your Gemini API key from https://aistudio.google.com/app/apikey"
            elif "quota" in error_msg.lower() or response.status_code == 429:
                error_msg = "API Quota Exceeded (429). Please wait a moment or use a different key."

            return {"valid": False, "error": error_msg}
        except Exception as e:
            return {"valid": False, "error": f"Connection error: {str(e)}"}

    @staticmethod
    def is_jsx_code(file_path: str, code: str, project_summary: str) -> bool:
        """
        Detects if a file is a React component / JSX file.
        Uses strict checks to avoid false positives on non-React JS files.
        """
        if file_path.endswith((".jsx", ".tsx")):
            return True

        # Strong signal: explicit React import
        has_react_import = bool(
            re.search(r'import\s+React', code) or
            re.search(r'from\s+[\'"]react[\'"]', code) or
            re.search(r'require\s*\(\s*[\'"]react[\'"]\s*\)', code)
        )
        if has_react_import:
            return True

        # Medium signal: JSX-specific patterns (PascalCase components + className)
        has_jsx_component = bool(re.search(r'<\s*[A-Z][A-Za-z0-9]*[\s/>]', code))
        has_classname = bool(re.search(r'className\s*=', code))
        has_jsx_fragment = bool(re.search(r'<>|</>|<React\.Fragment', code))
        has_hooks = bool(re.search(r'use(State|Effect|Ref|Memo|Callback|Context|Reducer)\s*\(', code))

        # Require at least 2 JSX signals to avoid false positives
        jsx_signals = sum([has_jsx_component, has_classname, has_jsx_fragment, has_hooks])
        if jsx_signals >= 2:
            return True

        # If project is known React, lower the threshold
        if "react" in project_summary.lower() and jsx_signals >= 1:
            return True

        return False

    @staticmethod
    def convert_file(
        api_key: str,
        code: str,
        file_path: str,
        target_extension: str,
        model: str = "gemini-2.0-flash",
        strictness: str = "strict",
        project_summary: str = "",
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends a JavaScript file to Gemini API with specialized prompt instructions
        and returns the converted TypeScript code.
        """
        if not api_key or not api_key.strip():
            return {
                "success": False,
                "error": "Gemini API Key is missing. Please click 'Set API Key' in the top bar to enter your key."
            }

        target_model = GeminiService._normalize_model(model)
        is_jsx = GeminiService.is_jsx_code(file_path, code, project_summary)
        is_node = "express" in project_summary.lower() or "node" in project_summary.lower()

        # Target extension adjustment for React components
        if is_jsx and target_extension not in [".tsx", ".jsx"]:
            target_extension = ".tsx"

        # Select prompt template
        if is_jsx:
            template = PROMPT_TEMPLATES["react"]
            source_lang = "jsx"
            target_lang = "tsx"
        elif is_node:
            template = PROMPT_TEMPLATES["node_backend"]
            source_lang = "javascript"
            target_lang = "typescript"
        elif strictness == "strict":
            template = PROMPT_TEMPLATES["strict"]
            source_lang = "javascript"
            target_lang = "typescript"
        else:
            template = PROMPT_TEMPLATES["standard"]
            source_lang = "javascript"
            target_lang = "typescript"

        user_prompt = template.format(
            file_path=file_path,
            target_extension=target_extension,
            project_summary=project_summary or "Standard modern JavaScript project",
            source_lang=source_lang,
            target_lang=target_lang,
            code=code
        )

        if custom_instructions and custom_instructions.strip():
            user_prompt += f"\n\nAdditional User Conversion Instructions:\n{custom_instructions.strip()}"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={api_key.strip()}"
        headers = {"Content-Type": "application/json"}
        
        system_content = SYSTEM_INSTRUCTION

        # Build payload with both systemInstruction (camelCase) and prompt
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_content}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 8192
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            # If 404, bad request, or deprecated model, dynamically resolve working replacement model
            if response.status_code != 200:
                err_text = response.text
                if "no longer available" in err_text or "not found for API version" in err_text or response.status_code in [404, 400]:
                    new_model = GeminiService._resolve_working_model(api_key, target_model, err_text)
                    if new_model and new_model != target_model:
                        target_model = new_model
                        fallback_url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={api_key.strip()}"
                        fb_res = requests.post(fallback_url, headers=headers, json=payload, timeout=60)
                        if fb_res.status_code == 200:
                            response = fb_res

            # If still error, retry without systemInstruction (embedding it directly in user prompt)
            if response.status_code != 200:
                fallback_payload = {
                    "contents": [{
                        "parts": [{"text": f"{system_content}\n\n{user_prompt}"}]
                    }],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 8192
                    }
                }
                retry_url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={api_key.strip()}"
                retry_res = requests.post(retry_url, headers=headers, json=fallback_payload, timeout=60)
                if retry_res.status_code == 200:
                    response = retry_res

            if response.status_code != 200:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                
                if "API key not valid" in error_msg:
                    error_msg = "Invalid Gemini API Key. Please click 'Set API Key' in the top bar to update it."
                elif response.status_code == 429 or "quota" in error_msg.lower():
                    error_msg = "Gemini API Quota Exceeded (429). Please wait a few seconds or check your plan in Google AI Studio."

                return {"success": False, "error": error_msg}

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return {"success": False, "error": "No code was generated by Gemini model."}

            candidate = candidates[0]
            finish_reason = candidate.get("finishReason", "UNKNOWN")

            if finish_reason in ["SAFETY", "RECITATION", "BLOCK", "PROHIBITED_CONTENT"]:
                return {
                    "success": False,
                    "error": f"Gemini content blocked by safety policy ({finish_reason})."
                }

            # Collect text parts, ignoring thoughts in thinking models
            content_obj = candidate.get("content", {})
            parts = content_obj.get("parts", [])
            
            non_thought_texts = []
            all_texts = []
            for p in parts:
                txt = p.get("text", "")
                if txt:
                    all_texts.append(txt)
                    if not p.get("thought", False):
                        non_thought_texts.append(txt)

            raw_text = "".join(non_thought_texts if non_thought_texts else all_texts).strip()

            if not raw_text:
                return {
                    "success": False,
                    "error": f"Gemini returned an empty response (finishReason: {finish_reason})."
                }

            converted_code = GeminiService._extract_code(raw_text)

            if not converted_code.strip():
                return {
                    "success": False,
                    "error": f"Failed to extract TypeScript code from Gemini output (finishReason: {finish_reason}). Raw output snippet: {raw_text[:200]}"
                }

            usage = data.get("usageMetadata", {})

            return {
                "success": True,
                "converted_code": converted_code,
                "target_file_path": GeminiService._get_target_file_path(file_path, target_extension),
                "model_used": target_model,
                "token_usage": usage
            }

        except requests.exceptions.Timeout:
            return {"success": False, "error": "Gemini API request timed out (60s limit). Check your internet connection."}
        except Exception as e:
            return {"success": False, "error": f"Conversion exception: {str(e)}"}

    @staticmethod
    def _extract_code(raw_text: str) -> str:
        """
        Extracts clean TypeScript / TSX code from Gemini output, handling all markdown variations.
        """
        if not raw_text:
            return ""
        text = raw_text.strip()
        
        # 1. Match fenced code blocks (```lang ... ```)
        pattern = r"```(?:typescript|tsx|ts|javascript|js|react|jsx)?[\s\r\n]*([\s\S]*?)```"
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            extracted = "\n\n".join(m.strip() for m in matches if m.strip())
            if extracted:
                return extracted

        # 2. Check for an unclosed code block (e.g. ```typescript\ncode... without closing ```)
        unclosed_match = re.search(r"```(?:typescript|tsx|ts|javascript|js|react|jsx)?[\s\r\n]*([\s\S]+)$", text, re.IGNORECASE)
        if unclosed_match:
            extracted = unclosed_match.group(1).strip()
            if extracted:
                return extracted

        # 3. Strip any leading/trailing backtick fences
        text = re.sub(r"^```[a-zA-Z0-9_-]*[\s\r\n]*", "", text)
        text = re.sub(r"[\s\r\n]*```\s*$", "", text)

        return text.strip()

    @staticmethod
    def _get_target_file_path(original_path: str, target_extension: str) -> str:
        """
        Maps a .js/.jsx file path to .ts/.tsx
        """
        for ext in [".jsx", ".js", ".mjs", ".cjs"]:
            if original_path.endswith(ext):
                return original_path[:-len(ext)] + target_extension
        return original_path + target_extension

