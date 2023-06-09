import sys
import argparse
import heapq # use for MRV/LCV heuristics 
import time
from copy import deepcopy

#implement various types of constraints
class Constraint:
    '''Base class for defining constraints. Each constraint can check if
    it has been satisfied, so each type of constraint must be a
    different class. For example a constraint of notEquals(V1,V2)
    must be a different class from a constraint of
    greaterThan(V1,V2), as they must implement different checks of
    satisfaction.

    However one can define a class of general table constraints, as
    below, that can capture many different constraints.

    On initialization the constraint's name can be given as well as
    the constraint's scope. IMPORTANT, the scope is ordered! E.g.,
    the constraint greaterThan(V1,V2) is not the same as the
    contraint greaterThan(V2,V1).
    '''
    def __init__(self, name, scope):
        '''create a constraint object, specify the constraint name (a
        string) and its scope (an ORDERED list of variable
        objects).'''
        self._scope = list(scope)
        self._name = "baseClass_" + name  #override in subconstraint types!

    def scope(self):
        return list(self._scope)

    def arity(self):
        return len(self._scope)

    def numUnassigned(self):
        i = 0
        for var in self._scope:
            if not var.isAssigned():
                i += 1
        return i

    def unAssignedVars(self):
        return [var for var in self.scope() if not var.isAssigned()]

    # def check(self):
    #     util.raiseNotDefined()

    def name(self):
        return self._name

    def __str__(self):
        return "Cnstr_{}({})".format(self.name(), map(lambda var: var.name(), self.scope()))

    def printConstraint(self):
        print("Cons: {} Vars = {}".format(
            self.name(), [v.name() for v in self.scope()]))

class TableConstraint(Constraint):
    '''General type of constraint that can be use to implement any type of
        constraint. But might require a lot of space to do so.
        A table constraint explicitly stores the set of satisfying
        tuples of assignments.'''

    def __init__(self, name, scope, satisfyingAssignments):
        '''Init by specifying a name and a set variables the constraint is over.
            Along with a list of satisfying assignments.
            Each satisfying assignment is itself a list, of length equal to
            the number of variables in the constraints scope.
            If sa is a single satisfying assignment, e.g, sa=satisfyingAssignments[0]
            then sa[i] is the value that will be assigned to the variable scope[i].


            Example, say you want to specify a constraint alldiff(A,B,C,D) for
            three variables A, B, C each with domain [1,2,3,4]
            Then you would create this constraint using the call
            c = TableConstraint('example', [A,B,C,D],
                                    [[1, 2, 3, 4], [1, 2, 4, 3], [1, 3, 2, 4],
                                    [1, 3, 4, 2], [1, 4, 2, 3], [1, 4, 3, 2],
                                    [2, 1, 3, 4], [2, 1, 4, 3], [2, 3, 1, 4],
                                    [2, 3, 4, 1], [2, 4, 1, 3], [2, 4, 3, 1],
                                    [3, 1, 2, 4], [3, 1, 4, 2], [3, 2, 1, 4],
                                    [3, 2, 4, 1], [3, 4, 1, 2], [3, 4, 2, 1],
                                    [4, 1, 2, 3], [4, 1, 3, 2], [4, 2, 1, 3],
                                    [4, 2, 3, 1], [4, 3, 1, 2], [4, 3, 2, 1]])
            as these are the only assignments to A,B,C respectively that
            satisfy alldiff(A,B,C,D) - all possible combinations possible that
            satisfy the constraint
        '''

        Constraint.__init__(self, name, scope)
        self._name = "TableCnstr_" + name
        self.satAssignments = satisfyingAssignments

    def check(self):
        '''check if current variable assignments are in the satisfying set'''
        assignments = []
        for v in self.scope(): # scope is the list of all variables the constraint affects
            if v.isAssigned(): # if the variable has been assigned a value
                assignments.append(v.getValue()) # add the value to the list
            else:
                return True
        return assignments in self.satAssignments # return list of whichever assignments are valid (listed in satisfyingAssignments)

    def hasSupport(self, var, val):
        '''check if var=val has an extension to an assignment of all variables in
        constraint's scope that satisfies the constraint. Important only to
        examine values in the variable's current domain as possible extensions. 
        
        In other words: TODO'''
        if var not in self.scope():
            return True   #var=val has support on any constraint it does not participate in
        vindex = self.scope().index(var) # get the index of the variable in the scope
        found = False
        for assignment in self.satAssignments: # for each assignment in the list of satisfying assignments
            if assignment[vindex] != val: #if the assignment doesn't assign var=val; check every other variable except the one you assigned
                continue   # this assignment can't work it bc doesn't make var=val; skip this assignment configuration
            found = True   #Otherwise it has potential (it's in the satisfied list for the one constraint). Assume found until shown otherwise
            for i, v in enumerate(self.scope()): # for each variable in the scope other than the one assigned
                if i != vindex and not v.inCurDomain(assignment[i]): # if it's not the variable we are checking and it's not in the variable's current domain
                    found = False  # the assignment doesn't work; assigned a value that's not in v's domain for a variable in the scope
                    break # move on to the next satisfying assignment/potential solution
            if found: # if found still true the assigment worked. We can stop
                break
        return found  # either way found has the right truth value; returns True if this assignment works for this one constraint 

