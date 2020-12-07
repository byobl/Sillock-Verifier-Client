from cx_Freeze import setup, Executable
import sys

buildOptions = dict(packages      = ["queue", "qtmodern.windows", "qtmodern.styles", "csv", "os", "sys"], 
                    excludes      = [],
                    includes      = ["guiWindow"],
                    include_files = ["style.qss", "gui.ini"]
                    )

base = None
if sys.platform == "win32":
    base = "Win32GUI"

exe = [Executable("main.py", base=base, icon = "sillock-logo.ico")]

setup(
    name        = 'Sillock',
    version     = '1.0',
    author      = "XENIA",
    description = "Sillock Verifier Client]",
    options     = dict(build_exe = buildOptions),
    executables = exe
)