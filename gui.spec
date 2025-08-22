# gui.spec

import os

# --- Helper function to find all Python scripts ---
def get_all_scripts(directory='.'):
    scripts = []
    # Exclude common virtual environment folders
    exclude_dirs = {os.path.join(directory, 'venv'), os.path.join(directory, '.venv')}
    for root, _, files in os.walk(directory):
        # Check if the current root is a subdirectory of any excluded directory
        if any(root.startswith(ex_dir) for ex_dir in exclude_dirs):
            continue
        for file in files:
            if file.endswith('.py'):
                scripts.append(os.path.join(root, file))
    return scripts

# ---------------------------------------------------

# Get all python scripts for the Analysis
all_project_scripts = get_all_scripts()

a = Analysis(
    # CORRECT: Pass all scripts directly into the Analysis constructor
    all_project_scripts,
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('Files', 'Files'),
        ('Fonts', 'Fonts'),
        ('Anime Version', 'Anime Version'),
        ('Manwha Version', 'Manwha Version')
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='The System',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # This is the same as --windowed
    icon=None # You can add an icon path here, e.g., 'assets/icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='The System'
)