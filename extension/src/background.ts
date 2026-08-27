// Background script for Privacy Gateway Agent

chrome.runtime.onInstalled.addListener(() => {
  console.log("Privacy Gateway Agent installed.");
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "SEND_DOM_TO_AGENT") {
    // Forward DOM to local Python agent
    fetch("http://127.0.0.1:8000/api/v1/perceive", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(request.payload)
    })
    .then(response => response.json())
    .then(data => sendResponse({ success: true, data }))
    .catch(error => {
      console.error("Error communicating with local agent:", error);
      sendResponse({ success: false, error: error.message });
    });
    
    // Return true to indicate we wish to send a response asynchronously
    return true;
  }
  
  if (request.action === "SEND_DOM_AND_ACT") {
    const taskQuery = encodeURIComponent(request.task || "Fill the checkout form");
    fetch(`http://127.0.0.1:8000/api/v1/perceive_and_act?task=${taskQuery}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(request.payload)
    })
    .then(response => response.json())
    .then(data => sendResponse({ success: true, data }))
    .catch(error => {
      console.error("Error communicating with local agent:", error);
      sendResponse({ success: false, error: error.message });
    });
    
    return true;
  }
});
