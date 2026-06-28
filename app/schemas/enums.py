from enum import Enum


class FeeType(str, Enum):
    fixed = "fixed"
    percentage = "percentage"


class FeeAppliesTo(str, Enum):
    per_booking = "per_booking"
    per_person = "per_person"
    per_adult = "per_adult"
    per_child = "per_child"


class ActivityType(str, Enum):
    safari = "safari"
    snorkeling = "snorkeling"
    diving = "diving"
    island_trip = "island_trip"
    submarine = "submarine"
    quad_biking = "quad_biking"
    fishing = "fishing"
    boat_trip = "boat_trip"
    other = "other"


class TripLocation(str, Enum):
    hurghada = "hurghada"
    marsa_alam = "marsa_alam"
    el_gouna = "el_gouna"
    safaga = "safaga"
    soma_bay = "soma_bay"
