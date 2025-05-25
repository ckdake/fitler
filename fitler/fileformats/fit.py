import fitparse


def parse_fit(file_path):
    """Parse a FIT file and return relevant activity data."""
    # should these get converted to tcx, or vice versa?
    # examples at fitdump -n session 998158033.fit
    fitfile = fitparse.FitFile(file_path)
    start_time = None
    distance = None
    for record in fitfile.get_messages("session"):
        data = {d.name: d.value for d in record}
        if "start_time" in data:
            start_time = str(data["start_time"])
        if "total_distance" in data:
            distance = float(data["total_distance"]) * 0.00062137  # meters to miles
    return {
        "start_time": start_time,
        "distance": distance,
    }