class State:
    '''Class for defining a state. '''

    def __init__(self):
        self.board = []
        self.dim = None # dimensions of the board (n x n)
        self.row_constraints = None
        self.col_constraints = None
        self.ship_constraints = None
        self.variables = [] # list of variables (cell-based_)
        self.varn = {} # dictionary of variables; key = str(i*dim+j), value = Variable class item
        self.hints = []

    def display(self):
        for i in self.board:
            for j in i:
                print(j, end="") 
            print("")
        print("")

    def read_from_file(self, filename):
        f = open(filename)
        lines = f.readlines()
        
        # the first 3 lines are not in the board:
        self.row_constraints = [int(x) for x in lines[0].strip()] # list of ints
        self.col_constraints = [int(x) for x in lines[1].strip()]
        self.ship_constraints = [int(x) for x in lines[2].strip()]

        # dim is the number of rows or cols:
        self.dim = len(self.row_constraints)

        # the rest of the lines are in the board:
        for l in lines[3:]:
            self.board.append([str(x) for x in l.rstrip()])

        f.close()
    
    def precondition_state(self):
        '''Given the inital state, precondition by using any information given.'''
        # look through the row and col constraints to see if there are any 0's:
        for i in range(len(self.row_constraints)):
            if self.row_constraints[i] == 0:
                # assign all variables in that row to '.':
                for j in range(len(self.board[i])):
                    self.board[i][j] = '.'
            if self.col_constraints[i] == 0:
                # assign all variables in that col to '.':
                for j in range(len(self.board)):
                    self.board[j][i] = '.'
        
        # look through the board for ship hints. replace with generic 'S' and
        # surround diagonals with water:
        for i in range(len(self.board)):
            for j in range(len(self.board[i])):
                if self.board[i][j] != '.' and self.board[i][j] != '0':
                    self.board[i][j] = 'S'
                    if i > 0 and j > 0:
                        self.board[i-1][j-1] = '.'
                    if i > 0 and j < len(self.board[i])-1:
                        self.board[i-1][j+1] = '.'
                    if i < len(self.board)-1 and j > 0:
                        self.board[i+1][j-1] = '.'
                    if i < len(self.board)-1 and j < len(self.board[i])-1:
                        self.board[i+1][j+1] = '.'

    def init_variables(self):
        '''Initialize the variables of the problem; each cell on the board is 
        a variable.'''

        # for every (i,j) cell on the board, create a variable:
        for i in range(self.dim): # for each row
            for j in range(self.dim): # for each col
                v = None
                if state.board[i][j] != '0': # if has been assigned (if they give initiial hints)
                    # create a new variable:
                    # v = Variable("v_{}_{}".format(i,j), [0,1])
                    if state.board[i][j] == '.':
                        v = Variable(str((i*self.dim+j)), self.board[i][j], j,i)
                        v._value = self.board[i][j]
                    else:
                        v = Variable(str((i*self.dim+j)), 'S', j,i)
                        v._value = 'S' # start by replacing all ship parts with just 'S'
                else:
                    # create a new variable:
                    v = Variable(str((i*self.dim+j)), ['S','.'],j,i)
        
                self.variables.append(v) # add the variable to the list of variables
                self.varn[str((i*self.dim+j))] = v # add the variable to the dictionary of variables
                # add the variable to the board:
                # self.board[i][j] = v #TODO - is this line necessary??

    def init_variables_bad(self):
        '''Initialize the variables of the problem; each cell on the board is 
        a variable.'''

        # for every (i,j) cell on the board, create a variable:
        for i in range(self.dim): # for each row
            for j in range(self.dim): # for each col
                v = None
                if state.board[i][j] != '0': # if has been assigned (if they give initiial hints)
                    # create a new variable:
                    # v = Variable("v_{}_{}".format(i,j), [0,1])
                    v = Variable(str((i*self.dim+j)), [self.board[i][j]], j,i)
                    v._value = self.board[i][j]
                else:
                    # create a new variable:
                    if i == 0 and j == 0: # top left corner
                        v = Variable(str((i*self.dim+j)), ['S','.','<','^'],j,i) # can't have 'v' or '>' or 'M' piece
                    elif i == self.dim-1 and j == self.dim-1: # bottom right corner
                        v = Variable(str((i*self.dim+j)), ['S','.','>','v'],j,i) # can't have '^' or '<' or 'M' piece
                    elif i == 0 and j == self.dim-1: # top right corner
                        v = Variable(str((i*self.dim+j)), ['S','.','>','^'],j,i) # can't have 'v' or '<' or 'M' piece
                    elif i == self.dim-1 and j == 0: # bottom left corner
                        v = Variable(str((i*self.dim+j)), ['S','.','<','v'],j,i) # can't have '^' or '>' or 'M' piece
                    elif i == 0: # top edge
                        v = Variable(str((i*self.dim+j)), ['S','.','<','>','^','M'],j,i) # can't have 'v' piece
                    elif i == self.dim-1: # bottom edge
                        v = Variable(str((i*self.dim+j)), ['S','.','<','>','v','M'],j,i) # can't have '^' piece
                    elif j == self.dim-1: # right edge
                        v = Variable(str((i*self.dim+j)), ['S','.','>','^','v','M'],j,i) # can't have '<' piece
                    elif j == 0: # left edge
                        v = Variable(str((i*self.dim+j)), ['S','.','<','^','v','M'],j,i) # can't have '>' piece
                    else:
                        v = Variable(str((i*self.dim+j)), ['S','.','<','>','^','v','M'],j,i) # variable with full domain 
                self.variables.append(v) # add the variable to the list of variables
                self.varn[str((i*self.dim+j))] = v # add the variable to the dictionary of variables
                # add the variable to the board:
                # self.board[i][j] = v #TODO - is this line necessary??

class Variable:
    '''Class for defining CSP variables.

    On initialization the variable object can be given a name and a
    list containing variable's domain of values. You can reset the
    variable's domain if you want to solve a similar problem where
    the domains have changed.

    To support CSP propagation, the class also maintains a current
    domain for the variable. Values pruned from the variable domain
    are removed from the current domain but not from the original
    domain. Values can be also restored.
    '''

    undoDict = dict()             # stores pruned values indexed by a TODO ???
                                        # (variable,value) reason pair
    def __init__(self, name, domain, x, y):
        '''Create a variable object, specifying its name (a
        string) and domain of values.
        '''
        self._name = name                # text name for variable
        self._dom = list(domain)         # Make a copy of passed domain
        self._curdom = list(domain)      # using list
        self.curdom_size = len(list(domain)) # the size of the current domain size
        self._value = None
        self.x = x
        self.y = y

    def __str__(self):
        return "Variable {}".format(self._name)

    def domain(self):
        '''return copy of variable domain'''
        return(list(self._dom))

    def domainSize(self):
        '''Return the size of the domain'''
        return(len(self.domain()))

    def resetDomain(self, newdomain):
        '''reset the domain of this variable'''
        self._dom = newdomain

    def getValue(self):
        return self._value

    def setValue(self, value):
        if value != None and not value in self._dom:
            print("Error: tried to assign value {} to variable {} that is not in {}'s domain".format(value,self._name,self._name))
        else:
            self._value = value    

    def unAssign(self):
        self.setValue(None)

    def isAssigned(self):
        return self.getValue() != None # True if the value has been assigned or False if None

    def name(self):
        return self._name

    def curDomain(self):
        '''return copy of variable current domain. But if variable is assigned
        return just its assigned value (this makes implementing hasSupport easier'''
        if self.isAssigned():
            return([self.getValue()])
        return(list(self._curdom))

    def curDomainSize(self):
        '''Return the size of the current domain'''
        if self.isAssigned():
            return(1)
        return(len(self._curdom))

    def inCurDomain(self, value):
        '''check if value is in current domain'''
        if self.isAssigned():
            return(value==self.getValue())
        return(value in self._curdom)

    def pruneValue(self, value, reasonVar, reasonVal):
        '''Remove value from current domain'''
        try:
            self._curdom.remove(value)
        except:
            print("Error: tried to prune value {} from variable {}'s domain, but value not present!".format(value, self._name))
        dkey = (reasonVar, reasonVal)
        if not dkey in Variable.undoDict:
            Variable.undoDict[dkey] = []
        Variable.undoDict[dkey].append((self, value))

    def restoreVal(self, value):
        self._curdom.append(value)

    def restoreCurDomain(self):
        self._curdom = self.domain()

    def reset(self):
        self.restoreCurDomain()
        self.unAssign()

    def dumpVar(self):
        print("Variable\"{}={}\": Dom = {}, CurDom = {}".format(self._name, self._value, self._dom, self._curdom))

    @staticmethod
    def clearUndoDict():
        undoDict = dict()

    @staticmethod
    def restoreValues(reasonVar, reasonVal):
        dkey = (reasonVar, reasonVal)
        if dkey in Variable.undoDict:
            for (var,val) in Variable.undoDict[dkey]:
                var.restoreVal(val)
            del Variable.undoDict[dkey]

