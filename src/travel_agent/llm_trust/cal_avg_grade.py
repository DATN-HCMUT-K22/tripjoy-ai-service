import json
from pathlib import Path

class AvgGrade:
    def __init__(self):
        self.avg_overall = 0.0
        self.avg_spatial_coherence = 0.0
        self.avg_temporal_feasibility = 0.0
        self.avg_poi_relevance_travel_type = 0.0
        self.avg_poi_relevance_budget = 0.0

def main():
    request_path = Path(__file__).with_name("grade_pro_without_reason.json")
    travel_requests = json.loads(request_path.read_text(encoding="utf-8"))

    n = len(travel_requests)
    avg = AvgGrade()

    for i in range(n):
        avg.avg_overall += travel_requests[i]["overall"]
        avg.avg_spatial_coherence += travel_requests[i]["subscores"]["spatial_coherence"]
        avg.avg_temporal_feasibility += travel_requests[i]["subscores"]["temporal_feasibility"]
        avg.avg_poi_relevance_travel_type += travel_requests[i]["subscores"]["poi_relevance_travel_type"]
        avg.avg_poi_relevance_budget += travel_requests[i]["subscores"]["poi_relevance_budget"]

    avg.avg_overall /= n
    avg.avg_spatial_coherence /= n
    avg.avg_temporal_feasibility /= n
    avg.avg_poi_relevance_travel_type /= n
    avg.avg_poi_relevance_budget /= n

    print("Average Overall:", avg.avg_overall)
    print("Average Spatial Coherence:", avg.avg_spatial_coherence)
    print("Average Temporal Feasibility:", avg.avg_temporal_feasibility)
    print("Average POI Relevance (Travel Type):", avg.avg_poi_relevance_travel_type)
    print("Average POI Relevance (Budget):", avg.avg_poi_relevance_budget)

if __name__ == "__main__":
    main()