/**
 * PyConvert Diff Engine
 * Computes line-by-line diffs between original JavaScript and converted TypeScript
 */

const DiffEngine = {
  computeLineDiff(oldText, newText) {
    const oldLines = (oldText || '').split(/\r?\n/);
    const newLines = (newText || '').split(/\r?\n/);

    const diff = [];
    let i = 0, j = 0;
    let addedCount = 0;
    let removedCount = 0;

    // LCS Matrix
    const matrix = Array.from({ length: oldLines.length + 1 }, () => 
      new Uint32Array(newLines.length + 1)
    );

    for (let r = 0; r < oldLines.length; r++) {
      for (let c = 0; c < newLines.length; c++) {
        if (oldLines[r] === newLines[c]) {
          matrix[r + 1][c + 1] = matrix[r][c] + 1;
        } else {
          matrix[r + 1][c + 1] = Math.max(matrix[r + 1][c], matrix[r][c + 1]);
        }
      }
    }

    // Backtrack to find diff
    let r = oldLines.length, c = newLines.length;
    const tempDiff = [];

    while (r > 0 || c > 0) {
      if (r > 0 && c > 0 && oldLines[r - 1] === newLines[c - 1]) {
        tempDiff.push({ type: 'neutral', marker: '  ', text: oldLines[r - 1] });
        r--;
        c--;
      } else if (c > 0 && (r === 0 || matrix[r][c - 1] >= matrix[r - 1][c])) {
        tempDiff.push({ type: 'added', marker: '+ ', text: newLines[c - 1] });
        addedCount++;
        c--;
      } else if (r > 0 && (c === 0 || matrix[r][c - 1] < matrix[r - 1][c])) {
        tempDiff.push({ type: 'removed', marker: '- ', text: oldLines[r - 1] });
        removedCount++;
        r--;
      }
    }

    tempDiff.reverse();

    return {
      lines: tempDiff,
      addedCount,
      removedCount
    };
  },

  renderDiffTo(containerEl, statsEl, oldText, newText) {
    if (!containerEl) return;

    if (!oldText && !newText) {
      containerEl.innerHTML = '<div class="empty-diff" style="padding: 20px; color: var(--text-dim); text-align: center;">No code to compare yet.</div>';
      if (statsEl) statsEl.textContent = '+0 added, -0 removed';
      return;
    }

    const { lines, addedCount, removedCount } = this.computeLineDiff(oldText, newText);

    if (statsEl) {
      statsEl.textContent = `+${addedCount} added, -${removedCount} removed`;
    }

    const html = lines.map(line => {
      const escapedText = DiffEngine.escapeHtml(line.text);
      return `<div class="diff-line ${line.type}">
        <span class="diff-marker">${line.marker}</span>
        <span class="diff-text">${escapedText || '&nbsp;'}</span>
      </div>`;
    }).join('');

    containerEl.innerHTML = html;
  },

  escapeHtml(str) {
    return (str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
};
