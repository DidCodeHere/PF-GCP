@echo off
echo Setting up Smart Property Finder...
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
echo Setup Complete!
echo To run the tool, type:
echo venv\Scripts\activate
echo python -m src.main
pause
