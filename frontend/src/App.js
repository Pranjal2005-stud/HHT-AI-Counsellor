import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { RotateCcw } from 'lucide-react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isAssessmentComplete, setIsAssessmentComplete] = useState(false);
  const [conversationStarted, setConversationStarted] = useState(false);
  const [showDomainButtons, setShowDomainButtons] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState(false);
  const [showRoadmapOption, setShowRoadmapOption] = useState(false);
  const [roadmapData, setRoadmapData] = useState(null);
  const [showDetailedRoadmap, setShowDetailedRoadmap] = useState(false);
  const [detailedRoadmapData, setDetailedRoadmapData] = useState(null);
  const [isTTSEnabled, setIsTTSEnabled] = useState(false);
  const messagesEndRef = useRef(null);
  const hasInitialized = useRef(false);
  const speechRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    if (!hasInitialized.current) {
      hasInitialized.current = true;
      startConversation();
    }
  }, []);

  const addMessage = (content, sender, type = 'text', data = null) => {
    setMessages(prev => [...prev, { content, sender, type, data, timestamp: Date.now() }]);
  };

  const addTypedMessage = (content, sender, type = 'text', data = null) => {
    if (sender === 'assistant') {
      setIsTyping(true);
      setTimeout(() => {
        setIsTyping(false);
        setMessages(prev => [...prev, { content, sender, type, data, timestamp: Date.now() }]);
        // Trigger TTS for assistant messages
        if (isTTSEnabled && content && type === 'text') {
          speakText(content);
        }
      }, 1500); // Simulate thinking time
    } else {
      setMessages(prev => [...prev, { content, sender, type, data, timestamp: Date.now() }]);
    }
  };

  // TTS Functions
  const speakText = (text) => {
    if (!isTTSEnabled || !text) return;
    
    // Don't cancel ongoing speech, let it complete and queue the new one
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9; // Slightly slower for clarity
    utterance.pitch = 1.0; // Natural pitch
    utterance.volume = 0.8; // Comfortable volume
    
    // Store reference
    speechRef.current = utterance;
    
    // Speak the text (will queue automatically if another is speaking)
    window.speechSynthesis.speak(utterance);
  };

  const toggleTTS = () => {
    if (isTTSEnabled) {
      // Only stop speech when user manually disables TTS
      window.speechSynthesis.cancel();
    }
    setIsTTSEnabled(!isTTSEnabled);
  };

  // Stop speech when component unmounts
  useEffect(() => {
    return () => {
      if (speechRef.current) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const startConversation = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/start`);
      setSessionId(response.data.session_id);
      addMessage("Hello! I'm your HHT AI Counsellor. I'm here to assess your technical skills and provide personalized learning recommendations. What's your name?", 'assistant');
      setConversationStarted(true);
    } catch (error) {
      addMessage("Sorry, I'm having trouble connecting. Please make sure the backend server is running.", 'assistant');
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || !sessionId) return;

    // Cancel speech when user starts sending a message
    if (isTTSEnabled && speechRef.current) {
      window.speechSynthesis.cancel();
    }

    const userMessage = inputValue.trim();
    setInputValue('');
    addMessage(userMessage, 'user');

    try {
      const userMessageCount = messages.filter(m => m.sender === 'user').length + 1;
      
      if (userMessageCount <= 2) {
        await handlePersonalInfo(userMessage, userMessageCount);
      } else if (userMessageCount === 3) {
        // Handle manual domain input if buttons weren't used
        const validDomains = ['backend', 'frontend', 'data analytics', 'machine learning', 'devops', 'cybersecurity', 'data engineering', 'algorithms', 'dsa'];
        const userDomain = userMessage.toLowerCase();
        const isValidDomain = validDomains.some(domain => userDomain.includes(domain.toLowerCase()));
        
        if (isValidDomain) {
          await handleDomainSelection(userMessage);
        } else {
          addTypedMessage("Sorry, I haven't been trained yet to provide counselling on that domain. Please select from the available options.", 'assistant');
          setShowDomainButtons(true);
        }
      } else {
        await handleRegularMessage(userMessage);
      }
    } catch (error) {
      addMessage("I encountered an error processing your message. Please try again.", 'assistant');
    }
  };


  const handlePersonalInfo = async (message, count) => {
    // Extract name from greeting
    if (count === 1) {
      // Extract name from various formats
      let extractedName = message;
      const namePatterns = [
        /(?:hi|hello|hey),?\s*my name is\s+(.+)/i,
        /(?:hi|hello|hey),?\s*i'm\s+(.+)/i,
        /my name is\s+(.+)/i,
        /i'm\s+(.+)/i,
        /call me\s+(.+)/i,
        /(?:hi|hello|hey),?\s+(.+)/i
      ];
      
      for (const pattern of namePatterns) {
        const match = message.match(pattern);
        if (match) {
          extractedName = match[1].trim();
          break;
        }
      }
      
      // Validate name (2-50 chars, letters and spaces only)
      if (/^[a-zA-Z\s]{2,50}$/.test(extractedName) && extractedName.split(' ').length <= 3) {
        addTypedMessage(`Nice to meet you, ${extractedName}! What's your educational background?`, 'assistant');
      } else {
        addTypedMessage("I didn't catch your name clearly. Could you please tell me your name?", 'assistant');
      }
    } else if (count === 2) {
      const userMessages = messages.filter(m => m.sender === 'user');
      const nameMessage = userMessages[0]?.content || '';
      
      // Extract name from first message
      let name = nameMessage;
      const namePatterns = [
        /(?:hi|hello|hey),?\s*my name is\s+(.+)/i,
        /(?:hi|hello|hey),?\s*i'm\s+(.+)/i,
        /my name is\s+(.+)/i,
        /i'm\s+(.+)/i,
        /call me\s+(.+)/i,
        /(?:hi|hello|hey),?\s+(.+)/i
      ];
      
      for (const pattern of namePatterns) {
        const match = nameMessage.match(pattern);
        if (match) {
          name = match[1].trim();
          break;
        }
      }
      
      try {
        await axios.post(`${API_BASE_URL}/personal-info`, {
          session_id: sessionId,
          name,
          location: 'Not specified',
          education: message
        });
        
        addTypedMessage("Perfect! Now, which tech domain interests you most?", 'assistant');
        setShowDomainButtons(true);
      } catch (error) {
        addTypedMessage("Let's continue. Which tech domain interests you most?", 'assistant');
        setShowDomainButtons(true);
      }
    }
  };

  const handleDomainSelection = async (domain) => {
    // Cancel speech when user interacts
    if (isTTSEnabled && speechRef.current) {
      window.speechSynthesis.cancel();
    }
    
    setShowDomainButtons(false);
    addMessage(domain, 'user');
    setIsTyping(true);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/answer`, {
        session_id: sessionId,
        answer: domain
      });

      if (response.data.message) {
        addTypedMessage(response.data.message, 'assistant');
      }
      
      if (response.data.question) {
        setTimeout(() => {
          addTypedMessage(response.data.question, 'assistant');
        }, response.data.message ? 2000 : 0);
      }
    } catch (error) {
      addMessage("I had trouble understanding your domain selection. Please try selecting from the available options.", 'assistant');
    } finally {
      setIsTyping(false);
    }
  };

  const handleRegularMessage = async (message) => {
    try {
      if (isAssessmentComplete) {
        // Check if this is a roadmap response when roadmap option is shown
        if (showRoadmapOption) {
          const lowerMessage = message.toLowerCase().trim();
          const isYes = ['yes', 'y', 'yeah', 'yep', 'sure', 'definitely', 'ok', 'okay'].includes(lowerMessage);
          const isNo = ['no', 'n', 'nope', 'never', 'not really', 'nah'].includes(lowerMessage);
          
          if (isYes || isNo) {
            handleRoadmapRequest(isYes);
            return;
          }
        }
        
        // Check if this is feedback/suggestion
        if (!feedbackGiven && (message.toLowerCase().includes('feedback') || 
            message.toLowerCase().includes('suggestion') || 
            message.toLowerCase().includes('experience') ||
            message.length > 10)) { // Assume longer messages are feedback
          
          // Send feedback to backend for AI-enhanced response
          try {
            const response = await axios.post(`${API_BASE_URL}/feedback`, {
              session_id: sessionId,
              feedback: message
            });
            
            setFeedbackGiven(true);
            addTypedMessage(response.data.message, 'assistant');
            
            // Add documentation links if provided
            if (response.data.docs && response.data.docs.length > 0) {
              setTimeout(() => {
                addMessage('', 'assistant', 'docs', response.data.docs);
              }, 1500);
            }
            
            return;
          } catch (error) {
            // Fallback response if API fails
            setFeedbackGiven(true);
            addTypedMessage("Thank you so much for your valuable feedback! It helps us improve our service.", 'assistant');
            return;
          }
        }
        
        // Handle other post-assessment questions
        const response = await axios.post(`${API_BASE_URL}/chat`, {
          session_id: sessionId,
          message: message
        });
        addTypedMessage(response.data.message || response.data.reply, 'assistant');
        
        // Add documentation links if provided
        if (response.data.docs && response.data.docs.length > 0) {
          setTimeout(() => {
            addMessage('', 'assistant', 'docs', response.data.docs);
          }, 1500);
        }
      } else {
        const response = await axios.post(`${API_BASE_URL}/answer`, {
          session_id: sessionId,
          answer: message
        });

        if (response.data.completed) {
          setIsAssessmentComplete(true);
          addTypedMessage(response.data.message, 'assistant');
          setTimeout(() => {
            addMessage('', 'assistant', 'assessment', response.data.recommendations);
          }, 1500);
          setTimeout(() => {
            addTypedMessage("Feel free to ask me any questions about your results or how to improve your skills!", 'assistant');
          }, 2000);
          
          // Show roadmap option
          setTimeout(() => {
            setShowRoadmapOption(true);
            addTypedMessage("Would you like a detailed 5-week roadmap for your domain?", 'assistant', 'roadmap-option');
          }, 3500);
        } else {
          if (response.data.message && response.data.message !== "Got it!") {
            addTypedMessage(response.data.message, 'assistant');
          }
          if (response.data.question) {
            setTimeout(() => {
              addTypedMessage(response.data.question, 'assistant');
            }, response.data.message && response.data.message !== "Got it!" ? 2000 : 0);
          }
        }
      }
    } catch (error) {
      addTypedMessage("I had trouble processing your answer. Could you please try again?", 'assistant');
    }
  };

  const handleDetailedRoadmapRequest = async (domain) => {
    // Cancel speech when user interacts
    if (isTTSEnabled && speechRef.current) {
      window.speechSynthesis.cancel();
    }
    
    setShowDetailedRoadmap(false);
    addMessage(`Show me detailed ${domain} roadmap`, 'user');
    setIsTyping(true);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/detailed-roadmap`, {
        domain: domain.toLowerCase()
      });
      
      setDetailedRoadmapData(response.data);
      addTypedMessage(`Here's your comprehensive ${response.data.title}:`, 'assistant');
      setTimeout(() => {
        addMessage('', 'assistant', 'detailed-roadmap', response.data);
      }, 1500);
    } catch (error) {
      addTypedMessage("I had trouble generating your detailed roadmap. Please try again later.", 'assistant');
    } finally {
      setIsTyping(false);
    }
  };

  const downloadRoadmapPDF = async (domain) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/download-roadmap`, {
        domain: domain.toLowerCase()
      }, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${domain}_roadmap.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      addTypedMessage(`📄 ${domain} roadmap PDF downloaded successfully!`, 'assistant');
    } catch (error) {
      addTypedMessage("Sorry, I couldn't generate the PDF. Please try again later.", 'assistant');
    }
  };
  const handleRoadmapRequest = async (wantsRoadmap) => {
    // Cancel speech when user interacts
    if (isTTSEnabled && speechRef.current) {
      window.speechSynthesis.cancel();
    }
    
    setShowRoadmapOption(false);
    
    if (wantsRoadmap) {
      addMessage("Yes, I'd like a roadmap", 'user');
      setIsTyping(true);
      
      try {
        const response = await axios.post(`${API_BASE_URL}/detailed-roadmap`, {
          session_id: sessionId
        });
        
        setRoadmapData(response.data);
        addTypedMessage(`Here's your comprehensive roadmap:`, 'assistant');
        setTimeout(() => {
          addMessage('', 'assistant', 'detailed-roadmap', response.data);
        }, 1500);
        
        // Add feedback prompt after roadmap
        setTimeout(() => {
          addTypedMessage("How was your experience? Any suggestions or feedback would be greatly appreciated!", 'assistant');
        }, 3000);
      } catch (error) {
        addTypedMessage("I had trouble generating your roadmap. Please try again later.", 'assistant');
      } finally {
        setIsTyping(false);
      }
    } else {
      addMessage("No, I'll continue without a roadmap", 'user');
      // Add feedback prompt directly
      setTimeout(() => {
        addTypedMessage("How was your experience? Any suggestions or feedback would be greatly appreciated!", 'assistant');
      }, 500);
    }
  };

  const restartConversation = () => {
    // Stop any ongoing speech
    if (speechRef.current) {
      window.speechSynthesis.cancel();
    }
    
    setSessionId(null);
    setMessages([]);
    setInputValue('');
    setIsAssessmentComplete(false);
    setConversationStarted(false);
    setShowDomainButtons(false);
    setFeedbackGiven(false);
    setShowRoadmapOption(false);
    setShowDetailedRoadmap(false);
    setRoadmapData(null);
    setDetailedRoadmapData(null);
    hasInitialized.current = false;
    startConversation();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const renderMessage = (message, index) => {
    if (message.type === 'assessment') {
      return (
        <div key={index} className="message assistant">
          <div className="message-avatar">AI</div>
          <div className="message-content">
            <div className="assessment-result">
              <h3>Assessment Results</h3>
              <div className="level-badge">
                {message.data.level} Level in {message.data.domain}
              </div>
              <p><strong>Score:</strong> {message.data.score} ({message.data.percentage})</p>
              
              {message.data.level_description && (
                <div className="level-description">
                  {message.data.level_description}
                </div>
              )}
              
              {message.data.areas_to_improve && message.data.areas_to_improve.length > 0 && (
                <div className="areas-to-improve">
                  <h4>Areas to Improve:</h4>
                  {message.data.areas_to_improve.map((item, i) => (
                    <div key={i} className="improvement-item">
                      <strong>Q: {item.question}</strong>
                      <span>{item.explanation}</span>
                    </div>
                  ))}
                </div>
              )}
              
              {message.data.explanation && (
                <div style={{margin: '16px 0', lineHeight: '1.6', color: '#333'}}>
                  {message.data.explanation}
                </div>
              )}
              
              <div className="recommendations">
                <h3>Recommended Topics</h3>
                <ul>
                  {message.data.topics.map((topic, i) => (
                    <li key={i}>{topic}</li>
                  ))}
                </ul>
                
                <h3>Suggested Projects</h3>
                <ul>
                  {message.data.projects.map((project, i) => (
                    <li key={i}>{project}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      );
    }

    if (message.type === 'roadmap') {
      return (
        <div key={index} className="message assistant">
          <div className="message-avatar">AI</div>
          <div className="message-content">
            <div className="roadmap-result">
              <h3>5-Week {message.data.domain} Learning Roadmap</h3>
              {Object.entries(message.data.roadmap).map(([week, content]) => (
                <div key={week} className="roadmap-week">
                  <h4>{content.title}</h4>
                  <ul>
                    {content.topics.map((topic, i) => (
                      <li key={i}>{topic}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>
      );
    }

    if (message.type === 'detailed-roadmap') {
      return (
        <div key={index} className="message assistant">
          <div className="message-avatar">AI</div>
          <div className="message-content">
            <div className="detailed-roadmap-result">
              <h3>{message.data.title}</h3>
              <p><strong>Description:</strong> {message.data.description}</p>
              <p><strong>Prerequisites:</strong> {message.data.prerequisites}</p>
              <p><strong>Duration:</strong> {message.data.duration}</p>
              
              <div className="roadmap-steps">
                {message.data.steps.map((step, i) => (
                  <div key={i} className="roadmap-step">
                    <h4>Step {step.step}: {step.title}</h4>
                    <p><strong>Duration:</strong> {step.duration}</p>
                    
                    <div className="step-section">
                      <h5>Topics to Learn:</h5>
                      <ul>
                        {step.topics.map((topic, j) => (
                          <li key={j}>{topic}</li>
                        ))}
                      </ul>
                    </div>
                    
                    <div className="step-section">
                      <h5>Practice Projects:</h5>
                      <ul>
                        {step.projects.map((project, j) => (
                          <li key={j}>{project}</li>
                        ))}
                      </ul>
                    </div>
                    
                    <div className="step-section">
                      <h5>Learning Resources:</h5>
                      <div className="resources-list">
                        {step.resources.map((resource, j) => (
                          <a 
                            key={j} 
                            href={resource.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="resource-link"
                          >
                            {resource.title} →
                          </a>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="career-section">
                <h4>Career Opportunities:</h4>
                <ul>
                  {message.data.career_paths.map((career, i) => (
                    <li key={i}>{career}</li>
                  ))}
                </ul>
              </div>
              
              <div className="tips-section">
                <h4>Success Tips:</h4>
                <ul>
                  {message.data.tips.map((tip, i) => (
                    <li key={i}>{tip}</li>
                  ))}
                </ul>
              </div>
              
              <div className="download-section">
                <button 
                  className="download-pdf-button"
                  onClick={() => downloadRoadmapPDF(message.data.title.split(' ')[0])}
                >
                  📄 Download PDF Roadmap
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }
    if (message.type === 'docs') {
      return (
        <div key={index} className="message assistant">
          <div className="message-avatar">AI</div>
          <div className="message-content">
            <div className="docs-links">
              <h4>📚 Official Documentation & Resources:</h4>
              <div className="docs-list">
                {message.data.map((doc, i) => (
                  <a 
                    key={i} 
                    href={doc.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="doc-link"
                  >
                    {doc.title} →
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div key={index} className={`message ${message.sender}`}>
        <div className="message-avatar">
          {message.sender === 'user' ? 'You' : 'AI'}
        </div>
        <div className="message-content">
          {message.content}
          {message.sender === 'assistant' && showDomainButtons && index === messages.length - 1 && (
            <div className="domain-buttons">
              {['Backend', 'Frontend', 'Data Analytics', 'Machine Learning', 'DevOps', 'Cybersecurity', 'Data Engineering', 'Algorithms'].map((domain) => (
                <button
                  key={domain}
                  className="domain-button"
                  onClick={() => handleDomainSelection(domain.toLowerCase())}
                >
                  {domain}
                </button>
              ))}
            </div>
          )}
          {message.type === 'roadmap-option' && showRoadmapOption && index === messages.length - 1 && (
            <div className="roadmap-buttons">
              <button
                className="roadmap-button yes"
                onClick={() => handleRoadmapRequest(true)}
              >
                Yes, show me the roadmap
              </button>
              <button
                className="roadmap-button no"
                onClick={() => handleRoadmapRequest(false)}
              >
                No, continue without roadmap
              </button>
            </div>
          )}
          {message.type === 'detailed-roadmap-option' && showDetailedRoadmap && index === messages.length - 1 && (
            <div className="detailed-roadmap-buttons">
              {['Frontend', 'Backend', 'Data Analytics', 'Machine Learning', 'DevOps', 'Cybersecurity', 'Data Engineering', 'Algorithms'].map((domain) => (
                <button
                  key={domain}
                  className="detailed-roadmap-button"
                  onClick={() => handleDetailedRoadmapRequest(domain)}
                >
                  {domain} Roadmap
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="header-content">
          <img src="/Logo.png?v=1" alt="HHT Logo" className="header-logo" />
          <h1 className="header-title">HHT AI Counsellor</h1>
        </div>
        {sessionId && (
          <button className="restart-button" onClick={restartConversation} title="Restart Conversation">
            <RotateCcw size={20} />
          </button>
        )}
      </div>
      
      <div className="chat-messages">
        {messages.map((message, index) => renderMessage(message, index))}
        
        {isTyping && (
          <div className="message assistant">
            <div className="message-avatar">AI</div>
            <div className="typing-indicator">
              <div className="typing-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <button
            className={`tts-toggle ${isTTSEnabled ? 'active' : ''}`}
            onClick={toggleTTS}
            title={isTTSEnabled ? 'Disable Text-to-Speech' : 'Enable Text-to-Speech'}
          >
            {isTTSEnabled ? '🔊' : '🔇'}
          </button>
          <textarea
            className="chat-input"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            rows={1}
            disabled={!sessionId}
          />
          <button
            className="send-button"
            onClick={sendMessage}
            disabled={!inputValue.trim() || !sessionId || isTyping}
          >
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;