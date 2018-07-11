# -*- mode: python -*-

block_cipher = None

added_files=[('../linux', 'linux'),
             ('../env.bsh', '.')]

# Package up bash too, why not
if os.name=='nt':
  import distutils.spawn
#  added_files.append((distutils.spawn.find_executable('bash'), 'vsi'))

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
          console=True )
