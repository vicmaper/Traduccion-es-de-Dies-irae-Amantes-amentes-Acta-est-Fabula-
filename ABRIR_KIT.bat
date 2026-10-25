@echo off
chcp 65001 >nul
cd /d "%~dp0kit"
where py >nul 2>nul && (py -3 di_kit.py %* & goto fin)
where python >nul 2>nul && (python di_kit.py %* & goto fin)
echo No encontre Python. Descarga mejor DiesIrae_ES.exe desde la seccion Releases del repositorio.
pause
:fin
