# battleship-solitaire

## Description

This solver is created in the form of a Constraint Satisfaction Problem (CSP). Similar to the common game of battleship, battleship
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

## How to run it

To run the program, 
