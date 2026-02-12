import random
import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go # type: ignore

def generate_mock_analytics(seed_str, pub_date_str=None):
    """
    Generates consistent 'fake' stats based on the input seed (url)
    and publish date.
    """
    # Seed the random generator so the stats for a specific article are always the same
    random.seed(seed_str)
    
    np.random.seed(sum(ord(c) for c in seed_str) % (2**32))
    
    # --- Date Handling ---
    try:
        pub_date = pd.to_datetime(pub_date_str).date() # type: ignore
    except:
        pub_date = datetime.date.today() - datetime.timedelta(days=30)
    
    today = datetime.date.today()
    if pub_date > today:
        pub_date = today - datetime.timedelta(days=1)
        
    days_diff = (today - pub_date).days
    date_range = [pub_date + datetime.timedelta(days=i) for i in range(days_diff + 1)]
    
    # --- Article clicks/traffic generation ---
    
    # Base "Background" Noise
    daily_clicks = np.random.randint(10, 100, size=len(date_range)).astype(float)
    
    # the usual initial viral spike
    initial_spike_height = random.randint(1337, 67000)
    decay_rate = random.uniform(0.45, 0.75) # Randomized decay "stickiness"
    
    for i in range(len(date_range)):
        # Calculate exponential decay + add a bit of daily noise to the spike
        spike_val = initial_spike_height * (decay_rate ** i)
        noise = random.uniform(0.8, 1.2) # some jitter :D
        daily_clicks[i] += (spike_val * noise)
    
    # mini-Resurgences
    num_bumps = 0
    if days_diff > 14:
        num_bumps = random.randint(1, max(2, days_diff // 60))
        
    for _ in range(num_bumps):
        # Pick a day after the initial spike has settled
        if len(date_range) > 10:
            bump_day = random.randint(7, len(date_range)-1)
            # Make the bump significant: 10-30% of the original spike
            bump_height = initial_spike_height * random.uniform(0.1, 0.3)
            # Apply a smaller mini-decay for the bump itself (3-day effect)
            for j in range(3):
                if bump_day + j < len(date_range):
                    daily_clicks[bump_day + j] += bump_height * (0.5 ** j)

    daily_clicks = [max(0, int(c * random.uniform(0.95, 1.05))) for c in daily_clicks]

    clicks_df = pd.DataFrame({"Date": date_range, "Views": daily_clicks})
    
    # read time
    avg_read_time = random.uniform(0.4, 8.0) # Minutes
    conversion_rate = random.uniform(0.5, 6.9) # Percent
    
    # --- Mock Age Distribution ---
    age_groups = ['16-24', '25-34', '35-44', '45-54', '55-64', '65+']
    age_data = [random.randint(10, 100) for _ in age_groups]
    
    # ---- Mock Gender distribution ---
    male = random.randint(35, 60)
    female = random.randint(40, 65)
    total = male + female
    gender_counts = [male / total * 100, female / total * 100]
    gender_labels = ["Male", "Female"]
    
    # --- Mock device split ---
    r1 = random.randint(65, 80)
    r2 = random.randint(20, 30)
    r3 = max(2, 100 - (r1 + r2)) # Other (Tablet/Console)
    
    # Normalize exactly to 100% just in case
    total = r1 + r2 + r3
    device_data = {
        "Mobile": (r1 / total) * 100,
        "Desktop": (r2 / total) * 100,
        "Other": (r3 / total) * 100
    }
    
    return {
        "views": sum(daily_clicks),
        "clicks_df": clicks_df,
        "read_time": avg_read_time,
        "conversions": conversion_rate,
        "age_data": pd.DataFrame({"Age Group": age_groups, "Readers": age_data}),
        "gender_data": {"labels": gender_labels, "counts": gender_counts},
        "device_data": device_data
    }