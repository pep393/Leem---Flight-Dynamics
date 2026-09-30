"""ASPID airbrakes control: apogee predictor + PI + Cd matching, and debug plots."""

import matplotlib.pyplot as plt
import numpy as np


def predict_apogee(z, vz, mass, rho, cd, area, g):
    """Closed-form 1D apogee with quadratic drag and constant air density."""
    k = 0.5 * rho * area * cd
    return z + mass / (2 * k) * np.log(1 + k * vz**2 / (mass * g))


class AirbrakesController:
    """Apogee error -> PI -> commanded airbrakes deceleration -> Cd (Cd matching) -> deployment."""

    def __init__(self, rocket, env, target_apogee, kp, ki, sampling_rate):
        self.rocket = rocket
        self.env = env
        self.target_apogee = target_apogee  # m ASL
        self.kp = kp
        self.ki = ki
        self.dt = 1 / sampling_rate
        self.i_term = 0.0
        self.deployment_grid = np.linspace(0, 1, 51)

    def update(self, time, state, air_brakes, active):
        """Returns the new deployment level and a dict with the variables to log."""
        z, vz = state[2], state[5]
        speed = np.linalg.norm(state[3:6])
        mach = speed / self.env.speed_of_sound.get_value_opt(z)
        rho = self.env.density.get_value_opt(z)
        mass = self.rocket.total_mass.get_value_opt(time)
        area = self.rocket.area  # Airbrakes reference area is the rocket area (default)
        cd_ab_of = air_brakes.drag_coefficient.get_value_opt  # Cd_ab(deployment, mach)
        cd_rocket = self.rocket.power_off_drag.get_value_opt(mach)
        d = air_brakes.deployment_level
        cd_ab = cd_ab_of(d, mach) if d > 0 else 0.0  # RocketPy ignores the airbrakes at d = 0

        # 1. Apogee predictor with the current configuration
        g = self.env.gravity.get_value_opt(z)
        apogee = predict_apogee(z, vz, mass, rho, cd_rocket + cd_ab, area, g)
        error = apogee - self.target_apogee

        p_term = a_cmd = a_max = cd_ab_cmd = deployment = 0.0
        if active:
            # Airbrakes Cd vs deployment at the current Mach, forced monotonic for the inversion
            cd_curve = np.maximum.accumulate([0.0] + [cd_ab_of(x, mach) for x in self.deployment_grid[1:]])
            q_area_mass = 0.5 * rho * speed**2 * area / mass  # deceleration = q_area_mass * Cd

            # 2. PI -> deceleration requested to the airbrakes, limited to the fully open value
            a_max = q_area_mass * cd_curve[-1]
            self.i_term = np.clip(self.i_term + self.ki * error * self.dt, 0, a_max)
            p_term = self.kp * error
            a_cmd = np.clip(p_term + self.i_term, 0, a_max)

            # 3. Cd matching: Cd that gives a_cmd -> deployment from the airbrakes Cd table
            cd_ab_cmd = a_cmd / q_area_mass
            deployment = np.interp(cd_ab_cmd, cd_curve, self.deployment_grid)
        else:
            self.i_term = 0.0

        return deployment, {
            "t": time, "active": active, "deployment": deployment, "mach": mach,
            "apogee_pred": apogee, "error": error, "p": p_term, "i": self.i_term,
            "a_cmd": a_cmd, "a_max": a_max, "cd_rocket": cd_rocket, "cd_ab_cmd": cd_ab_cmd, "cd_ab": cd_ab,
        }


def plot_airbrakes(flight, baseline_flight, target_apogee, activation_altitude):
    """Airbrakes debug plots. target_apogee in m ASL, activation_altitude in m AGL."""
    env, rocket = flight.env, flight.rocket
    air_brakes = rocket.air_brakes[0]
    elevation, burn_out = env.elevation, rocket.motor.burn_out_time

    # Controller log as arrays, coast phase only
    log = flight.get_controller_observed_variables()
    log = {key: np.array([step[key] for step in log]) for key in log[0]}
    coast = log["t"] > burn_out
    log = {key: value[coast] for key, value in log.items()}
    t = log["t"]

    fig, ax = plt.subplots(4, 2, figsize=(14, 16))
    ax = ax.flatten()

    ax[0].plot(t, log["deployment"], label="Deployment level")
    ax[0].plot(t, log["mach"], label="Mach")
    ax[0].fill_between(t, 0, 1, where=log["active"], color="green", alpha=0.1, label="Controller active")

    ax[1].plot(t, log["cd_rocket"], label="Rocket Cd (power off)")
    ax[1].plot(t, log["cd_ab_cmd"], label="Airbrakes Cd commanded")
    ax[1].plot(t, log["cd_ab"], "--", label="Airbrakes Cd actual")

    ax[2].plot(t, log["apogee_pred"] - elevation, label="Predicted apogee")
    ax[2].axhline(target_apogee - elevation, color="k", ls="--", label="Target")
    ax[2].axhline(flight.apogee - elevation, color="r", ls=":", label="Final apogee")

    # Predictor validation on the passive flight
    tb = np.linspace(burn_out, baseline_flight.apogee_time, 200)
    predicted = []
    for ti in tb:
        z, vz, cd = baseline_flight.z(ti), baseline_flight.vz(ti), rocket.power_off_drag(baseline_flight.mach_number(ti))
        predicted.append(predict_apogee(z, vz, rocket.total_mass(ti), env.density(z), cd, rocket.area, env.gravity(z)))
    ax[3].plot(tb, np.array(predicted) - baseline_flight.apogee, label="Flight without airbrakes")
    ax[3].axhline(0, color="k", lw=0.8)

    ax[4].plot(t, log["p"], label="P term")
    ax[4].plot(t, log["i"], label="I term")
    ax[4].plot(t, log["a_cmd"], label="Commanded deceleration")
    ax[4].plot(t, log["a_max"], "k--", label="Max deceleration (fully open)")

    for f, name in [(flight, "With airbrakes"), (baseline_flight, "Without airbrakes")]:
        ax[5].plot(f.altitude.x_array, f.altitude.y_array, label=f"{name} (apogee {f.apogee - elevation:.0f} m)")
        ax[6].plot(f.speed.x_array, f.speed.y_array, label=name)
    ax[5].axhline(activation_altitude, color="g", ls=":", label="Activation altitude")
    ax[5].axhline(target_apogee - elevation, color="k", ls="--", label="Target")

    # Airbrakes Cd table: interpolated curves (lines) and CSV points (dots)
    data = air_brakes.drag_coefficient.source
    deployment = np.linspace(0, 1, 101)
    for i, mach in enumerate([0.2, 0.4, 0.6, 0.8]):
        ax[7].plot(deployment, [air_brakes.drag_coefficient(x, mach) for x in deployment], f"C{i}", label=f"Mach {mach}")
        points = np.isclose(data[:, 1], mach)
        ax[7].scatter(data[points, 0], data[points, 2], color=f"C{i}")

    titles = ["Deployment and Mach", "Drag coefficients", "Apogee predictor", "Predictor error (predicted - real apogee)",
              "PI terms", "Altitude", "Speed", "Airbrakes Cd table"]
    ylabels = ["(-)", "Cd (-)", "Apogee AGL (m)", "Error (m)", "Deceleration (m/s²)", "Altitude AGL (m)",
               "Speed (m/s)", "Cd (-)"]
    for a, title, ylabel in zip(ax, titles, ylabels):
        a.set(title=title, xlabel="Time (s)", ylabel=ylabel)
        a.grid(True)
        a.legend()
    ax[7].set_xlabel("Deployment level (-)")
    fig.suptitle("ASPID airbrakes controller")
    fig.tight_layout()
    plt.show()
