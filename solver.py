from generate_data import generate_data
from utils import eucledian_distance, is_in_area
from ortools.linear_solver import pywraplp
import matplotlib.pyplot as plt

def mip(units, areas_demand, radius, budget, cpd, r):

    solver = pywraplp.Solver.CreateSolver('SCIP')

    # Decision Variables

    n = len(units)
    
    restaurant = []
    kitchen = []
    restaurant_production = []
    kitchen_production = []

    for i, unit in enumerate(units):
        restaurant.append(solver.IntVar(0, 1, 'R' + str(i)))
        kitchen.append(solver.IntVar(0, 1, 'K' + str(i)))
        restaurant_production.append(solver.IntVar(0, unit["capacity_restaurant"], 'X' + str(i)))
        kitchen_production.append(solver.IntVar(0, unit["capacity_kitchen"], 'Y' + str(i)))

    transport = []

    for i in range(n):
        transport.append([])
        for j in range(n):
            if i != j:
                transport[i].append(solver.IntVar(0, 1, 'T' + str(i) + str(j)))
            else:
                transport[i].append(solver.IntVar(0, 0, 'T' + str(i) + str(j)))

    # Constraints

    for i in range(n):
        solver.Add(kitchen[i] + restaurant[i] <= 1)
        solver.Add(restaurant_production[i] <= restaurant[i] * units[i]["capacity_restaurant"])
        solver.Add(kitchen_production[i] <= kitchen[i] * units[i]["capacity_kitchen"])

    for area in areas_demand:
        c1 = 0
        for i in range(n):
            c1 += restaurant_production[i] * is_in_area(area[0], units[i]["position"], radius)
        solver.Add(c1 <= area[1])

    for i in range(n):
        for j in range(n):
            solver.Add(kitchen[i] + restaurant[j] >= 2 * transport[i][j])

    for i in range(n):
        c2 = 0
        for j in range(n):
            c2 += transport[i][j] * restaurant_production[j]
        solver.Add(c2 <= kitchen_production[i])

    for i in range(n):
        c3 = 0
        for j in range(n):
            c3 += transport[i][j] * kitchen[j]
        solver.Add(c3 <= restaurant[i])
        solver.Add(c3 >= restaurant[i])

    cost = 0
    for i in range(n):
        cost += kitchen[i] * (units[i]["rent"] + units[i]["initial_kitchen"])
        cost += restaurant[i] * (units[i]["rent"] + units[i]["initial_restaurant"])

    transport_cost = 0
    for i in range(n):
        for j in range(n):
            transport_cost += transport[i][j] * eucledian_distance(units[i]["position"], units[j]["position"]) * cpd

    cost += transport_cost * 365

    customers = 0
    for i in range(n):
        customers += restaurant_production[i]

    solver.Maximize(r * customers - (1-r) * cost)

    status = solver.Solve()
    print('OPTIMAL:', status == pywraplp.Solver.OPTIMAL)

