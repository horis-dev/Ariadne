'''
AFLGo adds a simulated annealing algorithm to the power scheduling part, and calculates scores using both time and distance.
Seeds that run longer and are closer (smaller distance) score higher, allowing them to receive more fuzzing time.
'''

import math

# Fields to be added in each seed record
# cur_ms (current execution time in ms), start_time (fuzz start time),
# min_distance, max_distance (min/max distance observed during seed fuzzing; initialize both as -1)


# Configuration file must include the following entries
# cooling_schedule (temperature calculation method, default SAN_EXP)
# t_x (time-domain threshold to enter next stage), perf_score (seed score, initial 100), MAX_FACTOR (weight computation factor, default 32)

import time


def get_cur_time():
    # Return current timestamp in milliseconds
    current_time = time.time()
    return int(current_time * 1000)


def calculate_score(cooling_schedule, cur_ms, start_time, t_x, q_distance, min_distance, max_distance, perf_score,
                    MAX_FACTOR):

    """
    Python implementation of the C code logic for cooling schedule and score calculation.

    Parameters:
        cooling_schedule (str): Type of cooling schedule ("SAN_EXP", "SAN_LOG", "SAN_LIN", "SAN_QUAD").
        cur_ms (int): Current time in milliseconds.
        start_time (int): Start time in milliseconds.
        t_x (int): Time-domain threshold (minutes).
        q_distance (float): Current distance.
        min_distance (float): Seed minimum distance observed.
        max_distance (float): Seed maximum distance observed.
        perf_score (float): Initial performance score.
        MAX_FACTOR (float): Maximum factor value for scaling.

    Returns:
        float: Updated performance score.
    """
    # if (q_distance > 0) :
    #     if (max_distance <= 0) :
    #         max_distance = q_distance;
    #         min_distance = q_distance;
    #
    # if (q_distance > max_distance) :
    #     max_distance = q_distance;
    # if (q_distance < min_distance) :
    #     min_distance = q_distance;


    # Calculate elapsed time and progress
    t = (cur_ms - start_time) / 1000.0  # Convert ms to seconds
    progress_to_tx = t / (t_x * 60.0)  # Progress ratio toward t_x (t_x is in minutes)

    # Calculate temperature T based on cooling schedule
    if cooling_schedule == "SAN_EXP":
        T = 1.0 / math.pow(20.0, progress_to_tx)
    elif cooling_schedule == "SAN_LOG":
        T = 1.0 / (1.0 + 2.0 * math.log(1.0 + progress_to_tx * 13358.7268297))
    elif cooling_schedule == "SAN_LIN":
        T = 1.0 / (1.0 + 19.0 * progress_to_tx)
    elif cooling_schedule == "SAN_QUAD":
        T = 1.0 / (1.0 + 19.0 * math.pow(progress_to_tx, 2))
    else:
        raise ValueError("Unknown Power Schedule for Directed Fuzzing")

    # Calculate power factor
    power_factor = 1.0
    if q_distance > 0:
        # Normalize distance
        normalized_d = 0.0
        if max_distance != min_distance:
            normalized_d = (q_distance - min_distance) / (max_distance - min_distance)

        if normalized_d >= 0:
            # p balances distance and temperature:
            # when normalized_d is small (close), (1 - normalized_d) is large -> higher p
            p = (1.0 - normalized_d) * (1.0 - T) + 0.5 * T
            power_factor = math.pow(2.0, 2.0 * math.log2(MAX_FACTOR) * (p - 0.5))
        # else: print(f"WARN: Normalized distance negative: {normalized_d}")

    # Update performance score by applying the power factor
    perf_score *= power_factor

    return perf_score