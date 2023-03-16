# from select unasssigned variable:
    # select the variable with the smallest current domain: TODO - how to verify that it hasn't been assigned already?? 
    # best_var = csp.variables()[0]
    # best_var = None # initialize to None
    # best_var.curdom_size = 100 # initialize to a large number

# from old check ship constraints:

def check_ship_constraints_bad(assignment, state):
    '''Given the ship constraints as a list (state.ship_constraints), check if 
    the complete assignment satisfies the constraints and return True if it is
    the case, and False otherwise.
    - assignment is a dictionary of the form {var: value} with the new changes
    that must be implemented on a copy of the board
    - state is the state of the board, with the ship constraints
    '''

    # make a copy of the board, and implement the changes in assignment on it
    # TODO: fix and uncomment or delete this 
    # new_board = implement_assignment(assignment, state)
    # print("new_board: ", new_board)
    # new_board = [['.', '.', '.', '^', '.', '.'], ['S', '.', '.', 'M', '.', '.'], ['.', '.', '.', 'v', '.', '.'], ['.', '.', '.', '.', '.', 'S'], ['.', '^', '.', '^', '.', '.'], ['.', 'v', '.', 'v', '.', 'S']]

    # check that the correct number of each type of ship is present:
    submarines = state.ship_constraints[0] # 'S'
    destroyers = state.ship_constraints[1] # 1x2
    cruisers = state.ship_constraints[2] # 1x3
    battleships = state.ship_constraints[3] # 1x4

    # iterate through the board and reverse count each type of ship:
    # for i in range(len(new_board)):
    #     for j in range(len(new_board[i])):
    #         if new_board[i][j] == 'S':
    #             submarines -= 1
    #         elif new_board[i][j] == 'D':
    #             destroyers -= 1
    #         elif new_board[i][j] == 'C':
    #             cruisers -= 1
    #         elif new_board[i][j] == 'B':
    #             battleships -= 1
    
    # iterate through every row and look for horizontal ships or submarines:
    # for i in range(len(new_board)):
    #     for j in range(len(new_board[i])):
    #         if new_board[i][j] == 'S':
    #             submarines -= 1
    #         elif new_board[i][j] == 'M':

    # iterate through rows, looking for submarines and horizontal ships:
#     for i in range(len(new_board)):
#         for j in range(len(new_board[i])):
#             if new_board[i][j] == 'S':
#                 submarines -= 1
#             elif new_board[i][j] == '<': 
#                 if new_board[i][j+1] == '>': #<>
#                     destroyers -= 1 
#             elif new_board[i][j] == 'M':
#                 # check the sides as long as not on the edge of the board
#                 if j != 0 and j != len(new_board[i])-1:
#                     if new_board[i][j-1] == '<' and new_board[i][j+1] == '>': # <M>
#                         cruisers -= 1

#                         #TODO: implement checks for 1x4 horizontal ships
#                     # elif new_board[i][j-1] == 'M' or new_board[i][j+1]=='M': # another M to the left found -> <MM>
#                     #     battleships -= 1

#                 # if new_board[i][j-1] == 'S' or new_board[i][j+1] == 'S':
#                 #     submarines -= 1
#                 # elif new_board[i][j-1] == 'M' or new_board[i][j+1] == 'M':
#                 #     destroyers -= 1
#                 # elif new_board[i][j-1] == 'C' or new_board[i][j+1] == 'C':
#                 #     cruisers -= 1
#                 # elif new_board[i][j-1] == 'B' or new_board[i][j+1] == 'B':
#                 #     battleships -= 1

#                 #TODO TODO: actually, use the Nvalues class to check the ship constraint 

#     #TODO: iteraate through columns (make them lists or something), looking for vertical ships (not submaarines to avoid double count)

#     # if the number of ships of each type is not correct, return False
#     if submarines != 0 or destroyers != 0 or cruisers != 0 or battleships != 0:
#         return False
#     else:
#         return True
    
# def check_ship_constraints2(new_state):
#     '''Given the ship constraints as a list (state.ship_constraints), check if 
#     the complete assignment satisfies the constraints and return True if it is
#     the case, and False otherwise.
#     - assignment is a dictionary of the form {var: value} with the new changes
#     that must be implemented on a copy of the board
#     - state is the state of the board, with the ship constraints
#     '''

#     # make a copy of the board, and implement the changes in assignment on it
#     # new_state = implement_assignment2(assignment, state)

#     # check that the correct number of each type of ship is present:
#     submarines = state.ship_constraints[0]
#     destroyers = state.ship_constraints[1]
#     cruisers = state.ship_constraints[2]
#     battleships = state.ship_constraints[3]

#     # iterate through the board and reverse count each type of ship:
#     for i in range(len(new_state.board)):
#         for j in range(len(new_state.board[i])):
#             if new_state.board[i][j] == 'S':
#                 submarines -= 1
#             elif new_state.board[i][j] == 'D':
#                 destroyers -= 1
#             elif new_state.board[i][j] == 'C':
#                 cruisers -= 1
#             elif new_state.board[i][j] == 'B':
#                 battleships -= 1
    
#     # if the number of ships of each type is not correct, return False
#     if submarines != 0 or destroyers != 0 or cruisers != 0 or battleships != 0:
#         return False
#     else:
#         return True

# def implement_assignment2(assignment, state):
#     '''Given an assignment, implement the changes on a copy of the board and 
#     return that state. It can be later displayed with state.display()'''
    
#     if len(assignment) == 0:
#         return state
    
#     # make a copy of the original state using deepcopy:
#     new_state = copy.deepcopy(state)

#     for var in assignment:
#         new_state.board[var.y][var.x] = assignment[var]
#     return new_state

# I have two strings where one represents a board, and the second represents the transposed version. how 
# do i combine them into a single board while keeping any pieces that are not '.' or 'S' from being overwritten: 
# ......
# .S..<>
# .S....
# .S.S.S
# ...S..
# S....S and 

# .....S
# .^Mv..
# ......
# ...^v.
# .S....
# .S.S.S

# from check ship constraints:
