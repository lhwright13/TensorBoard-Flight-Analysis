// Flight Plugin Test App - External JS to avoid CSP violations

document.addEventListener('DOMContentLoaded', () => {
  // Update time and location
  document.getElementById('time').textContent = new Date().toLocaleTimeString();
  document.getElementById('location').textContent = window.location.href;
  console.log('[Flight Plugin Test] Page loaded successfully!');

  // Add click handler for test button
  const button = document.querySelector('.test-button');
  if (button) {
    button.addEventListener('click', testAPI);
  }
});

function testAPI() {
  const resultDiv = document.getElementById('api-result');
  resultDiv.innerHTML = '<p>Testing API...</p>';

  fetch('/data/plugin/flight/runs')
    .then(response => response.json())
    .then(data => {
      resultDiv.innerHTML = `
        <div style="background: rgba(74, 222, 128, 0.2); padding: 15px; border-radius: 8px;">
          <strong>✓ API Working!</strong><br>
          Found ${data.runs ? data.runs.length : 0} run(s)
        </div>
      `;
      console.log('[Flight Plugin Test] API response:', data);
    })
    .catch(err => {
      resultDiv.innerHTML = `
        <div style="background: rgba(239, 68, 68, 0.2); padding: 15px; border-radius: 8px;">
          <strong>✗ API Error:</strong> ${err.message}
        </div>
      `;
      console.error('[Flight Plugin Test] API error:', err);
    });
}
