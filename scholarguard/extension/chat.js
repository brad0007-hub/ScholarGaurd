(function(){
	const apiBase = window.SCHOLAR_GUARD_API || 'http://127.0.0.1:5000';
	const messagesEl = document.getElementById('messages');
	const resultsEl = document.getElementById('results');
	const form = document.getElementById('chat-form');
	const topicInput = document.getElementById('topic');
	const includeMixedInput = document.getElementById('includeMixed');

	function appendMessage(role, text){
		const div = document.createElement('div');
		div.className = `message ${role}`;
		div.textContent = text;
		messagesEl.appendChild(div);
		messagesEl.scrollTop = messagesEl.scrollHeight;
	}

	function badge(label){
		const l = (label||'mixed').toLowerCase();
		const div = document.createElement('span');
		div.className = `badge ${l}`;
		const dot = document.createElement('span');
		dot.className = 'dot';
		const txt = l === 'human' ? '🟢 Human' : (l === 'ai' ? '🔴 AI' : '🟠 Mixed');
		div.appendChild(dot);
		div.appendChild(document.createTextNode(` ${txt}`));
		return div;
	}

	function renderResults(items){
		resultsEl.innerHTML = '';
		if(!items || items.length === 0){
			const empty = document.createElement('div');
			empty.className = 'paper';
			empty.textContent = 'No results';
			resultsEl.appendChild(empty);
			return;
		}
		items.forEach(p => {
			const card = document.createElement('div');
			card.className = 'paper';
			const h3 = document.createElement('h3');
			h3.className = 'title';
			const link = document.createElement('a');
			link.href = p.link || '#';
			link.target = '_blank';
			link.rel = 'noopener noreferrer';
			link.textContent = p.title;
			h3.appendChild(link);
			const meta = document.createElement('div');
			meta.className = 'meta';
			meta.textContent = `${(p.authors||[]).join(', ')} • ${p.year||''}`;
			const summary = document.createElement('p');
			summary.textContent = p.summary || '';
			const b = badge(p.label);
			b.title = p.explanation || '';
			card.appendChild(h3);
			card.appendChild(meta);
			card.appendChild(b);
			card.appendChild(summary);
			resultsEl.appendChild(card);
		});
	}

	async function fetchPapers(topic, includeMixed){
		const url = new URL(apiBase + '/papers');
		if(topic) url.searchParams.set('topic', topic);
		url.searchParams.set('includeMixed', includeMixed ? 'true' : 'false');
		url.searchParams.set('limit', '8');
		const res = await fetch(url.toString());
		if(!res.ok) throw new Error('Request failed');
		return await res.json();
	}

	form.addEventListener('submit', async (e) => {
		e.preventDefault();
		const topic = topicInput.value.trim();
		const includeMixed = includeMixedInput.checked;
		appendMessage('user', topic || 'Top human-written papers');
		appendMessage('bot', 'Searching…');
		try{
			const data = await fetchPapers(topic, includeMixed);
			messagesEl.lastChild.textContent = `Found ${data.count} papers.`;
			renderResults(data.results);
		}catch(err){
			messagesEl.lastChild.textContent = 'Error fetching papers.';
		}
	});

	// Initial load
	fetchPapers('', false).then(d => {
		renderResults(d.results);
	}).catch(()=>{});
})();