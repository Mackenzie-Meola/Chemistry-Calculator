from bakery import assert_equal
from dataclasses import dataclass
from drafter import *
from chempy import Reaction, Substance


set_website_title("Chemistry Calculator")
set_site_information(
    author="Mackenzie Meola",
    description="Calculate limiting reagents, theoretical yield, and percent yield with ease.",
    sources="Thanks to the Drafter docs and my study group.",
    planning=["plan.pdf", "design.pdf"],
    links=["https://github.com/Mackenzie-Meola/Chemistry-Calculator"]
)
hide_debug_information()
set_website_framed(False) 

@dataclass
class Reactant:
    """Represents a single chemical reactant with its properties."""
    formula: str
    coefficient: int
    starting_mass: float
    molar_mass: float
    moles: float
    
    
@dataclass
class Product:
    """Represents a single chemical product with its properties."""
    formula: str
    coefficient: int
    molar_mass: float
    moles: float
    theoretical_yield: float



@dataclass
class State:
    """Main state holding all chemical calculation data for the web application."""
    chemical_equation: str
    reactants: list[Reactant]
    products: list[Product]
    limiting_reagent: str
    theoretical_yield: float
    actual_yield: float
    percent_yield: float
    unit: str
    has_actual_yield: bool
    error_message: str


def parse_reaction(state: State, equation: str) -> bool:
    '''Parses and validates a balanced chemical equation with 2 reactants and 1 product.
    Updates the state with Reactant and Product objects if valid.'''
    #try/except is used to safely catch parsing errors
    #from chempy when a user enters malformed text or invalid element symbols.
    try:
    # ChemPy converts the user's equation into reactant and product
    # dictionaries, including each substance's stoichiometric coefficient.        
        reaction = Reaction.from_string(equation, globals_=False)
        if len(reaction.reac) != 2 or len(reaction.prod) != 1:
            state.error_message = "Please enter an equation with 2 reactants and 1 product."
            return False
        substances = {}
        for formula in reaction.reac:
    # ChemPy parses each molecular formula and provides its molar mass.
            substances[formula] = Substance.from_formula(formula)
        for formula in reaction.prod:
            substances[formula] = Substance.from_formula(formula)

    # composition_violation returns a list of atom imbalances; any() checks if any
    # element count differs between reactants and products.
        violations = reaction.composition_violation(substances)
        if any(value != 0 for value in violations):
            state.error_message = "Please enter a balanced chemical equation."
            return False
        state.chemical_equation = equation
        state.reactants = []
        state.products = []
        
        for formula in reaction.reac:
            coefficient = reaction.reac[formula]
            substance = substances[formula]
            molar_mass = substance.mass
            new_reactant = Reactant(formula, coefficient, 0.0, molar_mass, 0.0)
            state.reactants.append(new_reactant)

        for formula in reaction.prod:
            coefficient = reaction.prod[formula]
            substance = substances[formula]
            molar_mass = substance.mass
            new_product = Product(
                formula, coefficient, molar_mass, 0.0, 0.0)
            state.products.append(new_product)

        return True

    except Exception:
        state.error_message = "Unable to read the chemical equation."
        return False

def get_initial_state() -> State:
    """Returns the starting empty state for the website."""
    return State(
        chemical_equation="",
        reactants=[],
        products=[],
        limiting_reagent="",
        theoretical_yield=0.0,
        actual_yield=0.0,
        percent_yield=0.0,
        unit="grams",
        has_actual_yield=False,
        error_message="")

def determine_limiting(reactants: list[Reactant]) -> int:
    """Determines the index of the limiting reactant based on the smallest
    mole-to-coefficient ratio. Returns -1 if the list is empty."""
    if len(reactants) == 0:
        return -1

    limiting_index = 0
    smallest_ratio = (
        reactants[0].moles / reactants[0].coefficient)

    for i in range(1, len(reactants)):
        ratio = (reactants[i].moles / reactants[i].coefficient)
        if ratio < smallest_ratio:
            smallest_ratio = ratio
            limiting_index = i

    return limiting_index


@route
def index(state: State) -> Page:
    """Renders the home page of the Chemistry Calculator."""
    return Page(state, [
        Header("Welcome to the Chemistry Calculator!"),
        Text("Calculate limiting reagents, theoretical yield, and percent yield with ease."),
        Button("Start Calculating", "input_reactants"),
        Button("About", "about_page")])

