// Wait for the DOM to be fully loaded before attaching event listeners
document.addEventListener('DOMContentLoaded', () => {

    // Get references to all the DOM elements we need
    const form = document.getElementById('crawl-form');
    const startUrlInput = document.getElementById('start-url');
    const crawlButton = document.getElementById('crawl-button');
    const buttonText = document.getElementById('button-text');
    const spinner = document.getElementById('spinner');
    const resultsContainer = document.getElementById('results-container');
    const statusMessage = document.getElementById('status-message');

    const API_URL = '/crawl'; 

    // --- Event Listener for Form Submission ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault(); 
        const startUrl = startUrlInput.value;

        if (!startUrl) {
            displayError("Please enter a valid URL.");
            return;
        }

        setLoading(true);
        resultsContainer.innerHTML = ''; 
        statusMessage.textContent = 'Crawling in progress... This may take a few minutes.';

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: startUrl }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! Status: ${response.status}`);
            }

            const results = await response.json();
            displayResults(results); // Call the new display function

        } catch (error) {
            console.error('Crawl failed:', error);
            displayError(error.message);
        } finally {
            setLoading(false);
        }
    });

    // --- Helper Functions ---

    function setLoading(isLoading) {
        if (isLoading) {
            crawlButton.disabled = true;
            crawlButton.classList.add('opacity-50', 'cursor-not-allowed');
            buttonText.textContent = 'Crawling...';
            spinner.classList.remove('hidden');
        } else {
            crawlButton.disabled = false;
            crawlButton.classList.remove('opacity-50', 'cursor-not-allowed');
            buttonText.textContent = 'Start Crawl';
            spinner.classList.add('hidden');
        }
    }

    function displayResults(results) {
        if (results.length === 0) {
            statusMessage.textContent = 'Crawl finished. No pages found or all pages failed to load.';
            return;
        }

        statusMessage.textContent = `Crawl finished. Processed ${results.length} URLs.`;
        const fragment = document.createDocumentFragment();
        
        results.forEach(item => {
            // Create the main card container
            const div = document.createElement('div');
            div.className = 'p-3 rounded-lg shadow-md border-l-4 break-words';
            
            // --- 1. Set Card Style based on Type ---
            let styleClasses = '';
            let statusText = `[${item.status}]`;

            // This is the color-coding you liked
            switch(item.type) {
                case 'Page':
                    styleClasses = 'bg-gray-800 border-green-500';
                    statusText = `[${item.status} OK]`;
                    break;
                case 'Blocked':
                    styleClasses = 'bg-yellow-900 border-yellow-500';
                    statusText = `[${item.status} BLOCKED]`;
                    break;
                case 'Error':
                    styleClasses = 'bg-red-900 border-red-500';
                    statusText = `[${item.status} ERROR]`;
                    break;
                case 'File':
                    styleClasses = 'bg-gray-700 border-gray-500';
                    statusText = `[${item.status} FILE]`;
                    break;
                case 'Redirect':
                    styleClasses = 'bg-blue-900 border-blue-500';
                    statusText = `[${item.status} REDIRECT]`;
                    break;
                default:
                    styleClasses = 'bg-gray-800 border-gray-500';
            }
            div.classList.add(...styleClasses.split(' '));

            // --- 2. Build the Card's Content ---
            
            // Status and Title Line
            const titleLine = document.createElement('div');
            titleLine.className = 'flex items-center space-x-2 mb-1';
            
            const statusSpan = document.createElement('span');
            statusSpan.className = 'font-mono font-bold text-sm';
            statusSpan.textContent = statusText;
            
            const titleSpan = document.createElement('span');
            titleSpan.className = 'font-semibold text-gray-100';
            titleSpan.textContent = item.title;
            
            titleLine.appendChild(statusSpan);
            titleLine.appendChild(titleSpan);

            // URL Link
            const link = document.createElement('a');
            link.href = item.url;
            link.textContent = item.url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.className = 'text-blue-400 hover:underline text-sm';

            // Note Line
            const noteLine = document.createElement('div');
            noteLine.className = 'text-gray-400 text-xs mt-2 italic';
            noteLine.textContent = `Note: ${item.note}`;
            
            // --- NEW: Tech Badges (CDN/WAF) ---
            const techLine = document.createElement('div');
            techLine.className = 'flex flex-wrap gap-2 mt-2'; // <-- TYPO IS FIXED HERE
            
            if (item.services) {
                // Add CDN Badge (Blue)
                if (item.services.cdn) {
                    const cdnBadge = document.createElement('span');
                    cdnBadge.className = 'text-xs bg-blue-700 text-blue-100 px-2 py-0.5 rounded-full';
                    cdnBadge.textContent = `CDN: ${item.services.cdn}`;
                    techLine.appendChild(cdnBadge);
                }
                // Add WAF/Security Badge (Red)
                if (item.services.waf) {
                    const wafBadge = document.createElement('span');
                    wafBadge.className = 'text-xs bg-red-700 text-red-100 px-2 py-0.5 rounded-full';
                    wafBadge.textContent = `Security: ${item.services.waf}`;
                    techLine.appendChild(wafBadge);
                }
            }
            
            // Assemble the card
            div.appendChild(titleLine);
            div.appendChild(link);
            if(item.note) {
                div.appendChild(noteLine);
            }
            if (item.services && (item.services.cdn || item.services.waf)) {
                div.appendChild(techLine);
            }
            
            fragment.appendChild(div);
        });

        resultsContainer.appendChild(fragment);
    }

    function displayError(message) {
        statusMessage.textContent = '';
        resultsContainer.innerHTML = `<div class="p-3 bg-red-900 text-red-100 rounded-lg border-l-4 border-red-500">${message}</div>`;
    }
});