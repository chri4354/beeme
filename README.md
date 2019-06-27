# beeme
BeeMe paper

Notebook is notebook1.ipynb.

To run the main:
python main.py processed\_action\_csv processed\_chat\_csv scenario,

e.g.
python main.py data/winter\_lemmed\_srt.csv data/winter\_lemmed\_chat.csv winter

--
The actual processing of these requires WN SQL. The code is nonetheless in the repo, and should work once WNSQL is installed.


Processing action files:
Input is an action file (needs to be CSV in the same format as in data/illustration/winter\_srt.csv

To do it, run
python process/procsrt.py CSVfile

e.g.
python process/procstr.py data/illustration/winter\_srt.csv
--

Processing chat files:
Input is a chat log as in data/illustration/winter\_chat.txt

To do it, run
python process/procchat.py CSVfile

e.g.
python process/procchat.py data/illustration/winter\_chat.txt