@route
def about_page(state: State) -> Page:
    """Renders the informational page explaining how the calculator works."""
    return Page(state, [
        Header("About the Chemistry Calculator"),
        Text("This website helps students understand chemical reactions by "
             "calculating limiting reagents, theoretical yield, and percent yield."),
        Button("Home", "index")])

@route
def input_reactants(state: State) -> Page:
    """Renders the page where users input a balanced chemical equation."""
    return Page(state, [
        Header("Enter Equation"),
        Text("Enter the balanced chemical equation."),
        TextArea("reaction"),
        Button("Continue", "input_masses")])


@route
def input_masses(state: State, reaction: str) -> Page:
    """Validates the equation and prompts the user for reactant masses and actual yield."""
    if not parse_reaction(state, reaction):
        return Page(state, [
            Header("Invalid Chemical Equation"),
            Text(state.error_message),
            Button("Try Again", "input_reactants")])

    components = [
        Header("Enter Reactant Masses"),
        Text("Enter the starting mass for each reactant."),
        TextBox("mass1"),
        TextBox("mass2"),
        Text("Enter the actual yield (grams)."),
        TextBox("actual_yield"),
        Button("Calculate", "calculate_results")]

    return Page(state, components)


@route
def calculate_results(state: State, mass1: float, mass2: float, actual_yield: float) -> Page:
    """Validates masses, computes limiting reagent and yields, and displays results."""
    if mass1 <= 0 or mass2 <= 0:
        return Page(state, [
            Header("Invalid Mass"),
            Text("Both reactant masses must be greater than zero."),
            Button("Try Again", "input_reactants")])

    if actual_yield < 0:
        return Page(state, [
                Header("Invalid Actual Yield"),
                Text("Actual yield cannot be negative."),
                Button("Try Again", "input_reactants")])
        
    state.actual_yield = float(actual_yield)
    state.has_actual_yield = True
    state.reactants[0].starting_mass = float(mass1)
    state.reactants[1].starting_mass = float(mass2)
    for reactant in state.reactants:
        reactant.moles = reactant.starting_mass / reactant.molar_mass
        
    limiting_index = determine_limiting(state.reactants)
    if limiting_index == -1:
        return Page(state, [
        Header("Calculation Error"),
        Text("No reactants were provided."),
        Button("Try Again", "input_reactants")])
    
    state.limiting_reagent = state.reactants[limiting_index].formula

    limiting_reactant = state.reactants[limiting_index]

    state.products[0].moles = (
        limiting_reactant.moles
        * state.products[0].coefficient
        / limiting_reactant.coefficient)

    state.theoretical_yield = (state.products[0].moles * state.products[0].molar_mass)

    if state.has_actual_yield and state.theoretical_yield != 0:
        state.percent_yield = (state.actual_yield / state.theoretical_yield) * 100

    return Page(state, [
        Header("Calculation Results"),
        Text("Limiting Reagent: " + state.limiting_reagent),
        Text("Theoretical Yield: " + str(state.theoretical_yield)),
        Text("Actual Yield: " + str(state.actual_yield)),
        Text("Percent Yield: " + str(state.percent_yield)),
        Button("Summary", "summary_page")])
    

@route
def summary_page(state: State) -> Page:
    """Displays a complete summary of the reaction and calculated yields."""
    components = [
        Header("Calculation Results"),
        Text("Chemical Equation: " + state.chemical_equation),
        Text("Limiting Reagent: " + state.limiting_reagent),
        Text("Theoretical Yield: " + str(state.theoretical_yield)),
        Text("Actual Yield: " + str(state.actual_yield)),
        Text("Percent Yield: " + str(state.percent_yield))]

    components.append(Button("Calculate Again", "reset_calculator"))

    return Page(state, components)

    
@route
def reset_calculator(state: State) -> Page:
    """Resets the application state back to initial defaults."""
    return Page(get_initial_state(), [
        Header("Calculator Reset"),
        Text("All previous calculation data has been cleared."),
        Button("Return to Home", "index")])


#Unit Tests for parse_reaction
test_state = get_initial_state()
assert_equal(parse_reaction(test_state, "2 H2 + O2 -> 2 H2O"), True)
assert_equal(test_state.reactants[0].formula, "H2")
assert_equal(test_state.reactants[1].formula, "O2")
assert_equal(test_state.products[0].formula, "H2O")
bad_state = get_initial_state()
assert_equal(parse_reaction(bad_state, "H2 + O2 -> H2O"), False)
assert_equal(bad_state.error_message, "Please enter a balanced chemical equation.")

