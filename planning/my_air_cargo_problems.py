from aimacode.logic import PropKB
from aimacode.planning import Action
from aimacode.search import (
     Node, Problem,
 )
from aimacode.utils import expr
from lp_utils import (
    FluentState, encode_state, decode_state,
)
from my_planning_graph import PlanningGraph

class AirCargoProblem(Problem):
    def __init__(self, cargos, planes, airports, initial: FluentState, goal: list):
        """

        :param cargos: list of str
            cargos in the problem
        :param planes: list of str
            planes in the problem
        :param airports: list of str
            airports in the problem
        :param initial: FluentState object
            positive and negative literal fluents (as expr) describing initial state
        :param goal: list of expr
            literal fluents required for goal test
        """
        self.state_map = initial.pos + initial.neg
        self.initial_state_TF = encode_state(initial, self.state_map)
        Problem.__init__(self, self.initial_state_TF, goal=goal)
        self.cargos = cargos
        self.planes = planes
        self.airports = airports
        self.actions_list = self.get_actions()

    def get_actions(self):
        '''
        This method creates concrete actions (no variables) for all actions in the problem
        domain action schema and turns them into complete Action objects as defined in the
        aimacode.planning module. It is computationally expensive to call this method directly;
        however, it is called in the constructor and the results cached in the `actions_list` property.

        Returns:
        ----------
        list<Action>
            list of Action objects
        '''

        # Here, we create concrete Action objects based on the domain action schema for: Load, Unload, and Fly
        # concrete actions definition: specific literal action that does not include variables as with the schema
        # for example, the action schema 'Load(c, p, a)' can represent the concrete actions 'Load(C1, P1, SFO)'
        # or 'Load(C2, P2, JFK)'.  The actions for the planning problem must be concrete because the problems in
        # forward search and Planning Graphs must use Propositional Logic

        def load_actions():
            '''Create all concrete Load actions and return a list

            :return: list of Action objects
            '''
            loads = []
            for a in self.airports:
                for p in self.planes:
                    for c in self.cargos:
                        precond_pos = [expr("At({}, {})".format(p, a)),
                                       expr("At({}, {})".format(c, a)),
                                       ]
                        precond_neg = []
                        effect_add = [expr("In({}, {})".format(c, p))]
                        effect_rem = [expr("At({}, {})".format(c, a))]
                        load = Action(expr("Load({}, {}, {})".format(c, p, a)),
                                     [precond_pos, precond_neg],
                                     [effect_add, effect_rem])
                        loads.append(load)
            return loads

        def unload_actions():
            '''Create all concrete Unload actions and return a list

            :return: list of Action objects
            '''
            unloads = []
            for a in self.airports:
                for p in self.planes:
                    for c in self.cargos:
                        precond_pos = [expr("At({}, {})".format(p, a)),
                                       expr("In({}, {})".format(c, p)),
                                       ]
                        precond_neg = []
                        effect_add = [expr("At({}, {})".format(c, a))]
                        effect_rem = [expr("In({}, {})".format(c, p))]
                        unload = Action(expr("Unload({}, {}, {})".format(c, p, a)),
                                     [precond_pos, precond_neg],
                                     [effect_add, effect_rem])
                        unloads.append(unload)
            return unloads

        def fly_actions():
            '''Create all concrete Fly actions and return a list

            :return: list of Action objects
            '''
            flys = []
            for fr in self.airports:
                for to in self.airports:
                    if fr != to:
                        for p in self.planes:
                            precond_pos = [expr("At({}, {})".format(p, fr)),
                                           ]
                            precond_neg = []
                            effect_add = [expr("At({}, {})".format(p, to))]
                            effect_rem = [expr("At({}, {})".format(p, fr))]
                            fly = Action(expr("Fly({}, {}, {})".format(p, fr, to)),
                                         [precond_pos, precond_neg],
                                         [effect_add, effect_rem])
                            flys.append(fly)
            return flys

        return load_actions() + unload_actions() + fly_actions()

    def actions(self, state: str) -> list:
        """ Return the actions that can be executed in the given state.

        :param state: str
            state represented as T/F string of mapped fluents (state variables)
            e.g. 'FTTTFF'
        :return: list of Action objects
        """

        # Lifted from example_have_cake.py
        possible_actions = []

        # Get a handle to our knowledge base of logical expressions (propositional logic)
        kb = PropKB()

        # Add the current state's positive sentence's clauses to the propositional logic KB
        kb.tell(decode_state(state, self.state_map).pos_sentence())

        # From all the concrete actions we can perform, select the ones that can be executed
        # from the current state. An action is executable if it satisfies a problem's preconditions.
        # That is, it must appear in a problem's positive preconditions and not be in a problem's negative ones.
        for action in self.actions_list:
            is_possible = True
            for clause in action.precond_pos:
                if clause not in kb.clauses:
                    is_possible = False
                    break
            for clause in action.precond_neg:
                if clause in kb.clauses:
                    is_possible = False
                    break
            if is_possible:
                possible_actions.append(action)
        return possible_actions

    def result(self, state: str, action: Action):
        """ Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state).

        :param state: state entering node
        :param action: Action applied
        :return: resulting state after action
        """

        # Lifted from example_have_cake.py
        new_state = FluentState([], [])

        # Get the current state
        old_state = decode_state(state, self.state_map)

        # Per the teaching materials, the precondition and effect of an action are each conjunctions of literals
        # (positive or negated atomic sentences). The precondition defines the states in which the action can be
        # executed, and the effect defines the result of executing the action. So, for each fluent (positive or
        # negative) in the old state, we need to look in the action's effects (both the add and remove effects) to
        # determine how the fluent will be carried over to the new state, as a positive or a negative fluent.
        for fluent in old_state.pos:
            if fluent not in action.effect_rem:
                new_state.pos.append(fluent)
        for fluent in old_state.neg:
            if fluent not in action.effect_add:
                new_state.neg.append(fluent)

        # The action may have positive and negative effects INDEPENDENTLY of the old state. If they're add effects,
        # we need to make sure these fluents are added to the new state's positive sentences. Similarly, if they're
        # remove effects, these fluents need to be added to the new state's negative sentences.
        for fluent in action.effect_add:
            if fluent not in new_state.pos:
                new_state.pos.append(fluent)
        for fluent in action.effect_rem:
            if fluent not in new_state.neg:
                new_state.neg.append(fluent)

        # Return the new state
        return encode_state(new_state, self.state_map)

    def goal_test(self, state: str) -> bool:
        """ Test the state to see if goal is reached

        :param state: str representing state
        :return: bool
        """
        kb = PropKB()
        kb.tell(decode_state(state, self.state_map).pos_sentence())
        for clause in self.goal:
            if clause not in kb.clauses:
                return False
        return True

    def h_1(self, node: Node):
        # note that this is not a true heuristic
        h_const = 1
        return h_const

    def h_pg_levelsum(self, node: Node):
        '''
        This heuristic uses a planning graph representation of the problem
        state space to estimate the sum of all actions that must be carried
        out from the current state in order to satisfy each individual goal
        condition.
        '''
        # requires implemented PlanningGraph class
        pg = PlanningGraph(self, node.state)
        pg_levelsum = pg.h_levelsum()
        return pg_levelsum

    def h_ignore_preconditions(self, node: Node):
        '''
        This heuristic estimates the minimum number of actions that must be
        carried out from the current state in order to satisfy all of the goal
        conditions by ignoring the preconditions required for an action to be
        executed.
        '''

        # Per https://discussions.udacity.com/t/understanding-ignore-precondition-heuristic/225906/2 :
        # The Node object describes the current state. Since we're ignoring preconditions,
        # we need to look at each goal condition in the goal state and count the number of
        # individual actions that will make them happen. Of course, if a goal condition
        # is already satisfied by the current state, then no additional action for this
        # condition needs to be perfomed.

        # Get a handle to our knowledge base of logical expressions (propositional logic)
        kb = PropKB()

        # Add the current state's positive sentence's clauses to the propositional logic KB
        kb.tell(decode_state(node.state, self.state_map).pos_sentence())

        # Use a slightly modified version of the goal_test() fn
        count = 0
        for clause in self.goal:
            if clause not in kb.clauses:
                count += 1
        return count

