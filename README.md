# battleship-solitaire

## Description

This solver is created in the form of a Constraint Satisfaction Problem (CSP) and the Arc Consistency (GAC) algorithm 
for CSC384: Introduction to Algorithms course, which uses
some of the provided starter code for class initializations. Similar to the common game of battleship, battleship
solitaire is a game where there is a board that may or may not have any hints. Every cell on the board can be a part of a ship or 
water. Each puzzle provides its own constraints:

* row constraints: the number for each row corresponds to the number of ship parts allowed in that row
* column constraints: the number of ship parts allowed in each column
* water constraints: every ship must be surrounded by water, including its corners
* ship constraints: the number of each type of ship that is present on the final board. A ship may be a 1x1 submarine, a 1x2 destoyer, a 1x3 cruiser,
or a 1x4 battleship
* ships can only be horizontal or vertical, not diagonal

See how the game works here: https://lukerissacher.com/battleships

## How it works

Each input file has the following format:

* the first line is a sequence of numbers, representing the row constraints
* the second line is a sequence of numbers, representing the column constraints
* the third line is a sequence of 4 numbers, representing the ship constraints. The first is the number of submarines (represented by 'S'), 
the second is the number of destroyers ('<>') the third is the number of cruisers ('<M>'), and the last is the number of battleships ('<MM>')
* the remaining lines represent the board, where water is represented by '.' and an unknown cell is represented by '0'. The largest board size 
accounted for is 10x10
  
Here is an example of an input text file: 
  
      43213321
      22334203
      3321
      00000^00
      00000000
      00000000
      0000000.
      00000000
      00000000
      00000000
      00000000
  
The several functions and lines in the main function serve to initialize constraint classes and read in the input file. 
The output text file (output.txt) will be blank at first. Upon running the code, the solution board will be written into it. 
Here is an example output text file:
  
      .^.^.^.S
      .v.M.v..
      ...v...S
      ^.......
      v.^.^...
      ..M.M..S
      ..v.M...
      ....v...

## How to run it

To run the program, ensure that the necessary files are in the same folder. The terminal command used is:
        python3 battle.py --inputfile input.txt --outputfile output.txt

The solution will be printed into the output file, and it will also be displayed in the terminal with the time elapsed.
