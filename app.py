import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch, VerticalPitch
import warnings

warnings.filterwarnings('ignore')

# Define file paths for each league's shot data
LEAGUE_FILES = {
    'ENG-Premier League': 'epl_shots.csv',
    'ESP-La Liga': 'laliga_shots.csv',
    'FRA-Ligue 1': 'fra_shots.csv',
    'GER-Bundesliga': 'ger_shots.csv',
    'ITA-Serie A': 'ita_shots.csv'
}

# Load data for all leagues
all_shots_data = {}
for league, file_path in LEAGUE_FILES.items():
    try:
        df = pd.read_csv(file_path)
        # Add a 'league' column to identify the source league
        df['league'] = league
        all_shots_data[league] = df
    except FileNotFoundError:
        st.error(f"Error: '{file_path}' not found. Please make sure the data file is in the same directory.")
        st.stop()

# Combine all data into a single DataFrame
combined_shots_df = pd.concat(all_shots_data.values(), ignore_index=True)

# Handle missing values for columns used in filters
combined_shots_df['team'] = combined_shots_df['team'].fillna('Unknown')
combined_shots_df['player'] = combined_shots_df['player'].fillna('Unknown')
combined_shots_df['game'] = combined_shots_df['game'].fillna('Unknown')
combined_shots_df['situation'] = combined_shots_df['situation'].fillna('Unknown')
combined_shots_df['body_part'] = combined_shots_df['body_part'].fillna('Unknown')
combined_shots_df['result'] = combined_shots_df['result'].fillna('Unknown')


# Streamlit App
st.set_page_config(layout="wide")

st.sidebar.header("Filter Options")

# League Filter - Default to ENG-Premier League
leagues = sorted(combined_shots_df['league'].unique())
selected_league = st.sidebar.selectbox("Select League", leagues, index=leagues.index('ENG-Premier League'))

# Filter data based on selected league
filtered_by_league = combined_shots_df[combined_shots_df['league'] == selected_league].copy()

# Team Filter (dependent on selected league)
teams = sorted(filtered_by_league['team'].unique())
# Add "All" option and set it as default
teams_with_all = ['All'] + teams
selected_teams = st.sidebar.multiselect("Select Team(s)", teams_with_all, default=['All'])

# Filter data based on selected teams to populate subsequent filters
# If "All" is selected, use the DataFrame filtered by league, otherwise filter by selected teams
if 'All' in selected_teams:
    filtered_by_teams = filtered_by_league.copy()
else:
    filtered_by_teams = filtered_by_league[filtered_by_league['team'].isin(selected_teams)]

# Player Filter (dependent on selected teams)
all_players = sorted(filtered_by_teams['player'].unique())
selected_players = st.sidebar.multiselect("Select Player(s)", all_players)

# Match Filter (dependent on selected teams)
all_games = sorted(filtered_by_teams['game'].unique())
selected_games = st.sidebar.multiselect("Select Match(es)", all_games)

# Situation Filter (dependent on selected teams)
situations = sorted(filtered_by_teams['situation'].unique())
selected_situations = st.sidebar.multiselect("Select Situation(s)", situations)

# Body Part Filter (dependent on selected teams)
body_parts = sorted(filtered_by_teams['body_part'].unique())
selected_body_parts = st.sidebar.multiselect("Select Body Part(s)", body_parts)

# Result Filter (dependent on selected teams)
results = sorted(filtered_by_teams['result'].unique())
selected_results = st.sidebar.multiselect("Select Result(s)", results)


# Apply all filters
filtered_shots = filtered_by_teams.copy() # Start with data filtered by teams

if selected_players:
    filtered_shots = filtered_shots[filtered_shots['player'].isin(selected_players)]

if selected_games:
    filtered_shots = filtered_shots[filtered_shots['game'].isin(selected_games)]

if selected_situations:
    filtered_shots = filtered_shots[filtered_shots['situation'].isin(selected_situations)]

if selected_body_parts:
    filtered_shots = filtered_shots[filtered_shots['body_part'].isin(selected_body_parts)]

if selected_results:
     filtered_shots = filtered_shots[filtered_shots['result'].isin(selected_results)]

# Drop rows with missing values in plotting columns
filtered_shots = filtered_shots.dropna(subset=['location_x', 'location_y', 'xg', 'result'])

# Display total number of shots
st.sidebar.subheader("Total Shots")
st.sidebar.info(f"Number of shots: {len(filtered_shots)}")


# Check if filtered_shots is empty
if filtered_shots.empty:
    st.write("No shots match the selected filters.")
else:
    # Create a Pitch object
    pitch = Pitch(pitch_type='statsbomb',
                  pitch_color='grass', stripe=True, line_color='#c7d5cc')

    # Create a new figure and axes for the plot
    fig, ax = pitch.draw(figsize=(12, 8))

    # Define colors for each outcome
    result_colors = {
        'Goal': 'yellow',
        'Missed Shot': 'red',
        'Blocked Shot': 'gray',
        'Saved Shot': 'blue',
        'Shot On Post': 'orange',
        'Unknown': 'purple' # Added color for unknown result
    }

    # Scatter plot shots, colored by outcome
    scatter = pitch.scatter(filtered_shots['location_x'] * 120, filtered_shots['location_y'] * 80,
                            s=filtered_shots['xg'] * 1500,  # Scale marker size by xG, increased scaling factor
                            color=filtered_shots['result'].map(result_colors),  # Color by outcome
                            edgecolors='white', linewidth=1, alpha=0.7,
                            ax=ax)

    # Dynamic Title
    title_parts = ["Shot Map"]
    title_parts.append(f"for {selected_league}")
    if selected_teams and 'All' not in selected_teams:
        title_parts.append(f"({', '.join(selected_teams)})")
    if selected_players:
        title_parts.append(f"by {', '.join(selected_players)}")
    if selected_games:
        title_parts.append(f"in {', '.join(selected_games)}")
    if selected_situations:
        title_parts.append(f"from {', '.join(selected_situations)}")
    if selected_body_parts:
        title_parts.append(f"with {', '.join(selected_body_parts)}")
    if selected_results:
        title_parts.append(f"({', '.join(selected_results)})")


    plt.title(" ".join(title_parts))

    # Create a custom legend
    # Ensure only colors for results present in the filtered data are included
    present_results = filtered_shots['result'].unique()
    handles = [plt.Line2D([0], [0], marker='o', color='w', label=result,
                          markerfacecolor=result_colors.get(result, 'black'), markersize=10)
               for result in result_colors if result in present_results]


    plt.legend(handles=handles, title='Shot Result')
    st.pyplot(fig)
