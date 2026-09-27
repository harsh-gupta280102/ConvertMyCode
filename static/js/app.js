/**
 * PyConvert Main Application Controller
 * Orchestrates state, API key BYOK management, batch conversion, and project lifecycle.
 */

const AppState = {
  apiKey: localStorage.getItem('pyconvert_gemini_api_key') || '',
  selectedModel: (() => {
    const saved = localStorage.getItem('pyconvert_gemini_model');
    if (!saved || saved === 'gemini-1.5-flash' || saved === 'gemini-2.0-flash' || saved === 'gemini-2.0-flash-lite') {
      return 'gemini-3.6-flash';
    }
    return saved;
  })(),
  strictness: 'strict',
  customInstructions: '',
  concurrency: 3,

  project: null,
  analysis: null,
  recommendedTsconfig: null,
  convertedMap: {}, // filePath -> converted TypeScript code
  activeFile: null,
  isConvertingBatch: false,

  getActiveConvertedCode() {
    if (!this.activeFile) return '';
    return this.activeFile.converted_code || this.convertedMap[this.activeFile.path] || '';
  },

  setActiveConvertedCode(code) {
    if (!this.activeFile) return;
    this.activeFile.converted_code = code;
    this.convertedMap[this.activeFile.path] = code;
    this.activeFile.status = 'converted';
    TreeViewer.updateNodeStatus(this.activeFile.path, 'converted');
    this.updateStats();
  },

  selectFile(fileObj) {
    this.activeFile = fileObj;
    
    // Update studio top bar
    document.getElementById('active-file-path').textContent = fileObj.path;
    document.getElementById('active-file-icon').textContent = TreeViewer.getFileIcon(fileObj.name, fileObj.extension);
    
    const badge = document.getElementById('active-file-badge');
    badge.style.display = 'inline-block';
    
    const isConv = fileObj.is_convertible;
    const statusText = isConv ? (fileObj.status || 'pending').toUpperCase() : 'STATIC';
    badge.textContent = statusText;
    badge.className = `file-status-badge ${isConv ? fileObj.status : 'unmodified'}`;

    const btnConvertSingle = document.getElementById('btn-convert-single');
    btnConvertSingle.disabled = !isConv || this.isConvertingBatch;
    btnConvertSingle.querySelector('span').textContent = isConv ? 'Convert File' : 'Static File (Preserved)';

    // Render original code in source panel
    EditorManager.renderSourceCode(fileObj.content, fileObj.extension);

    // Render converted code or static notice in target panel
    if (isConv) {
      const convertedCode = fileObj.converted_code || this.convertedMap[fileObj.path] || '';
      EditorManager.renderTargetCode(convertedCode, fileObj.target_extension);
    } else {
      const staticNotice = `// 🔒 Static File (Preserved As-Is)\n// This file (${fileObj.name}) is not a JavaScript file.\n// It is preserved unchanged in your converted project archive.`;
      EditorManager.renderTargetCode(staticNotice, fileObj.extension);
    }
  },

  updateStats() {
    if (!this.project) return;
    const total = this.project.stats.convertible_files;
    const converted = Object.keys(this.convertedMap).length;
    
    document.getElementById('stat-file-count').textContent = `${converted}/${total} TS`;
    document.getElementById('stat-lines').textContent = `${this.project.stats.total_lines} loc`;
    
    if (this.analysis) {
      document.getElementById('stat-framework').textContent = this.analysis.project_type;
    }

    const btnExport = document.getElementById('btn-export-zip');
    btnExport.disabled = converted === 0;

    const btnConvertAll = document.getElementById('btn-convert-all');
    btnConvertAll.disabled = total === 0 || this.isConvertingBatch;
  }
};

// UI Initializer
document.addEventListener('DOMContentLoaded', () => {
  EditorManager.init();
  TreeViewer.init();
  initModals();
  initDropZone();
  initFolderUpload();
  initSampleButtons();
  initConvertButtons();
  initExportButton();
  updateApiKeyStatusUI();
});

/* ==========================================================================
   Modals & API Key Management
   ========================================================================== */