class water_constraints(Constraint): #TODO modify starter code 
    '''NValues constraint over a set of variables.  Among the variables in
    the constraint's scope the number that have been assigned
    values in the set 'required_values' is in the range
    [lower_bound, upper_bound] (lower_bound <= #of variables
    assigned 'required_value' <= upper_bound)

    For example, if we have 4 variables V1, V2, V3, V4, each with
    domain [1, 2, 3, 4], then the call
    NValuesConstraint('test_nvalues', [V1, V2, V3, V4], [1,4], 2,
    3) will only be satisfied by assignments such that at least 2
    the V1, V2, V3, V4 are assigned the value 1 or 4, and at most 3
    of them have been assigned the value 1 or 4.

    '''

    def __init__(self, name, scope, required_values, lower_bound, upper_bound):
        Constraint.__init__(self,name, scope)
        self._name = "NValues_" + name
        self._required = required_values
        self._lb = lower_bound
        self._ub = upper_bound

    def check(self):
        assignments = []
        for v in self.scope():
            if v.isAssigned():
                assignments.append(v.getValue())
            else:
                return True
        rv_count = 0

        #print "Checking {} with assignments = {}".format(self.name(), assignments)

        for v in assignments:
            if v in self._required:
                rv_count += 1

        #print "rv_count = {} test = {}".format(rv_count, self._lb <= rv_count and self._ub >= rv_count)

        return self._lb <= rv_count and self._ub >= rv_count

    def hasSupport(self, var, val):
        '''check if var=val has an extension to an assignment of the
        other variable in the constraint that satisfies the constraint

        HINT: check the implementation of AllDiffConstraint.hasSupport
                a similar approach is applicable here (but of course
                there are other ways as well)
        '''
        if var not in self.scope():
            return True   #var=val has support on any constraint it does not participate in

        #define the test functions for findvals
        def valsOK(l):
            '''tests a list of assignments which are pairs (var,val)
            to see if they can satisfy this sum constraint'''
            rv_count = 0 #count of required values
            vals = [val for (var, val) in l] #list of values in the assignment
            for v in vals:
                if v in self._required: #if the value is a required value
                    rv_count += 1
            least = rv_count + self.arity() - len(vals) #the least number of required values that could be in the assignment
            most =  rv_count #the most number of required values that could be in the assignment
            return self._lb <= least and self._ub >= most #return true if the number of required values is in the range
        varsToAssign = self.scope() #list of variables in the constraint
        varsToAssign.remove(var) #remove the variable that is being assigned
        x = findvals(varsToAssign, [(var, val)], valsOK, valsOK) #find an assignment that satisfies the constraint
        return x

class row_constraints(Constraint):
    '''Ensures that the number of ship parts in a row correspond to 
    the given numbers of how many ships parts should be in that row
    (self.row_constraint). The scope is all the variables in a row.'''
    def __init__(self, name, scope, row_constraint):
        Constraint.__init__(self, name, scope)
        self._name = "row_constraints" + name
        self.row_constraint = row_constraint
        # self.col_constraints = col_constraints

    def hasSupport(self, var, val):
        '''Checks if the variables other than the one assigned (val) are 
        a valid combination overall with this one constraint.
        - var is the variable that is assigned/fixed: format is Variable type
        - val is the value that is assigned to var: format is a string
        '''
        if var not in self.scope():
            return True # var=val has support on any constraint it does not participate in
        
        def check_rows(l):
            ''' TODO tests a list of assignments which are pairs (var,val)
            to see if they can satisfy the all diff. l is a list of tuples
            for the variables of one row, and k is the constraint number '''
            ship_parts = 0
            for i in range(len(l)):
                if l[i][1] == 'S':
                    ship_parts += 1
            if len(l) < len(self.scope()):
                return ship_parts <= self.row_constraint # True if valid so far (num ship parts <= row constraint)
            else:
                return ship_parts == self.row_constraint # True if valid (num ship parts == row constraint)
            # vals = [val for (var, val) in l]
            # return len(set(vals)) == len(vals)

        def check_rows_bad(l):
            ''' TODO tests a list of assignments which are pairs (var,val)
            to see if they can satisfy the all diff. l is a list of tuples
            for the variables of one row, and k is the constraint number '''
            ship_parts = 0
            for i in range(len(l)):
                if l[i][1] == 'S' or l[i][1] == 'M' or l[i][1] == '<'\
                    or l[i][1] == '>' or l[i][1] == '^' or l[i][1] == 'v':
                    ship_parts += 1
            if len(l) < len(self.scope()):
                return ship_parts <= self.row_constraint # True if valid so far (num ship parts <= row constraint)
            else:
                return ship_parts == self.row_constraint # True if valid (num ship parts == row constraint)
            # vals = [val for (var, val) in l]
            # return len(set(vals)) == len(vals)

        varsToAssign = self.scope() # all variables in row k
        varsToAssign.remove(var) # remove the already assigned variable

        # findvals takes the variable with the largest domain and tries to assign it
        # assigns every value in its domain and recursively checks if it satisfiess
        # the constraint
        x = findvals(varsToAssign, [(var, val)], check_rows, check_rows) 
        return x # returns True if it finds a valid combination

