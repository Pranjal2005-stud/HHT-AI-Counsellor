import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const API_BASE_URL = 'https://hht-ai-counsellor.onrender.com';

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
  const messagesEndRef = useRef(null);
  const hasInitialized = useRef(false);

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

    const userMessage = inputValue.trim();
    setInputValue('');
    addMessage(userMessage, 'user');
    setIsTyping(true);

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
          addMessage("Sorry, I haven't been trained yet to provide counselling on that domain. Please select from the available options.", 'assistant');
          setShowDomainButtons(true);
        }
      } else {
        await handleRegularMessage(userMessage);
      }
    } catch (error) {
      addMessage("I encountered an error processing your message. Please try again.", 'assistant');
    } finally {
      setIsTyping(false);
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
        addMessage(`Nice to meet you, ${extractedName}! What's your educational background?`, 'assistant');
      } else {
        addMessage("I didn't catch your name clearly. Could you please tell me your name?", 'assistant');
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
        
        addMessage("Perfect! Now, which tech domain interests you most?", 'assistant');
        setShowDomainButtons(true);
      } catch (error) {
        addMessage("Let's continue. Which tech domain interests you most?", 'assistant');
        setShowDomainButtons(true);
      }
    }
  };

  const handleDomainSelection = async (domain) => {
    setShowDomainButtons(false);
    addMessage(domain, 'user');
    setIsTyping(true);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/answer`, {
        session_id: sessionId,
        answer: domain
      });

      if (response.data.message) {
        addMessage(response.data.message, 'assistant');
      }
      
      if (response.data.question) {
        addMessage(response.data.question, 'assistant');
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
            addMessage(response.data.message, 'assistant');
            
            // Add documentation links if provided
            if (response.data.docs && response.data.docs.length > 0) {
              addMessage('', 'assistant', 'docs', response.data.docs);
            }
            
            return;
          } catch (error) {
            // Fallback response if API fails
            setFeedbackGiven(true);
            addMessage("Thank you so much for your valuable feedback! It helps us improve our service.", 'assistant');
            return;
          }
        }
        
        // Handle other post-assessment questions
        const response = await axios.post(`${API_BASE_URL}/chat`, {
          session_id: sessionId,
          message: message
        });
        addMessage(response.data.message || response.data.reply, 'assistant');
        
        // Add documentation links if provided
        if (response.data.docs && response.data.docs.length > 0) {
          addMessage('', 'assistant', 'docs', response.data.docs);
        }
      } else {
        const response = await axios.post(`${API_BASE_URL}/answer`, {
          session_id: sessionId,
          answer: message
        });

        if (response.data.completed) {
          setIsAssessmentComplete(true);
          addMessage(response.data.message, 'assistant');
          addMessage('', 'assistant', 'assessment', response.data.recommendations);
          addMessage("Feel free to ask me any questions about your results or how to improve your skills!", 'assistant');
          
          // Show roadmap option
          setTimeout(() => {
            setShowRoadmapOption(true);
            addMessage("Would you like a detailed 5-week roadmap for your domain?", 'assistant', 'roadmap-option');
          }, 1000);
        } else {
          if (response.data.message && response.data.message !== "Got it!") {
            addMessage(response.data.message, 'assistant');
          }
          if (response.data.question) {
            addMessage(response.data.question, 'assistant');
          }
        }
      }
    } catch (error) {
      addMessage("I had trouble processing your answer. Could you please try again?", 'assistant');
    }
  };

  const handleRoadmapRequest = async (wantsRoadmap) => {
    setShowRoadmapOption(false);
    
    if (wantsRoadmap) {
      addMessage("Yes, I'd like a roadmap", 'user');
      setIsTyping(true);
      
      try {
        const response = await axios.post(`${API_BASE_URL}/roadmap`, {
          session_id: sessionId
        });
        
        setRoadmapData(response.data.roadmap);
        addMessage(response.data.message, 'assistant');
        addMessage('', 'assistant', 'roadmap', response.data);
        
        // Add feedback prompt after roadmap
        setTimeout(() => {
          addMessage("How was your experience? Any suggestions or feedback would be greatly appreciated!", 'assistant');
        }, 1000);
      } catch (error) {
        addMessage("I had trouble generating your roadmap. Please try again later.", 'assistant');
      } finally {
        setIsTyping(false);
      }
    } else {
      addMessage("No, I'll continue without a roadmap", 'user');
      // Add feedback prompt directly
      setTimeout(() => {
        addMessage("How was your experience? Any suggestions or feedback would be greatly appreciated!", 'assistant');
      }, 500);
    }
  };

  const restartConversation = () => {
    setSessionId(null);
    setMessages([]);
    setInputValue('');
    setIsAssessmentComplete(false);
    setConversationStarted(false);
    setShowDomainButtons(false);
    setFeedbackGiven(false);
    setShowRoadmapOption(false);
    setRoadmapData(null);
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
        </div>
      </div>
    );
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="header-content">
          <img src="/Logo.png" alt="HHT Logo" className="header-logo" />
          <h1 className="header-title">HHT AI Counsellor</h1>
        </div>
        {conversationStarted && (
          <button className="restart-button" onClick={restartConversation} title="Restart Conversation">
            ⟲
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