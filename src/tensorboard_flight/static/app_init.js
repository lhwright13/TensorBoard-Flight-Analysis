// Flight Plugin App Initialization - External JS to avoid CSP violations

console.log('[Flight Plugin] Initializing app...');

// Wait for DOM to be ready
function initializeApp() {
  console.log('[Flight Plugin] DOM ready, checking for tensorboard_flight...');

  const root = document.getElementById('root');
  if (!root) {
    console.error('[Flight Plugin] Root element not found!');
    return;
  }

  if (window.tensorboard_flight) {
    console.log('[Flight Plugin] tensorboard_flight found, rendering app...');

    // Render the React app
    window.tensorboard_flight.render(root);

    // Fetch available runs and load the first one
    console.log('[Flight Plugin] Fetching runs...');
    fetch('/data/plugin/flight/runs')
      .then(response => {
        console.log('[Flight Plugin] Runs response status:', response.status);
        return response.json();
      })
      .then(data => {
        console.log('[Flight Plugin] Runs data:', data);

        if (data.runs && data.runs.length > 0) {
          const firstRun = data.runs[0].run;
          console.log('[Flight Plugin] Loading first run:', firstRun);

          // Fetch episodes for the first run
          fetch(`/data/plugin/flight/episodes?run=${encodeURIComponent(firstRun)}`)
            .then(response => response.json())
            .then(episodesData => {
              console.log('[Flight Plugin] Episodes data:', episodesData);

              if (episodesData.episodes && episodesData.episodes.length > 0) {
                const firstEpisode = episodesData.episodes[0];
                console.log('[Flight Plugin] Loading first episode:', firstEpisode.episode_id);

                // Fetch full episode data
                fetch(`/data/plugin/flight/episode_data?run=${encodeURIComponent(firstRun)}&episode_id=${encodeURIComponent(firstEpisode.episode_id)}`)
                  .then(response => response.json())
                  .then(episode => {
                    console.log('[Flight Plugin] Episode data loaded:', episode);

                    if (window.tensorboard_flight.loadEpisode) {
                      window.tensorboard_flight.loadEpisode(episode);
                      console.log('[Flight Plugin] Episode loaded into app');
                    }
                  })
                  .catch(err => console.error('[Flight Plugin] Error loading episode:', err));
              } else {
                console.log('[Flight Plugin] No episodes found for this run');
              }
            })
            .catch(err => console.error('[Flight Plugin] Error loading episodes:', err));
        } else {
          console.log('[Flight Plugin] No runs found');
        }
      })
      .catch(err => {
        console.error('[Flight Plugin] Error loading runs:', err);
        root.innerHTML = '<div class="loading" style="color: #ef4444;">Error: Could not load flight data</div>';
      });
  } else {
    console.error('[Flight Plugin] tensorboard_flight not found on window object');
    root.innerHTML = '<div class="loading" style="color: #ef4444;">Error: Flight plugin failed to load</div>';
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
