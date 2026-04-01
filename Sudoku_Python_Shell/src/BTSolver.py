import SudokuBoard
import Variable
import Domain
import Trail
import Constraint
import ConstraintNetwork
import time
import random

class BTSolver:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__ ( self, gb, trail, val_sh, var_sh, cc ):
        self.network = ConstraintNetwork.ConstraintNetwork(gb)
        self.hassolution = False
        self.gameboard = gb
        self.trail = trail

        self.varHeuristics = var_sh
        self.valHeuristics = val_sh
        self.cChecks = cc

    # ==================================================================
    # Consistency Checks
    # ==================================================================

    # Basic consistency check, no propagation done
    def assignmentsCheck ( self ):
        for c in self.network.getConstraints():
            if not c.isConsistent():
                return False
        return True

    """
        Part 1 TODO: Implement the Forward Checking Heuristic

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        Note: remember to trail.push variables before you assign them
        Return: a tuple of a dictionary and a bool. The dictionary contains all MODIFIED variables, mapped to their MODIFIED domain.
                The bool is true if assignment is consistent, false otherwise.
    """
    def forwardChecking ( self ):
        assignedVars = []
        modifiedVars = {}

        # find all assigned variables
        for c in self.network.constraints:
            for v in c.vars:
                if v.isAssigned():
                    assignedVars.append(v)

        # for each assigned var, remove assigned value from its neighbors
        for av in assignedVars:
            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.isChangeable() and not neighbor.isAssigned() and neighbor.getDomain().contains(av.getAssignment()):
                    self.trail.push(neighbor)
                    neighbor.removeValueFromDomain(av.getAssignment())
                    modifiedVars[neighbor] = neighbor.getDomain()
                    # end if var has empty domain
                    if neighbor.domain.size() == 0:
                        return (modifiedVars, False)

        return (modifiedVars, True)

    # =================================================================
	# Arc Consistency
	# =================================================================
    def arcConsistency( self ):
        assignedVars = []
        for c in self.network.constraints:
            for v in c.vars:
                if v.isAssigned():
                    assignedVars.append(v)
        while len(assignedVars) != 0:
            av = assignedVars.pop(0)
            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.isChangeable and not neighbor.isAssigned() and neighbor.getDomain().contains(av.getAssignment()):
                    neighbor.removeValueFromDomain(av.getAssignment())
                    if neighbor.domain.size() == 1:
                        neighbor.assignValue(neighbor.domain.values[0])
                        assignedVars.append(neighbor)

    
    """
        Part 2 TODO: Implement both of Norvig's Heuristics

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        (2) If a constraint has only one possible place for a value
            then put the value there.

        Note: remember to trail.push variables before you assign them
        Return: a pair of a dictionary and a bool. The dictionary contains all variables 
		        that were ASSIGNED during the whole NorvigCheck propagation, and mapped to the values that they were assigned.
                The bool is true if assignment is consistent, false otherwise.
    """
    def norvigCheck ( self ):
        assigned = {}
        changed = True

        while changed:
            changed = False

            (modified, consistent) = self.forwardChecking()

            if not consistent:
                return (assigned, False)

            for c in self.network.constraints:
                for d in range(1, 10):
                    candidate = []

                    for v in c.vars:
                        if v.getDomain().contains(d):
                            candidate.append(v)

                    if len(candidate) == 1:
                        v = candidate[0]

                        if not v.isAssigned():
                            self.trail.push(v)
                            v.assignValue(d)

                            assigned[v] = d
                            changed = True

        return (assigned, True)

    """
         Optional TODO: Implement your own advanced Constraint Propagation

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournCC ( self ):

        # A3 Algorithm (Google Search)
        (modified, consistent) = self.forwardChecking()
        if not consistent:
            return False

        (modified, consistent) = self.norvigCheck()
        if not consistent:
            return False

        self.arcConsistency()

        # Naked Twin Constraint (Google Search)
        for c in self.network.constraints:
            twins = []

            for v in c.vars:
                if v.getDomain().size() == 2 and not v.isAssigned():
                    twins.append(v)

            for i in range(len(twins)):
                for j in range(i+1, len(twins)):

                    v1 = twins[i]
                    v2 = twins[j]

                    if v1.getDomain().values == v2.getDomain().values:
                        value = v1.getDomain().values

                        # eliminate other variables
                        for v in c.vars:
                            if v != v1 and v != v2 and not v.isAssigned():
                                for val in value:
                                    if v.getDomain().contains(val):
                                        self.trail.push(v)
                                        v.removeValueFromDomain(val)

        return True

    # ==================================================================
    # Variable Selectors
    # ==================================================================

    # Basic variable selector, returns first unassigned variable
    def getfirstUnassignedVariable ( self ):
        for v in self.network.variables:
            if not v.isAssigned():
                return v

        # Everything is assigned
        return None

    """
        Part 1 TODO: Implement the Minimum Remaining Value Heuristic

        Return: The unassigned variable with the smallest domain
    """
    def getMRV ( self ):
        best_value = None
        min_remaining = float('inf')

        # iterate through all variables in the network and compare
        for var in self.network.variables:
            if not var.isAssigned():
                num_value = var.getDomain().size()
                if num_value < min_remaining:
                    min_remaining = num_value
                    best_value = var

        return best_value

    """
        Part 2 TODO: Implement the Minimum Remaining Value Heuristic
                       with Degree Heuristic as a Tie Breaker

        Return: The unassigned variable with the smallest domain and affecting the  most unassigned neighbors.
                If there are multiple variables that have the same smallest domain with the same number of unassigned neighbors, add them to the list of Variables.
                If there is only one variable, return the list of size 1 containing that variable.
    """
    def MRVwithTieBreaker ( self ):
        unassigned_vars = []

        # get list of unassigned vars
        for v in self.network.variables:
            if not v.isAssigned():
                unassigned_vars.append(v)

        if len(unassigned_vars) == 0:
            return [None]

        min_domain = min(v.domain.size() for v in unassigned_vars)

        # find all vars with min domain
        mrv_vars = []
        for v in unassigned_vars:
            if v.domain.size() == min_domain:
                mrv_vars.append(v)

        if len(mrv_vars) == 1:
            return mrv_vars

        # find number of constraints each var has on other variables
        var_degrees = []
        for v in mrv_vars:
            unassigned_neighbors = 0
            for neighbor in self.network.getNeighborsOfVariable(v):
                if not neighbor.isAssigned():
                    unassigned_neighbors += 1
            var_degrees.append((v, unassigned_neighbors))

        max_degree = max(degree for v, degree in var_degrees)

        # find all vars that match max number of constraints
        result = []
        for v, degree in var_degrees:
            if degree == max_degree:
                result.append(v)

        return result


    """
         Optional TODO: Implement your own advanced Variable Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVar ( self ):
        unassigned_vars = []

        for v in self.network.variables:
            if not v.isAssigned():
                unassigned_vars.append(v)

        if len(unassigned_vars) == 0:
            return None

        best_var = None
        best_score = float('-inf')

        for v in unassigned_vars:
            domain_score = 1.0 / v.domain.size() if v.domain.size() > 0 else 0
            degree = 0
            neighbor_constraint_sum = 0

            for neighbor in self.network.getNeighborsOfVariable(v):
                if not neighbor.isAssigned():
                    degree += 1
                    neighbor_constraint_sum += 1.0 / neighbor.domain.size() if neighbor.domain.size() > 0 else 0

            score = (3.0 * domain_score) + (1.5 * degree) + (1.0 * neighbor_constraint_sum)

            if score > best_score:
                best_score = score
                best_var = v

        return best_var
        

    # ==================================================================
    # Value Selectors
    # ==================================================================

    # Default Value Ordering
    def getValuesInOrder ( self, v ):
        values = v.domain.values
        return sorted( values )

    """
        Part 1 TODO: Implement the Least Constraining Value Heuristic

        The Least constraining value is the one that will knock the least
        values out of it's neighbors domain.

        Return: A list of v's domain sorted by the LCV heuristic
                The LCV is first and the MCV is last
    """
    def getValuesLCVOrder ( self, v ):
        value_constraints = []

        # for each value in domain, count how many neighbors would be constrained
        for value in v.domain.values:
            count = 0

            for neighbor in self.network.getNeighborsOfVariable(v):
                if neighbor.isChangeable() and not neighbor.isAssigned():
                    if neighbor.getDomain().contains(value):
                        count += 1

            value_constraints.append((value, count))

        # sort by count
        value_constraints.sort(key=lambda x: x[1])
        result = []
        for value, count in value_constraints:
            result.append(value)
        return result

    """
         Optional TODO: Implement your own advanced Value Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVal ( self, v ):
        if not v.domain.values:
            return []

        value_scores = []

        for value in v.domain.values:
            impact_score = 0

            for neighbor in self.network.getNeighborsOfVariable(v):
                if neighbor.isChangeable() and not neighbor.isAssigned():
                    if neighbor.getDomain().contains(value):
                        base_impact = 1

                        neighbor_size = neighbor.domain.size()
                        if neighbor_size == 2:
                            criticality_weight = 10
                        elif neighbor_size == 3:
                            criticality_weight = 5
                        elif neighbor_size <= 5:
                            criticality_weight = 2
                        else:
                            criticality_weight = 1

                        impact_score += base_impact * criticality_weight

            value_scores.append((value, impact_score))

        value_scores.sort(key=lambda x: x[1])
        result = []
        for value, impact_score in value_scores:
            result.append(value)
        return result

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve ( self, time_left=600):
        if time_left <= 60:
            return -1

        start_time = time.time()
        if self.hassolution:
            return 0

        # Variable Selection
        v = self.selectNextVariable()

        # check if the assigment is complete
        if ( v == None ):
            # Success
            self.hassolution = True
            return 0

        # Attempt to assign a value
        for i in self.getNextValues( v ):

            # Store place in trail and push variable's state on trail
            self.trail.placeTrailMarker()
            self.trail.push( v )

            # Assign the value
            v.assignValue( i )

            # Propagate constraints, check consistency, recur
            if self.checkConsistency():
                elapsed_time = time.time() - start_time 
                new_start_time = time_left - elapsed_time
                if self.solve(time_left=new_start_time) == -1:
                    return -1
                
            # If this assignment succeeded, return
            if self.hassolution:
                return 0

            # Otherwise backtrack
            self.trail.undo()
        
        return 0

    def checkConsistency ( self ):
        if self.cChecks == "forwardChecking":
            return self.forwardChecking()[1]

        if self.cChecks == "norvigCheck":
            return self.norvigCheck()[1]

        if self.cChecks == "tournCC":
            return self.getTournCC()

        else:
            return self.assignmentsCheck()

    def selectNextVariable ( self ):
        if self.varHeuristics == "MinimumRemainingValue":
            return self.getMRV()

        if self.varHeuristics == "MRVwithTieBreaker":
            return self.MRVwithTieBreaker()[0]

        if self.varHeuristics == "tournVar":
            return self.getTournVar()

        else:
            return self.getfirstUnassignedVariable()

    def getNextValues ( self, v ):
        if self.valHeuristics == "LeastConstrainingValue":
            return self.getValuesLCVOrder( v )

        if self.valHeuristics == "tournVal":
            return self.getTournVal( v )

        else:
            return self.getValuesInOrder( v )

    def getSolution ( self ):
        return self.network.toSudokuBoard(self.gameboard.p, self.gameboard.q)