function initModals() {
  const modalApiKey = document.getElementById('modal-api-key');
  const modalSettings = document.getElementById('modal-settings');
  const modalScanPath = document.getElementById('modal-scan-path');

  // Open API Key Modal
  document.getElementById('btn-api-key').addEventListener('click', () => {
    document.getElementById('input-api-key').value = AppState.apiKey;
    document.getElementById('modal-model-select').value = AppState.selectedModel;
    document.getElementById('key-validation-alert').style.display = 'none';
    modalApiKey.style.display = 'flex';
  });

  document.getElementById('btn-close-key-modal').addEventListener('click', () => {
    modalApiKey.style.display = 'none';
  });

  // Toggle API Key password visibility
  document.getElementById('btn-toggle-key-visibility').addEventListener('click', () => {
    const input = document.getElementById('input-api-key');
    input.type = input.type === 'password' ? 'text' : 'password';
  });

  // Test Key Connection
  document.getElementById('btn-test-key').addEventListener('click', async () => {
    const key = document.getElementById('input-api-key').value.trim();
    const model = document.getElementById('modal-model-select').value;
    const alertBox = document.getElementById('key-validation-alert');

    if (!key) {
      alertBox.textContent = 'Please enter a Gemini API Key to test.';
      alertBox.className = 'alert-box error';
      alertBox.style.display = 'block';
      return;
    }

    alertBox.textContent = 'Testing connection with Google Gemini...';
    alertBox.className = 'alert-box';
    alertBox.style.display = 'block';

    try {
      const res = await API.validateKey(key, model);
      if (res.valid) {
        alertBox.textContent = `✓ ${res.message} (${model})`;
        alertBox.className = 'alert-box success';
      } else {
        alertBox.textContent = `✕ ${res.error}`;
        alertBox.className = 'alert-box error';
      }
    } catch (err) {
      alertBox.textContent = `✕ Validation error: ${err.message}`;
      alertBox.className = 'alert-box error';
    }
  });

  // Save API Key
  document.getElementById('btn-save-key').addEventListener('click', () => {
    const key = document.getElementById('input-api-key').value.trim();
    const model = document.getElementById('modal-model-select').value;

    AppState.apiKey = key;
    AppState.selectedModel = model;
    localStorage.setItem('pyconvert_gemini_api_key', key);
    localStorage.setItem('pyconvert_gemini_model', model);

    document.getElementById('model-select').value = model;
    updateApiKeyStatusUI();
    modalApiKey.style.display = 'none';
    showToast('Gemini API settings saved successfully!', 'success');
  });

  // Model select dropdown in nav
  const modelSelect = document.getElementById('model-select');
  modelSelect.value = AppState.selectedModel;
  modelSelect.addEventListener('change', (e) => {
    AppState.selectedModel = e.target.value;
    localStorage.setItem('pyconvert_gemini_model', AppState.selectedModel);
    showToast(`Active model changed to ${e.target.value}`, 'info');
  });

  // Settings Modal
  document.getElementById('btn-settings').addEventListener('click', () => {
    modalSettings.style.display = 'flex';
  });

  document.getElementById('btn-close-settings-modal').addEventListener('click', () => {
    modalSettings.style.display = 'none';
  });

  document.getElementById('btn-save-settings').addEventListener('click', () => {
    const strictRadio = document.querySelector('input[name="strictness"]:checked');
    AppState.strictness = strictRadio ? strictRadio.value : 'strict';
    AppState.customInstructions = document.getElementById('input-custom-prompt').value;
    AppState.concurrency = parseInt(document.getElementById('input-concurrency').value, 10) || 3;
    
    modalSettings.style.display = 'none';
    showToast('Conversion settings saved!', 'success');
  });

  // Scan Local Path Modal
  document.getElementById('btn-scan-path').addEventListener('click', () => {
    modalScanPath.style.display = 'flex';
  });

  document.getElementById('btn-close-scan-modal').addEventListener('click', () => {
    modalScanPath.style.display = 'none';
  });

  document.getElementById('btn-submit-scan-path').addEventListener('click', async () => {
    const pathInput = document.getElementById('input-local-path').value.trim();
    const errBox = document.getElementById('scan-error-alert');
    errBox.style.display = 'none';

    if (!pathInput) {
      errBox.textContent = 'Please enter a valid directory path.';
      errBox.style.display = 'block';
      return;
    }

    try {
      showToast('Scanning directory structure...', 'info');
      const data = await API.scanPath(pathInput);
      loadProjectData(data);
      modalScanPath.style.display = 'none';
      showToast(`Loaded ${data.project.stats.total_files} files from disk!`, 'success');
    } catch (err) {
      errBox.textContent = err.message;
      errBox.style.display = 'block';
    }
  });
}

function updateApiKeyStatusUI() {
  const label = document.getElementById('api-key-label');
  const dot = document.getElementById('key-status-indicator');

  if (AppState.apiKey && AppState.apiKey.length > 5) {
    label.textContent = 'API Key Set';
    dot.className = 'key-status-indicator ready';
  } else {
    label.textContent = 'Set API Key';
    dot.className = 'key-status-indicator';
  }
}

