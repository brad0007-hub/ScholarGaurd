(function(){
	const API = 'http://127.0.0.1:5000';
	const SCAN_INTERVAL_MS = 1500;
	let scanning = false;

	function classifyToBadge(label){
		const span = document.createElement('span');
		span.style.display = 'inline-flex';
		span.style.alignItems = 'center';
		span.style.gap = '6px';
		span.style.marginLeft = '8px';
		span.style.padding = '0 8px';
		span.style.borderRadius = '999px';
		span.style.fontSize = '12px';
		span.style.border = '1px solid rgba(0,0,0,0.15)';
		const dot = document.createElement('span');
		dot.style.width = '8px';
		dot.style.height = '8px';
		dot.style.borderRadius = '50%';
		let txt = '🟠 Mixed', color = '#f39c12', bg = 'rgba(243,156,18,0.08)';
		if(label === 'human'){ txt = '🟢 Human'; color = '#2ecc71'; bg = 'rgba(46,204,113,0.08)'; }
		if(label === 'ai'){ txt = '🔴 AI'; color = '#e74c3c'; bg = 'rgba(231,76,60,0.08)'; }
		dot.style.background = color;
		span.style.background = bg;
		span.style.color = color;
		span.appendChild(dot);
		span.appendChild(document.createTextNode(' '+txt));
		return span;
	}

	async function detect(title){
		try{
			const res = await fetch(API + '/detect', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ title })
			});
			if(!res.ok) return null;
			return await res.json();
		}catch(e){ return null; }
	}

	async function scan(){
		if(scanning) return; scanning = true;
		const items = document.querySelectorAll('div.gs_r.gs_or.gs_scl');
		await Promise.all(Array.from(items).map(async item => {
			if(item.dataset.sgProcessed) return;
			const titleEl = item.querySelector('h3.gs_rt');
			if(!titleEl) { item.dataset.sgProcessed = '1'; return; }
			const titleText = titleEl.textContent.trim();
			if(!titleText){ item.dataset.sgProcessed = '1'; return; }
			const res = await detect(titleText);
			if(res){
				const b = classifyToBadge((res.label||'mixed').toLowerCase());
				b.title = res.explanation || '';
				titleEl.appendChild(b);
			}
			item.dataset.sgProcessed = '1';
		}));
		scanning = false;
	}

	setInterval(scan, SCAN_INTERVAL_MS);
	document.addEventListener('visibilitychange', ()=>{ if(!document.hidden) scan(); });
	scan();
})();