# samplemind-server.spec — PyInstaller build spec
#
# Produces a single-file standalone binary: samplemind-server
# This binary IS the Flask server — no Python installation required.
#
# Tauri bundles this as a "sidecar" (a companion executable) and manages
# its lifecycle: spawn on app start, kill on app exit.
#
# To build:
#   cd SampleMind-AI
#   .venv/bin/pyinstaller samplemind-server.spec
#
# Output: dist/samplemind-server  (Linux/macOS) or dist/samplemind-server.exe (Windows)

import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE

# The entry point — same script we run manually
block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],                     # add src/ to Python path so imports work
    binaries=[],
    datas=[
        # Bundle the Flask templates and static files into the binary
        ('src/web/templates', 'web/templates'),
        ('src/web/static',    'web/static'),
    ],
    hiddenimports=[
        # librosa uses numba which lazy-imports these — PyInstaller misses them
        'numba',
        'numba.core',
        'llvmlite',
        'sklearn',
        'sklearn.utils._cython_blas',
        'sklearn.neighbors._typedefs',
        'scipy.special._ufuncs_cxx',
        'scipy.linalg.cython_blas',
        'scipy.linalg.cython_lapack',
        # Flask internals
        'flask',
        'jinja2',
        'werkzeug',
        'click',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude things we don't need to keep the binary smaller
        'tkinter',
        'matplotlib.tests',
        'numpy.testing',
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='samplemind-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                   # compress the binary (requires upx installed)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,               # keep console so logs are visible during development
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,               # single file, not a folder
)
