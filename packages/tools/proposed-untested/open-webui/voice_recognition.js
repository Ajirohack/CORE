// Client-side script for voice recognition
const recognition = new webkitSpeechRecognition();
recognition.continuous = false;
recognition.interimResults = false;
recognition.lang = 'en-US';

recognition.start();

recognition.onresult = (event) => {
  const transcript = event.results[0][0].transcript;
  console.log('User said: ', transcript);
  // Send transcript to backend for AI processing
};
