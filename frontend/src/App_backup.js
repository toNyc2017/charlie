import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import API_BASE_URL from './config';  // Import the API base URL

function App() {
    const [file, setFile] = useState(null);
    const [question, setQuestion] = useState("");
    const [response, setResponse] = useState(null);

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
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
    };

    const handleQuestionChange = (e) => {
        setQuestion(e.target.value);
    };

    const handleQuery = async () => {
        const res = await axios.post(`${API_BASE_URL}/query/`, { question });

        setResponse(res.data);
    };

    return (
        <div className="App">
            <h1>Upload Document</h1>
            <input type="file" onChange={handleFileChange} />
            <button onClick={handleFileUpload}>Upload</button>
            <h1>Query Vector Index</h1>
            <input type="text" value={question} onChange={handleQuestionChange} placeholder="Type your question" />
            <button onClick={handleQuery}>Ask</button>
            {response && (
                <div>
                    <h2>Response</h2>
                    <pre>{JSON.stringify(response, null, 2)}</pre>
                </div>
            )}
        </div>
    );
}

export default App;
