# app/utils/config.py

CONFIG: dict = {
    "mode": "simulator",          # "simulator" | "obd"
    "max_speed_beg": 40,          # km/h ceiling for Beginner
    "max_speed_med": 60,          # km/h ceiling for Medium
    "max_speed_pro": 80,          # km/h ceiling for Pro
    "min_gear_change_speed": 20,  # km/h below which >2nd gear triggers downshift warning
}
