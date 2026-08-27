import { useState } from 'react'
import './App.css'

function App() {
  const [status, setStatus] = useState<string>('Idle');
  const [elementCount, setElementCount] = useState<number | null>(null);
  const [task, setTask] = useState<string>('');

  const processPage = async (actionType: "SEND_DOM_TO_AGENT" | "SEND_DOM_AND_ACT") => {
    setStatus(actionType === "SEND_DOM_TO_AGENT" ? 'Capturing Screen & DOM...' : 'Thinking with LLM...');
    
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (tab.id) {
      chrome.tabs.captureVisibleTab(tab.windowId, { format: 'png' }, (dataUrl) => {
        if (chrome.runtime.lastError) {
          console.error("Screenshot error:", chrome.runtime.lastError);
        }
        
        chrome.tabs.sendMessage(tab.id!, { action: "EXTRACT_DOM" }, (response) => {
          if (chrome.runtime.lastError) {
            setStatus('Error: ' + chrome.runtime.lastError.message);
            return;
          }
          
          if (response && response.domState) {
            setElementCount(response.domState.elements.length);
            setStatus(actionType === "SEND_DOM_TO_AGENT" ? 'Sending to Local Agent...' : 'LLM is Generating Plan...');
            
            if (dataUrl) response.domState.image_data = dataUrl;
            
            chrome.runtime.sendMessage({
              action: actionType,
              payload: response.domState,
              task: task
            }, (bgResponse) => {
              if (bgResponse && bgResponse.success) {
                if (actionType === "SEND_DOM_AND_ACT") {
                  setStatus(`Executing ${bgResponse.data.actions_executed} actions on page...`);
                  
                  // Forward the plan to the content script to execute it!
                  if (bgResponse.data.plan) {
                    chrome.tabs.sendMessage(tab.id!, { 
                      action: "EXECUTE_PLAN", 
                      plan: bgResponse.data.plan 
                    }, () => {
                      setStatus(`Success! AI Task Completed.`);
                    });
                  } else {
                    setStatus('Success! But no plan was returned.');
                  }
                } else {
                  setStatus(`Success! Processed ${bgResponse.data.elements_processed} elements & Visuals.`);
                }
              } else {
                setStatus('Error connecting to local agent.');
              }
            });
          }
        });
      });
    }
  };

  return (
    <div className="card">
      <h2>Privacy Gateway Agent</h2>
      <p>Status: {status}</p>
      {elementCount !== null && <p>Elements Found: {elementCount}</p>}
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '15px' }}>
        <button onClick={() => processPage("SEND_DOM_TO_AGENT")}>
          Perceive Page (Monitor Only)
        </button>
        
        <hr style={{ width: '100%', borderColor: 'rgba(255,255,255,0.1)', margin: '10px 0' }} />
        
        <input 
          type="text" 
          placeholder="What do you want the AI to do?" 
          value={task}
          onChange={(e) => setTask(e.target.value)}
          style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', color: '#000' }}
        />
        <button 
          onClick={() => processPage("SEND_DOM_AND_ACT")}
          style={{ background: '#3b82f6', color: 'white' }}
          disabled={!task}
        >
          Execute Task with LLM
        </button>
      </div>
    </div>
  )
}

export default App