class col_constraints(Constraint):
    '''Ensures that the number of ship parts in a column correspond to 
    the given numbers of how many ships parts should be in that column
    (self.col_constraint). The scope is the a list of variables in a column.'''
    def __init__(self, name, scope, col_constraint):
        Constraint.__init__(self, name, scope)
        self._name = "col_constraints" + name
        # self.row_constraints = row_constraints
        self.col_constraint = col_constraint

    def check(self, k): # TODO fix - probably wrong
        '''Loop through every variable in the scope (variables in column 
        k and checks if it breaks the constraint.'''

        assignments = [] # list of values for the col
        ship_parts = 0 # initialize number of ship parts in the col
        # num =  # number of ship parts in the col

        # for v in self.scope()[k]: # loop through variables in col k
        #     if v.isAssigned():
        #         assignments.append(v.getValue())
        #         # increment ship_parts if the value is a ship part:
        #         if v.getValue() == 'S' or v.getValue() == 'M' or v.getValue() == '<'\
        #             or v.getValue() == '>' or v.getValue() == '^' or v.getValue() == 'v':
        #             ship_parts += 1
        #     else:
        #         # if ship_parts <= col constraint TODO??????????
        #         return True # if not all variables are assigned, return True
        pass
        # for ass in assignments:
        # # return 

    def hasSupport(self, var, val):
        ''' TODO Checks if the variables other than the one assigned (val) are 
        a valid combination overall with this one constraint.
        - var is the variable that is assigned/fixed
        - val is the value that is assigned to var
        '''
        if var not in self.scope():
            return True # var=val has support on any constraint it does not participate in
        
        def check_cols(l):
            '''tests a list of assignments which are pairs (var,val)
            to see if they can satisfy the all diff'''
            ship_parts = 0
            for i in range(len(l)):
                if l[i][1] == 'S' or l[i][1] == 'M' or l[i][1] == '<'\
                    or l[i][1] == '>' or l[i][1] == '^' or l[i][1] == 'v':
                    ship_parts += 1
            if len(l) < len(self.scope()):
                return ship_parts <= self.col_constraint
            else:
                return ship_parts <= self.col_constraint # True if valid (num ship parts <= col constraint)
            # vals = [val for (var, val) in l]
            # return len(set(vals)) == len(vals)

        varsToAssign = self.scope()
        varsToAssign.remove(var)

        # findvals takes the variable with the largest domain and tries to assign it
        # assigns every value in its domain and recursively checks if it satisfiess
        # the constraint
        x = findvals(varsToAssign, [(var, val)], check_cols, check_cols) 
        return x

#object for holding a constraint problem
class CSP:
    '''CSP class groups together a set of variables and a set of
    constraints to form a CSP problem. Provides a useful place
    to put some other functions that depend on which variables
    and constraints are active'''

    def __init__(self, name, variables, constraints):
        '''create a CSP problem object passing it a name, a list of
        variable objects, and a list of constraint objects'''
        self._name = name
        self._variables = variables
        self._constraints = constraints
        self.solution = ''

        #some sanity checks
        varsInCnst = set()
        for c in constraints:
            varsInCnst = varsInCnst.union(c.scope())
        for v in variables:
            if v not in varsInCnst:
                print("Warning: variable {} is not in any constraint of the CSP {}".format(v.name(), self.name()))
        for v in varsInCnst:
            if v not in variables:
                print("Error: variable {} appears in constraint but specified as one of the variables of the CSP {}".format(v.name(), self.name()))

        self.constraints_of = [[] for i in range(len(variables))]
        for c in constraints:
            for v in c.scope():
                i = variables.index(v)
                self.constraints_of[i].append(c)

    def name(self):
        return self._name

    def variables(self):
        return list(self._variables)

    def constraints(self):
        return list(self._constraints)

    def constraintsOf(self, var):
        '''return constraints with var in their scope'''
        try:
            i = self.variables().index(var)
            return list(self.constraints_of[i])
        except:
            print("Error: tried to find constraint of variable {} that isn't in this CSP {}".format(var, self.name()))

    def unAssignAllVars(self):
        '''unassign all variables'''
        for v in self.variables():
            v.unAssign()

    def check(self, solutions):
        '''each solution is a list of (var, value) pairs. Check to see
        if these satisfy all the constraints. Return list of
        erroneous solutions'''

        #save values to restore later
        current_values = [(var, var.getValue()) for var in self.variables()]
        errs = []

        for s in solutions:
            s_vars = [var for (var, val) in s]

            if len(s_vars) != len(self.variables()):
                errs.append([s, "Solution has incorrect number of variables in it"])
                continue

            if len(set(s_vars)) != len(self.variables()):
                errs.append([s, "Solution has duplicate variable assignments"])
                continue

            if set(s_vars) != set(self.variables()):
                errs.append([s, "Solution has incorrect variable in it"])
                continue

            for (var, val) in s:
                var.setValue(val)

            for c in self.constraints():
                if not c.check():
                    errs.append([s, "Solution does not satisfy constraint {}".format(c.name())])
                    break

        for (var, val) in current_values:
            var.setValue(val)

        return errs

    def gac_enforce(self, constraints, assignedvar, assignedval):
        '''Establish GAC on all affected constraints.
        - constraints is a list of constraints not known to GAC
        - assignedvar is the variable that was just assigned a value
        - assignedval is the value that was just assigned to assignedvar
        '''
        while len(constraints) > 0:
            c = constraints.pop() # make constraint GAC
            for var in c.scope(): # for each variable in the constraint's scope
                for val in var._curdom: # for each value in the variable's domain
                    if not c.hasSupport(var, val): # if the value doesn't satisfy the constraint
                        var.pruneValue(val, assignedvar, assignedval) # remove the value from the variable's domain
                        if var.curdom_size == 0: # if the domain is empty
                            return "DWO" # domain wipe out
                        for c2 in self.constraintsOf(var): # for each constraint in the CSP that involves the variable
                            if c2 != c and not c2 in constraints:
                                constraints.append(c2) # or use insert?
        return "OK"

    def gac(self, unassignedvars, state): # can use unAssignedVars from Constraint class
        '''Establish GAC on all constraints involving unassigned variables.'''
        # sol_found = False
        if len(unassignedvars) == 0: # if complete assignment
            # check ship constraints:
            assigned = {}
            for v in csp.variables():
                if v.isAssigned() == True:
                    assigned[v] = v.getValue()
            # print("assigned from gac: ", assigned)

            try_it = check_ship_constraints(assigned, state) # (True, board) if ship_constraints satisfied
            if try_it[0] == True:
                print("try_it[1]: ")
                print(try_it[1]) 
                self.solution += deepcopy(try_it[1])
                sol_found = True
                # self.solution.append(deepcopy(assigned)) # or return check_ship_constraaints[1] because thats the filled in board?
                return True # TODO what should i be returning? or breaak here??
            else:
                return  False# TODO what should i be returning? if anything?

        var = unassignedvars.pop() # selecte next variable to assign
        for val in var.curDomain():
            var.setValue(val) # assign var = val
            noDWO = True
            if self.gac_enforce(self.constraintsOf(var), var, val) == "DWO": # constraintsOf() returns constraints with var in their scope
                # only vara's domain changed-constraints with var have to be checked
                noDWO = False
            if noDWO:
                sol_found = self.gac(unassignedvars, state) # recursive call
                if sol_found == True:
                    return True
            # restore values pruned by var = val assignment:
            var.restoreValues(var, val)
        var.unAssign() # unassign var; same as var.setValue(None)
        unassignedvars.append(var) # put var back on the stack. use insert??
        return False
        
    def __str__(self):
        return "CSP {}".format(self.name())

