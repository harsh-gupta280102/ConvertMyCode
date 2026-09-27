/**
 * PyConvert Editor Manager
 * Manages Prism syntax highlighting, split view modes, in-place code editing, and diff rendering.
 */

const EditorManager = {
  currentMode: 'split', // 'split' | 'diff' | 'ts-only'
  isEditingTS: false,

  init() {
    this.setupViewModeToggles();
    this.setupEditToggle();
    this.setupCopyButton();
  },

  setupViewModeToggles() {
    const buttons = document.querySelectorAll('.mode-btn');
    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        buttons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.setViewMode(btn.dataset.mode);
      });
    });
  },

  setViewMode(mode) {
    this.currentMode = mode;
    const panelSource = document.getElementById('panel-source');
    const panelTarget = document.getElementById('panel-target');
    const panelDiff = document.getElementById('panel-diff');

    if (mode === 'split') {
      panelSource.style.display = 'flex';
      panelTarget.style.display = 'flex';
      panelDiff.style.display = 'none';
    } else if (mode === 'diff') {
      panelSource.style.display = 'none';
      panelTarget.style.display = 'none';
      panelDiff.style.display = 'flex';
      this.updateDiffView();
    } else if (mode === 'ts-only') {
      panelSource.style.display = 'none';
      panelTarget.style.display = 'flex';
      panelDiff.style.display = 'none';
    }
  },

  setupEditToggle() {
    const btnToggle = document.getElementById('btn-toggle-edit');
    const preTarget = document.getElementById('pre-target');
    const textarea = document.getElementById('editor-target-raw');

    btnToggle.addEventListener('click', () => {
      this.isEditingTS = !this.isEditingTS;
      if (this.isEditingTS) {
        btnToggle.textContent = '💾 Save & Preview';
        btnToggle.classList.add('active');
        textarea.value = AppState.getActiveConvertedCode();
        preTarget.style.display = 'none';
        textarea.style.display = 'block';
        textarea.focus();
      } else {
        btnToggle.textContent = '✏️ Edit';
        btnToggle.classList.remove('active');
        const updatedCode = textarea.value;
        AppState.setActiveConvertedCode(updatedCode);
        this.renderTargetCode(updatedCode, AppState.activeFile?.target_extension || '.ts');
        preTarget.style.display = 'block';
        textarea.style.display = 'none';
      }
    });

    textarea.addEventListener('input', () => {
      AppState.setActiveConvertedCode(textarea.value);
    });
  },

  setupCopyButton() {
    const btnCopy = document.getElementById('btn-copy-ts');
    btnCopy.addEventListener('click', () => {
      const code = AppState.getActiveConvertedCode();
      if (!code) {
        showToast('No TypeScript code to copy', 'info');
        return;
      }
      navigator.clipboard.writeText(code).then(() => {
        showToast('Copied TypeScript to clipboard!', 'success');
      }).catch(() => {
        showToast('Failed to copy to clipboard', 'error');
      });
    });
  },

  renderSourceCode(code, extension) {
    const codeEl = document.getElementById('code-source');
    const linesEl = document.getElementById('js-line-count');
    
    codeEl.textContent = code || '// Select a file to view code';
    const lines = (code || '').split('\n').length;
    linesEl.textContent = `${lines} lines`;

    // Prism language class
    const isJsx = extension === '.jsx';
    codeEl.className = isJsx ? 'language-jsx' : 'language-javascript';
    if (window.Prism) {
      Prism.highlightElement(codeEl);
    }
  },

  renderTargetCode(code, extension) {
    const codeEl = document.getElementById('code-target');
    const linesEl = document.getElementById('ts-line-count');
    const textarea = document.getElementById('editor-target-raw');
    const preEl = document.getElementById('pre-target');
    
    codeEl.textContent = code || '// Converted TypeScript will appear here...';
    textarea.value = code || '';
    const lines = code ? code.split('\n').length : 0;
    linesEl.textContent = `${lines} lines`;

    const isTsx = extension === '.tsx';
    codeEl.className = isTsx ? 'language-tsx' : 'language-typescript';
    if (window.Prism && code) {
      Prism.highlightElement(codeEl);
    } else {
      const existingRows = preEl?.querySelector('.line-numbers-rows');
      if (existingRows) existingRows.remove();
    }

    if (this.currentMode === 'diff') {
      this.updateDiffView();
    }
  },

  updateDiffView() {
    const diffContainer = document.getElementById('diff-container');
    const diffStats = document.getElementById('diff-stats');
    const sourceCode = AppState.activeFile?.content || '';
    const targetCode = AppState.getActiveConvertedCode() || '';

    DiffEngine.renderDiffTo(diffContainer, diffStats, sourceCode, targetCode);
  }
};
