@echo off
:: Debug launcher — shows errors in a console window.
:: Use this if the desktop shortcut / glmapp.cmd does nothing.
set PYTHONPATH=%~dp0;%PYTHONPATH%
python -m glmcode.gui --debug %*
if errorlevel 1 pause