def select_unassigned_variable(csp):
    '''Select the next unassigned variable without a value. Pick variables based
    on the smallest domain (Most Constrained Variable Heuristic). 

    - csp.variables is a list of all variables in the CSP

    The function returns the best variable (the unassigned variable with the
    smallest domain) or None if there is no unassigned variable left.
    '''

    best_var = None

    # initialize the best_var with the first unasssigned variable:
    for v in csp.variables():
        if v.isAssigned() == False:
            best_var = v
            break
    
    # if the domain is empty (the for loop finishes), then there is no unassigned variable:
    if best_var == None:
        return best_var # return None if there is no unassigned variable left 

    for v in csp.variables():
        if v.curdom_size < best_var.curdom_size:
            if v.isAssigned() == False:
                if best_var == None: # at first, take the first unassigned variable
                    best_var = v
                else:
                    best_var = v
    return best_var
    # best_var = min(csp.variables(), key=lambda v: v.curdom_size) # returns the variable with the smallest domain

def order_domain_values(var, assignment, csp):
    '''TODO. Try all possible values for unassigned variable'''
    # return var.curDomain()
    pass

def convert_to_str(board):
    '''Convert the board to a string.'''
    board_str = ""
    for row in board:
        for col in row:
            board_str += str(col)
        board_str += "\n"
    return board_str

# Backtracking search:
def backtrack_search(csp, state):
    # The assignment should contain all variables that have already been assigned (hints)
    assignment = {}
    for v in csp.variables():
        if v.isAssigned() == True:
            assignment[v] = v.getValue()
    # print("assignment: ", assignment)
    return backtrack(assignment, csp, state)

def backtrack(assignment, csp, state):
    '''Try to assign values that satisfy the constraints. If it can't, backtrack and try again.'''
    # if assignment is complete, return assignment TODO - check what "complete" is and later implement forward checking 
    if len(assignment) == len(csp.variables()):

        # now check if it satisfies the ship/water constraints, combine into final board: 
        if check_ship_constraints(assignment, state)[0] == True:
            return assignment
        else:
            return None
    
    var = select_unassigned_variable(csp)
    
    if var == None: # if there are no unassigned variables left
        return assignment

    for value in var._curdom:
        all_constraints = [] # list of what constraints are satisfied
        for c in csp.constraintsOf(var): # loop through all the constraints (the conslist initialized in main)
            if c.hasSupport(var, value) == True:
                all_constraints.append(True)
            else:
                all_constraints.append(False)
        if all(all_constraints) == True: # only if all constraints are satisfied, assign the value
            assignment[var] = value
            var.setValue(value)

            result = backtrack(assignment, csp, state) # look at remaining unassigned variables (recursive call)
            if result != None: # if result is not a failure
                return result # if it worked, return the 
        # find bad value with variable, and remove it from the assignment dictionary bsince it doesn't satisfy a constraint
        # print("result: ", result)
            del assignment[var] # remove var from assignment, so it's now unassigned
            var.unAssign() # unassign var (it's value is reset to None)

        # var._curdom.remove(value)
        # remove it 
        # assignment.pop(var) # remove var from assignment
    return None # failure; no solution
        
def check_ship_constraints(assignment, state):
    '''Given check if a full assignment (of a board) satisfies the original 
    state's ship constraints. It returns a tuple (True/False, message). The 
    message is either a string output of the solution or an error message.'''

    # the correct number of each type of ship is present:
    submarines = state.ship_constraints[0] # 'S'
    destroyers = state.ship_constraints[1] # 1x2
    cruisers = state.ship_constraints[2] # 1x3
    battleships = state.ship_constraints[3] # 1x4

    # implement the assignment changes to the board:
    new_board = implement_assignment(assignment, state)
    # print("HINTS: ", state.hints)

    rows_list = new_board # the board is a list of rows
    rows = convert_to_str(rows_list) # convert the board to a string
    cols_list = list(zip(*rows_list)) # transpose the board to have a list of columns
    cols = convert_to_str(cols_list) # convert the board to a string

    # replace sequences of S's with their representative ships:
    rows = rows.replace("SSSS", "<MM>")
    rows = rows.replace("SSS", "<M>")
    rows = rows.replace("SS", "<>")
    cols = cols.replace("SSSS", "^MMv")
    cols = cols.replace("SSS", "^Mv")
    cols = cols.replace("SS", "^v")

    # if there are any consecutive ship parts that are from different ships (!= '.' then it's BAD)
    # check rows:
    bad_cases = 0
    bad_cases += rows.count("><")
    bad_cases += rows.count(">S")
    bad_cases += rows.count("S<")
    bad_cases += cols.count("v^")
    bad_cases += cols.count("vS")
    bad_cases += cols.count("S^")

    if bad_cases > 0:
        return (False, "Error: Ships overlap.")

    dim = len(rows_list)

    # count the number of each type of ship other than S:
    destroyers_count = rows.count("<>") + cols.count("^v")
    cruisers_count = rows.count("<M>") + cols.count("^Mv")
    battleships_count = rows.count("<MM>") + cols.count("^MMv")

    # convert col string back to list of lists, and split it at the newlines:
    cols_list = []
    for i in range(dim):
        cols_list.append(cols.splitlines()[i])
        for c in range(dim):
            cols_list[i] = list(cols_list[i])

    # transpose the cols list back: 
    cols_list = list(zip(*cols_list))   
    # print("cols_list: ", cols_list)

    # convert back to string:
    cols = convert_to_str(cols_list)

    # combine both to get solution board. Overwrite anything in rows with col elem  if not in ['S', '.', '\n']:
    sol_board = ""

    for i in range(len(rows)):
        if cols[i] not in ['S', '.', '\n']:
            sol_board += cols[i]
        else:
            sol_board += rows[i]
        

    submarines_count = sol_board.count('S')
    # print("submarines count: ", submarines_count)
    # print(sol_board)

    # ensure that all of the previous hints are still in place: TODO FIX THIS
    # take out all \n characters:
    sol_string = sol_board.replace("\n", "")
    # print("sol_string: ", sol_string)
    for hint in state.hints:
        # check that coordinate of hint is in same place as string equivalent in sol_board
        str_x = hint[1]
        str_y = hint[0]*dim
        # print("is this running?")
        # print(hint._value)
        if hint[2] != sol_string[str_y + str_x]:
            return (False, "Error: Hint is not in the correct place.")

    # check if the number of each type of ship is correct:
    if submarines_count == submarines and destroyers_count == destroyers and \
        cruisers_count == cruisers and battleships_count == battleships:
        return True, sol_board
    
    return False, "wrong"

