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
    const [filePath, setFilePath] = useState("");  // New state for the file path

    const [downloadPathMessage, setDownloadPathMessage] = useState(""); 
    const [isFileReady, setIsFileReady] = useState(false);  // New state to check if file is ready for download
    const [selectedDatabases, setSelectedDatabases] = useState([]);
    const [databases, setDatabases] = useState([]);
    const [promptTemplates, setPromptTemplates] = useState([]);
    const [selectedTemplate, setSelectedTemplate] = useState("");
    const [loading, setLoading] = useState(false);


    const fetchDatabases = async () => {
        const response = await axios.get(`${API_BASE_URL}/vector-databases`);
        console.log("Fetched databases:", response.data);
        setDatabases(response.data);
    };
    
    const handleDatabaseDelete = (deletedDatabase) => {
        setDatabases(databases.filter(database => database !== deletedDatabase));
    };
    

    const fetchPromptTemplates = async () => {
        const response = await axios.get(`${API_BASE_URL}/prompt-templates`);
        console.log("Fetched prompt templates:", response.data);
        setPromptTemplates(response.data);
    };


    /* eslint-disable react-hooks/exhaustive-deps */
    useEffect(() => {
        fetchDatabases();
        fetchPromptTemplates();
    }, []);
    /* eslint-enable react-hooks/exhaustive-deps */
   
    const handleFileChange = (e) => {
        console.log("handle FileChange called");
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
        if (selectedDatabases.length === 0) {
            setResponse({ error: 'Please select at least one database.' });
            return;
        }

        if (!selectedTemplate) {
            setResponse({ error: 'Please select a prompt template.' });
            return;
        }

        setLoading(true);
        setResponse(null);
        console.log("Submitting query:", question, selectedDatabases, selectedTemplate);

        try {
            const res = await axios.post(`${API_BASE_URL}/query/`, {
                question,
                databases: selectedDatabases,
                template: selectedTemplate
            });

            console.log("Query returned. ", res.data);


            /* determine if selectedTemplate is one of: "SuperLong" or "Tear Sheet" or "Long Form" or "One Page Current Events" or "Sector Overview" */
            
            if (selectedTemplate === "SuperLong" || selectedTemplate === "Tear Sheet" || selectedTemplate === "Long Form" || selectedTemplate === "One Page Current Events" || selectedTemplate === "Sector Overview") {
            
            
            /*if (selectedTemplate === "SuperLong" or selectedTemplate === "TearSheet") */
                // Handle the file download for SuperLong template
                let filePath = res.data.file_path;

                // Sanitize the file path
                filePath = filePath.replace(/['"]/g, "").trim().replace(/ /g, "_");

                setFilePath(filePath);  // Set the file path state
                setIsFileReady(true);   // Mark the file as ready for download
            } else {
                setResponse(res.data);
            }
        } catch (error) {
            console.error('Error handling query:', error);
            setResponse({ error: 'An error occurred while processing your request.' });
        }
        finally {
            setLoading(false);  // Set loading to false when query finishes
        }
    };


    
    
    const handleDownload = () => {
        const filename = filePath.split('/').pop(); // Extract the filename from the path
        const url = `${API_BASE_URL}/download?file_path=${encodeURIComponent(filePath)}`;
    
        console.log(`Download URL: ${url}`); // Log the URL to the console for verification
    
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename); // Set the dynamic filename here
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Set the download path message
        setDownloadPathMessage(`File downloaded to your default Downloads folder as: ${filename}`);
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
            <div className="status-container">
            {loading && <div className="status-message flashing">Working...</div>}
            {!loading && response && <div className="status-message">Done working</div>}
            </div> 
            <div className="button-container">
                <div className="file-upload">
                    <input id="file-input" type="file" onChange={handleFileChange} />
                    <label htmlFor="file-input" className="large-button">Choose File</label>
                </div>
                <button className="large-button" onClick={handleFileUpload}>Upload</button>
                {isFileReady && (
                    <button className="large-button" onClick={handleDownload}>Download Created File</button>
                )}
            </div>
            <div className="boxes-container">  {/* Add this container */}
                <AvailableDatabases onDatabasesChange={handleDatabaseChange} databases={databases} selectedDatabases={selectedDatabases} fetchDatabases={fetchDatabases}  onDatabaseDelete={handleDatabaseDelete} />
                <AvailablePromptTemplates onTemplateChange={handleTemplateChange} templates={promptTemplates} selectedTemplate={selectedTemplate} />
            </div>
            {fileName && <p className="file-name">{fileName}</p>}

            <h1>What do you want to do?</h1>
            <div className="query-container">
            <input type="text" value={question} onChange={handleQuestionChange} placeholder="Type your question" className="query-box" />
            <button className="large-button" onClick={handleQuery}>Ask</button>
            </div> 
            {response && (
                <div className="result-box">
                    <h2>Response</h2>
                    {response.error ? (
                        <p className="error">{response.error}</p>
                    ) : (
                        <>
                            <p><strong>Question:</strong> {response.question}</p>
                            <p><strong>Answer:</strong> {response.answer}</p>
                        </>
                    )}
                </div>
            )}
        </div>
    );
    
    
}

export default App;
