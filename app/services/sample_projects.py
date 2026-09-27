"""
Sample JavaScript Projects for Quick Demonstration & Testing
"""
from typing import Dict, Any, List

SAMPLE_PROJECTS: Dict[str, Dict[str, Any]] = {
    "express_api": {
        "id": "express_api",
        "name": "Express & Node.js Backend API",
        "description": "Full REST API with Express routing, JWT auth middleware, user controllers, and MongoDB models in JavaScript.",
        "icon": "server",
        "files": [
            {
                "path": "package.json",
                "content": """{
  "name": "express-auth-api",
  "version": "1.0.0",
  "main": "server.js",
  "dependencies": {
    "express": "^4.19.2",
    "cors": "^2.8.5",
    "jsonwebtoken": "^9.0.2",
    "bcryptjs": "^2.4.3"
  }
}"""
            },
            {
                "path": "src/server.js",
                "content": """const express = require('express');
const cors = require('cors');
const userRoutes = require('./routes/userRoutes');
const { errorHandler } = require('./middleware/errorHandler');

const app = express();
const PORT = process.env.PORT || 4000;

app.use(cors());
app.use(express.json());

app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.use('/api/users', userRoutes);
app.use(errorHandler);

app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});

module.exports = app;"""
            },
            {
                "path": "src/controllers/userController.js",
                "content": """const jwt = require('jsonwebtoken');
const { users, findUserByEmail, createUser } = require('../models/userModel');

const JWT_SECRET = process.env.JWT_SECRET || 'super-secret-key-123';

/**
 * Register a new user
 * @param {Object} req - Express request
 * @param {Object} res - Express response
 */
async function register(req, res) {
  const { name, email, password, role = 'user' } = req.body;
  
  if (!name || !email || !password) {
    return res.status(400).json({ error: 'Name, email, and password are required' });
  }

  const existing = findUserByEmail(email);
  if (existing) {
    return res.status(409).json({ error: 'User already exists' });
  }

  const newUser = createUser({ name, email, password, role });
  const token = jwt.sign({ id: newUser.id, role: newUser.role }, JWT_SECRET, { expiresIn: '1d' });

  return res.status(201).json({
    message: 'User registered successfully',
    user: { id: newUser.id, name: newUser.name, email: newUser.email, role: newUser.role },
    token
  });
}

/**
 * Get current user profile
 * @param {Object} req
 * @param {Object} res
 */
function getProfile(req, res) {
  const userId = req.user.id;
  const user = users.find(u => u.id === userId);
  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }
  return res.json({ id: user.id, name: user.name, email: user.email, role: user.role });
}

module.exports = {
  register,
  getProfile
};"""
            },
            {
                "path": "src/middleware/authMiddleware.js",
                "content": """const jwt = require('jsonwebtoken');
const JWT_SECRET = process.env.JWT_SECRET || 'super-secret-key-123';

function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  jwt.verify(token, JWT_SECRET, (err, decodedUser) => {
    if (err) {
      return res.status(403).json({ error: 'Invalid or expired token' });
    }
    req.user = decodedUser;
    next();
  });
}

function requireAdmin(req, res, next) {
  if (!req.user || req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Admin privileges required' });
  }
  next();
}

module.exports = {
  authenticateToken,
  requireAdmin
};"""
            },
            {
                "path": "src/middleware/errorHandler.js",
                "content": """function errorHandler(err, req, res, next) {
  console.error('Unhandled Error:', err.message, err.stack);
  const status = err.statusCode || 500;
  res.status(status).json({
    success: false,
    error: err.message || 'Internal Server Error',
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
  });
}

module.exports = { errorHandler };"""
            },
            {
                "path": "src/models/userModel.js",
                "content": """const users = [
  { id: '1', name: 'Alice Admin', email: 'alice@example.com', password: 'hashed_password_1', role: 'admin' },
  { id: '2', name: 'Bob User', email: 'bob@example.com', password: 'hashed_password_2', role: 'user' }
];

function findUserByEmail(email) {
  return users.find(u => u.email.toLowerCase() === email.toLowerCase());
}

function createUser(userData) {
  const newUser = {
    id: String(Date.now()),
    name: userData.name,
    email: userData.email,
    password: userData.password,
    role: userData.role || 'user',
    createdAt: new Date().toISOString()
  };
  users.push(newUser);
  return newUser;
}

module.exports = {
  users,
  findUserByEmail,
  createUser
};"""
            },
            {
                "path": "src/routes/userRoutes.js",
                "content": """const express = require('express');
const { register, getProfile } = require('../controllers/userController');
const { authenticateToken } = require('../middleware/authMiddleware');

const router = express.Router();

router.post('/register', register);
router.get('/profile', authenticateToken, getProfile);

module.exports = router;"""
            }
        ]
    },

    "react_components": {
        "id": "react_components",
        "name": "React Dashboard & UI Component Library",
        "description": "Interactive React dashboard UI with custom hooks, state management, modal, data table, and analytics chart in JSX.",
        "icon": "layout",
        "files": [
            {
                "path": "package.json",
                "content": """{
  "name": "react-dashboard-ui",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "lucide-react": "^0.378.0"
  },
  "devDependencies": {
    "vite": "^5.2.0"
  }
}"""
            },
            {
                "path": "src/components/DataTable.jsx",
                "content": """import React, { useState, useMemo } from 'react';

export function DataTable({ data = [], columns = [], pageSize = 5, onRowClick }) {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState('asc');

  const filteredData = useMemo(() => {
    return data.filter(item => {
      if (!searchTerm) return true;
      return Object.values(item).some(val => 
        String(val).toLowerCase().includes(searchTerm.toLowerCase())
      );
    });
  }, [data, searchTerm]);

  const sortedData = useMemo(() => {
    if (!sortColumn) return filteredData;
    return [...filteredData].sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];
      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredData, sortColumn, sortDirection]);

  const totalPages = Math.ceil(sortedData.length / pageSize) || 1;
  const paginatedData = sortedData.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const handleSort = (key) => {
    if (sortColumn === key) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(key);
      setSortDirection('asc');
    }
  };

  return (
    <div className="table-container">
      <div className="table-header">
        <input
          type="text"
          placeholder="Search records..."
          value={searchTerm}
          onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
          className="search-input"
        />
        <span className="total-count">{sortedData.length} items</span>
      </div>

      <table className="custom-table">
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col.key} onClick={() => handleSort(col.key)} className="sortable-th">
                {col.label} {sortColumn === col.key ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {paginatedData.map((row, idx) => (
            <tr key={row.id || idx} onClick={() => onRowClick && onRowClick(row)}>
              {columns.map(col => (
                <td key={col.key}>
                  {col.render ? col.render(row[col.key], row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pagination">
        <button disabled={currentPage === 1} onClick={() => setCurrentPage(p => p - 1)}>
          Previous
        </button>
        <span>Page {currentPage} of {totalPages}</span>
        <button disabled={currentPage === totalPages} onClick={() => setCurrentPage(p => p + 1)}>
          Next
        </button>
      </div>
    </div>
  );
}"""
            },
            {
                "path": "src/hooks/useLocalStorage.js",
                "content": """import { useState, useEffect } from 'react';

/**
 * Hook to synchronize state with window.localStorage
 * @param {string} key
 * @param {any} initialValue
 */
export function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(storedValue));
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  return [storedValue, setStoredValue];
}"""
            },
            {
                "path": "src/components/MetricCard.jsx",
                "content": """import React from 'react';

export function MetricCard({ title, value, change, isPositive = true, icon, subtitle }) {
  return (
    <div className="metric-card">
      <div className="metric-header">
        <span className="metric-title">{title}</span>
        {icon && <div className="metric-icon">{icon}</div>}
      </div>
      <div className="metric-body">
        <span className="metric-value">{value}</span>
        {change !== undefined && (
          <span className={`metric-change ${isPositive ? 'positive' : 'negative'}`}>
            {isPositive ? '↑' : '↓'} {change}%
          </span>
        )}
      </div>
      {subtitle && <p className="metric-subtitle">{subtitle}</p>}
    </div>
  );
}"""
            },
            {
                "path": "src/App.jsx",
                "content": """import React, { useState } from 'react';
import { MetricCard } from './components/MetricCard';
import { DataTable } from './components/DataTable';
import { useLocalStorage } from './hooks/useLocalStorage';

export default function App() {
  const [theme, setTheme] = useLocalStorage('theme_mode', 'dark');
  const [selectedUser, setSelectedUser] = useState(null);

  const sampleUsers = [
    { id: '1', name: 'Sophia Clark', role: 'Staff Engineer', status: 'Active', score: 98 },
    { id: '2', name: 'Ethan Miller', role: 'Product Designer', status: 'Reviewing', score: 84 },
    { id: '3', name: 'Liam Davies', role: 'DevOps Lead', status: 'Active', score: 92 },
    { id: '4', name: 'Ava Johnson', role: 'Frontend Architect', status: 'Active', score: 96 }
  ];

  const columns = [
    { key: 'name', label: 'Full Name' },
    { key: 'role', label: 'Role' },
    {
      key: 'status',
      label: 'Status',
      render: (val) => <span className={`status-pill ${val.toLowerCase()}`}>{val}</span>
    },
    { key: 'score', label: 'Score' }
  ];

  return (
    <div className={`dashboard-root ${theme}`}>
      <header className="dashboard-topbar">
        <h1>Engineering Team Analytics</h1>
        <button onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}>
          Toggle {theme === 'dark' ? 'Light' : 'Dark'} Mode
        </button>
      </header>

      <div className="metrics-grid">
        <MetricCard title="Total Team Members" value="48" change={12.4} isPositive={true} />
        <MetricCard title="Sprint Velocity" value="94.2%" change={3.1} isPositive={true} />
        <MetricCard title="Open PRs" value="7" change={2} isPositive={false} />
      </div>

      <main className="dashboard-content">
        <DataTable
          data={sampleUsers}
          columns={columns}
          onRowClick={(row) => setSelectedUser(row)}
        />

        {selectedUser && (
          <div className="detail-drawer">
            <h3>User Details</h3>
            <p><strong>Name:</strong> {selectedUser.name}</p>
            <p><strong>Role:</strong> {selectedUser.role}</p>
            <p><strong>Score:</strong> {selectedUser.score}</p>
            <button onClick={() => setSelectedUser(null)}>Close</button>
          </div>
        )}
      </main>
    </div>
  );
}"""
            }
        ]
    }
}
