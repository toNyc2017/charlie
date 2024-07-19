import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import API_BASE_URL from './config';
import AvailableDatabases from './AvailableDatabases';
import AvailablePromptTemplates from './AvailablePromptTemplates';
import logo from './stamos-capital-white.png';  // Import the logo image

function App() {
    const [file, setFile] = useState(null);
    const [question, setQuestion] = useState("");
    const [response, setResponse] = useState(null);
    const [fileName, setFileName] = useState("");  // New state for the file name
    const [selectedDatabases, setSelectedDatabases] = useState([]);
    const [databases, setDatabases] = useState([]);
    const [promptTemplates, setPromptTemplates] = useState([]);
    const [selectedTemplate, setSelectedTemplate] = useState("");






    const fetchDatabases = async () => {
        const response = await axios.get(`${API_BASE_URL}/vector-databases`);
        console.log("Fetched databases:", response.data);
        setDatabases(response.data);
    };

    const fetchPromptTemplates = async () => {
        const response = await axios.get(`${API_BASE_URL}/prompt-templates`);
        console.log("Fetched prompt templates:", response.data);
        setPromptTemplates(response.data);
    };


    useEffect(() => {
        
        fetchDatabases();
        fetchPromptTemplates();
    }, []);

   
    const handleFileChange = (e) => {
        const chosenFile = e.target.files[0];
        setFile(chosenFile);
        setFileName(chosenFile ? chosenFile.name : "");  // Set the file name state
    };

    const handleFileUpload = async () => {
        console.log("handle File Upload called");
        const formData = new FormData();
        formData.append('file', file);

        const res = await axios.post(`${API_BASE_URL}/upload/`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });

        setResponse(res.data);
        console.log("File Upload Complete. about to fetch databases");
        fetchDatabases();
    };

    const handleQuestionChange = (e) => {
        setQuestion(e.target.value);
    };
    
    const handleQuery = async () => {
        console.log("handleQuery called");
        if (selectedDatabases.length === 0) {
            setResponse({ error: 'Please select at least one database.' });
            console.log("DATABASE ERROR");
            return;
        }
    
        if (!selectedTemplate) {
            
            setResponse({ error: 'Please select a prompt template.' });
            console.log("handleQuery TEMPLATE ERROR");
            return;
        }
    
        try {
            console.log("handleQuery CALLING ENDPOINT");
            const res = await axios.post(`${API_BASE_URL}/query/`, {
                question,
                databases: selectedDatabases,
                template: selectedTemplate
            });
    
            // Clean the response
            
            
            console.log("handleQuery ENDPOINT RETURNED. Response:", res.data);
            const cleanedResponse = res.data.answer
                .replace(/\*\*/g, '') // Remove '**'
                .replace(/\\n/g, ''); // Remove '\n'
            
            setResponse({ question: res.data.question, answer: cleanedResponse });
            
        } catch (error) {
            console.error("Error querying the backend:", error);
            setResponse({ error: 'An error occurred while querying the backend.' });
        }
    };
    

    const handleDatabaseChange = (newSelectedDatabases) => {
        console.log("handleDatabaseChange called");
        setSelectedDatabases(newSelectedDatabases);
    };

    const handleTemplateChange = (newSelectedTemplate) => {
        setSelectedTemplate(newSelectedTemplate);
    };

    return (
        <div className="App">
            <img src={logo} alt="Logo" className="logo" />  {/* Add the logo here */}
            <h1>Ask Stamos About Your Documents</h1>
            <h1>Upload Document</h1>
            <div className="button-container">
                <div className="file-upload">
                    <input id="file-input" type="file" onChange={handleFileChange} />
                    <label htmlFor="file-input" className="large-button">Choose File</label>
                </div>
                <button className="large-button" onClick={handleFileUpload}>Upload</button>
            </div>
            <div className="boxes-container">  {/* Add this container */}
                <AvailableDatabases onDatabasesChange={handleDatabaseChange} databases={databases} selectedDatabases={selectedDatabases} fetchDatabases={fetchDatabases} />
                <AvailablePromptTemplates onTemplateChange={handleTemplateChange} templates={promptTemplates} selectedTemplate={selectedTemplate} />
            </div>
            {fileName && <p className="file-name">{fileName}</p>}
            <h1>Query Vector Index</h1>
            <input type="text" value={question} onChange={handleQuestionChange} placeholder="Type your question" className="query-box" />
            <button className="large-button" onClick={handleQuery}>Ask</button>
            {response && (
                <div className="result-box">
                    <h2>Response</h2>
                    <p><strong>Question:</strong> {response.question}</p>
                    <p><strong>Answer:</strong> {response.answer}</p>
                </div>
            )}
        </div>
    );
}

export default App;
