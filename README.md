<h1>DAT550-Project-Chess_bot</h1>
A repository for a UiS project.

Members: Raphaël Gauthier, Harry Chicheortiche, Ronald Paleczny

The project consists of designing a chess bot through several methods:
<ul>
Four baseline models using decision tree, random forest and a Monte-Carlo Tree Search.
Two complex models using CNN
</ul>

The following explains how to use the code we wrote.

### First installation steps
First, you need to clone the repository into a direction on your computer using https or SSH. Then install the needed libraires. The recommended method is to create a virtual environment with:
<ul>
<li>python -m venv .venv (Windows)</li>
<li>python3 -m venv .venv (Linux)</li>
</ul>

The activate the environment:
<ul>
<li>source .venv/bin/activate (Linux)</li>
<li>source .venv/Scripts/activate (Windows + bash terminal)</li>
</ul>

Then do the following command in your terminal: pip install -r requirements.txt
If this does not work, just install the mentionned libraries in the file without their version like: 
<li>pip install chess matplotlib pandas numpy seaborn pyqt5 tqdm zstandard</li>

If you have another method to create an environment like anaconda, it should work.

<h3>Stockfish evaluator</h3>
You need to install the stockfish bot in order to evaluate the bots. You can download it on this <a href = https://stockfishchess.org/download/>link</a>




