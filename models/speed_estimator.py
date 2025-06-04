class SpeedEstimator:
    def __init__(self, real_distance_m: float):
        self.real_distance = real_distance_m
        self.cross_times = {}

    def update_and_get_speed(self, track_id, y_c, t, line1, line2):
        rec = self.cross_times.setdefault(track_id, {})

        if 't1' not in rec and y_c >= line1:
            rec['t1'] = t

        if 't1' in rec and 't2' not in rec and y_c >= line2:
            rec['t2'] = t
            dt = rec['t2'] - rec['t1']
            if dt > 0:
                return round(self.real_distance / dt * 3.6, 1)

        return None