def check_ship_constraints_verybad(assignment, state):
    '''Given check if a full assignment (of a board) satisfies the original 
    state's ship constraints.'''

    # the correct number of each type of ship is present:
    submarines = state.ship_constraints[0] # 'S'
    destroyers = state.ship_constraints[1] # 1x2
    cruisers = state.ship_constraints[2] # 1x3
    battleships = state.ship_constraints[3] # 1x4

    # implement the assignment changes to the board:
    new_board = implement_assignment(assignment, state)
    # new_board = [['.', '.', '.', '^', '.', '.'], ['S', '.', '.', 'M', '.', '.'], ['.', '.', '.', 'v', '.', '.'], ['.', '.', '.', '.', '.', 'S'], ['.', '^', '.', '^', '.', '.'], ['.', 'v', '.', 'v', '.', 'S']]

    #TODO - redo everything from here. convert new_board into strings to iteratate better

    rows_list = new_board # the board is a list of rows
    cols_list = list(zip(*rows_list)) # transpose the board to have a list of columns

    # iterate through rows list, looking for any consecutive 'S's. 
    for j in range(len(rows_list)):
        row = rows_list[j]
        for i in range(len(row)):
            if row[i] == 'S': # could be 'S', 'SS', 'SSS', or 'SSSS'
                if i < len(row)-1:
                    if row[i+1] == 'S':
                        if i < len(row)-2:
                            if row[i+2] == 'S':
                                if i < len(row)-3:
                                    if row[i+3] == 'S':
                                        # found a battleship, so replace 'SSSS' with '<MM>
                                        row[i+3] = '>'
                                        row[i+2] = 'M'
                                        row[i+1] = 'M'
                                        row[i] = '<'
                                        battleships -= 1
                                    else:
                                        # found a cruiser, so replace 'SSS' with '<M>'
                                        row[i+2] = '>'
                                        row[i+1] = 'M'
                                        row[i] = '<'
                                        cruisers -= 1
                                else:
                                    # found a cruiser, so replace 'SSS' with '<M>'
                                        row[i+2] = '>'
                                        row[i+1] = 'M'
                                        row[i] = '<'
                                        cruisers -= 1
                                    
                            else:
                                # found a destroyer, so replace 'SS' with '<>'
                                    row[i+1] = '>'
                                    row[i] = '<'
                                    destroyers -= 1
                        else:
                            # found a destroyer, so replace 'SS' with '<>'
                            row[i+1] = '>'
                            row[i] = '<'
                            destroyers -= 1
                else:
                    # found a submarine or intersected with a vertical ship (so check above and below)
                    if j > 0:
                        if rows_list[j-1][i] == 'S':
                            # intersected (another S above it)
                            pass
                        elif j < len(rows_list)-1:
                            if rows_list[j+1][i] == 'S':
                                # intersected (another S below it)
                                pass
                            else:
                                submarines -=1
                        else:
                            # found a submarine
                            submarines -= 1
                    
    
    # iterate through cols list, looking for any consecutive 'S's - make modifications to the rows_list though
    for col in cols_list:
        for i in range(len(col)):
            if col[i] == 'S':
                if i < len(col)-1:
                    if col[i+1] == 'S':
                        if i < len(col)-2:
                            if col[i+2] == 'S':
                                if i < len(col)-3:
                                    if col[i+3] == 'S':
                                        # found a battleship, so replace 'SSSS' with '<MM>
                                        rows_list[i+3][i] = '^'
                                        rows_list[i+2][i] = 'M'
                                        rows_list[i+1][i] = 'M'
                                        rows_list[i][i] = 'v'
                                        battleships -= 1
                                    else:
                                        # found a cruiser, so replace 'SSS' with '<M>'
                                        rows_list[i+2][i] = '^'
                                        rows_list[i+1][i] = 'M'
                                        rows_list[i][i] = 'v'
                                        cruisers -= 1
                                else:
                                    # found a cruiser, so replace 'SSS' with '<M>'
                                    rows_list[i+2][i] = '^'
                                    rows_list[i+1][i] = 'M'
                                    rows_list[i][i] = 'v'
                                    cruisers -= 1
                            else:
                                # found a destroyer, so replace 'SS' with '<>'
                                rows_list[i+1][i] = '^'
                                rows_list[i][i] = 'v'
                                destroyers -= 1
                        else:
                            # found a destroyer, so replace 'SS' with '<>'
                            rows_list[i+1][i] = '^'
                            rows_list[i][i] = 'v'
                            destroyers -= 1

                # else:
                # otherwise, found a submarine, so pass

    print("remaaining submarines not found: ", submarines)
    print("remaaining destroyers not found: ", destroyers)
    print("remaaining cruisers not found: ", cruisers)
    print("remaaining battleships not found: ", battleships)

    if submarines == 0 and destroyers == 0 and cruisers == 0 and battleships == 0:
        return [True, rows_list] # returns a tuple: (True, the new board)
    else:
        return [False, None] # does not satisfy the ship constraints

