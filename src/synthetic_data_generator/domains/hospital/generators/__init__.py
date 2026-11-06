"""Generators of the hospital domain (added to the shared ones)."""

from .ids import patient_id, appointment_id
from .rooms import patient_room, facility_room
from .appointments import appointment_type
from .weather import condition, temperature


GENERATORS = {

    "patient_id": patient_id,
    "appointment_id": appointment_id,

    "room_number": patient_room,
    "patient_room": patient_room,
    "facility_room": facility_room,

    "appointment_type": appointment_type,

    "temperature": temperature,
    "condition": condition,
}