#Unit Test for get_inital_state
assert_equal(
    get_initial_state(),
    State("", [], [], "", 0.0, 0.0, 0.0, "grams", False, ""))

#Unit Tests for determine_limiting
assert_equal(determine_limiting([]), -1)
assert_equal(determine_limiting([Reactant("H2", 2, 4.0, 2.0, 2.0),
                               Reactant("O2", 1, 64.0, 32.0, 2.0)]), 0)
assert_equal(determine_limiting([Reactant("H2", 2, 10.0, 2.0, 5.0),
                                Reactant("O2", 1, 32.0, 32.0, 1.0)]), 1)

#Unit Test for index
assert_equal(index(get_initial_state()), Page(get_initial_state(), [
        Header("Welcome to the Chemistry Calculator!"),
        Text("Calculate limiting reagents, theoretical yield, and percent yield with ease."),
        Button("Start Calculating", "input_reactants"),
        Button("About", "about_page")]))

#Unit Test for about_page
assert_equal(about_page(get_initial_state()), Page(get_initial_state(), [
        Header("About the Chemistry Calculator"),
        Text(
            "This website helps students understand chemical reactions by "
            "calculating limiting reagents, theoretical yield, and percent yield."),
            Button("Home", "index")]))

#Unit Test for input_reactants
assert_equal(input_reactants(get_initial_state()), Page(get_initial_state(), [
        Header("Enter Equation"),
        Text("Enter the balanced chemical equation."),
        TextArea("reaction"),
        Button("Continue", "input_masses")]))

#Unit Test for input_masses
invalid_eq_state = get_initial_state()
assert_equal(
    input_masses(invalid_eq_state, "H2 + O2 -> H2O"),
    Page(invalid_eq_state, [
        Header("Invalid Chemical Equation"),
        Text("Please enter a balanced chemical equation."),
        Button("Try Again", "input_reactants")]))

valid_eq_state = get_initial_state()
assert_equal(
    input_masses(valid_eq_state, "2 H2 + O2 -> 2 H2O"),
    Page(valid_eq_state, [
        Header("Enter Reactant Masses"),
        Text("Enter the starting mass for each reactant."),
        TextBox("mass1"),
        TextBox("mass2"),
        Text("Enter the actual yield (grams)."),
        TextBox("actual_yield"),
        Button("Calculate", "calculate_results")]))

#Unit Test for calculate_results
calc_state = get_initial_state()
parse_reaction(calc_state, "2 H2 + O2 -> 2 H2O")
assert_equal(calculate_results(calc_state, -5.0, 32.0, 18.0), Page(calc_state, [
        Header("Invalid Mass"),
        Text("Both reactant masses must be greater than zero."),
        Button("Try Again", "input_reactants")]))
assert_equal(calculate_results(calc_state, 4.0, 32.0, -2.0), Page(calc_state, [
        Header("Invalid Actual Yield"),
        Text("Actual yield cannot be negative."),
        Button("Try Again", "input_reactants")]))

valid_calc_state = get_initial_state()
parse_reaction(valid_calc_state, "2 H2 + O2 -> 2 H2O")
result_page = calculate_results(valid_calc_state, 4.0, 64.0, 30.0)
assert_equal(valid_calc_state.limiting_reagent, "H2")
assert_equal(
    result_page,
    Page(valid_calc_state, [
        Header("Calculation Results"),
        Text("Limiting Reagent: " + valid_calc_state.limiting_reagent),
        Text("Theoretical Yield: " + str(valid_calc_state.theoretical_yield)),
        Text("Actual Yield: " + str(valid_calc_state.actual_yield)),
        Text("Percent Yield: " + str(valid_calc_state.percent_yield)),
        Button("Summary", "summary_page")]))

#Unit Test for summary_page
assert_equal(summary_page(valid_calc_state), Page(valid_calc_state, [
        Header("Calculation Results"),
        Text("Chemical Equation: " + valid_calc_state.chemical_equation),
        Text("Limiting Reagent: " + valid_calc_state.limiting_reagent),
        Text("Theoretical Yield: " + str(valid_calc_state.theoretical_yield)),
        Text("Actual Yield: " + str(valid_calc_state.actual_yield)),
        Text("Percent Yield: " + str(valid_calc_state.percent_yield)),
        Button("Calculate Again", "reset_calculator")]))

#Unit Test for reset_calculator
assert_equal(reset_calculator(bad_state), Page(get_initial_state(), [        Header("Calculator Reset"),
        Text("All previous calculation data has been cleared."),
        Button("Return to Home", "index")]))

start_server(get_initial_state())

