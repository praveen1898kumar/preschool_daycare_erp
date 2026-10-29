/**
 * Browser-Native Voice-to-Text Observation Dictator
 * Uses HTML5 Web Speech API (Zero API Costs, No Google/Twilio subscriptions)
 */
class SpeechDictator {
  constructor(btnId, targetInputId, statusIndicatorId) {
    this.btn = document.getElementById(btnId);
    this.targetInput = document.getElementById(targetInputId);
    this.indicator = document.getElementById(statusIndicatorId);
    this.isListening = false;
    this.recognition = null;

    this.init();
  }

  init() {
    if (!this.btn || !this.targetInput) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      this.btn.classList.add('opacity-50', 'cursor-not-allowed');
      this.btn.title = "Speech recognition not supported in this browser";
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-IN'; // Indian English / general

    this.recognition.onstart = () => {
      this.isListening = true;
      this.btn.classList.add('bg-rose-500', 'text-white', 'animate-pulse');
      this.btn.classList.remove('bg-indigo-50', 'text-indigo-600');
      if (this.indicator) this.indicator.innerText = "Listening... Speak clearly";
      LittleMillennium.toast('Microphone Active', 'Dictate your classroom observation now', 'info');
    };

    this.recognition.onresult = (event) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }
      if (finalTranscript) {
        const currentVal = this.targetInput.value;
        this.targetInput.value = currentVal ? `${currentVal} ${finalTranscript}` : finalTranscript;
      }
    };

    this.recognition.onerror = (event) => {
      console.warn("Speech recognition error:", event.error);
      this.stop();
      LittleMillennium.toast('Voice Dictation', 'Microphone paused or permissions required', 'warning');
    };

    this.recognition.onend = () => {
      this.stop();
    };

    this.btn.addEventListener('click', (e) => {
      e.preventDefault();
      if (this.isListening) {
        this.stop();
      } else {
        this.start();
      }
    });
  }

  start() {
    try {
      this.recognition.start();
    } catch (e) {
      console.error(e);
    }
  }

  stop() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
    }
    this.isListening = false;
    this.btn.classList.remove('bg-rose-500', 'text-white', 'animate-pulse');
    this.btn.classList.add('bg-indigo-50', 'text-indigo-600');
    if (this.indicator) this.indicator.innerText = "";
  }
}

window.SpeechDictator = SpeechDictator;
