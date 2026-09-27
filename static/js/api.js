/**
 * PyConvert API Client
 * Facilitates all REST communication with FastAPI backend
 */

const API = {
  async getModels() {
    const res = await fetch('/api/models');
    if (!res.ok) throw new Error('Failed to fetch models');
    return res.json();
  },

  async validateKey(apiKey, model) {
    const res = await fetch('/api/validate-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey, model: model })
    });
    return res.json();
  },

  async scanPath(folderPath) {
    const res = await fetch('/api/scan-path', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder_path: folderPath })
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `Scan error: ${res.statusText}`);
    }
    return res.json();
  },

  async getSamples() {
    const res = await fetch('/api/samples');
    return res.json();
  },

  async loadSample(sampleId) {
    const res = await fetch(`/api/load-sample/${sampleId}`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to load sample');
    }
    return res.json();
  },

  async analyzeProject(files) {
    const res = await fetch('/api/analyze-project', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(files)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Analysis error: ${res.statusText}`);
    }
    return res.json();
  },

  async convertFile({ apiKey, filePath, code, targetExtension, model, strictness, projectSummary, customInstructions }) {
    const res = await fetch('/api/convert-file', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: apiKey,
        file_path: filePath,
        code: code,
        target_extension: targetExtension,
        model: model,
        strictness: strictness,
        project_summary: projectSummary,
        custom_instructions: customInstructions
      })
    });

    // Safely read response body as text first to avoid crashing on empty/non-JSON responses
    const responseText = await res.text();

    let data;
    try {
      data = JSON.parse(responseText);
    } catch (_parseErr) {
      // Response body was empty or not valid JSON
      if (!res.ok) {
        throw new Error(`Server error (HTTP ${res.status}): ${responseText.slice(0, 200) || res.statusText}`);
      }
      throw new Error(`Invalid response from server: ${responseText.slice(0, 200) || 'empty response body'}`);
    }

    if (!res.ok) {
      throw new Error(data.detail || data.error || `Server error (HTTP ${res.status})`);
    }

    if (!data.success) {
      throw new Error(data.error || 'Conversion failed');
    }
    return data;
  },

  async batchConvert({ apiKey, model, strictness, projectSummary, customInstructions, files, concurrency }) {
    const res = await fetch('/api/batch-convert', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: apiKey,
        model: model,
        strictness: strictness,
        project_summary: projectSummary,
        custom_instructions: customInstructions,
        files: files,
        concurrency: concurrency || 3
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Batch conversion error: ${res.statusText}`);
    }
    return res.json();
  },

  async exportZip({ files, convertedMap, tsconfig, packageJson }) {
    const res = await fetch('/api/export-zip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        files: files,
        converted_map: convertedMap,
        tsconfig: tsconfig,
        package_json: packageJson
      })
    });
    if (!res.ok) throw new Error('Failed to generate ZIP archive');
    return res.blob();
  },

  async exportDisk({ files, convertedMap, tsconfig, packageJson, outputDir }) {
    const res = await fetch('/api/export-disk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        files: files,
        converted_map: convertedMap,
        tsconfig: tsconfig,
        package_json: packageJson,
        output_dir: outputDir
      })
    });
    return res.json();
  }
};
