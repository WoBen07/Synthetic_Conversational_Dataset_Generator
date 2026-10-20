import random

from .rooms import rooms_for


# Appointment type -> facility room groups it can take place in.
# Every value already reads as a complete noun phrase ("cardiology
# appointment", "blood test"), so language schemas must not append
# another "appointment" after {{appointment.appointment_type}}.
TYPE_LOCATIONS = {
    # General medical
    "doctor appointment": ["consultation"],
    "general practitioner visit": ["consultation"],
    "medical consultation": ["consultation"],
    "follow-up appointment": ["consultation"],
    "routine check-up": ["consultation"],
    "annual health check": ["consultation"],
    "preventive examination": ["consultation"],
    "health screening": ["consultation"],

    # Specialists
    "cardiology appointment": ["cardiology", "consultation"],
    "dermatology appointment": ["consultation"],
    "neurology appointment": ["consultation"],
    "orthopedic appointment": ["consultation"],
    "gynecology appointment": ["consultation"],
    "urology appointment": ["consultation"],
    "ENT appointment": ["consultation", "hearing"],
    "ophthalmology appointment": ["eye"],
    "psychiatry appointment": ["consultation"],
    "oncology appointment": ["consultation"],
    "gastroenterology appointment": ["consultation"],
    "pulmonology appointment": ["pulmonary", "consultation"],
    "endocrinology appointment": ["consultation"],
    "rheumatology appointment": ["consultation"],
    "allergy specialist appointment": ["consultation"],

    # Treatments and therapies
    "physiotherapy session": ["therapy"],
    "occupational therapy session": ["therapy"],
    "speech therapy session": ["therapy"],
    "physical rehabilitation session": ["therapy"],
    "pain management appointment": ["treatment", "consultation"],
    "massage therapy session": ["therapy"],
    "exercise therapy session": ["therapy"],

    # Diagnostics
    "medical examination": ["consultation"],
    "blood test": ["laboratory"],
    "laboratory appointment": ["laboratory"],
    "X-ray appointment": ["radiology"],
    "MRI scan": ["mri"],
    "CT scan": ["ct"],
    "ultrasound examination": ["ultrasound"],
    "heart ultrasound": ["ultrasound", "cardiology"],
    "ECG appointment": ["cardiology"],
    "lung function test": ["pulmonary"],
    "eye examination": ["eye"],
    "hearing test": ["hearing"],
    "bone density scan": ["radiology"],

    # Procedures
    "vaccination appointment": ["treatment"],
    "injection appointment": ["treatment"],
    "wound care appointment": ["treatment"],
    "dressing change": ["treatment"],
    "minor procedure": ["treatment"],
    "surgery consultation": ["consultation"],
    "pre-surgery examination": ["consultation"],
    "post-surgery follow-up": ["consultation"],

    # Dental
    "dentist appointment": ["dental"],
    "dental check-up": ["dental"],
    "teeth cleaning appointment": ["dental"],
    "dental treatment": ["dental"],

    # Care-related
    "nursing appointment": ["treatment"],
    "care assessment": ["consultation"],
    "medication review": ["consultation"],
}


TYPES = list(TYPE_LOCATIONS)


DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]


def locations_for(appointment_type):
    return rooms_for(
        TYPE_LOCATIONS[appointment_type]
    )


def appointment_type():

    chosen = random.choice(
        TYPES
    )

    # The location is drawn together with the type so the two always
    # fit (no dental treatment in the waiting room).
    return {
        "value": chosen,
        "location": random.choice(
            locations_for(chosen)
        )
    }


def weekday():
    return random.choice(
        DAYS
    )
