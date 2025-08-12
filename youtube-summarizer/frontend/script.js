document.getElementById('summarize-btn').addEventListener('click', async () => {
    const url = document.getElementById('youtube-url').value;
    if (!url) {
        alert('Please enter a YouTube URL.');
        return;
    }

    const summarizeBtn = document.getElementById('summarize-btn');
    const loader = document.getElementById('loader');
    
    summarizeBtn.disabled = true;
    summarizeBtn.textContent = 'Summarizing...';
    loader.style.display = 'block';
    document.getElementById('results').classList.add('hidden');

    try {
        // The fetch request now points to the same origin, so we can use a relative path.
        const response = await fetch('/api/summarize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url }),
        });

        const data = await response.json();

        if (!response.ok) {
            // Use the error message from the server if available
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }
        
        displayResults(data);

    } catch (error) {
        console.error('Fetch Error:', error);
        alert(`An error occurred: ${error.message}. Please check the console for more details.`);
    } finally {
        // This block runs whether the request succeeded or failed.
        summarizeBtn.disabled = false;
        summarizeBtn.textContent = 'Summarize';
        loader.style.display = 'none';
    }
});

function displayResults(data) {
    document.getElementById('summary-text').textContent = data.summary || 'No summary available.';
    
    const lessonsList = document.getElementById('lessons-list');
    lessonsList.innerHTML = '';
    if (Array.isArray(data.lessons)) {
        data.lessons.forEach(lesson => {
            const li = document.createElement('li');
            li.textContent = lesson;
            lessonsList.appendChild(li);
        });
    }

    document.getElementById('relevance-text').textContent = data.relevance || 'No relevance analysis available.';

    const learnList = document.getElementById('learn-list');
    learnList.innerHTML = '';
    if (Array.isArray(data.learn)) {
        data.learn.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            learnList.appendChild(li);
        });
    }

    document.getElementById('results').classList.remove('hidden');
}