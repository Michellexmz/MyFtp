# -*- mode: python -*-

block_cipher = None


a = Analysis(['clientGui.py'],
             pathex=['/home/mixie/project/myftp/source/client'],
             binaries=None,
             datas=None,
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
          name='clientGui',
          debug=False,
          strip=False,
          upx=True,
          console=True )