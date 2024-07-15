import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import API_BASE_URL from './config';
import AvailableDatabases from './AvailableDatabases';

function App() {
    const [file, setFile] = useState(null);
    const [question, setQuestion] = useState("");
    const [response, setResponse] = useState(null);
    const [fileName, setFileName] = useState("");  // New state for the file name
    const [selectedDatabases, setSelectedDatabases] = useState([]);
    const [databases, setDatabases] = useState([]);

    const handleFileChange = (e) => {
        const chosenFile = e.target.files[0];
        setFile(chosenFile);
        setFileName(chosenFile ? chosenFile.name : "");  // Set the file name state
    };

    const handleFileUpload = async () => {
        const formData = new FormData();
        formData.append('file', file);

        const res = await axios.post(`${API_BASE_URL}/upload/`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });

        setResponse(res.data);
        // Fetch databases again after file upload
        fetchDatabases();
    };

    const handleQuestionChange = (e) => {
        setQuestion(e.target.value);
    };

    const handleQuery = async () => {
        // Check if at least one database is selected
        if (selectedDatabases.length === 0) {
            setResponse({ error: 'Please select at least one database.' });
            return;
        }

        // Query the backend with the question and selected databases
        const res = await axios.post(`${API_BASE_URL}/query/`, {
            question,
            databases: selectedDatabases
        });

        // Clean the response
        const cleanedResponse = res.data.answer
            .replace(/\*\*/g, '') // Remove '**'
            .replace(/\\n/g, ''); // Remove '\n'

        setResponse({ question: res.data.question, answer: cleanedResponse });
    };

    const fetchDatabases = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/vector-databases`, { timeout: 30000 }); // 30 seconds timeout
            console.log("Fetched databases:", response.data);
            setDatabases(response.data);
        } catch (error) {
            console.error("Error fetching databases:", error);
        }
    };

    useEffect(() => {
        fetchDatabases();
    }, []);

    return (
        <div className="App">
            <h1>Ask Charlie About Your Documents</h1> {/* Add your title here */}
            <h1>Upload Document</h1>

            <div className="button-container">
                <div className="file-upload">
                    <input id="file-input" type="file" onChange={handleFileChange} />
                    <label htmlFor="file-input" className="large-button">Choose File</label>
                </div>
                <button className="large-button" onClick={handleFileUpload}>Upload</button>
            </div>

            <AvailableDatabases onDatabasesChange={setSelectedDatabases} databases={databases} selectedDatabases={selectedDatabases} /> {/* Add this line */}
            {fileName && <p className="file-name">{fileName}</p>} {/* Display the file name */}
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