def air_cargo_p1() -> AirCargoProblem:
    '''
    Problem 1 initial state and goal:
    Init(At(C1, SFO) ∧ At(C2, JFK)
        ∧ At(P1, SFO) ∧ At(P2, JFK)
        ∧ Cargo(C1) ∧ Cargo(C2)
        ∧ Plane(P1) ∧ Plane(P2)
        ∧ Airport(JFK) ∧ Airport(SFO))
    Goal(At(C1, JFK) ∧ At(C2, SFO))
    '''
    cargos = ['C1', 'C2']
    planes = ['P1', 'P2']
    airports = ['JFK', 'SFO']
    pos = [expr('At(C1, SFO)'),
           expr('At(C2, JFK)'),
           expr('At(P1, SFO)'),
           expr('At(P2, JFK)'),
           ]
    neg = [expr('At(C2, SFO)'),
           expr('In(C2, P1)'),
           expr('In(C2, P2)'),
           expr('At(C1, JFK)'),
           expr('In(C1, P1)'),
           expr('In(C1, P2)'),
           expr('At(P1, JFK)'),
           expr('At(P2, SFO)'),
           ]
    init = FluentState(pos, neg)
    goal = [expr('At(C1, JFK)'),
            expr('At(C2, SFO)'),
            ]
    return AirCargoProblem(cargos, planes, airports, init, goal)