def check_ship_constraints_bad(assignment, state):
    '''Given check if a full assignment (of a board) satisfies the original 
    state's ship constraints.'''

    # the correct number of each type of ship is present:
    submarines = state.ship_constraints[0] # 'S'
    destroyers = state.ship_constraints[1] # 1x2
    cruisers = state.ship_constraints[2] # 1x3
    battleships = state.ship_constraints[3] # 1x4

    # implement the assignment changes to the board:
    new_board = implement_assignment(assignment, state)
    # new_board = [['.', '.', '.', '^', '.', '.'], ['S', '.', '.', 'M', '.', '.'], ['.', '.', '.', 'v', '.', '.'], ['.', '.', '.', '.', '.', 'S'], ['.', '^', '.', '^', '.', '.'], ['.', 'v', '.', 'v', '.', 'S']]

    rows_list = new_board # the board is a list of rows
    cols_list = list(zip(*rows_list)) # transpose the board to have a list of columns

    # iterate through rows list, looking for 'S', '<>', '<M>', '<MM>'
    for row in rows_list:
        for i in range(len(row)):
            if row[i] == 'S':
                submarines -= 1
            if row[i] == '<' and i != len(row)-1: # if it's the last element, it can't be a ship
                if row[i+1] == '>':
                    destroyers -= 1 # found a 1x2
                elif row[i+1] == 'M' and i != len(row)-2: # if it's the second last element, it can't be a ship
                    if row[i+2] == '>':
                        cruisers -= 1 # found a 1x3
                    elif row[i+2] == 'M' and i != len(row)-3: # if it's the third last element, it can't be a ship
                        if row[i+3] == '>':
                            battleships -= 1 # found a 1x4

    # iterate through cols list, looking for '^v', '^Mv', '^MMv'
    for col in cols_list:
        for i in range(len(col)):
            if col[i] == '^' and i != len(col)-1:
                if col[i+1] == 'v':
                    destroyers -= 1 # found a 2x1
                elif col[i+1] == 'M' and i != len(col)-2:
                    if col[i+2] == 'v':
                        cruisers -= 1 # found a 3x1
                    elif col[i+2] == 'M' and i != len(col)-3:
                        if col[i+3] == 'v':
                            battleships -= 1 # found a 4x1

    if submarines == 0 and destroyers == 0 and cruisers == 0 and battleships == 0:
        return True
    else:
        return False # does not satisfy the ship constraints

def implement_assignment(assignment, state):
    '''Given an assignment and initial state, implement the changes on a copy of 
    the board and return that state.'''
    # make a board (list of lists) with the same dimensions as the original board:
    new_board = [['0' for j in range(state.dim)] for i in range(state.dim)]

    if assignment==None:
        return state.board

    for var in assignment:
        new_board[var.y][var.x] = assignment[var]
    return new_board

def findvals(remainingVars, assignment, finalTestfn, partialTestfn=lambda x: True):
    '''Helper function for finding an assignment to the variables of a constraint
    that together with var=val satisfy the constraint. That is, this
    function looks for a supporing tuple.

    findvals uses recursion to build up a complete assignment, one value
    from every variable's current domain, along with var=val.
    It tries all ways of constructing such an assignment (using recursive DFS).

    If partialTestfn is supplied, it will use this function to test
    all partial assignments---if the function returns False
    it will terminate trying to grow that assignment.

    It will test all full assignments to "allVars" using finalTestfn
    returning once it finds a full assignment that passes this test.

    returns True if it finds a suitable full assignment, False if none
    exist. (yes we are using an algorithm that is exactly like backtracking!)'''

    '''finalTestfn returns True if the assignment is a solution to the constraint.
    That's the function where we implement the constraint. partialTestfn 
    returns True if the assignment is a partial solution to the constraint. It 
    works by 
    '''

    # print "==>findvars([",
    # for v in remainingVars: print v.name(), " ",
    # print "], [",
    # for x,y in assignment: print "({}={}) ".format(x.name(),y),
    # print ""

    #sort the variables call the internal version with the variables sorted
    remainingVars.sort(reverse=True, key=lambda v: v.curDomainSize()) # sort by variables with the largest domain size (LCV)
    return findvals_(remainingVars, assignment, finalTestfn, partialTestfn)

def findvals_(remainingVars, assignment, finalTestfn, partialTestfn):
    '''findvals_ internal function with remainingVars sorted by the size of
    their current domain.

    - remainingVars is a list of variables that have not yet been assigned
    - assignment is a list of (var,val) pairs that have already been assigned
    - finalTestfn is a function that returns True if the assignment is a solution
    - partialTestfn is a function that returns True if the assignment is a partial solution
    '''
    if len(remainingVars) == 0: #if there are no more variables to assign
        return finalTestfn(assignment) # return the final test function (True if the constraint is satisfied)
    var = remainingVars.pop() # get the variable with the largest domain size
    for val in var.curDomain(): # for each value in the variable's domain
        assignment.append((var, val)) # add the variable and value to the assignment
        if partialTestfn(assignment): # if the partial test function returns true (the assignment is a partial solution to the constraint)
            if findvals_(remainingVars, assignment, finalTestfn, partialTestfn): # recursively call findvals_ to find the next variable in the assignment
                return True
        assignment.pop()   #(var,val) didn't work since we didn't do the return
    remainingVars.append(var) # put the variable back in the list of remaining variables - nothing works for this value
    return False

def write_solution(solution, outputfile): 
    '''Given the solution, write it to the output file.'''

    file = open(outputfile, "w")

    file.write(solution)
    file.close()

