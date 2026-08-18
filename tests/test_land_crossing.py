"""
Automated Land-Crossing Navigation Audit Test
===============================================
Verifies that no edge or route segment in smart-ship-routing/traffic.json
intersects major coastal/land polygons (Peninsular India, Sri Lanka, Sumatra, Java, Malay Peninsula).
"""

import json
import pytest

LAND_POLYGONS = {
    "Sri_Lanka": [
        (9.80, 80.20), (9.40, 80.80), (8.60, 81.20), (7.00, 81.80), 
        (5.90, 80.60), (6.00, 80.20), (6.90, 79.80), (7.90, 79.80), (8.80, 79.70), (9.80, 80.20)
    ],
    "Peninsular_India": [
        (8.15, 77.55), (8.50, 78.10), (10.00, 79.80), (13.10, 80.30), 
        (16.20, 81.80), (17.70, 83.30), (20.00, 87.00), (22.00, 70.00), (19.00, 72.70), 
        (15.40, 73.70), (12.00, 75.00), (10.00, 76.10), (8.15, 77.55)
    ],
    "Sumatra": [
        (5.60, 95.30), (4.00, 98.00), (2.00, 101.00), (-1.00, 104.00),
        (-5.90, 106.00), (-5.50, 104.50), (-3.00, 102.00), (0.00, 99.00),
        (3.00, 96.50), (5.60, 95.30)
    ],
    "Java": [
        (-5.90, 106.00), (-6.50, 108.50), (-7.00, 112.00), (-8.70, 114.50),
        (-8.80, 114.00), (-7.80, 110.00), (-7.00, 106.00), (-5.90, 106.00)
    ],
    "Malay_Peninsula": [
        (1.50, 103.50), (1.60, 104.00), (4.00, 103.50), (6.00, 102.20),
        (10.00, 99.20), (14.00, 100.00), (14.00, 98.00), (10.00, 98.50),
        (7.00, 99.50), (4.50, 101.00), (2.50, 101.80), (1.50, 103.50)
    ]
}


def _is_point_in_poly(lat: float, lon: float, poly: list) -> bool:
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        if ((poly[i][0] > lat) != (poly[j][0] > lat)) and \
           (lon < (poly[j][1] - poly[i][1]) * (lat - poly[i][0]) / (poly[j][0] - poly[i][0]) + poly[i][1]):
            inside = not inside
        j = i
    return inside


def test_no_graph_edges_intersect_land():
    """
    Scans every navigation edge in smart-ship-routing/traffic.json along 20 intermediate points.
    Asserts zero intersections with major land polygons.
    """
    with open("smart-ship-routing/traffic.json", "r", encoding="utf-8") as f:
        graph_data = json.load(f)

    nodes = {n['id']: n for n in graph_data['nodes']}
    violations = []

    for edge in graph_data['edges']:
        src = nodes[edge['source_id']]
        tgt = nodes[edge['target_id']]
        lat1, lon1 = src['latitude'], src['longitude']
        lat2, lon2 = tgt['latitude'], tgt['longitude']

        for step in range(2, 19):
            t = step / 20.0
            sample_lat = lat1 + t * (lat2 - lat1)
            sample_lon = lon1 + t * (lon2 - lon1)
            for land_name, poly in LAND_POLYGONS.items():
                if _is_point_in_poly(sample_lat, sample_lon, poly):
                    violations.append(
                        f"Edge {edge['id']} ({src['id']} -> {tgt['id']}) intersects {land_name} at ({sample_lat:.2f}, {sample_lon:.2f})"
                    )

    assert len(violations) == 0, f"Land crossing violations detected: {violations}"
