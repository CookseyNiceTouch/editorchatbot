# Getting Started

This project has two main parts:
- **Backend:** Flask API (Python, in `/backend`)
- **Frontend:** Electron app with React + Vite (JavaScript/TypeScript, in project root and `/electron`)

---

## 1. Backend (Flask API)

### Prerequisites
- Python (the version you used for your conda environment)
- Conda (recommended)
- DaVinci Resolve (for API features)
- The required Python packages (see below)

### Setup & Run

```bash
# Open a terminal and activate your conda environment
conda activate your_env_name

# Go to the backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Set your environment variables (e.g., ANTHROPIC_API_KEY)
# You can use a .env file in the backend directory

# Run the Flask app
python app.py
```

The backend will start on `http://127.0.0.1:5000/`.

---

## 2. Frontend (Electron + React + Vite)

### Prerequisites
- Node.js (v18+ recommended)
- npm

### Setup & Run

```bash
# Open a new terminal (keep backend running in the other one)
# In the project root directory:

# Install dependencies
npm install

# Start the Vite dev server and Electron app
npm run dev
```

This will launch the Electron app, which connects to your running Flask backend.

---

### Notes

- Make sure the Flask backend is running before starting the Electron app.
- If you need to build the Electron app for production, use:
  ```bash
  npm run build
  ```
- For API keys and secrets, use a `.env` file in the `backend` directory.

---

# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type aware lint rules:

- Configure the top-level `parserOptions` property like this:

```js
export default {
  // other rules...
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    project: ['./tsconfig.json', './tsconfig.node.json'],
    tsconfigRootDir: __dirname,
  },
}
```

- Replace `plugin:@typescript-eslint/recommended` to `plugin:@typescript-eslint/recommended-type-checked` or `plugin:@typescript-eslint/strict-type-checked`
- Optionally add `plugin:@typescript-eslint/stylistic-type-checked`
- Install [eslint-plugin-react](https://github.com/jsx-eslint/eslint-plugin-react) and add `plugin:react/recommended` & `plugin:react/jsx-runtime` to the `extends` list