def mip_simple(units, areas_demand, radius, budget, cpd, r):

    solver = pywraplp.Solver.CreateSolver('SCIP')

    # Decision Variables

    n = len(units)
    
    restaurant = []
    kitchen = []

    for i in range(n):
        restaurant.append(solver.IntVar(0, 1, 'R' + str(i)))
        kitchen.append(solver.IntVar(0, 1, 'K' + str(i)))

    transport = []

    for i in range(n):
        transport.append([])
        for j in range(n):
            if i != j:
                transport[i].append(solver.IntVar(0, 1, 'T' + str(i) + str(j)))
            else:
                transport[i].append(solver.IntVar(0, 0, 'T' + str(i) + str(j)))

    # Constraints

    for i in range(n):
        solver.Add(kitchen[i] + restaurant[i] <= 1)

    for area in areas_demand:
        c1 = 0
        for i in range(n):
            c1 += restaurant[i] * units[i]["capacity_restaurant"] * is_in_area(area[0], units[i]["position"], radius)
        solver.Add(c1 <= area[1])

    for i in range(n):
        for j in range(n):
            solver.Add(kitchen[i] + restaurant[j] >= 2 * transport[i][j])

    for i in range(n):
        for j in range(n):
            solver.Add(transport[i][j] + transport[j][i] <= 1)

    M = 100000
    for i in range(n):
        c = 0
        for j in range(n):
            c += transport[i][j] + transport[j][i]
        # solver.Add(restaurant[i] + M * kitchen[i] >= c)
        #                 0               0          0
        #                 0               1          0 -> inf
        #                 1               0          1

        solver.Add(restaurant[i] <= c + M * kitchen[i])
        #               0           0           0
        #               0           0 -> inf    1
        #               1           1 -> inf    0

    for i in range(n):
        c = 0
        for j in range(n):
            c += (transport[i][j] + transport[j][i]) * units[j]["capacity_restaurant"]
        solver.Add(c <= units[i]["capacity_kitchen"])
                         

    cost = 0
    for i in range(n):
        cost += kitchen[i] * (units[i]["rent"] + units[i]["initial_kitchen"])
        cost += restaurant[i] * (units[i]["rent"] + units[i]["initial_restaurant"])

    transport_cost = 0
    for i in range(n):
        for j in range(n):
            transport_cost += transport[i][j] * eucledian_distance(units[i]["position"], units[j]["position"]) * cpd

    cost += transport_cost * 365

    solver.Add(cost <= budget)

    customers = 0
    for i in range(n):
        customers += restaurant[i] * units[i]["capacity_restaurant"] * 365

    solver.Maximize(customers * r - cost)
    # solver.Maximize(customers)

    status = solver.Solve()
    print('OPTIMAL:', status == pywraplp.Solver.OPTIMAL)
    
    restaurant_solution = [ v.solution_value() for v in restaurant ]
    kitchen_solution = [ v.solution_value() for v in kitchen ]
    transport_solution = [ [ v.solution_value() for v in arr ] for arr in transport ]

    return (restaurant_solution, kitchen_solution, transport_solution)

def greedy(units, areas_demand, radius, budget, cpd, r):
    units_kitchen = sorted(units, key= lambda unit: unit["rent"] + unit["initial_kitchen"] )
    units_restaurant = sorted(units, key= lambda unit: unit["rent"] + unit["initial_restaurant"] )

    kitchen = [0 for _ in units]
    restaurant = [0 for _ in units]
    transport = [ [0 for _ in units ] for _ in units ]

    n = len(units)
    curr_kitchen = 0
    for i in range(n):
        pass

def calc_cost(kitchen, restaurant, transport, units, cpd):
    cost = 0
    n = len(units)
    for i in range(n):
        if kitchen[i] == 1:
            cost += units[i]["initial_kitchen"] + units[i]["rent"]
        if restaurant[i] == 1:
            cost += units[i]["initial_restaurant"] + units[i]["rent"]

    transport_cost = 0
    for i in range(n):
        for j in range(n):
            if transport[i][j] == 1:
                transport_cost += eucledian_distance(units[i]["position"], units[j]["position"]) * cpd
    
    cost += transport_cost * 365
    return cost

if __name__ == '__main__':
    units, areas_demand = generate_data(
        areas=6,
        radius=10, 
        demand_range=(1e8,1e9), 
        capacity_kitchen_range=(2000, 3000),
        capacity_restaurant_range=(300, 400),
        num_units_per_area=(2,3),
        sparcity=15)
    
    solution = mip_simple(units, areas_demand, radius=5, budget=10000000, cpd=1, r=5)

    print(solution[0])
    print(solution[1])
    print(solution[2])

    x = [ unit["position"][0] for unit in units ]
    y = [ unit["position"][1] for unit in units ]

    for i in range(len(solution[2])):
        for j in range(len(solution[2])):
            if solution[2][i][j] ==  1:
                    plt.plot([units[i]["position"][0], units[j]["position"][0]],
                             [units[i]["position"][1], units[j]["position"][1]], 'r--', alpha=.2)

    for area in areas_demand:
        plt.gca().add_patch(plt.Circle(area[0], radius=10, alpha=.1))
        plt.scatter([area[0][0]], [area[0][1]], lw=.4, c='blue', marker='+')

    for i, (x_, y_) in enumerate(zip(x, y)):
        plt.scatter([x_], [y_], 
        marker="${}$".format(units[i]["capacity_restaurant"]) if solution[0][i] == 1 else "${}$".format(units[i]["capacity_kitchen"]) if solution[1][i] == 1 else "x",
        lw=.5, 
        s=200,
        c= "g" if solution[0][i] == 1 else "r" if solution[1][i] == 1 else "black")
    
    plt.grid(color='gray', ls = '--', lw = 0.25)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()









