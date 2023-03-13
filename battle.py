import sys
import argparse
import heapq # use for MRV/LCV heuristics 

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
    
    def init_variables(self):
        '''Initialize the variables of the problem; each cell on the board is 
        a variable.'''

        # for every (i,j) cell on the board, create a variable:
        for i in range(self.dim): # for each row
            for j in range(self.dim): # for each col
                v = None
                if state.board[i][j] != '0': # if has been assigned
                    # create a new variable:
                    # v = Variable("v_{}_{}".format(i,j), [0,1])
                    v = Variable(str((i*self.dim+j)), [self.board[i][j]])
                else:
                    # create a new variable:
                    if i == 0 and j == 0: # top left corner
                        v = Variable(str((i*self.dim+j)), ['S','.','<','^']) # can't have 'v' or '>' or 'M' piece
                    elif i == self.dim-1 and j == self.dim-1: # bottom right corner
                        v = Variable(str((i*self.dim+j)), ['S','.','>','v']) # can't have '^' or '<' piece
                    elif i == 0 and j == self.dim-1: # top right corner
                        v = Variable(str((i*self.dim+j)), ['S','.','>','^']) # can't have 'v' or '<' piece
                    elif i == self.dim-1 and j == 0: # bottom left corner
                        v = Variable(str((i*self.dim+j)), ['S','.','<','v']) # can't have '^' or '>' piece
                    elif i == 0: # top edge
                        v = Variable(str((i*self.dim+j)), ['S','.','<','>','^','M']) # can't have 'v' piece
                    elif i == self.dim-1: # bottom edge
                        v = Variable(str((i*self.dim+j)), ['S','.','<','>','v','M']) # can't have '^' piece
                    elif j == self.dim-1: # right edge
                        v = Variable(str((i*self.dim+j)), ['S','.','>','^','v','M']) # can't have '<' piece
                    elif j == 0: # left edge
                        v = Variable(str((i*self.dim+j)), ['S','.','<','^','v','M']) # can't have '>' piece
                    else:
                        v = Variable(str((i*self.dim+j)), ['S','.','<','>','^','v','M']) # variable with full domain 
                self.variables.append(v)
                self.varn[str((i*self.dim+j))] = v
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

    undoDict = dict()             #stores pruned values indexed by a
                                        #(variable,value) reason pair
    def __init__(self, name, domain):
        '''Create a variable object, specifying its name (a
        string) and domain of values.
        '''
        self._name = name                #text name for variable
        self._dom = list(domain)         #Make a copy of passed domain
        self._curdom = list(domain)      #using list
        self._value = None

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

class NValuesConstraint(Constraint): #TODO modify starter code 
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
            rv_count = 0
            vals = [val for (var, val) in l]
            for v in vals:
                if v in self._required:
                    rv_count += 1
            least = rv_count + self.arity() - len(vals)
            most =  rv_count
            return self._lb <= least and self._ub >= most
        varsToAssign = self.scope()
        varsToAssign.remove(var)
        x = findvals(varsToAssign, [(var, val)], valsOK, valsOK)
        return x

class row_col_constraints(Constraint):
    '''Ensures that the number of ship parts in a row or column correspond to 
    the given numbers of how many ships parts should be in that row or column 
    (self.row_constraints and self.col_constraints).'''
    def __init__(self, name, scope, row_constraints, col_constraints):
        Constraint.__init__(self, name, scope)
        self._name = "row_col_constraints" + name
        self.row_constraints = row_constraints
        self.col_constraints = col_constraints

    def check(self, k):
        '''Loop through every variable in the scope (variables in row or column 
        k and checks if it breaks the constraint.'''

        assignments = [] # list of values for the row or col
        ship_parts = 0 # initialize number of ship parts in the row or col
        num =  # number of ship parts in the row or col

        for v in self.scope()[k]: # loop through variables in row or col k
            if v.isAssigned():
                assignments.append(v.getValue())
                # increment ship_parts if the value is a ship part:
                if v.getValue() == 'S' or v.getValue() == 'M' or v.getValue() == '<'\
                    or v.getValue() == '>' or v.getValue() == '^' or v.getValue() == 'v':
                    ship_parts += 1
            else:
                # if ship_parts <= row or col constraint TODO??????????
                return True # if not all variables are assigned, return True
        pass
        # for ass in assignments:
        # # return 

        def hasSupport(self, var, val):
            '''Checks if the variables other than the one assigned (val) are 
            a valid combination overall with this one constraint.'''
            if var not in self.scope():
                return True # var=val has support on any constraint it does not participate in
            
            pass

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
    
    def __str__(self):
        return "CSP {}".format(self.name())

def select_unassigned_variable(csp):
    '''TODO. '''
    # return csp.variables()[0]
    # return min(csp.variables(), key=lambda var: len(var.curDomain()))
    pass

def order_domain_values(var, assignment, csp):
    '''TODO. Try all possible values for unassigned variable'''
    # return var.curDomain()
    pass

def is_consistent(var, value, assignment, csp):
    '''TODO. Check if value is consistent with the assignment and constraints?'''
    # return True
    pass

# Backtracking search:
def backtrack_search(csp):
    return backtrack_search({}, csp)

def backtrack(assignment, csp):
    # if assignment is complete, return assignment TODO - check what "complete" is and later implement forward checking 
    if len(assignment) == len(csp.variables()):
        return assignment
    var = select_unassigned_variable(csp)
    for value in order_domain_values(var, assignment, csp):
        if is_consistent(var, value, assignment, csp):
            assignment[var] = value
            # inferences = inference(var, value, assignment, csp) #TODO random suggested code
            # if inferences != False:
            #     assignment.update(inferences)
            #     result = backtrack(assignment, csp)
            #     if result != False:
            #         return result
            # assignment.pop(var)
            result = backtrack(assignment, csp) # look at remaining unassigned variables (recursive call
            if result != False: # if result is not a failure
                return result
        assignment.pop(var) # remove var from assignment
    return False # failure; no solution


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
    their current domain'''
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


if __name__ == '__main__':

    # read a test file
    filename = 'input.txt'
    
    state = State()
    state.read_from_file(filename)
    state.display()
    state.init_variables() # initialize variables

    print("row constraints:", state.row_constraints)
    print("col constraints:", state.col_constraints)
    print("ship constraints:", state.ship_constraints)
    print("dimensions: ", state.dim)

