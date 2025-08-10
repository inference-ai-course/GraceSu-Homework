async function fetchHistory() {
    const res = await fetch('/history/');
    const history = await res.json();
    console.log(res);
    console.log(history);
    const historyDiv = document.getElementById('history');
    historyDiv.innerHTML = '';
    history.forEach(turn => {
        const p = document.createElement('p');
        p.className = turn.role;
        console.log("turn", turn);
        console.log("turn.role", turn.role);
        console.log("turn.content", turn.content);
        p.textContent = `${turn.role}: ${turn.content}`;
        historyDiv.appendChild(p);
    });
}

document.getElementById('audioForm').onsubmit = async (e) => {
    e.preventDefault();
    const input = document.getElementById('audioInput');
    if (!input.files.length) return;
    const formData = new FormData();
    formData.append('file', input.files[0]);
    await sendAudioAsForm(formData);
};

async function sendAudioAsForm(formData) {
    const res = await fetch('/chat/', {
        method: 'POST',
        body: formData
    });
    if (res.ok) {
        const blob = await res.blob();
        const audioUrl = URL.createObjectURL(blob);
        console.log("blob", blob);
        document.getElementById('responseAudio').innerHTML = `<audio controls src="${audioUrl}"></audio>`;
        fetchHistory();
    } else {
        alert('Error: ' + res.statusText);
    }
}


// Microphone recording logic
let mediaRecorder;
let audioChunks = [];
const micBtn = document.getElementById('micBtn');
const micStatus = document.getElementById('micStatus');

micBtn.onclick = async () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        micBtn.textContent = '🎤 Record';
        micStatus.textContent = 'Stopped.';
        return;
    }
    if (!navigator.mediaDevices) {
        alert('Microphone not supported.');
        return;
    }
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) audioChunks.push(e.data);
        };
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            // save to recording.wav
            const formData = new FormData();
            console.log("audioBlob", audioBlob);
            formData.append('file', audioBlob, 'recording.wav');
            await sendAudioAsForm(formData);
        };
        mediaRecorder.start();
        micBtn.textContent = '⏹️ Stop';
        micStatus.textContent = 'Recording...';
    } catch (err) {
        alert('Could not access microphone: ' + err);
    }
};

// Initial load
fetchHistory();
