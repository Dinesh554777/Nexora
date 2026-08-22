import csv
import os
import statistics


def load_patient_data():
    """
    Load patient data from patient_data.csv
    """

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data", "patient_data.csv")

    patients = []

    with open(csv_path, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            patients.append({
                "patient_id": row["patient_id"],
                "age": int(row["age"]),
                "sex": row["sex"],
                "meniscus_thickness_mm": float(
                    row["meniscus_thickness_mm"]
                ),
                "oa_status": row["oa_status"]
            })

    return patients


def average_thickness(patients):
    """
    Calculate average meniscus thickness.
    """

    if not patients:
        return 0

    values = [
        patient["meniscus_thickness_mm"]
        for patient in patients
    ]

    return round(statistics.mean(values), 2)


def calculate_oa_comparison(patients):
    """
    Compare average meniscus thickness
    between OA and non-OA groups.
    """

    oa_patients = [
        p for p in patients
        if p["oa_status"].lower() == "yes"
    ]

    non_oa_patients = [
        p for p in patients
        if p["oa_status"].lower() == "no"
    ]

    return {
        "oa_average_thickness_mm":
            average_thickness(oa_patients),

        "non_oa_average_thickness_mm":
            average_thickness(non_oa_patients),

        "oa_patient_count":
            len(oa_patients),

        "non_oa_patient_count":
            len(non_oa_patients)
    }


def calculate_sex_analysis(patients):
    """
    Calculate average meniscus thickness
    for male and female patients.
    """

    male_patients = [
        p for p in patients
        if p["sex"].upper() == "M"
    ]

    female_patients = [
        p for p in patients
        if p["sex"].upper() == "F"
    ]

    return {
        "male_average_thickness_mm":
            average_thickness(male_patients),

        "female_average_thickness_mm":
            average_thickness(female_patients),

        "male_patient_count":
            len(male_patients),

        "female_patient_count":
            len(female_patients)
    }


def calculate_correlation(patients):
    """
    Calculate Pearson correlation between
    age and meniscus thickness.

    Implemented without external libraries.
    """

    if len(patients) < 2:
        return 0

    ages = [
        p["age"]
        for p in patients
    ]

    thickness = [
        p["meniscus_thickness_mm"]
        for p in patients
    ]

    mean_age = statistics.mean(ages)
    mean_thickness = statistics.mean(thickness)

    numerator = sum(
        (age - mean_age) *
        (thick - mean_thickness)
        for age, thick in zip(ages, thickness)
    )

    age_squared = sum(
        (age - mean_age) ** 2
        for age in ages
    )

    thickness_squared = sum(
        (thick - mean_thickness) ** 2
        for thick in thickness
    )

    denominator = (
        age_squared * thickness_squared
    ) ** 0.5

    if denominator == 0:
        return 0

    correlation = numerator / denominator

    return round(correlation, 3)


def generate_analytics():
    """
    Generate complete OA analytics.
    """

    patients = load_patient_data()

    oa_analysis = calculate_oa_comparison(patients)
    sex_analysis = calculate_sex_analysis(patients)
    correlation = calculate_correlation(patients)

    return {
        "total_patients": len(patients),
        "oa_analysis": oa_analysis,
        "sex_analysis": sex_analysis,
        "age_thickness_correlation": correlation
    }


if __name__ == "__main__":

    analytics = generate_analytics()

    print("\n===================================")
    print("        OA ANALYTICS")
    print("===================================\n")

    print("Total Patients:",
          analytics["total_patients"])

    print("\n--- OA Comparison ---")

    print(
        "OA Average Thickness:",
        analytics["oa_analysis"]
        ["oa_average_thickness_mm"],
        "mm"
    )

    print(
        "Non-OA Average Thickness:",
        analytics["oa_analysis"]
        ["non_oa_average_thickness_mm"],
        "mm"
    )

    print(
        "OA Patients:",
        analytics["oa_analysis"]
        ["oa_patient_count"]
    )

    print(
        "Non-OA Patients:",
        analytics["oa_analysis"]
        ["non_oa_patient_count"]
    )

    print("\n--- Sex Analysis ---")

    print(
        "Male Average Thickness:",
        analytics["sex_analysis"]
        ["male_average_thickness_mm"],
        "mm"
    )

    print(
        "Female Average Thickness:",
        analytics["sex_analysis"]
        ["female_average_thickness_mm"],
        "mm"
    )

    print("\n--- Age vs Thickness ---")

    print(
        "Correlation:",
        analytics["age_thickness_correlation"]
    )

    print("\n===================================\n")