def air_cargo_p2() -> AirCargoProblem:
    '''
    Problem 2 initial state and goal:
    Init(At(C1, SFO) ∧ At(C2, JFK) ∧ At(C3, ATL)
        ∧ At(P1, SFO) ∧ At(P2, JFK) ∧ At(P3, ATL)
        ∧ Cargo(C1) ∧ Cargo(C2) ∧ Cargo(C3)
        ∧ Plane(P1) ∧ Plane(P2) ∧ Plane(P3)
        ∧ Airport(JFK) ∧ Airport(SFO) ∧ Airport(ATL))
    Goal(At(C1, JFK) ∧ At(C2, SFO) ∧ At(C3, SFO))
    '''
    cargos = ['C1', 'C2', 'C3']
    planes = ['P1', 'P2', 'P3']
    airports = ['ATL', 'JFK', 'SFO']
    # List where the cargo and planes are
    pos = [expr('At(C1, SFO)'),
           expr('At(C2, JFK)'),
           expr('At(C3, ATL)'),
           expr('At(P1, SFO)'),
           expr('At(P2, JFK)'),
           expr('At(P3, ATL)'),
           ]
    # List where the cargo and planes aren't
    # Indicate that the cargo hasn't been loaded in any of the planes yet
    neg = [expr('At(C1, ATL)'),
           expr('At(C1, JFK)'),
           expr('At(C2, ATL)'),
           expr('At(C2, SFO)'),
           expr('At(C3, JFK)'),
           expr('At(C3, SFO)'),
           expr('At(P1, ATL)'),
           expr('At(P1, JFK)'),
           expr('At(P2, ATL)'),
           expr('At(P2, SFO)'),
           expr('At(P3, JFK)'),
           expr('At(P3, SFO)'),
           expr('In(C1, P1)'),
           expr('In(C1, P2)'),
           expr('In(C1, P3)'),
           expr('In(C2, P1)'),
           expr('In(C2, P2)'),
           expr('In(C2, P3)'),
           expr('In(C3, P1)'),
           expr('In(C3, P2)'),
           expr('In(C3, P3)'),
           ]
    init = FluentState(pos, neg)
    # List goals: C1 -> JFK and C2,C3 -> SFO
    goal = [expr('At(C1, JFK)'),
            expr('At(C2, SFO)'),
            expr('At(C3, SFO)'),
            ]
    return AirCargoProblem(cargos, planes, airports, init, goal)


def air_cargo_p3() -> AirCargoProblem:
    '''
    Init(At(C1, SFO) ∧ At(C2, JFK) ∧ At(C3, ATL) ∧ At(C4, ORD)
        ∧ At(P1, SFO) ∧ At(P2, JFK)
        ∧ Cargo(C1) ∧ Cargo(C2) ∧ Cargo(C3) ∧ Cargo(C4)
        ∧ Plane(P1) ∧ Plane(P2)
        ∧ Airport(JFK) ∧ Airport(SFO) ∧ Airport(ATL) ∧ Airport(ORD))
    Goal(At(C1, JFK) ∧ At(C3, JFK) ∧ At(C2, SFO) ∧ At(C4, SFO))
    '''
    cargos = ['C1', 'C2', 'C3', 'C4']
    planes = ['P1', 'P2']
    airports = ['ATL', 'JFK', 'ORD', 'SFO']
    # List where the cargo and planes are
    pos = [expr('At(C1, SFO)'),
           expr('At(C2, JFK)'),
           expr('At(C3, ATL)'),
           expr('At(C4, ORD)'),
           expr('At(P1, SFO)'),
           expr('At(P2, JFK)'),
           ]
    # List where the cargo and planes aren't
    # Indicate that the cargo hasn't been loaded in any of the planes yet
    neg = [expr('At(C1, ATL)'),
           expr('At(C1, JFK)'),
           expr('At(C1, ORD)'),
           expr('At(C2, ATL)'),
           expr('At(C2, ORD)'),
           expr('At(C2, SFO)'),
           expr('At(C3, JFK)'),
           expr('At(C3, ORD)'),
           expr('At(C3, SFO)'),
           expr('At(C4, ATL)'),
           expr('At(C4, JFK)'),
           expr('At(C4, SFO)'),
           expr('At(P1, ATL)'),
           expr('At(P1, JFK)'),
           expr('At(P1, ORD)'),
           expr('At(P2, ATL)'),
           expr('At(P2, ORD)'),
           expr('At(P2, SFO)'),
           expr('In(C1, P1)'),
           expr('In(C1, P2)'),
           expr('In(C2, P1)'),
           expr('In(C2, P2)'),
           expr('In(C3, P1)'),
           expr('In(C3, P2)'),
           expr('In(C4, P1)'),
           expr('In(C4, P2)'),
           ]
    init = FluentState(pos, neg)
    # List goals: C1,C3 -> JFK and C2,C4 -> SFO
    goal = [expr('At(C1, JFK)'),
            expr('At(C2, SFO)'),
            expr('At(C3, JFK)'),
            expr('At(C4, SFO)'),
            ]
    return AirCargoProblem(cargos, planes, airports, init, goal)

if __name__ == '__main__':
    problems = [air_cargo_p1(), air_cargo_p2(), air_cargo_p3()]
    for p in problems:
        # Lifted from example_have_cake.py
        print("**** PROBLEM SETUP ****")
        print("Initial state for this problem is {}".format(p.initial))
        print("Actions for this domain are:")
        for a in p.actions_list:
            print('   {}{}'.format(a.name, a.args))
        print("Fluents in this problem are:")
        for f in p.state_map:
            print('   {}'.format(f))
        print("Goal requirement for this problem are:")
        for g in p.goal:
            print('   {}'.format(g))
        print()
