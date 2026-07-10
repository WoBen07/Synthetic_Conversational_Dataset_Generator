import random


TYPES = [
    # General medical
    "doctor appointment",
    "general practitioner visit",
    "medical consultation",
    "follow-up appointment",
    "routine check-up",
    "annual health check",
    "preventive examination",
    "health screening",
    
    # Specialists
    "cardiology appointment",
    "dermatology appointment",
    "neurology appointment",
    "orthopedic appointment",
    "gynecology appointment",
    "urology appointment",
    "ENT appointment",
    "ophthalmology appointment",
    "psychiatry appointment",
    "oncology appointment",
    "gastroenterology appointment",
    "pulmonology appointment",
    "endocrinology appointment",
    "rheumatology appointment",
    "allergy specialist appointment",

    # Treatments and therapies
    "physiotherapy",
    "occupational therapy",
    "speech therapy",
    "physical rehabilitation session",
    "pain management appointment",
    "massage therapy session",
    "exercise therapy session",

    # Diagnostics
    "medical examination",
    "blood test",
    "laboratory appointment",
    "X-ray appointment",
    "MRI scan appointment",
    "CT scan appointment",
    "ultrasound examination",
    "heart ultrasound appointment",
    "ECG appointment",
    "lung function test",
    "eye examination",
    "hearing test",
    "bone density scan",

    # Procedures
    "vaccination appointment",
    "injection appointment",
    "wound care appointment",
    "dressing change appointment",
    "minor procedure appointment",
    "surgery consultation",
    "pre-surgery examination",
    "post-surgery follow-up",

    # Dental
    "dentist appointment",
    "dental check-up",
    "teeth cleaning appointment",
    "dental treatment appointment",

    # Care-related
    "home care visit",
    "nursing appointment",
    "care assessment",
    "medication review appointment"
]


DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]


def appointment_type():
    return random.choice(
        TYPES
    )


def weekday():
    return random.choice(
        DAYS
    )