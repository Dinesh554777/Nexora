import csv
import os


def load_implants():
    """
    Load implant sizes from implants.csv
    """

    # services folder-la irundhu ../data/implants.csv
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data", "implants.csv")

    implants = []

    with open(csv_path, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            implants.append({
                "implant_id": row["implant_id"],
                "implant_size": row["implant_size"],
                "femur_width": float(row["femur_width"]),
                "femur_ap": float(row["femur_ap"]),
                "tibia_width": float(row["tibia_width"]),
                "tibia_ap": float(row["tibia_ap"])
            })

    return implants


def calculate_difference(patient, implant):
    """
    Calculate anatomical difference between
    patient measurements and implant dimensions.
    """

    difference = (
        abs(patient["femur_width"] - implant["femur_width"])
        + abs(patient["femur_ap"] - implant["femur_ap"])
        + abs(patient["tibia_width"] - implant["tibia_width"])
        + abs(patient["tibia_ap"] - implant["tibia_ap"])
    )

    return difference


def calculate_match_score(difference):
    """
    Convert anatomical difference into a simple
    normalized matching score.
    """

    score = 100 / (1 + difference)

    return round(score, 2)


def match_implants(
    femur_width,
    femur_ap,
    tibia_width,
    tibia_ap,
    top_n=3
):
    """
    Find the closest implant sizes for a patient's
    anatomical measurements.

    This function accepts measurements directly,
    so later real AI/segmentation output can be
    connected without changing the matching logic.
    """

    patient = {
        "femur_width": float(femur_width),
        "femur_ap": float(femur_ap),
        "tibia_width": float(tibia_width),
        "tibia_ap": float(tibia_ap)
    }

    implants = load_implants()

    results = []

    for implant in implants:

        difference = calculate_difference(patient, implant)
        score = calculate_match_score(difference)

        results.append({
            "implant_id": implant["implant_id"],
            "implant_size": implant["implant_size"],
            "difference_mm": round(difference, 2),
            "match_score": score
        })

    # Lowest anatomical difference = best match
    results.sort(key=lambda x: x["difference_mm"])

    return results[:top_n]


if __name__ == "__main__":

    # -------------------------------
    # DUMMY PATIENT DATA
    # -------------------------------

    patient_measurements = {
        "femur_width": 68.2,
        "femur_ap": 61.4,
        "tibia_width": 72.1,
        "tibia_ap": 46.8
    }

    recommendations = match_implants(
        patient_measurements["femur_width"],
        patient_measurements["femur_ap"],
        patient_measurements["tibia_width"],
        patient_measurements["tibia_ap"]
    )

    print("\n===================================")
    print("   IMPLANT SIZE RECOMMENDATION")
    print("===================================\n")

    for index, result in enumerate(recommendations, start=1):

        print(f"Rank {index}")
        print(f"Implant ID       : {result['implant_id']}")
        print(f"Implant Size     : {result['implant_size']}")
        print(f"Difference       : {result['difference_mm']} mm")
        print(f"Match Score      : {result['match_score']}")
        print("-----------------------------------")