if __name__ == '__main__':
    # For running in terminal purposes:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputfile",
        type=str,
        required=True,
        help="The input file that contains the puzzle."
    )
    parser.add_argument(
        "--outputfile",
        type=str,
        required=True,
        help="The output file that contains the solution."
    )
    args = parser.parse_args()
    
    state = State()
    state.read_from_file(args.inputfile)
    state.display()

    # find and store any hints in the board:
    for i in range(state.dim):
        for j in range(state.dim):
            if state.board[i][j] != '0':
                val = state.board[i][j]
                state.hints.append((i, j, val))
    
    print("HINTS:", state.hints)

    # precondition the board: surround any ships with water, fill any 0 rows/cols with water
    state.precondition_state()
    print("\npreconditioned board:")
    state.display()

    state.init_variables() # initialize variables


    # print("row constraints:", state.row_constraints)
    # print("col constraints:", state.col_constraints)
    # # print("ship constraints:", state.ship_constraints)
    # print("\nnumber of submarines: ", state.ship_constraints[0])
    # print("number of destroyers (1x2): ", state.ship_constraints[1])
    # print("number of cruisers (1x3): ", state.ship_constraints[2])
    # print("number of battleships (1x4): ", state.ship_constraints[3])
    # print("dimensions: ", state.dim)

    conslist = [] # list containing all the constraints in format 

    # ***************** initialize water constraints **************************

    # starting at row 2, iterate through every other row. for each variable
    # in that row, add a water constraint for each of its 4 diagonals (4
    # binary constraints for each variable). vertical edges will only have 2 
    # binary constraints each. if we get to the bottom row, the corners will only 
    # have 1 binary constraint to check, and the rest will only have 2. 
    # of each pair of diagonal vars, at least one must 
    # be water. TODO later - implement water constraint for submarines and tails. 

    for i in range(1, state.dim, 2):
        for j in range(state.dim):
            if i == state.dim-1 and j==0: # bottom left corner - only check top right diagonal
                # below parameters: name, vars, vals, min # of those vars that can have that val, max # of those vars that can have that val
                conslist.append(water_constraints('water'+str(i)+str(j), [state.varn[str(i*state.dim+j)], state.varn[str((i-1)*state.dim+j+1)]], ['.'], 1, 2))
            elif i == state.dim-1 and j==state.dim-1: # bottom right corner - only check top left diagonal
                conslist.append(water_constraints('water'+str(i)+str(j), [state.varn[str(i*state.dim+j)], state.varn[str((i-1)*state.dim+j-1)]], ['.'], 1, 2))
            elif i == state.dim-1: # bottom edge - check top left and top right diagonals
                conslist.append(water_constraints('water'+str(i)+str(j), [state.varn[str(i*state.dim+j)], state.varn[str((i-1)*state.dim+j-1)]], ['.'], 1, 2)) # top left diagonal
                conslist.append(water_constraints('water'+str(i)+str(j), [state.varn[str(i*state.dim+j)], state.varn[str((i-1)*state.dim+j+1)]], ['.'], 1, 2)) # top right diagonal
            elif j == 0: # left edge - check top right and bottom right diagonals
                conslist.append(water_constraints('water'+str(i)+str(j), [state.varn[str(i*state.dim+j)], state.varn[str((i-1)*state.dim+j+1)]], ['.'], 1, 2)) # top right diagonal
                conslist.append(water_constraints('water'+str(i)+str(j), [state.varn[str(i*state.dim+j)], state.varn[str((i+1)*state.dim+j+1)]], ['.'], 1, 2)) # bottom right diagonal
            elif j == state.dim-1: # right edge - check top left and bottom left diagonals
                conslist.append(water_constraints('water'+str(i)+str(j), [state.varn[str(i*state.dim+j)], state.varn[str((i-1)*state.dim+j-1)]], ['.'], 1, 2)) # top left diagonal
                conslist.append(water_constraints('water'+str(i)+str(j), [state.varn[str(i*state.dim+j)], state.varn[str((i+1)*state.dim+j-1)]], ['.'], 1, 2)) # bottom left diagonal
            else: # middle - check all 4 diagonals
                conslist.append(water_constraints('water'+str(i)+str(j), [state.varn[str(i*state.dim+j)], state.varn[str((i-1)*state.dim+j+1)]], ['.'], 1, 2)) # top right diagonal
                conslist.append(water_constraints('water'+str(i)+str(j), [state.varn[str(i*state.dim+j)], state.varn[str((i+1)*state.dim+j+1)]], ['.'], 1, 2)) # bottom right diagonal
                conslist.append(water_constraints('water'+str(i)+str(j), [state.varn[str(i*state.dim+j)], state.varn[str((i-1)*state.dim+j-1)]], ['.'], 1, 2)) # top left diagonal
                conslist.append(water_constraints('water'+str(i)+str(j), [state.varn[str(i*state.dim+j)], state.varn[str((i+1)*state.dim+j-1)]], ['.'], 1, 2)) # bottom left diagonal

    # ***************** initialize row and column constraints *****************
    for i in range(state.dim):
        rowi = []
        coli = []
        for j in range(state.dim):
            rowi.append(state.varn[str(i*state.dim+j)]) # varn is the dictionary of variables
            coli.append(state.varn[str(i+j*state.dim)])
        conslist.append(row_constraints('row'+str(i),rowi,state.row_constraints[i]))
        conslist.append(col_constraints('col'+str(i),coli,state.col_constraints[i])) #TODO - i or j?

    # create the CSP:
    csp = CSP('Battleship', state.variables, conslist)

    # call gac on unassigned variables:
    unassigned = []
    pre_assigned = []
    # print("state variables: ", state.variables)
    for var in state.variables:
        if not var.isAssigned():
            unassigned.append(var)
        else:
            pass
            #var._curdom.remove(var.getValue())
            # pre_assigned.append(deepcopy(var))

    # ************************ run backtracking search ************************
    # print("\n********** Running backtracking search... **********")
    # start = time.time()
    # assignment = backtrack_search(csp, state) # format: {var1: value1, var2: value2, ...}
    # end = time.time()
    # print("\nTime taken: ", end-start)

    # print("\n checking ship constraints: ", check_ship_constraints(assignment, state))
    # print("sol board: ", sol_board)

    # ********************************* run GAC *******************************

    print("\n********** Running GAC... **********")
    start = time.time()
    # print("unassigned variaables before GAC: ", unassigned)
    assignment = csp.gac(unassigned, state)
    assignment = csp.solution
    # print(assignment)
    # assignment = {}
    # for i in state.variables:
    #     assignment[i] = i.getValue()
    # print("assignment after GAC: ", assignment)
    end = time.time()
    print("\nTime taken: ", end-start)

    # # ******************* print backtracking solution ***********************
    # print("\nSolution:")
    # sol_board = implement_assignment(assignment, state)
    # for i in range(len(sol_board)):
    #     for j in range(len(sol_board[i])):
    #         print(sol_board[i][j], end='')
    #     print()

    # ********************* write solution to output ************************

    # print("\nWriting solution to output file...")
    # print("type of csp.solution: ", type(csp.solution))
    write_solution(csp.solution, args.outputfile)