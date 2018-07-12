# -*- mode: python -*-

block_cipher = None

added_files=[('../linux', 'linux'),
             ('../env.bsh', '.')]

# Add for recipes
added_files.append(('../docker', 'docker'))

# Add tests to test just executable
added_files.append(('../tests', 'test'))

if os.name=='nt':
  console=False
  # console=True
else:
  console=True

a = Analysis(['just.py'],
             pathex=['.'],
             binaries=[],
             datas=added_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='just',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=console )
