/**
 * PyConvert Visual File Tree Renderer
 * Interactive directory explorer with collapsible folders, search filtering, and status badges.
 */

const TreeViewer = {
  container: null,
  activeFilePath: null,
  expandedFolders: new Set(),
  searchFilter: '',

  init() {
    this.container = document.getElementById('tree-container');
    const searchInput = document.getElementById('file-search-input');
    
    searchInput.addEventListener('input', (e) => {
      this.searchFilter = e.target.value.toLowerCase().trim();
      this.render();
    });
  },

  render() {
    if (!AppState.project || !AppState.project.tree) {
      this.container.innerHTML = `
        <div class="empty-tree-placeholder">
          <div class="placeholder-icon">📁</div>
          <p>No project loaded yet.</p>
          <span class="subtext">Upload a JavaScript folder or choose a sample above.</span>
        </div>
      `;
      return;
    }

    this.container.innerHTML = '';
    const rootEl = this.createNodeElement(AppState.project.tree, 0);
    this.container.appendChild(rootEl);
  },

  createNodeElement(node, depth) {
    const nodeEl = document.createElement('div');
    nodeEl.className = 'tree-node';

    const isDir = node.type === 'directory';
    const path = node.path || node.name;

    if (isDir) {
      // Check if folder contains any matches if search is active
      if (this.searchFilter && !this.folderMatchesSearch(node)) {
        return nodeEl; // Hide folder if no match
      }

      const isExpanded = this.expandedFolders.has(path) || (this.searchFilter.length > 0) || depth < 2;
      if (isExpanded) this.expandedFolders.add(path);

      const row = document.createElement('div');
      row.className = 'tree-row';
      row.style.paddingLeft = `${depth * 14 + 6}px`;

      row.innerHTML = `
        <span class="tree-toggle ${isExpanded ? 'expanded' : ''}">▶</span>
        <span class="tree-icon">📁</span>
        <span class="tree-label">${node.name}</span>
      `;

      const childrenContainer = document.createElement('div');
      childrenContainer.className = 'tree-children';
      childrenContainer.style.display = isExpanded ? 'block' : 'none';

      row.addEventListener('click', (e) => {
        e.stopPropagation();
        const expanded = !this.expandedFolders.has(path);
        if (expanded) {
          this.expandedFolders.add(path);
        } else {
          this.expandedFolders.delete(path);
        }
        row.querySelector('.tree-toggle').classList.toggle('expanded', expanded);
        childrenContainer.style.display = expanded ? 'block' : 'none';
      });

      nodeEl.appendChild(row);

      if (node.children && node.children.length > 0) {
        node.children.forEach(child => {
          const childEl = this.createNodeElement(child, depth + 1);
          childrenContainer.appendChild(childEl);
        });
      }

      nodeEl.appendChild(childrenContainer);
    } else {
      // File node
      if (this.searchFilter && !node.path.toLowerCase().includes(this.searchFilter)) {
        return nodeEl; // Hide file if not matching search
      }

      const row = document.createElement('div');
      row.className = `tree-row ${this.activeFilePath === node.path ? 'active' : ''}`;
      row.style.paddingLeft = `${depth * 14 + 18}px`;

      const icon = this.getFileIcon(node.name, node.extension);
      const statusBadge = this.getStatusBadge(node);

      row.innerHTML = `
        <span class="tree-icon">${icon}</span>
        <span class="tree-label" title="${node.path}">${node.name}</span>
        ${statusBadge}
      `;

      row.addEventListener('click', (e) => {
        e.stopPropagation();
        this.selectFile(node);
      });

      nodeEl.appendChild(row);
    }

    return nodeEl;
  },

  selectFile(fileObj) {
    this.activeFilePath = fileObj.path;
    AppState.selectFile(fileObj);
    
    // Update active class in DOM
    const allRows = this.container.querySelectorAll('.tree-row');
    allRows.forEach(r => r.classList.remove('active'));
    
    // Find current row
    const matchingRow = Array.from(allRows).find(r => 
      r.querySelector('.tree-label')?.getAttribute('title') === fileObj.path
    );
    if (matchingRow) matchingRow.classList.add('active');
  },

  getFileIcon(filename, ext) {
    const fn = filename.toLowerCase();
    if (fn === 'package.json') return '📦';
    if (fn.startsWith('tsconfig')) return '⚙️';
    if (ext === '.jsx') return '⚛️';
    if (ext === '.tsx') return '💠';
    if (ext === '.js' || ext === '.mjs' || ext === '.cjs') return '🟨';
    if (ext === '.ts' || ext === '.mts' || ext === '.cts') return '🟦';
    if (ext === '.css' || ext === '.scss') return '🎨';
    if (ext === '.html') return '🌐';
    if (ext === '.json') return '📋';
    if (ext === '.md') return '📝';
    return '📄';
  },

  getStatusBadge(node) {
    if (!node.is_convertible) {
      return `<span class="tree-status-badge unmodified" title="This static file will be preserved as-is">STATIC</span>`;
    }
    const status = node.status || 'pending';
    if (status === 'pending') {
      const isJsx = node.extension === '.jsx' || node.is_jsx;
      return `<span class="tree-status-badge pending">${isJsx ? 'JSX' : 'JS'}</span>`;
    } else if (status === 'converting') {
      return `<span class="tree-status-badge converting">⚡ AI</span>`;
    } else if (status === 'converted') {
      const isTsx = node.target_extension === '.tsx' || node.is_jsx;
      return `<span class="tree-status-badge converted">${isTsx ? '✓ TSX' : '✓ TS'}</span>`;
    } else if (status === 'error') {
      return `<span class="tree-status-badge error">ERR</span>`;
    }
    return '';
  },

  folderMatchesSearch(folderNode) {
    if (folderNode.name.toLowerCase().includes(this.searchFilter)) return true;
    if (!folderNode.children) return false;
    return folderNode.children.some(child => {
      if (child.type === 'directory') return this.folderMatchesSearch(child);
      return child.path.toLowerCase().includes(this.searchFilter);
    });
  },

  updateNodeStatus(filePath, status) {
    const file = AppState.project?.files.find(f => f.path === filePath);
    if (file) {
      file.status = status;
      this.render();
    }
  }
};
