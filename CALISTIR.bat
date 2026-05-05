@echo off
chcp 65001 > nul
title SMMM Takip Sistemi
cd /d "%~dp0"
start "" /B "C:\Users\selim\.local\bin\python3.14.exe" main.py
