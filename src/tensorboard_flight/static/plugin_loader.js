// TensorBoard plugin loader - find container in DOM and inject iframe

export function render(providedContainer) {
  console.log('[Flight Plugin] render() called with container:', providedContainer);

  // TensorBoard doesn't provide container, so we need to find it in the DOM
  // Look for the plugin container in the page
  let container = providedContainer;

  if (!container) {
    console.log('[Flight Plugin] No container provided, searching DOM...');

    // TensorBoard creates container AFTER calling render(), so we need to poll for it
    let attempts = 0;
    const maxAttempts = 50; // Try for 5 seconds

    const findAndInject = () => {
      attempts++;
      console.log(`[Flight Plugin] Search attempt ${attempts}/${maxAttempts}`);

      // Look for common TensorBoard plugin container patterns
      const selectors = [
        '[data-name="flight"]',
        '.flight-dashboard',
        '#flight-dashboard',
        '[class*="flight"]',
        '.tf-dashboard-container',
        '.tf-tensorboard-plugin-content',
        'tf-flight-dashboard',
        'paper-tabs + *', // Container after tabs
        'body > * > * > *' // Dive deeper into body
      ];

      for (const selector of selectors) {
        container = document.querySelector(selector);
        if (container && container !== document.body && container !== document.documentElement) {
          console.log('[Flight Plugin] Found container with selector:', selector, container);
          injectIframe(container);
          return;
        }
      }

      if (attempts < maxAttempts) {
        setTimeout(findAndInject, 100);
      } else {
        console.error('[Flight Plugin] Could not find plugin container after', maxAttempts, 'attempts!');
        console.log('[Flight Plugin] Body HTML:', document.body.innerHTML.substring(0, 1000));
        console.log('[Flight Plugin] All divs:', document.querySelectorAll('div'));

        // LAST RESORT: TensorBoard isn't creating a container, so use body directly
        console.log('[Flight Plugin] Injecting directly into document.body as last resort');
        injectIframe(document.body);
      }
    };

    // Start searching
    findAndInject();

    // Return a placeholder element for now
    const placeholder = document.createElement('div');
    placeholder.textContent = 'Loading Flight Plugin...';
    placeholder.style.padding = '20px';
    placeholder.style.background = '#f0f0f0';
    placeholder.style.border = '1px solid #ccc';
    return placeholder;
  }

  injectIframe(container);
}

function injectIframe(container) {
  console.log('[Flight Plugin] Injecting iframe into container:', container);

  // Clear any existing content
  container.innerHTML = '';

  // Create and style the iframe
  const iframe = document.createElement('iframe');
  iframe.src = '/data/plugin/flight/index.html';
  iframe.style.width = '100%';
  iframe.style.height = '800px';
  iframe.style.minHeight = '600px';
  iframe.style.border = 'none';
  iframe.style.display = 'block';

  console.log('[Flight Plugin] Created iframe with src:', iframe.src);

  iframe.onload = () => {
    console.log('[Flight Plugin] iframe loaded successfully!');
  };

  iframe.onerror = (e) => {
    console.error('[Flight Plugin] iframe failed to load:', e);
  };

  // Directly append iframe to the container
  container.appendChild(iframe);
  console.log('[Flight Plugin] Appended iframe to container');

  // Debug after 1 second
  setTimeout(() => {
    console.log('[Flight Plugin] iframe in document?', document.contains(iframe));
    console.log('[Flight Plugin] iframe parent:', iframe.parentElement);
  }, 1000);
}
