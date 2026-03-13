from typing import List
from math import radians, sin, cos, sqrt, atan2
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from ..models.models import OrToolPlace, Coordinate


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Tính khoảng cách giữa 2 tọa độ (km)
    """
    R = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def build_distance_matrix(places):
    """
    Tạo distance matrix giữa các places
    """
    size = len(places)
    matrix = [[0] * size for _ in range(size)]

    for i in range(size):
        for j in range(size):

            if i == j:
                matrix[i][j] = 0
                continue

            p1 = places[i].coordinate
            p2 = places[j].coordinate

            dist = haversine_distance(
                p1.latitude,
                p1.longitude,
                p2.latitude,
                p2.longitude
            )

            matrix[i][j] = int(dist * 1000)  # meters

    return matrix


def optimize_route(places) -> List[int]:
    """
    Tối ưu thứ tự đường đi ngắn nhất.

    Args:
        places: list place (có field index và coordinate)

    Returns:
        List[int] : thứ tự index của places
    """

    if len(places) <= 1:
        return [p.index for p in places]

    distance_matrix = build_distance_matrix(places)

    manager = pywrapcp.RoutingIndexManager(
        len(distance_matrix),
        1,   # 1 vehicle
        0    # start node
    )

    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):

        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)

        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()

    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        return [p.index for p in places]

    route = []

    index = routing.Start(0)

    while not routing.IsEnd(index):

        node = manager.IndexToNode(index)
        route.append(places[node].index)

        index = solution.Value(routing.NextVar(index))

    return route

# if __name__ == "__main__":

#     # Một vài địa điểm ở TP.HCM
#     places = [
#         OrToolPlace(0, Coordinate(10.762622, 106.660172)),  # District 5
#         OrToolPlace(1, Coordinate(10.782900, 106.695000)),  # Tao Dan Park
#         OrToolPlace(2, Coordinate(10.776889, 106.700806)),  # Notre Dame
#         OrToolPlace(3, Coordinate(10.823099, 106.629664)),  # Go Vap
#         OrToolPlace(4, Coordinate(10.848000, 106.772000)),  # Thu Duc
#     ]

#     route = optimize_route(places)

#     print("\nOptimized route order:")
#     print(route)