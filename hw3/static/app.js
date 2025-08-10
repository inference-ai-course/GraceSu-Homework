async function fetchHistory() {
    const res = await fetch('/history/');
    const history = await res.json();
    const historyDiv = document.getElementById('history');
    historyDiv.innerHTML = '';
    history.forEach(turn => {
        const p = document.createElement('p');
        p.className = turn.role;
        const titleCasedRole = turn.role.charAt(0).toUpperCase() + turn.role.slice(1).toLowerCase();
        p.innerHTML = `<strong>${titleCasedRole}</strong>: ${turn.content}`;
        historyDiv.appendChild(p);
    });
}

document.getElementById('audioForm').onsubmit = async (e) => {
    e.preventDefault();
    const input = document.getElementById('audioInput');
    if (!input.files.length) return;
    const formData = new FormData();
    formData.append('file', input.files[0]);
    
    // Create audio URL for input file preview
    const inputAudioUrl = URL.createObjectURL(input.files[0]);
    const inputAudio = document.getElementById('inputAudioPlayer');
    
    inputAudio.src = inputAudioUrl;
    // Auto-play the input audio
    inputAudio.play();
    
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
        
        // Check if any audio is currently playing
        const inputAudio = document.getElementById('inputAudioPlayer');
        const responseAudioContent = document.getElementById('responseAudioContent');
        const existingResponseAudio = responseAudioContent.querySelector('audio');
        
        // Create new response audio element
        const newResponseAudio = document.createElement('audio');
        newResponseAudio.controls = true;
        newResponseAudio.src = audioUrl;
        
        // Check if we need to wait for audio to finish
        if ((inputAudio && !inputAudio.paused) || (existingResponseAudio && !existingResponseAudio.paused)) {
            // Wait for current audio to finish, then play response
            const playResponseWhenReady = () => {
                newResponseAudio.play();
            };
            
            if (inputAudio && !inputAudio.paused) {
                inputAudio.addEventListener('ended', playResponseWhenReady, { once: true });
            }
            if (existingResponseAudio && !existingResponseAudio.paused) {
                existingResponseAudio.addEventListener('ended', playResponseWhenReady, { once: true });
            }
        } else {
            // No audio playing, start immediately
            newResponseAudio.autoplay = true;
        }
        
        // Add the new audio to the page
        responseAudioContent.innerHTML = '';
        responseAudioContent.appendChild(newResponseAudio);
        fetchHistory();
    } else {
        alert('Error: ' + res.statusText);
    }
}


// Microphone recording logic
// let mediaRecorder;
// let audioChunks = [];
// const micBtn = document.getElementById('micBtn');
// const micStatus = document.getElementById('micStatus');

// micBtn.onclick = async () => {
//     if (mediaRecorder && mediaRecorder.state === 'recording') {
//         mediaRecorder.stop();
//         micBtn.textContent = '🎤 Record';
//         micStatus.textContent = 'Stopped.';
//         return;
//     }
//     if (!navigator.mediaDevices) {
//         alert('Microphone not supported.');
//         return;
//     }
//     try {
//         const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
//         mediaRecorder = new MediaRecorder(stream);
//         audioChunks = [];
//         mediaRecorder.ondataavailable = e => {
//             if (e.data.size > 0) audioChunks.push(e.data);
//         };
//         mediaRecorder.onstop = async () => {
//             const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
//             // save to recording.wav
//             const formData = new FormData();
//             console.log("audioBlob", audioBlob);
//             formData.append('file', audioBlob, 'recording.wav');
//             await sendAudioAsForm(formData);
//         };
//         mediaRecorder.start();
//         micBtn.textContent = '⏹️ Stop';
//         micStatus.textContent = 'Recording...';
//     } catch (err) {
//         alert('Could not access microphone: ' + err);
//     }
// };

// Initial load
fetchHistory();
