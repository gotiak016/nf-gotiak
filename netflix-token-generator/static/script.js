document.getElementById('cookieForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const resultDiv = document.getElementById('result');
    resultDiv.classList.remove('hidden');
    resultDiv.innerHTML = '<p>⏳ Checking cookies and generating token…</p>';

    try {
        const response = await fetch('/check', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (response.ok) {
            const links = data.links;
            resultDiv.innerHTML = `
                <p>✅ Cookies are valid!</p>
                <p><strong>NFToken:</strong> <code>${data.nftoken}</code></p>
                <h3>Login Links</h3>
                <ul>
                    <li><a href="${links.pc}" target="_blank" rel="noopener">💻 PC / Laptop</a></li>
                    <li><a href="${links.mobile}" target="_blank" rel="noopener">📱 Mobile / Phone</a></li>
                    <li><a href="${links.tv}" target="_blank" rel="noopener">📺 TV (tv8)</a></li>
                </ul>
                <p class="note">The token may expire. Use it immediately.</p>
            `;
        } else {
            resultDiv.innerHTML = `<p>❌ Error: ${data.error}</p>`;
        }
    } catch (err) {
        resultDiv.innerHTML = `<p>❌ Request failed: ${err.message}</p>`;
    }
});