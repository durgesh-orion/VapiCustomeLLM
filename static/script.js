document.addEventListener("DOMContentLoaded", async () => {
  const chatMessages = document.getElementById("chatMessages");
  const userInput = document.getElementById("userInput");
  const sendButton = document.getElementById("sendButton");
  const callButton = document.getElementById("callButton");
  const callStatus = document.getElementById("callStatus");
  const requestDetails = document.getElementById("requestDetails");
  const serverResponse = document.getElementById("serverResponse");
  const callLogs = document.getElementById("callLogs");

  let conversationHistory = [];
  let isCallActive = false;
  let vapi = null;

  // Vapi phone number - replace with your actual Vapi phone number
  const VAPI_PHONE_NUMBER = "+1234567890"; // Replace with your Vapi number

  // Initialize Vapi when needed
  async function initializeVapiInstance() {
    if (!vapi) {
      try {
        if (!window.VapiAI) {
          throw new Error(
            "VapiAI SDK not loaded. Please check script inclusion."
          );
        }
        vapi = new window.VapiAI("a2909ba7-1cc7-49bf-960a-326f74c491ca"); // Replace with your API key
        logOutput(callLogs, "Vapi client initialized successfully");
      } catch (error) {
        logOutput(callLogs, `Error initializing Vapi client: ${error.message}`);
        throw error;
      }
    }
    return vapi;
  }

  // Elements
  const transcript = document.getElementById("transcript");

  function addMessage(content, role) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${role}`;

    const messageContent = document.createElement("div");
    messageContent.className = "message-content";
    messageContent.textContent = content;

    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // Disable input and button while processing
    userInput.disabled = true;
    sendButton.disabled = true;

    // Add user message to chat
    addMessage(message, "user");

    // Add to conversation history
    conversationHistory.push({
      role: "user",
      content: message,
    });

    try {
      const response = await fetch("http://localhost:8000/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": "a2909ba7-1cc7-49bf-960a-326f74c491ca",
        },
        body: JSON.stringify({
          messages: conversationHistory,
        }),
      });

      const data = await response.json();

      if (data.messages && data.messages[0]) {
        const assistantMessage = data.messages[0].content;
        addMessage(assistantMessage, "assistant");

        // Add to conversation history
        conversationHistory.push({
          role: "assistant",
          content: assistantMessage,
        });
      }
    } catch (error) {
      console.error("Error:", error);
      addMessage(
        "Sorry, there was an error processing your request.",
        "assistant"
      );
    }

    // Clear and re-enable input
    userInput.value = "";
    userInput.disabled = false;
    sendButton.disabled = false;
    userInput.focus();
  }

  function logOutput(element, message) {
    const timestamp = new Date().toLocaleTimeString();
    element.innerHTML += `[${timestamp}] ${message}\n`;
    element.scrollTop = element.scrollHeight;
  }

  async function checkMicrophonePermission() {
    try {
      logOutput(callLogs, "Requesting microphone access...");
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (stream) {
        logOutput(callLogs, "Microphone access granted");
        return true;
      }
    } catch (error) {
      console.error("Microphone permission error:", error);
      logOutput(
        callLogs,
        "Error: Microphone access denied. Please enable microphone access in your browser settings."
      );
      return false;
    }
  }

  async function initializeCall() {
    try {
      logOutput(callLogs, "Initializing Vapi...");

      // Initialize Vapi instance
      vapi = await initializeVapiInstance();

      // Configure Vapi assistant
      await vapi.start({
        transcriber: {
          provider: "deepgram",
          model: "nova-2",
          language: "en-US",
        },
        model: {
          provider: "groq",
          model: "llama-3.3-70b-versatile",
          messages: [
            {
              role: "system",
              content: "You are a helpful AI assistant.",
            },
          ],
        },
        voice: {
          provider: "11labs",
          voiceId: "rachel", // Using a default 11labs voice
        },
      });

      // Set up event listeners
      vapi.on("message", (data) => {
        if (data.type === "transcript") {
          logOutput(transcript, `User: ${data.text}`);
        }
      });

      vapi.on("error", (error) => {
        logOutput(callLogs, `Error: ${error.message}`);
        resetCallState();
      });

      vapi.on("call-start", () => {
        logOutput(callLogs, "Call started successfully");
        callStatus.textContent = "Call in progress...";
      });

      vapi.on("call-end", () => {
        logOutput(callLogs, "Call ended");
        resetCallState();
      });

      vapi.on("speech-start", () => {
        logOutput(callLogs, "AI is speaking...");
      });

      vapi.on("speech-end", () => {
        logOutput(callLogs, "AI finished speaking");
      });

      return true;
    } catch (error) {
      console.error("Error initializing call:", error);
      logOutput(callLogs, `Error initializing call: ${error.message}`);
      return false;
    }
  }

  function resetCallState() {
    isCallActive = false;
    callButton.classList.remove("active");
    callButton.innerHTML = '<i class="fas fa-phone"></i> Start Call';
    callStatus.textContent = "";
  }

  async function toggleCall() {
    if (!isCallActive) {
      // Check microphone permission first
      const hasMicPermission = await checkMicrophonePermission();
      if (!hasMicPermission) {
        return;
      }

      // Start call
      isCallActive = true;
      callButton.classList.add("active");
      callButton.innerHTML = '<i class="fas fa-phone-slash"></i> End Call';
      callStatus.textContent = "Initializing call...";

      const success = await initializeCall();
      if (!success) {
        resetCallState();
      }
    } else {
      // End call
      try {
        callStatus.textContent = "Ending call...";
        await vapi.stop();
        resetCallState();
      } catch (error) {
        console.error("Error ending call:", error);
        logOutput(callLogs, `Error ending call: ${error.message}`);
      }
    }
  }

  // Event listeners
  callButton.addEventListener("click", toggleCall);

  sendButton.addEventListener("click", sendMessage);

  userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Initial log
  logOutput(callLogs, 'System ready. Click "Start Call" to begin.');
});