/* ==========================================================================
   Project Ingestion (Upload & Drag-Drop)
   ========================================================================== */

function initFolderUpload() {
  const folderInput = document.getElementById('folder-input');
  folderInput.addEventListener('change', async (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;

    showToast(`Processing ${files.length} uploaded files...`, 'info');
    await processUploadedFileList(files);
  });

  document.getElementById('btn-refresh').addEventListener('click', () => {
    if (AppState.project) {
      TreeViewer.render();
      showToast('Explorer refreshed', 'info');
    }
  });
}

function initDropZone() {
  const dropZone = document.getElementById('drop-zone');

  ['dragenter', 'dragover'].forEach(name => {
    dropZone.addEventListener(name, (e) => {
      e.preventDefault();
      dropZone.style.borderColor = 'var(--cyan)';
      dropZone.style.background = 'rgba(0, 210, 255, 0.12)';
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    dropZone.addEventListener(name, (e) => {
      e.preventDefault();
      dropZone.style.borderColor = '';
      dropZone.style.background = '';
    });
  });

  dropZone.addEventListener('drop', async (e) => {
    const items = e.dataTransfer.items;
    if (items && items.length > 0) {
      const files = [];
      for (let i = 0; i < items.length; i++) {
        const item = items[i].webkitGetAsEntry ? items[i].webkitGetAsEntry() : null;
        if (item) {
          await traverseFileTree(item, '', files);
        }
      }
      if (files.length > 0) {
        showToast(`Ingested ${files.length} files from drag & drop!`, 'info');
        await buildProjectFromFlatFiles(files);
      }
    }
  });
}

async function traverseFileTree(item, path, fileList) {
  if (item.isFile) {
    const file = await new Promise((resolve) => item.file(resolve));
    const content = await file.text();
    fileList.push({
      file,
      path: (path ? path + '/' : '') + item.name,
      content
    });
  } else if (item.isDirectory) {
    // Skip node_modules and hidden folders
    if (['node_modules', '.git', 'dist', 'build'].includes(item.name)) return;
    const dirReader = item.createReader();
    const entries = await new Promise((resolve) => dirReader.readEntries(resolve));
    for (const entry of entries) {
      await traverseFileTree(entry, (path ? path + '/' : '') + item.name, fileList);
    }
  }
}

async function processUploadedFileList(files) {
  const flatFiles = [];
  for (const file of files) {
    const relPath = (file.webkitRelativePath || file.name).replace(/\\/g, '/');
    if (relPath.includes('node_modules/') || relPath.includes('.git/')) continue;
    try {
      const content = await file.text();
      flatFiles.push({ path: relPath, content });
    } catch (e) {
      // Binary or unreadable
      flatFiles.push({ path: relPath, content: '' });
    }
  }
  await buildProjectFromFlatFiles(flatFiles);
}

async function buildProjectFromFlatFiles(flatFiles) {
  const files_flat = [];
  const stats = {
    total_files: 0,
    convertible_files: 0,
    total_lines: 0,
    convertible_lines: 0,
    estimated_tokens: 0
  };

  for (const item of flatFiles) {
    const rel_path = item.path;
    const parts = rel_path.split('/');
    const name = parts[parts.length - 1];
    const extMatch = name.match(/\.[^.]+$/);
    const ext = extMatch ? extMatch[0].toLowerCase() : '';

    const is_convertible = ['.js', '.jsx', '.mjs', '.cjs'].includes(ext);
    const content = item.content || '';
    const lines = content ? content.split(/\r?\n/).length : 0;

    // Detect React JSX in file (strict detection)
    let is_jsx = ext === '.jsx';
    if (ext === '.js' && is_convertible) {
      const hasReactImport = /import\s+React|from\s+['"]react['"]|require\s*\(\s*['"]react['"]\s*\)/.test(content);
      if (hasReactImport) {
        is_jsx = true;
      } else {
        const jsxSignals = [
          /<\s*[A-Z][A-Za-z0-9]*[\s/>]/.test(content),
          /className\s*=/.test(content),
          /<>|<\/>|<React\.Fragment/.test(content),
          /use(State|Effect|Ref|Memo|Callback|Context|Reducer)\s*\(/.test(content)
        ].filter(Boolean).length;
        is_jsx = jsxSignals >= 2;
      }
    }

    const target_ext = is_jsx ? '.tsx' : ({ '.js': '.ts', '.jsx': '.tsx', '.mjs': '.mts', '.cjs': '.cts' }[ext] || ext);
    const target_path = is_convertible ? rel_path.slice(0, -ext.length) + target_ext : rel_path;

    const fileObj = {
      name,
      path: rel_path,
      abs_path: null,
      type: 'file',
      extension: ext,
      is_convertible,
      is_jsx,
      target_extension: target_ext,
      target_path,
      size: content.length,
      lines,
      content,
      status: is_convertible ? 'pending' : 'unmodified'
    };
    files_flat.push(fileObj);

    stats.total_files += 1;
    stats.total_lines += lines;
    if (is_convertible) {
      stats.convertible_files += 1;
      stats.convertible_lines += lines;
      stats.estimated_tokens += Math.floor(content.length / 3.5) + (lines * 3);
    }
  }

  // Build tree
  const rootName = flatFiles[0]?.path.split('/')[0] || 'Uploaded Project';
  const tree = { name: rootName, path: '.', type: 'directory', children: [] };

  for (const f of files_flat) {
    const parts = f.path.split('/');
    let currentLevel = tree.children;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (i === parts.length - 1) {
        currentLevel.push(f);
      } else {
        let foundDir = currentLevel.find(c => c.type === 'directory' && c.name === part);
        if (!foundDir) {
          foundDir = { name: part, path: parts.slice(0, i + 1).join('/'), type: 'directory', children: [] };
          currentLevel.push(foundDir);
        }
        currentLevel = foundDir.children;
      }
    }
  }

  // Analyze frameworks & generate tsconfig
  const analysisData = await API.analyzeProject ? await API.analyzeProject(files_flat).catch(() => null) : null;

  loadProjectData({
    project: {
      root_name: rootName,
      root_path: `[Upload: ${rootName}]`,
      tree,
      files: files_flat,
      stats
    },
    analysis: analysisData?.analysis || { project_type: 'JavaScript Project', frameworks: [] },
    tsconfig: analysisData?.tsconfig || ''
  });

  showToast(`Loaded ${files_flat.length} files successfully!`, 'success');
}

/* ==========================================================================
   Sample Projects Loader
   ========================================================================== */

function initSampleButtons() {
  document.querySelectorAll('.sample-tag').forEach(btn => {
    btn.addEventListener('click', async () => {
      const sampleId = btn.dataset.sample;
      try {
        showToast(`Loading sample project: ${sampleId}...`, 'info');
        const data = await API.loadSample(sampleId);
        loadProjectData(data);
        showToast(`Sample "${data.project.root_name}" loaded!`, 'success');
      } catch (err) {
        showToast(`Failed to load sample: ${err.message}`, 'error');
      }
    });
  });
}

function loadProjectData(data) {
  AppState.project = data.project;
  AppState.analysis = data.analysis;
  AppState.recommendedTsconfig = data.tsconfig;
  AppState.convertedMap = {};
  AppState.activeFile = null;

  TreeViewer.render();
  AppState.updateStats();

  // Automatically select first convertible file if present
  const firstConvertible = data.project.files.find(f => f.is_convertible);
  if (firstConvertible) {
    TreeViewer.selectFile(firstConvertible);
  } else if (data.project.files.length > 0) {
    TreeViewer.selectFile(data.project.files[0]);
  }
}

/* ==========================================================================
   Conversion Logic (Single & Batch)
   ========================================================================== */

function initConvertButtons() {
  // Single File Conversion
  document.getElementById('btn-convert-single').addEventListener('click', async () => {
    const file = AppState.activeFile;
    if (!file || !file.is_convertible) return;

    if (!ensureApiKey()) return;

    const btn = document.getElementById('btn-convert-single');
    btn.disabled = true;
    btn.querySelector('span').textContent = 'Converting...';
    file.status = 'converting';
    TreeViewer.updateNodeStatus(file.path, 'converting');

    try {
      const res = await API.convertFile({
        apiKey: AppState.apiKey,
        filePath: file.path,
        code: file.content,
        targetExtension: file.target_extension,
        model: AppState.selectedModel,
        strictness: AppState.strictness,
        projectSummary: AppState.analysis?.summary || '',
        customInstructions: AppState.customInstructions
      });

      file.converted_code = res.converted_code;
      AppState.convertedMap[file.path] = res.converted_code;
      file.status = 'converted';
      TreeViewer.updateNodeStatus(file.path, 'converted');
      EditorManager.renderTargetCode(res.converted_code, file.target_extension);
      AppState.updateStats();
      showToast(`Successfully converted ${file.name} to ${file.target_extension}!`, 'success');
    } catch (err) {
      file.status = 'error';
      TreeViewer.updateNodeStatus(file.path, 'error');
      showToast(`Conversion failed: ${err.message}`, 'error');
    } finally {
      btn.disabled = false;
      btn.querySelector('span').textContent = 'Convert File';
    }
  });

  // Batch Project Conversion
  document.getElementById('btn-convert-all').addEventListener('click', async () => {
    if (!AppState.project) return;
    if (!ensureApiKey()) return;

    const convertibleFiles = AppState.project.files.filter(f => f.is_convertible);
    if (!convertibleFiles.length) {
      showToast('No convertible JavaScript files found.', 'info');
      return;
    }

    AppState.isConvertingBatch = true;
    AppState.updateStats();

    const progressBar = document.getElementById('batch-progress-bar');
    const progressFill = document.getElementById('progress-fill');
    const progressPct = document.getElementById('progress-percentage');
    const progressStatus = document.getElementById('progress-status-text');

    progressBar.style.display = 'block';
    progressFill.style.width = '0%';
    progressPct.textContent = '0%';

    let completed = 0;
    const total = convertibleFiles.length;

    // Concurrency queue runner
    const concurrency = AppState.concurrency || 3;
    const queue = [...convertibleFiles];

    async function worker() {
      while (queue.length > 0) {
        const file = queue.shift();
        if (!file) break;

        file.status = 'converting';
        TreeViewer.updateNodeStatus(file.path, 'converting');
        progressStatus.textContent = `Converting ${file.name} (${completed + 1}/${total})...`;

        try {
          const res = await API.convertFile({
            apiKey: AppState.apiKey,
            filePath: file.path,
            code: file.content,
            targetExtension: file.target_extension,
            model: AppState.selectedModel,
            strictness: AppState.strictness,
            projectSummary: AppState.analysis?.summary || '',
            customInstructions: AppState.customInstructions
          });

          file.converted_code = res.converted_code;
          AppState.convertedMap[file.path] = res.converted_code;
          file.status = 'converted';
          TreeViewer.updateNodeStatus(file.path, 'converted');

          // If this is currently active in editor, refresh view
          if (AppState.activeFile?.path === file.path) {
            EditorManager.renderTargetCode(res.converted_code, file.target_extension);
          }
        } catch (err) {
          console.error('Error converting file', file.path, err);
          file.status = 'error';
          TreeViewer.updateNodeStatus(file.path, 'error');
        }

        completed++;
        const pct = Math.round((completed / total) * 100);
        progressFill.style.width = `${pct}%`;
        progressPct.textContent = `${pct}%`;
        AppState.updateStats();
      }
    }

    const workers = Array.from({ length: Math.min(concurrency, total) }, () => worker());
    await Promise.all(workers);

    AppState.isConvertingBatch = false;
    AppState.updateStats();
    progressStatus.textContent = `Completed! ${Object.keys(AppState.convertedMap).length}/${total} files converted to TypeScript.`;
    showToast('Batch project conversion completed!', 'success');

    setTimeout(() => {
      progressBar.style.display = 'none';
    }, 4000);
  });
}

function ensureApiKey() {
  if (!AppState.apiKey || AppState.apiKey.trim().length < 6) {
    showToast('Please set your Gemini API Key first.', 'error');
    document.getElementById('modal-api-key').style.display = 'flex';
    return false;
  }
  return true;
}

/* ==========================================================================
   Export Zip
   ========================================================================== */

function initExportButton() {
  document.getElementById('btn-export-zip').addEventListener('click', async () => {
    if (!AppState.project || !Object.keys(AppState.convertedMap).length) {
      showToast('No converted files to export.', 'info');
      return;
    }

    try {
      showToast('Building TypeScript project ZIP archive...', 'info');
      const blob = await API.exportZip({
        files: AppState.project.files,
        convertedMap: AppState.convertedMap,
        tsconfig: AppState.recommendedTsconfig,
        packageJson: null
      });

      // Trigger browser download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${(AppState.project.root_name || 'project').toLowerCase().replace(/\s+/g, '-')}-typescript.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      showToast('Downloaded TypeScript project ZIP archive!', 'success');
    } catch (err) {
      showToast(`Export error: ${err.message}`, 'error');
    }
  });
}

/* ==========================================================================
   Toast Notification Helper
   ========================================================================== */

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icons = {
    success: '✓',
    error: '✕',
    info: 'ℹ'
  };

  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || '•'}</span>
    <span class="toast-message">${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => {
      if (toast.parentNode) container.removeChild(toast);
    }, 300);
  }, 4000);
}
