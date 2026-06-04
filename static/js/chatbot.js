(function () {
  const chatbotWidget = document.getElementById("chatbotWidget");
  const chatbotToggle = document.getElementById("chatbotToggle");
  const chatbotClose = document.getElementById("chatbotClose");
  const chatbotForm = document.getElementById("chatbotForm");
  const chatbotInput = document.getElementById("chatbotInput");
  const chatbotMessages = document.getElementById("chatbotMessages");
  const chatbotFaqs = document.querySelectorAll(".chatbot-faqs button");

  if (!chatbotWidget) {
    return;
  }

  function addChatbotMessage(text, type) {
    const message = document.createElement("div");
    const paragraph = document.createElement("p");
    message.className = "chatbot-message " + type + "-message";
    paragraph.textContent = text;
    message.appendChild(paragraph);
    chatbotMessages.appendChild(message);
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
  }

  async function askBackend(message) {
    try {
      const response = await fetch("/api/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message }),
      });
      if (!response.ok) {
        return "Më vjen keq, serveri nuk u përgjigj. Provo më vonë.";
      }
      const data = await response.json();
      return data.response;
    } catch (err) {
      return "Më vjen keq, ka një problem me lidhjen me serverin.";
    }
  }

  chatbotToggle.addEventListener("click", () => {
    chatbotWidget.classList.toggle("is-open");
    if (chatbotWidget.classList.contains("is-open")) {
      chatbotInput.focus();
    }
  });

  chatbotClose.addEventListener("click", () => {
    chatbotWidget.classList.remove("is-open");
  });

  chatbotForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const userMessage = chatbotInput.value.trim();
    if (!userMessage) {
      return;
    }
    addChatbotMessage(userMessage, "user");
    chatbotInput.value = "";
    const reply = await askBackend(userMessage);
    addChatbotMessage(reply, "bot");
  });

  chatbotFaqs.forEach((button) => {
    button.addEventListener("click", async () => {
      const question = button.dataset.question;
      addChatbotMessage(question, "user");
      const reply = await askBackend(question);
      addChatbotMessage(reply, "bot");
    });
  });
})();
