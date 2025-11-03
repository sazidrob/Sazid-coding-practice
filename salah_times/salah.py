#!/usr/bin/env python3


import math
import datetime
import time
import requests
import tkinter as tk
from tkinter import ttk, messagebox

# -------------------------
# Astronomical utilities
# -------------------------

def to_rad(d):
    return d * math.pi / 180.0

def to_deg(r):
    return r * 180.0 / math.pi

def fix_angle(angle):
    # normalize to [0,360)
    a = angle % 360.0
    if a < 0:
        a += 360.0
    return a

def julian_day(year, month, day):
    # From Fliegel & Van Flandern algorithm (works for Gregorian years)
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jd = day + ((153 * m + 2)//5) + 365*y + y//4 - y//100 + y//400 - 32045
    # Return Julian Day at 0h UT
    return float(jd)

def sun_position(jd):
    # Returns (declination in degrees, equation of time in minutes)
    # Approx solar position using simplified VSOP-like formulas (sufficient for prayer times)
    # Convert JD to Julian centuries since J2000.0
    T = (jd - 2451545.0) / 36525.0

    # Geometric mean longitude of the Sun (deg)
    L0 = fix_angle(280.46646 + 36000.76983*T + 0.0003032*T*T)
    # Mean anomaly (deg)
    M = fix_angle(357.52911 + 35999.05029*T - 0.0001537*T*T)
    # Eccentricity of Earth's orbit
    e = 0.016708634 - 0.000042037*T - 0.0000001267*T*T
    # Sun's equation of center
    C = (1.914602 - 0.004817*T - 0.000014*T*T)*math.sin(to_rad(M)) \
        + (0.019993 - 0.000101*T)*math.sin(to_rad(2*M)) \
        + 0.000289*math.sin(to_rad(3*M))
    # True longitude
    true_long = L0 + C
    # Apparent longitude (deg), corrected for nutation and aberration
    omega = 125.04 - 1934.136 * T
    lambda_sun = true_long - 0.00569 - 0.00478 * math.sin(to_rad(omega))
    # Obliquity of the ecliptic
    eps0 = 23.4392911111111 - 0.0130041666667*T - 1.666666667e-7*T*T + 5.02777778e-7*T*T*T
    eps = eps0 + 0.00256 * math.cos(to_rad(omega))

    # Declination
    decl = to_deg(math.asin(math.sin(to_rad(eps)) * math.sin(to_rad(lambda_sun))))

    # Equation of time (in minutes)
    # EoT = 4 * (L0 - 0.0057183 - alpha + ...). We'll use a commonly used approximation:
    y = math.tan(to_rad(eps/2.0))
    y *= y
    sin2L0 = math.sin(2.0 * to_rad(L0))
    sinM   = math.sin(to_rad(M))
    cos2L0 = math.cos(2.0 * to_rad(L0))
    sin4L0 = math.sin(4.0 * to_rad(L0))
    sin2M  = math.sin(2.0 * to_rad(M))

    Etime = y * sin2L0 - 2.0*e*sinM + 4.0*e*y*sinM*cos2L0 - 0.5*y*y*sin4L0 - 1.25*e*e*sin2M
    Etime = to_deg(Etime) * 4.0  # in minutes

    return decl, Etime

def sun_decl_and_eq_time_for_date(date):
    # date is datetime.date
    jd = julian_day(date.year, date.month, date.day)
    # We'll compute at midday to reduce small changes
    decl, eqt = sun_position(jd + 0.5)
    return decl, eqt

def time_to_string(t):
    if t is None:
        return "--:--"
    # t is hours as float (UTC-based)
    h = int(math.floor(t)) % 24
    m = int(round((t - math.floor(t)) * 60))
    if m == 60:
        m = 0
        h = (h + 1) % 24
    return "{:02d}:{:02d}".format(h, m)

# -------------------------
# Prayer time calculations
# -------------------------

def compute_solar_noon(longitude, tz, date):
    # longitude in degrees (+E), tz is hours offset from UTC (e.g., -5 for EST)
    # compute equation of time for the date
    decl, eqt = sun_decl_and_eq_time_for_date(date)
    # approximate solar noon (UTC) in fractional hours:
    # solar_noon_utc = 12:00 - eqt(min) - longitude/15
    solar_noon_utc = 12.0 - (eqt / 60.0) - (longitude / 15.0)
    # convert to local time by adding timezone offset
    solar_noon_local = solar_noon_utc + tz
    return solar_noon_local

def hour_angle_for_solar_zenith(latitude, decl, zenith_deg):
    # returns hour angle in degrees (absolute)
    # zenith = angle between sun and vertical (i.e., 90 + altitude)
    # formula: cos(H) = (cos(zenith) - sin(lat)*sin(dec)) / (cos(lat)*cos(dec))
    lat_r = to_rad(latitude)
    dec_r = to_rad(decl)
    zen_r = to_rad(zenith_deg)
    cosH = (math.cos(zen_r) - math.sin(lat_r)*math.sin(dec_r)) / (math.cos(lat_r)*math.cos(dec_r))
    if cosH < -1 or cosH > 1:
        return None  # sun doesn't reach that zenith (e.g., polar day/night)
    H = math.degrees(math.acos(cosH))
    return H

def time_for_angle(angle_deg, latitude, longitude, tz, date):
    # angle_deg is negative if below horizon (e.g., -18 for fajr), or zenith angle (e.g., 90.833 for sunrise)
    # We'll treat inputs as solar altitude angle in degrees (altitude). Convert to zenith = 90 - altitude.
    # If angle given as zenith angle ( > 90 ), pass directly.
    # We'll standardize input:
    altitude = angle_deg
    if altitude <= 90 and altitude >= -90:
        zenith = 90.0 - altitude
    else:
        zenith = angle_deg
    decl, eqt = sun_decl_and_eq_time_for_date(date)
    H = hour_angle_for_solar_zenith(latitude, decl, zenith)
    if H is None:
        return None
    # hour angle H is degrees; convert to hours = H / 15
    delta_hours = H / 15.0
    noon = compute_solar_noon(longitude, tz, date)
    # two times: noon +/- delta_hours (local)
    t1 = noon - delta_hours
    t2 = noon + delta_hours
    return t1, t2  # t1 = morning time, t2 = evening time

def asr_time(latitude, longitude, tz, date, factor):
    # factor = 1 for standard, 2 for Hanafi.
    # Asr occurs when the length of an object's shadow equals factor + tangent of sun altitude.
    # Compute the angle (zenith) where tangent of sun altitude = 1 / (factor + 1?) But simpler: use formula:
    # cos(H) = (sin(z) - sin(lat)*sin(dec)) / (cos(lat)*cos(dec))
    # where z = arctan(1/(factor + tan(|lat-dec|)??)
    # Simpler known formula: asr occurs when sun altitude = arctan(1/(factor + tan(|latitude - declination|))) ??? This is messy.
    # Use geometrical method: the angle between sun and vertical where shadow length = factor => altitude = atan(1/(factor + tan(abs(lat-dec)))) is often used in prayer-time libraries.
    # To keep accuracy good, we'll compute zenith angle z such that:
    #   cot(zenith - decl) = factor + tan(|latitude - decl|)
    # But that's complicated. Instead we'll compute from the formula used by PrayTimes:
    #   angle = -atan(1/(factor + tan(|latitude - decl|))) in degrees (but negative altitude)
    decl, eqt = sun_decl_and_eq_time_for_date(date)
    lat_r = to_rad(latitude)
    dec_r = to_rad(decl)
    # Following the PrayTimes approach:
    # angle = atan(1/(factor + tan(|lat - decl|)))
    # altitude_asr = to_deg(math.atan(1.0 / (factor + abs(math.tan(lat_r - dec_r)))))
    # However some sources use: angle = -to_deg(math.atan(1/(factor + math.tan(abs(lat - decl)))))
    # We'll follow the commonly used variant:
    try:
        angle_rad = math.atan(1.0 / (factor + abs(math.tan(lat_r - dec_r))))
    except Exception:
        return None
    altitude_asr = to_deg(angle_rad)  # positive small angle
    # We need the corresponding zenith:
    zenith = 90.0 - altitude_asr
    H = hour_angle_for_solar_zenith(latitude, decl, zenith)
    if H is None:
        return None
    delta_hours = H / 15.0
    noon = compute_solar_noon(longitude, tz, date)
    return noon + delta_hours  # Asr is afternoon time (after noon)

# -------------------------
# High-level prayer calc
# -------------------------

def calculate_prayer_times(latitude, longitude, tz, date,
                           fajr_angle=18.0, isha_angle=17.0,
                           asr_method='Standard'):
    # tz is hours offset from UTC (e.g., -5)
    # fajr_angle / isha_angle are degrees below horizon (positive numbers)
    # asr_method: 'Standard' or 'Hanafi'
    # returns dictionary of times in local hours (float)
    # angles: for sunrise/sunset use -0.833 (sun center, refraction)
    times = {
        'Fajr': None,
        'Sunrise': None,
        'Dhuhr': None,
        'Asr': None,
        'Maghrib': None,
        'Isha': None
    }
    # Dhuhr (solar noon)
    noon = compute_solar_noon(longitude, tz, date)
    times['Dhuhr'] = noon

    # Sunrise / Sunset: use altitude = -0.833
    sun_times = time_for_angle(-0.833, latitude, longitude, tz, date)
    if sun_times is not None:
        times['Sunrise'] = sun_times[0]
        times['Maghrib'] = sun_times[1]  # sunset -> Maghrib begins

    # Fajr: altitude = -fajr_angle (e.g., -18)
    fajr_times = time_for_angle(-fajr_angle, latitude, longitude, tz, date)
    if fajr_times is not None:
        times['Fajr'] = fajr_times[0]

    # Isha: altitude = -isha_angle
    isha_times = time_for_angle(-isha_angle, latitude, longitude, tz, date)
    if isha_times is not None:
        times['Isha'] = isha_times[1]

    # Asr:
    factor = 1.0 if asr_method == 'Standard' else 2.0
    asr = asr_time(latitude, longitude, tz, date, factor)
    times['Asr'] = asr

    return times

# -------------------------
# Tkinter GUI
# -------------------------

class SalahApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Salah Times — salah.py")
        self.resizable(False, False)
        self.create_widgets()
        self.update_clock()
        # default date is today
        self.date_var.set(datetime.date.today().isoformat())

    def create_widgets(self):
        frm = ttk.Frame(self, padding=12)
        frm.grid(row=0, column=0)

        # Location inputs
        ttk.Label(frm, text="Latitude:").grid(row=0, column=0, sticky="e")
        self.lat_entry = ttk.Entry(frm, width=12)
        self.lat_entry.grid(row=0, column=1)
        self.lat_entry.insert(0, "40.7128")  # default NYC

        ttk.Label(frm, text="Longitude:").grid(row=0, column=2, sticky="e")
        self.lon_entry = ttk.Entry(frm, width=12)
        self.lon_entry.grid(row=0, column=3)
        self.lon_entry.insert(0, "-74.0060")

        ttk.Label(frm, text="Timezone (UTC offset):").grid(row=1, column=0, sticky="e")
        self.tz_entry = ttk.Entry(frm, width=12)
        self.tz_entry.grid(row=1, column=1)
        self.tz_entry.insert(0, "-5")  # EST default (no DST handling)

        ttk.Label(frm, text="Date (YYYY-MM-DD):").grid(row=1, column=2, sticky="e")
        self.date_var = tk.StringVar()
        self.date_entry = ttk.Entry(frm, width=12, textvariable=self.date_var)
        self.date_entry.grid(row=1, column=3)

        # Method selection
        ttk.Label(frm, text="Method:").grid(row=2, column=0, sticky="e")
        self.method_combo = ttk.Combobox(frm, values=["MWL (Fajr18/Isha17)", "ISNA (15/15)", "UmmAlQura (Fajr18/Isha-fixed)"], state="readonly", width=20)
        self.method_combo.grid(row=2, column=1, columnspan=2, sticky="w")
        self.method_combo.current(0)

        ttk.Label(frm, text="Asr Method:").grid(row=2, column=3, sticky="e")
        self.asr_combo = ttk.Combobox(frm, values=["Standard", "Hanafi"], state="readonly", width=8)
        self.asr_combo.grid(row=2, column=4)
        self.asr_combo.current(0)

        # Buttons
        self.calc_btn = ttk.Button(frm, text="Calculate", command=self.on_calculate)
        self.calc_btn.grid(row=3, column=0, pady=(8,0))

        self.now_btn = ttk.Button(frm, text="Use Current Location/Date (quick)", command=self.use_quick_defaults)
        self.now_btn.grid(row=3, column=1, columnspan=2, pady=(8,0))

        self.live_var = tk.BooleanVar(value=False)
        self.live_check = ttk.Checkbutton(frm, text="Auto-update every minute", variable=self.live_var)
        self.live_check.grid(row=3, column=3, columnspan=2, sticky="w", pady=(8,0))

        # Results area
        sep = ttk.Separator(frm, orient="horizontal")
        sep.grid(row=4, column=0, columnspan=5, sticky="we", pady=8)

        self.result_labels = {}
        row = 5
        for name in ("Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"):
            ttk.Label(frm, text=name + ":").grid(row=row, column=0, sticky="e")
            lbl = ttk.Label(frm, text="--:--", width=12, anchor="w", font=("TkDefaultFont", 11, "bold"))
            lbl.grid(row=row, column=1, columnspan=2, sticky="w")
            self.result_labels[name] = lbl
            row += 1

        # Status and clock
        self.clock_label = ttk.Label(frm, text="", font=("TkDefaultFont", 9))
        self.clock_label.grid(row=row, column=0, columnspan=3, sticky="w", pady=(8,0))
        self.status_label = ttk.Label(frm, text="Ready.", font=("TkDefaultFont", 9))
        self.status_label.grid(row=row, column=3, columnspan=2, sticky="e", pady=(8,0))

    import requests  # <-- add this import at the top of your file

def use_quick_defaults(self):
    """Fetch user location automatically via IP and set today's date."""
    try:
        resp = requests.get("http://ip-api.com/json/", timeout=5).json()
        if resp["status"] == "success":
            lat = round(resp["lat"], 4)
            lon = round(resp["lon"], 4)
            city = resp.get("city", "")
            tz = resp.get("timezone", "")
            # timezone is like 'America/New_York'; we can get offset from UTC dynamically
            offset_hours = datetime.datetime.now(datetime.timezone.utc).astimezone().utcoffset().total_seconds() / 3600
            offset_hours = round(offset_hours, 1)

            self.lat_entry.delete(0, tk.END)
            self.lat_entry.insert(0, str(lat))
            self.lon_entry.delete(0, tk.END)
            self.lon_entry.insert(0, str(lon))
            self.tz_entry.delete(0, tk.END)
            self.tz_entry.insert(0, str(offset_hours))
            self.date_var.set(datetime.date.today().isoformat())

            self.status_label.config(text=f"Detected {city or 'your area'} (UTC{offset_hours:+g})")
            self.on_calculate()
        else:
            raise Exception("Location lookup failed")
    except Exception as e:
        self.status_label.config(text="Location not found — enter manually.")
        messagebox.showwarning("Location Error", f"Could not detect location:\n{e}")

    def on_calculate(self):
        lat_s = self.lat_entry.get().strip()
        lon_s = self.lon_entry.get().strip()
        tz_s = self.tz_entry.get().strip()
        date_s = self.date_var.get().strip()
        method = self.method_combo.get()
        asr_method = self.asr_combo.get()
        try:
            lat = float(lat_s)
            lon = float(lon_s)
            tz = float(tz_s)
        except Exception:
            messagebox.showerror("Input error", "Latitude, Longitude, and Timezone must be numeric.")
            return
        try:
            y,m,d = map(int, date_s.split("-"))
            date = datetime.date(y,m,d)
        except Exception:
            messagebox.showerror("Input error", "Date must be YYYY-MM-DD")
            return

        # select angles per method
        if method.startswith("MWL"):
            fajr_angle = 18.0
            isha_angle = 17.0
        elif method.startswith("ISNA"):
            fajr_angle = 15.0
            isha_angle = 15.0
        else:  # Umm al-Qura-ish
            fajr_angle = 18.0
            # Umm al-Qura often uses fixed Isha time after Maghrib; but we'll use a smaller twilight angle
            isha_angle = 18.0  # approximate

        times = calculate_prayer_times(lat, lon, tz, date,
                                       fajr_angle=fajr_angle,
                                       isha_angle=isha_angle,
                                       asr_method=asr_method)

        # Display
        for key, val in times.items():
            if val is None:
                display = "--:--"
            else:
                display = time_to_string(val)
            self.result_labels[key].config(text=display)

        self.status_label.config(text="Calculated for {} (UTC{:+g})".format(date.isoformat(), tz))

    def update_clock(self):
        now = datetime.datetime.now()
        self.clock_label.config(text="Local time: " + now.strftime("%Y-%m-%d %H:%M:%S"))
        # auto-update if checked
        if self.live_var.get():
            # update date field to today
            self.date_var.set(datetime.date.today().isoformat())
            self.on_calculate()
        # schedule next update (every 10 seconds for the clock; calculations every 60 sec if live)
        self.after(10000, self.update_clock)

# -------------------------
# Main
# -------------------------

def main():
    app = SalahApp()
    # initial calculate
    try:
        app.on_calculate()
    except Exception:
        pass
    app.mainloop()

if __name__ == "__main__":
    main()
